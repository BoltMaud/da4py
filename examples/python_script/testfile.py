import sys

from pm4py.objects.log.util.log import project_traces

from da4py.main.utils import formulas
from pm4py.objects.petri import importer
from pm4py.objects.log.importer.xes import factory as xes_importer
from da4py.main.conformanceChecking.conformanceArtefacts import ConformanceArtefacts
from pm4py.visualization.petrinet import factory as vizu


# USE : python3 testfile.py model log size_of_run max_d distance out_putfile


net, m0, mf = importer.factory.apply("../../examples/medium/model2.pnml")
log = xes_importer.apply("../../examples/medium/model2.xes")
artefacts=ConformanceArtefacts()
artefacts.setMax_d(14)
artefacts.setSize_of_run(8)
artefacts.setDistance_type("hamming")
artefacts.setSilentLabel(None)
artefacts.multiAlignment(net, m0, mf,log)
#print(artefacts.getPrecision())
print( artefacts.getRun())
print(artefacts.getTracesWithDistances())
