import sys

from da4py.main.conformanceArtefacts import ConformanceArtefacts
from pm4py.objects.petri import importer
from pm4py.objects.log.importer.xes import factory as xes_importer
from pm4py.visualization.petrinet import factory as vizu

# USE : python3 testfile.py model log size_of_run max_d distance out_putfile

# import the model and the log with pm4py
net, m0, mf = importer.pnml.import_net("/Users/mboltenhagen/Documents/PhD/Farman/experimentation_Mathilde/ENFINSTATION3.pnml")
log = xes_importer.import_log("/Users/mboltenhagen/Documents/PhD/Farman/experimentation_Mathilde/STATION3_ACCEPTEDPARSED_INPUT_POSITIVE_sub.xes")

# visualize the model
vizu.apply(net,m0,mf).view()

# create a conformanceArtefacts instance
artefacts= ConformanceArtefacts(solver="g3")
artefacts.setSize_of_run(8)
artefacts.setMax_d(8)
artefacts.setSilentLabel(None)
artefacts.setDistance_type("edit")

# do some antiAlingment
artefacts.antiAlignment(net,m0,mf,log)
print(artefacts.getRun())
print(artefacts.getTracesWithDistances())

