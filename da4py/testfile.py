import sys
import os
from da4py.main import formulas
from da4py.main.conformanceArtefacts import ConformanceArtefacts
import pm4py.objects.petri.importer.factory as importer
from pm4py.objects.log.importer.xes import factory as xes_importer
from pm4py.visualization.petrinet import factory as vizu

model="/Users/mboltenhagen/Documents/PhD/Josep&Thomas/markovian-accuracy/artificial-logs-models/fig1.pnml"

traces="/Users/mboltenhagen/Documents/PhD/Josep&Thomas/markovian-accuracy/artificial-logs-models/accepting-pns/artificial.xes"

net, m0, mf = importer.pnml.import_net(model)
log = xes_importer.import_log(traces)

'''
vizu.apply(net,m0,mf).view()
artefacts= ConformanceArtefacts()
artefacts.setSilentLabel("tau")
artefacts.setDistance_type("edit")
artefacts.setSize_of_run(10)
artefacts.setMax_d(20)
# do some antiAlingment
artefacts.antiAlignment(net,m0,mf,log)
print("ANTI - HAMMING")
print(artefacts.getRun())
print(artefacts.getTracesWithDistances())
print(artefacts.getPrecision())
'''

artefacts= ConformanceArtefacts()
artefacts.setSilentLabel("tau")
artefacts.setDistance_type("hamming")
artefacts.setOptimizeSup(True)
artefacts.setSize_of_run(10)
artefacts.setMax_d(20)
# do some antiAlingment
artefacts.multiAlignment(net,m0,mf,log)
print("MULTI - EDIT")
print(artefacts.getRun())
print(artefacts.getTracesWithDistances())
#print(artefacts.getPrecision())

'''
net, m0, mf = importer.pnml.import_net(model)
log = xes_importer.import_log(traces)
artefacts= ConformanceArtefacts()
artefacts.setOptimizeSup(True)
artefacts.setSilentLabel("tau")
artefacts.setDistance_type("hamming")
artefacts.setSize_of_run(10)
artefacts.setMax_d(20)
# do some antiAlingment
artefacts.antiAlignment(net,m0,mf,log)
print("ANTI - EDIT")
print(artefacts.getRun())
print(artefacts.getTracesWithDistances())
#print(artefacts.getPrecision())
'''