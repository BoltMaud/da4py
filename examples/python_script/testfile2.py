import sys
import time
from pm4py.objects import petri
from pm4py.objects.log.log import EventStream
from pm4py.objects.petri import importer, check_soundness
from pm4py.objects.log.importer.xes import factory as xes_importer
# import the model and the log with pm4py
from pm4py.objects.petri.petrinet import PetriNet, Marking
import pm4py.algo.conformance.alignments.factory as alignments

from da4py.main.analytics.amstc import Amstc, samplingForAmstc

net_path= sys.argv[1]
log_path=sys.argv[2]
sampleSize=sys.argv[3]
sizeOfRun=sys.argv[4]
maxD=sys.argv[5]
maxNbC=sys.argv[6]
m=sys.argv[7]

net, m0, mf = importer.factory.apply(net_path)
from pm4py.visualization.petrinet import factory as vizu
#vizu.apply(net,m0,mf).view()
log = xes_importer.apply(log_path)

samplingForAmstc(net,m0,mf,log,sampleSize,sizeOfRun,maxD,maxNbC,m)