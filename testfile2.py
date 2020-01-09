import sys
import time

from pm4py.objects.petri import importer
from pm4py.objects.log.importer.xes import factory as xes_importer


# import the model and the log with pm4py
from da4py.main.analytics.amstc import Amstc

net, m0, mf = importer.pnml.import_net("./examples/medium/model2.pnml")
from pm4py.visualization.petrinet import factory as vizu
#vizu.apply(net,m0,mf).view()
log = xes_importer.import_log("./examples/medium/model2bis.xes")

# visualize the model
#vizu.apply(net,m0,mf).view()

clustering = Amstc(net,m0,mf,log,7, 2,6,3,"tau")


clustering.testPrint()

# on veut un min de t par cluster mais un max de traces classifier pour une distance donné ?