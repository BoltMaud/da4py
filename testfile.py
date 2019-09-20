from src.main.pnToFormulas import petri_net_to_SAT
from src.main import variablesGenerator as vg

# last version is not updated for importer, mine is
import sys
sys.path.append('../pm4py-source')
from pm4py.objects.petri import importer
import timeit

##################################################################
### this is my developpement file
##################################################################

net, m0, mf = importer.pnml.import_net("/Users/mboltenhagen/Documents/PhD/Josep&Thomas/model-loops/M1_petri_pnml.pnml")
#vizu.apply(net, m0,mf).view()


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

