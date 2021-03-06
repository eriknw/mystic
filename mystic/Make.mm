# -*- Makefile -*-

PROJECT = mystic
PACKAGE = mystic

BUILD_DIRS = \
	
RECURSE_DIRS = $(BUILD_DIRS)

#--------------------------------------------------------------------------
#

all: export
	BLD_ACTION="all" $(MM) recurse

release: tidy
	cvs release .

update: clean
	cvs update .

#--------------------------------------------------------------------------
#
# export

EXPORT_PYTHON_MODULES = \
    __init__.py \
    _genSow.py \
    _scipy060optimize.py \
    _scipyoptimize.py \
    abstract_map_solver.py \
    abstract_nested_solver.py \
    abstract_solver.py \
    constraints.py \
    differential_evolution.py \
    filters.py \
    forward_model.py \
    helputil.py \
    linesearch.py \
    monitors.py \
    mystic_math.py \
    nested.py \
    python_map.py \
    scipy_optimize.py \
    solvers.py \
    strategy.py \
    termination.py \
    tools.py \
    munge.py \
    metropolis.py \
    scemtools.py \
    svmtools.py \
    svctools.py \

export:: export-python-modules

# End of file
