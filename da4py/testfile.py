import sys

from da4py.main import formulas
from da4py.main.conformanceArtefacts import ConformanceArtefacts
from pm4py.objects.petri import importer
from pm4py.objects.log.importer.xes import factory as xes_importer
from pm4py.visualization.petrinet import factory as vizu

# USE : python3 testfile.py model log size_of_run max_d distance out_putfile

# import the model and the log with pm4py
net, m0, mf = importer.pnml.import_net("/Users/mboltenhagen/Documents/PhD/Josep&Thomas/markovian-accuracy/artificial-logs-models/accepting-pns/fig1.apnml")
log = xes_importer.import_log("/Users/mboltenhagen/Documents/PhD/Josep&Thomas/markovian-accuracy/artificial-logs-models/accepting-pns/artificial.xes")

# visualize the model
#vizu.apply(net,m0,mf).view()

# create a conformanceArtefacts instance
artefacts= ConformanceArtefacts()
#artefacts.setSilentLabel("tau")
artefacts.setDistance_type("hamming")
#artefacts.setMax_nbTraces(3)
artefacts.setSize_of_run(10)
artefacts.setMax_d(22)
# do some antiAlingment
artefacts.antiAlignment(net,m0,mf,log)
print(artefacts.getRun())
print(artefacts.getTracesWithDistances())
print(artefacts.getPrecision())



