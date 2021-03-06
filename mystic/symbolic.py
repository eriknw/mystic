#!/usr/bin/env python
#
# Author: Alta Fang (altafang @caltech and alta @princeton)
# Author: Mike McKerns (mmckerns @caltech and @uqfoundation)
# Copyright (c) 2010-2014 California Institute of Technology.
# License: 3-clause BSD.  The full license text is available at:
#  - http://trac.mystic.cacr.caltech.edu/project/mystic/browser/mystic/LICENSE
#
# originally coded by Alta Fang, 2010
# refactored by Mike McKerns, 2012
"""Tools for working with symbolic constraints.
"""
from __future__ import division

__all__ = ['linear_symbolic','replace_variables','get_variables','solve',
           'penalty_parser','constraints_parser','generate_conditions',
           'generate_solvers','generate_penalty','generate_constraint']

from numpy import ndarray, asarray
from _symbolic import solve
from mystic.tools import list_or_tuple_or_ndarray, flatten

# XXX: another function for the inverse... symbolic to matrix? (good for scipy)
def linear_symbolic(A=None, b=None, G=None, h=None):
    """Convert linear equality and inequality constraints from matrices to a 
symbolic string of the form required by mystic's constraint parser.

Inputs:
    A -- (ndarray) matrix of coefficients of linear equality constraints
    b -- (ndarray) vector of solutions of linear equality constraints
    G -- (ndarray) matrix of coefficients of linear inequality constraints
    h -- (ndarray) vector of solutions of linear inequality constraints

    NOTE: Must provide A and b; G and h; or A, b, G, and h;
          where Ax = b and Gx <= h. 

    For example:
    >>> A = [[3., 4., 5.],
    ...      [1., 6., -9.]]
    >>> b = [0., 0.]
    >>> G = [1., 0., 0.]
    >>> h = [5.]
    >>> print linear_symbolic(A,b,G,h)
    1.0*x0 + 0.0*x1 + 0.0*x2 <= 5.0
    3.0*x0 + 4.0*x1 + 5.0*x2 = 0.0
    1.0*x0 + 6.0*x1 + -9.0*x2 = 0.0
"""
    eqstring = ""
    # Equality constraints
    if A != None and b != None:
        # If one-dimensional and not in a nested list, add a list layer
        try:
            ndim = len(A[0])
        except:
            ndim = len(A)
            A = [A]

        # Flatten b, in case it's in the form [[0, 1, 2]] for example.
        if len(b) == 1:
            b = list(ndarray.flatten(asarray(b)))

        # Check dimensions and give errors if incorrect.
        if len(A) != len(b):
            raise Exception("Dimensions of A and b are not consistent.")

        # 'matrix multiply' and form the string
        for i in range(len(b)):
            Asum = ""
            for j in range(ndim):
                Asum += str(A[i][j]) + '*x' + str(j) + ' + '
            eqstring += Asum.rstrip(' + ') + ' = ' + str(b[i]) + '\n'

    # Inequality constraints
    ineqstring = ""
    if G != None and h != None:
        # If one-dimensional and not in a nested list, add a list layer
        try:
            ndim = len(G[0])
        except:
            ndim = len(G)
            G = [G]

        # Flatten h, in case it's in the form [[0, 1, 2]] for example.
        if len(h) == 1:
            h = list(ndarray.flatten(asarray(h)))

        # Check dimensions and give errors if incorrect.
        if len(G) != len(h):
            raise Exception("Dimensions of G and h are not consistent.")

        # 'matrix multiply' and form the string
        for i in range(len(h)):
            Gsum = ""
            for j in range(ndim):
                Gsum += str(G[i][j]) + '*x' + str(j) + ' + '
            ineqstring += Gsum.rstrip(' + ') + ' <= ' + str(h[i]) + '\n'
    totalconstraints = ineqstring + eqstring
    return totalconstraints 


