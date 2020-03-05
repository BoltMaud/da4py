import random
import sys
import time
from copy import deepcopy

import editdistance
from pm4py.algo.filtering.log.variants.variants_filter import get_variants
from pm4py.objects import petri
from pm4py.objects.log.log import EventStream
from pm4py.objects.log.util.log import project_traces
from pm4py.objects.petri import importer, check_soundness
from pm4py.objects.log.importer.xes import factory as xes_importer
from pm4py.objects.log.exporter.xes import factory as xes_exporter
# import the model and the log with pm4py
from pm4py.objects.petri.petrinet import PetriNet, Marking
import pm4py.algo.conformance.alignments.factory as alignments

from da4py.main.analytics.amstc import Amstc,  samplingVariantsForAmstc
from da4py.main.analytics.antiAlignmentBetweenNets import  apply as antinets
from pm4py.objects.log.util import xes as xes_util

net_path="../../examples/medium/model2.pnml"
log_path="../../examples/medium/model2.xes"

sampleSize=9
sizeOfRun=8
maxD=1
maxNbC=5
m=2

net, m0, mf = importer.factory.apply(net_path)
from pm4py.visualization.petrinet import factory as vizu
log = xes_importer.apply(log_path)

vizu.apply(net,m0,mf).view()


clustering=samplingVariantsForAmstc(net,m0,mf,log,sampleSize,sizeOfRun,maxD,maxNbC,m,maxCounter=1,debug=1)
for centroid, list in clustering:
    for a in list:
        print(a)

'''
net_path="/Users/mboltenhagen/Documents/PhD/da4py/examples/medium/model2.pnml"
net_path="/Users/mboltenhagen/Documents/PhD/da4py/examples/tiny/A-B.pnml"

net1, m01, mf1 = importer.factory.apply(net_path)
net2, m02, mf2 = importer.factory.apply(net_path)


antinets(net1, m01, mf1, net2, m02, mf2, 2, 2)


'''

