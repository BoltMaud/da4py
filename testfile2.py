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

clustering = Amstc(net,m0,mf,log,4, 0,4,3,"tau")
print("Runtime",clustering.getTime())
for (centroid,traces) in clustering.getClustering():
    print(centroid, traces)