def replace_variables(constraints, variables=None, markers='$'):
    """Replace variables in constraints string with a marker.
Returns a modified constraints string.

Inputs:
    constraints -- a string of symbolic constraints, with one constraint
        equation per line. Constraints can be equality and/or inequality
        constraints. Standard python syntax should be followed (with the
        math and numpy modules already imported).
    variables -- list of variable name strings. The variable names will
        be replaced in the order that they are provided, where if the
        default marker "$i" is used, the first variable will be replaced
        with "$0", the second with "$1", and so on.

    For example:
        >>> variables = ['spam', 'eggs']
        >>> constraints = '''spam + eggs - 42'''
        >>> print replace_variables(constraints, variables, 'x')
        'x0 + x1 - 42'

Additional Inputs:
    markers -- desired variable name. Default is '$'. A list of variable
        name strings is also accepted for when desired variable names
        don't have the same base.

    For example:
        >>> variables = ['x1','x2','x3']
        >>> constraints = "min(x1*x2) - sin(x3)"
        >>> print replace_variables(constraints, variables, ['x','y','z'])
        'min(x*y) - sin(z)'
"""
    if variables is None: variables = []
    elif isinstance(variables, str): variables = list((variables,))

    # substitite one list of strings for another
    if list_or_tuple_or_ndarray(markers):
        equations = replace_variables(constraints,variables,'_')
        vars = get_variables(equations,'_')
        indices = [int(v.strip('_')) for v in vars]
        for i in range(len(vars)):
            equations = equations.replace(vars[i],markers[indices[i]])
        return equations

    # Sort by decreasing length of variable name, so that if one variable name 
    # is a substring of another, that won't be a problem. 
    variablescopy = variables[:]
    def comparator(x, y):
        return len(y) - len(x)
    variablescopy.sort(comparator)

    # Figure out which index goes with which variable.
    indices = []
    for item in variablescopy:
        indices.append(variables.index(item))

    # Default is markers='$', as '$' is not a special symbol in Python,
    # and it is unlikely a user will choose it for a variable name.
    if markers in variables:
        marker = '_$$$$$$$$$$' # even less likely...
    else:
        marker = markers

    '''Bug demonstrated here:
    >>> equation = """x3 = max(y,x) + x"""
    >>> vars = ['x','y','z','x3']
    >>> print replace_variables(equation,vars)
    $4 = ma$1($2,$1) + $1
    ''' #FIXME: don't parse if __name__ in __builtins__, globals, or locals?
    for i in indices: #FIXME: or better, use 're' pattern matching
        constraints = constraints.replace(variables[i], marker + str(i))
    return constraints.replace(marker, markers)


def get_variables(constraints, variables='x'):
    """extract a list of the string variable names from constraints string

Inputs:
    constraints -- a string of symbolic constraints, with one constraint
        equation per line. Constraints can be equality and/or inequality
        constraints. Standard python syntax should be followed (with the
        math and numpy modules already imported).

    For example:
        >>> constraints = '''
        ...     x1 + x2 = x3*4
        ...     x3 = x2*x4'''
        >>> get_variables(constraints)
        ['x1', 'x2', 'x3', 'x4'] 

Additional Inputs:
    variables -- desired variable name. Default is 'x'. A list of variable
        name strings is also accepted for when desired variable names
        don't have the same base, and can include variables that are not
        found in the constraints equation string.

    For example:
        >>> constraints = '''              
        ...     y = min(u,v) - z*sin(x)
        ...     z = x**2 + 1.0 
        ...     u = v*z'''
        >>> get_variables(constraints, list('pqrstuvwxyz'))
        ['u', 'v', 'x', 'y', 'z']
"""
    if list_or_tuple_or_ndarray(variables):
        equations = replace_variables(constraints,variables,'_')
        vars = get_variables(equations,'_')
        indices = [int(v.strip('_')) for v in vars]
        varnamelist = []
        from numpy import sort
        for i in sort(indices):
            varnamelist.append(variables[i])
        return varnamelist

    import re
    target = variables+'[0-9]+'
    varnamelist = []
    equation_list = constraints.splitlines()
    for equation in equation_list:
        vars = re.findall(target,equation)
        for var in vars:
            if var not in varnamelist:
                varnamelist.append(var)
    return varnamelist


