import sys

from pm4py.objects.log.util.log import project_traces

from da4py.main.utils import formulas
from da4py.main.conformanceChecking.conformanceArtefacts import ConformanceArtefacts
from pm4py.objects.petri import importer
from pm4py.objects.log.importer.xes import factory as xes_importer

# USE : python3 testfile.py model log size_of_run max_d distance out_putfile

# import the model and the log with pm4py
net, m0, mf = importer.pnml.import_net("../examples/medium/model2.pnml")
log = xes_importer.import_log("../examples/medium/model2.xes")

# visualize the model
from pm4py.visualization.petrinet import factory as vizu
#vizu.apply(net,m0,mf).view()

# create a conformanceArtefacts instance
artefacts= ConformanceArtefacts()
artefacts.setSize_of_run(7)
artefacts.setMax_d(14)
#artefacts.setDistance_type(sys.argv[5])

# do some antiAlingment
#artefacts.antiAlignment(net,m0,mf,log)

#print( artefacts.getRun())
#print(artefacts.getTracesWithDistances())
#print(artefacts.getPrecision())

import pm4py.evaluation.replay_fitness.factory as fitness
print(project_traces(log))
print(fitness.apply(log,net,m0,mf,variant="alignments"))

import pm4py.algo.conformance.alignments.factory as ali
alignments= ali.apply(log,net,m0,mf)
for a in alignments:
    print(a)
