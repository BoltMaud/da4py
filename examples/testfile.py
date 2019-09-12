from darksider4py.pn_to_formulas import petri_net_to_SAT
from darksider4py import variablesGenerator as vg

# last version is not updated for importer, mine is
import sys
sys.path.append('../pm4py-source')
from pm4py.objects.petri import importer
from pm4py.visualization.petrinet import factory as vizu

##################################################################
### this is my developpement file
##################################################################

net, m0, mf = importer.pnml.import_net("../examples/dev.pnml")
#vizu.apply(net, m0,mf).view()
variables=vg.variablesGenerator()
formulas = petri_net_to_SAT(net, m0,mf,variables,10)
cnf= formulas.clausesToCnf(variables.iterator)

print(cnf.nbVars)
[print(t) for t in cnf.listOfClauses]
