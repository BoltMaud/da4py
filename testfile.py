from src.main.alignmentEditDistance import generalAlignmentEditDistance
from src.main.pnToFormulas import petri_net_to_SAT
from src.main.logToFormulas import log_to_SAT

from src.main import variablesGenerator as vg

# last version is not updated for importer, mine is
import sys
import os
sys.path.append('../pm4py-source')
from pm4py.objects.petri import importer
from pm4py.objects.log.importer.xes import factory as xes_importer
from pm4py.objects.conversion.log import factory as log_conv_fact


import timeit

##################################################################
### this is my developpement file
##################################################################

#vizu.apply(net, m0,mf).view()

'''
import pysat.solvers as SATSolvers

variables=vg.VariablesGenerator()
start=timeit.default_timer()
formulas = petri_net_to_SAT(net, m0,mf,variables,12)
nbVars=variables.iterator
cnf= formulas.clausesToCnf(nbVars)
simple=timeit.default_timer()
print("without simplification :",simple-start)


for name in ['cd','g3','g4','lgl','mcm','mcb','mpl','mc','m22','mgh']:
    debut=timeit.default_timer()
    solver = SATSolvers.Solver(name=name)
    solver.append_formula(cnf)
    print("\n",solver.solve())
    fin = timeit.default_timer()
    print(name,fin-debut)

'''
variables=vg.VariablesGenerator()

net, m0, mf = importer.pnml.import_net("../examples/AouC.pnml")
log = xes_importer.import_log("../examples/A.xes")


generalAlignmentEditDistance(net,m0,mf,log,3,max_d=3)
