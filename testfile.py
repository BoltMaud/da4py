from src.main.alignmentEditDistance import alignmentEditDistance
from src.main import variablesGenerator as vg

# last version is not updated for importer, mine is
import sys

sys.path.append('../pm4py-source')
from pm4py.objects.petri import importer
from pm4py.objects.log.importer.xes import factory as xes_importer
from pm4py.visualization.petrinet import factory as vizu

net, m0, mf = importer.pnml.import_net("/Users/mboltenhagen/Documents/PhD/Josep&Thomas/model-loops/M8_petri_pnml.pnml")
log = xes_importer.import_log("./examples/M8.xes")

# net, m0, mf = importer.pnml.import_net("./examples/AouC.pnml")
# log = xes_importer.import_log("./examples/A.xes")

# vizu.apply(net,m0,mf).view()
alignmentEditDistance(net, m0, mf, log, 15, max_d=6)
