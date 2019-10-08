
import sys

from src.main.conformanceArtefacts import ConformanceArtefacts

# last version is not updated for importer, mine is
sys.path.append('../pm4py-source')
from pm4py.objects.petri import importer
from pm4py.objects.log.importer.xes import factory as xes_importer
from pm4py.visualization.petrinet import factory as vizu

net, m0, mf = importer.pnml.import_net("./medium/CloseToM8.pnml")
log = xes_importer.import_log("./medium/CloseToM8.xes")


#vizu.apply(net,m0,mf).view()

artefacts= ConformanceArtefacts(6,13)
artefacts.multiAlignment(net,m0,mf,log)
print(artefacts.getRun())
print(artefacts.getTracesWithDistances())