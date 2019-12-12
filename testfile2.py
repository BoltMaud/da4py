import sys
import time

from pm4py.objects.petri import importer
from pm4py.objects.log.importer.xes import factory as xes_importer


# import the model and the log with pm4py
from da4py.main.analytics.amstc import Amstc

net, m0, mf = importer.pnml.import_net("./examples/tiny/AouC.pnml")
from pm4py.visualization.petrinet import factory as vizu
#vizu.apply(net,m0,mf).view()
log = xes_importer.import_log("./examples/tiny/2trAB.xes")

# visualize the model
#vizu.apply(net,m0,mf).view()

clustering = Amstc(net,m0,mf,log,1, 2)


clustering.testPrint()

# on veut un min de t par cluster mais un max de traces classifier pour une distance donné ?