def penalty_parser(constraints, variables='x', nvars=None):
    """parse symbolic constraints into penalty constraints.
Returns a tuple of inequality constraints and a tuple of equality constraints.

Inputs:
    constraints -- a string of symbolic constraints, with one constraint
        equation per line. Constraints can be equality and/or inequality
        constraints. Standard python syntax should be followed (with the
        math and numpy modules already imported).

    For example:
        >>> constraints = '''
        ...     x2 = x0/2.
        ...     x0 >= 0.'''
        >>> penalty_parser(constraints, nvars=3)
        (('-(x[0] - (0.))',), ('x[2] - (x[0]/2.)',))

Additional Inputs:
    nvars -- number of variables. Includes variables not explicitly
        given by the constraint equations (e.g. 'x2' in the example above).
    variables -- desired variable name. Default is 'x'. A list of variable
        name strings is also accepted for when desired variable names
        don't have the same base, and can include variables that are not
        found in the constraints equation string.
    """
   #from mystic.tools import src
   #ndim = len(get_variables(src(func), variables))
    if list_or_tuple_or_ndarray(variables):
        if nvars != None: variables = variables[:nvars]
        constraints = replace_variables(constraints, variables)
        varname = '$'
        ndim = len(variables)
    else:
        varname = variables # varname used below instead of variables
        myvar = get_variables(constraints, variables)
        if myvar: ndim = max([int(v.strip(varname)) for v in myvar]) + 1
        else: ndim = 0
    if nvars != None: ndim = nvars

    # Parse the constraints string
    lines = constraints.splitlines()
    eqconstraints = []
    ineqconstraints = []
    for line in lines:
        if line.strip():
            fixed = line
            # Iterate in reverse in case ndim > 9.
            indices = list(range(ndim))
            indices.reverse()
            for i in indices:
                fixed = fixed.replace(varname + str(i), 'x[' + str(i) + ']') 
            constraint = fixed.strip()

            # Replace 'spread', 'mean', and 'variance' (uses numpy, not mystic)
            if constraint.find('spread(') != -1:
                constraint = constraint.replace('spread(', 'ptp(')
            if constraint.find('mean(') != -1:
                constraint = constraint.replace('mean(', 'average(')
            if constraint.find('variance(') != -1:
                constraint = constraint.replace('variance(', 'var(')

            # Sorting into equality and inequality constraints, and making all
            # inequality constraints in the form expression <= 0. and all 
            # equality constraints of the form expression = 0.
            split = constraint.split('>')
            direction = '>'
            if len(split) == 1:
                split = constraint.split('<')
                direction = '<'
            if len(split) == 1:
                split = constraint.split('=')
                direction = '='
            if len(split) == 1:
                print "Invalid constraint: ", constraint
            eqn = {'lhs':split[0].rstrip('=').strip(), \
                   'rhs':split[-1].lstrip('=').strip()}
            expression = '%(lhs)s - (%(rhs)s)' % eqn
            if direction == '=':
                eqconstraints.append(expression)
            elif direction == '<':
                ineqconstraints.append(expression)
            else:
                ineqconstraints.append('-(' + expression + ')')

    return tuple(ineqconstraints), tuple(eqconstraints)


