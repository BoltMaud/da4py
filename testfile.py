from darksider4py.main.pn_to_formulas import petri_net_to_SAT
from darksider4py.main import variablesGenerator as vg

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


from pysat.solvers import Glucose3

variables=vg.VariablesGenerator()
start=timeit.default_timer()
formulas = petri_net_to_SAT(net, m0,mf,variables,12)
nbVars=variables.iterator
cnf= formulas.clausesToCnf(nbVars)
simple=timeit.default_timer()
print("without simplification :",simple-start)
g = Glucose3()
g.append_formula(cnf)
print(g.solve())
stop = timeit.default_timer()
print("solve",stop-simple)
print("total",stop-start)
