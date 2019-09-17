from darksider4py.formulas import Cnf_formula
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

net, m0, mf = importer.pnml.import_net("../examples/A.pnml")
#vizu.apply(net, m0,mf).view()
variables=vg.VariablesGenerator()
formulas = petri_net_to_SAT(net, m0,mf,variables,1)
print(variables.iterator)
print(formulas)
nbVars=variables.iterator
cnf= Cnf_formula(formulas.clausesToCnf(nbVars))
for t in cnf.listOfClauses:
    print(t)


from pysat.solvers import Glucose3
g = Glucose3()
for (a,b) in cnf.listOfClauses :
    list = a+[-1*b1 for b1 in b]
    g.add_clause(list)
print(g.solve())