def constraints_parser(constraints, variables='x', nvars=None):
    """parse symbolic constraints into a tuple of constraints solver equations.
The left-hand side of each constraint must be simplified to support assignment.

Inputs:
    constraints -- a string of symbolic constraints, with one constraint
        equation per line. Constraints can be equality and/or inequality
        constraints. Standard python syntax should be followed (with the
        math and numpy modules already imported).

    For example:
        >>> constraints = '''
        ...     x2 = x0/2.
        ...     x0 >= 0.'''
        >>> constraints_parser(constraints, nvars=3)
        ('x[2] = x[0]/2.', 'x[0] = max(0., x[0])')

Additional Inputs:
    nvars -- number of variables. Includes variables not explicitly
        given by the constraint equations (e.g. 'x2' in the example above).
    variables -- desired variable name. Default is 'x'. A list of variable
        name strings is also accepted for when desired variable names
        don't have the same base, and can include variables that are not
        found in the constraints equation string.
    """
   #from mystic.tools import src
   #ndim = len(get_variables(src(func), variables))
    if list_or_tuple_or_ndarray(variables):
        if nvars != None: variables = variables[:nvars]
        constraints = replace_variables(constraints, variables)
        varname = '$'
        ndim = len(variables)
    else:
        varname = variables # varname used below instead of variables
        myvar = get_variables(constraints, variables)
        if myvar: ndim = max([int(v.strip(varname)) for v in myvar]) + 1
        else: ndim = 0
    if nvars != None: ndim = nvars

    # Parse the constraints string
    lines = constraints.splitlines()
    parsed = [] #XXX: in penalty_parser is eqconstraints, ineqconstraints
    for line in lines:
        if line.strip():
            fixed = line
            # Iterate in reverse in case ndim > 9.
            indices = list(range(ndim))
            indices.reverse()
            for i in indices:
                fixed = fixed.replace(varname + str(i), 'x[' + str(i) + ']') 
            constraint = fixed.strip()

            # Replace 'ptp', 'average', and 'var' (uses mystic, not numpy)
            if constraint.find('ptp(') != -1:
                constraint = constraint.replace('ptp(', 'spread(')
            if constraint.find('average(') != -1:
                constraint = constraint.replace('average(', 'mean(')
            if constraint.find('var(') != -1:
                constraint = constraint.replace('var(', 'variance(')
            if constraint.find('prod(') != -1:
                constraint = constraint.replace('prod(', 'product(')

            #XXX: below this line the code is different than penalty_parser
            # convert "<" to min(LHS, RHS) and ">" to max(LHS,RHS)
            split = constraint.split('>')
            expression = '%(lhs)s = max(%(rhs)s, %(lhs)s)'
            if len(split) == 1: # didn't contain '>'
                split = constraint.split('<')
                expression = '%(lhs)s = min(%(rhs)s, %(lhs)s)'
            if len(split) == 1: # didn't contain '>' or '<'
                split = constraint.split('=')
                expression = '%(lhs)s = %(rhs)s'
            if len(split) == 1: # didn't contain '>', '<', or '='
                print "Invalid constraint: ", constraint
            eqn = {'lhs':split[0].rstrip('=').strip(), \
                   'rhs':split[-1].lstrip('=').strip()}
            expression = expression % eqn

            # allow mystic.math.measures impose_* on LHS
            lhs,rhs = expression.split('=')
            if lhs.find('spread(') != -1:
              lhs = lhs.split('spread')[-1]
              rhs = ' impose_spread( (' + rhs.lstrip() + '),' + lhs + ')'
            if lhs.find('mean(') != -1:
              lhs = lhs.split('mean')[-1]
              rhs = ' impose_mean( (' + rhs.lstrip() + '),' + lhs + ')'
            if lhs.find('variance(') != -1:
              lhs = lhs.split('variance')[-1]
              rhs = ' impose_variance( (' + rhs.lstrip() + '),' + lhs + ')'
            if lhs.find('sum(') != -1:
              lhs = lhs.split('sum')[-1]
              rhs = ' impose_sum( (' + rhs.lstrip() + '),' + lhs + ')'
            if lhs.find('product(') != -1:
              lhs = lhs.split('product')[-1]
              rhs = ' impose_product( (' + rhs.lstrip() + '),' + lhs + ')'
            expression = "=".join([lhs,rhs])

            parsed.append(expression)

    return tuple(parsed)


def generate_conditions(constraints, variables='x', nvars=None, locals=None):
    """generate penalty condition functions from a set of constraint strings

Inputs:
    constraints -- a string of symbolic constraints, with one constraint
        equation per line. Constraints can be equality and/or inequality
        constraints. Standard python syntax should be followed (with the
        math and numpy modules already imported).

    For example:
        >>> constraints = '''
        ...     x0**2 = 2.5*x3 - 5.0
        ...     exp(x2/x0) >= 7.0'''
        >>> ineqf,eqf = generate_conditions(constraints, nvars=4)
        >>> print ineqf[0].__doc__
        '-(exp(x[2]/x[0]) - (7.0))'
        >>> ineqf[0]([1,0,1,0])
        4.2817181715409554
        >>> print eqf[0].__doc__
        'x[0]**2 - (2.5*x[3] - 5.0)'
        >>> eqf[0]([1,0,1,0])
        6.0

Additional Inputs:
    nvars -- number of variables. Includes variables not explicitly
        given by the constraint equations (e.g. 'x2' in the example above).
    variables -- desired variable name. Default is 'x'. A list of variable
        name strings is also accepted for when desired variable names
        don't have the same base, and can include variables that are not
        found in the constraints equation string.
    locals -- a dictionary of additional variables used in the symbolic
        constraints equations, and their desired values.
    """
    ineqconstraints, eqconstraints = penalty_parser(constraints, \
                                      variables=variables, nvars=nvars)

    # default is globals with numpy and math imported
    globals = {}
    code = """from math import *; from numpy import *;"""
    code += """from numpy import mean as average;""" # use np.mean not average
   #code += """from mystic.math.measures import spread, variance, mean;"""
    code = compile(code, '<string>', 'exec')
    exec code in globals
    if locals is None: locals = {}
    globals.update(locals) #XXX: allow this?
    
    # build an empty local scope to exec the code and build the functions
    results = {'equality':[], 'inequality':[]}
    for funcs, conditions in zip(['equality','inequality'], \
                                 [eqconstraints, ineqconstraints]):
      for func in conditions:
        fid = str(id(func))
        fdict = {'name':fid, 'equation':func, 'container':funcs}
        # build the condition function
        code = """
def %(container)s_%(name)s(x): return eval('%(equation)s')
%(container)s_%(name)s.__name__ = '%(container)s'
%(container)s_%(name)s.__doc__ = '%(equation)s'""" % fdict
        #XXX: should locals just be the above dict of functions, or should we...
        # add the condition to container then delete the condition
        code += """
%(container)s.append(%(container)s_%(name)s)
del %(container)s_%(name)s""" % fdict
        code = compile(code, '<string>', 'exec')
        exec code in globals, results

    #XXX: what's best form to return?  will couple these with ptypes
    return tuple(results['inequality']), tuple(results['equality'])
   #return results


