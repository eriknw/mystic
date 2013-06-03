#!/usr/bin/env python
#Adapted from parallel_desolve.py by mmckerns@caltech.edu

__doc__ = """
# Tests MP version of Storn and Price's Polynomial 'Fitting' Problem.
# 
# Exact answer: Chebyshev Polynomial of the first kind. T8(x)
  
# Reference:
#
# [1] Storn, R. and Price, K. Differential Evolution - A Simple and Efficient
# Heuristic for Global Optimization over Continuous Spaces. Journal of Global
# Optimization 11: 341-359, 1997.

# To run in parallel:  (must install 'pathos')
python mpmap_desolve.py
"""

try:
  from pathos.multiprocessing import ProcessingPool as Pool
except:
  print __doc__


from mystic.solvers import DifferentialEvolutionSolver2
from mystic.termination import ChangeOverGeneration, VTR
from mystic.strategy import Best1Exp
from mystic.monitors import VerboseMonitor
from mystic.tools import random_seed
from mystic.math import poly1d

#from raw_chebyshev8 import chebyshev8cost as ChebyshevCost     # no globals
#from raw_chebyshev8b import chebyshev8cost as ChebyshevCost    # use globals
from mystic.models.poly import chebyshev8cost as ChebyshevCost  # no helper

ND = 9
NP = 40
MAX_GENERATIONS = NP*NP
NNODES = NP/5

seed = 100


if __name__=='__main__':
    def print_solution(func):
        print poly1d(func)
        return

    psow = VerboseMonitor(10)
    ssow = VerboseMonitor(10)

    random_seed(seed)
    print "first sequential..."
    solver = DifferentialEvolutionSolver2(ND,NP)  #XXX: sequential
    solver.SetRandomInitialPoints(min=[-100.0]*ND, max=[100.0]*ND)
    solver.SetEvaluationLimits(generations=MAX_GENERATIONS)
    solver.SetGenerationMonitor(ssow)
    solver.Solve(ChebyshevCost, VTR(0.01), strategy=Best1Exp, \
                 CrossProbability=1.0, ScalingFactor=0.9, disp=1)
    print ""
    print_solution( solver.bestSolution )

    #'''
    random_seed(seed)
    print "\n and now parallel..."
    solver2 = DifferentialEvolutionSolver2(ND,NP)  #XXX: parallel
    solver2.SetMapper(Pool(NNODES).map)
    solver2.SetRandomInitialPoints(min=[-100.0]*ND, max=[100.0]*ND)
    solver2.SetEvaluationLimits(generations=MAX_GENERATIONS)
    solver2.SetGenerationMonitor(psow)
    solver2.Solve(ChebyshevCost, VTR(0.01), strategy=Best1Exp, \
                  CrossProbability=1.0, ScalingFactor=0.9, disp=1)
    print ""
    print_solution( solver2.bestSolution )
    #'''

# end of file