def generate_solvers(constraints, variables='x', nvars=None, locals=None):
    """generate constraints solver functions from a set of constraint strings

Inputs:
    constraints -- a string of symbolic constraints, with one constraint
        equation per line. Constraints can be equality and/or inequality
        constraints. Standard python syntax should be followed (with the
        math and numpy modules already imported). The left-hand side of
        each equation must be simplified to support assignment.

    For example:
        >>> constraints = '''
        ...     x2 = x0/2.
        ...     x0 >= 0.'''
        >>> solv = generate_solvers(constraints, nvars=3)
        >>> print solv[0].__doc__
        'x[2] = x[0]/2.'
        >>> solv[0]([1,2,3])
        [1, 2, 0.5]
        >>> print solv[1].__doc__
        'x[0] = max(0., x[0])'
        >>> solv[1]([-1,2,3])
        [0.0, 2, 3]

Additional Inputs:
    nvars -- number of variables. Includes variables not explicitly
        given by the constraint equations (e.g. 'x2' in the example above).
    variables -- desired variable name. Default is 'x'. A list of variable
        name strings is also accepted for when desired variable names
        don't have the same base, and can include variables that are not
        found in the constraints equation string.
    locals -- a dictionary of additional variables used in the symbolic
        constraints equations, and their desired values.
    """
    _constraints = constraints_parser(constraints, \
                                      variables=variables, nvars=nvars)

    # default is globals with numpy and math imported
    globals = {}
    code = """from math import *; from numpy import *;"""
    code += """from numpy import mean as average;""" # use np.mean not average
    code += """from mystic.math.measures import spread, variance, mean;"""
    code += """from mystic.math.measures import impose_spread, impose_mean;"""
    code += """from mystic.math.measures import impose_sum, impose_product;"""
    code += """from mystic.math.measures import impose_variance;"""
    code = compile(code, '<string>', 'exec')
    exec code in globals
    if locals is None: locals = {}
    globals.update(locals) #XXX: allow this?
    
    # build an empty local scope to exec the code and build the functions
    results = {'solver':[]}
    for func in _constraints:
        fid = str(id(func))
        fdict = {'name':fid, 'equation':func, 'container':'solver'}
        # build the condition function
        code = """
def %(container)s_%(name)s(x):
    '''%(equation)s'''
    exec('%(equation)s')
    return x
%(container)s_%(name)s.__name__ = '%(container)s'
""" % fdict #XXX: better, check if constraint satisfied... if not, then solve
        #XXX: should locals just be the above dict of functions, or should we...
        # add the condition to container then delete the condition
        code += """
%(container)s.append(%(container)s_%(name)s)
del %(container)s_%(name)s""" % fdict
        code = compile(code, '<string>', 'exec')
        exec code in globals, results

    #XXX: what's best form to return?  will couple these with ctypes ?
    return tuple(results['solver'])
   #return results


def generate_penalty(conditions, ptype=None, **kwds):
    """Converts a penalty constraint function to a mystic.penalty function.

Inputs:
    conditions -- a penalty constraint function, or list of constraint functions
    ptype -- a mystic.penalty type, or a list of mystic.penalty types
        of the same length as the given conditions

    For example:
        >>> constraints = '''
        ...     x2 = x0/2.
        ...     x0 >= 0.'''
        >>> ineqf,eqf = generate_conditions(constraints, nvars=3)
        >>> penalty = generate_penalty((ineqf,eqf))
        >>> penalty([1.,2.,0.])
        25.0
        >>> penalty([1.,2.,0.5])
        0.0

Additional Inputs:
    k -- penalty multiplier
    h -- iterative multiplier
"""
    # allow for single condition, list of conditions, or nested list
    if not list_or_tuple_or_ndarray(conditions):
        conditions = list((conditions,))
    else: pass #XXX: should be fine...
    conditions = list(flatten(conditions))

    # allow for single ptype, list of ptypes, or nested list
    if ptype is None:
        ptype = []
        from mystic.penalty import quadratic_equality, quadratic_inequality
        for condition in conditions:
            if 'inequality' in condition.__name__: 
                ptype.append(quadratic_inequality)
            else:
                ptype.append(quadratic_equality)
    elif not list_or_tuple_or_ndarray(ptype):
        ptype = list((ptype,))*len(conditions)
    else: pass #XXX: is already a list, should be the same len as conditions
    ptype = list(flatten(ptype))

    # iterate through penalties, building a compound penalty function
    pf = lambda x:0.0
    pfdoc = ""
    for penalty, condition in zip(ptype, conditions):
        pfdoc += "%s: %s\n" % (penalty.__name__, condition.__doc__)
        apply = penalty(condition, **kwds)
        pf = apply(pf)
    pf.__doc__ = pfdoc.rstrip('\n')
    pf.__name__ = 'penalty'
    return pf


def generate_constraint(conditions, ctype=None, **kwds):
    """Converts a constraint solver to a mystic.constraints function.

Inputs:
    conditions -- a constraint solver, or list of constraint solvers
    ctype -- a mystic.constraints type, or a list of mystic.constraints types
        of the same length as the given conditions

NOTES:
    This simple constraint generator doesn't check for conflicts in conditions,
    but simply applies conditions in the given order. This constraint generator
    assumes that a single variable has been isolated on the left-hand side
    of each constraints equation, thus all constraints are of the form
    "x_i = f(x)". This solver picks speed over robustness, and thus relies on
    the user to formulate the constraints so that they do not conflict.

    For example:
        >>> constraints = '''
        ...     x0 = cos(x1) + 2.
        ...     x1 = x2*2.'''
        >>> solv = generate_solvers(constraints)
        >>> constraint = generate_constraint(solv)
        >>> constraint([1.0, 0.0, 1.0])
        [1.5838531634528576, 2.0, 1.0]

    Standard python math conventions are used. For example, if an 'int'
    is used in a constraint equation, one or more variable may be evaluate
    to an 'int' -- this can affect solved values for the variables.

    For example:
        >>> constraints = '''
        ...     x2 = x0/2.
        ...     x0 >= 0.'''
        >>> solv = generate_solvers(constraints, nvars=3)
        >>> print solv[0].__doc__
        'x[2] = x[0]/2.'
        >>> print solv[1].__doc__
        'x[0] = max(0., x[0])'
        >>> constraint = generate_constraint(solv)
        >>> constraint([1,2,3])
        [1, 2, 0.5]
        >>> constraint([-1,2,-3])
        [0.0, 2, 0.0]
"""
    # allow for single condition, list of conditions, or nested list
    if not list_or_tuple_or_ndarray(conditions):
        conditions = list((conditions,))
    else: pass #XXX: should be fine...
    conditions = list(flatten(conditions))

    # allow for single ctype, list of ctypes, or nested list
    if ctype is None:
        from mystic.coupler import inner #XXX: outer ?
        ctype = list((inner,))*len(conditions)
    elif not list_or_tuple_or_ndarray(ctype):
        ctype = list((ctype,))*len(conditions)
    else: pass #XXX: is already a list, should be the same len as conditions
    ctype = list(flatten(ctype))

    # iterate through solvers, building a compound constraints solver
    cf = lambda x:x
    cfdoc = ""
    for wrapper, condition in zip(ctype, conditions):
        cfdoc += "%s: %s\n" % (wrapper.__name__, condition.__doc__)
        apply = wrapper(condition, **kwds)
        cf = apply(cf)
    cf.__doc__ = cfdoc.rstrip('\n')
    cf.__name__ = 'constraint'
    return cf


# EOF
