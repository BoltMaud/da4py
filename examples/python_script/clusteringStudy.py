#!/usr/bin/env python
# -*- coding:utf-8 -*-
##
## clusteringStudy.py
##
##  Created on: July, 2020
##      Author: Boltenhagen Mathilde
##      E-mail: boltenhagen lsv . fr
##

'''

Compare the Super-Instances of Scalable Mixed-Paradigm Trace Clustering using Super-Instances to the AMSTC method.
Paper: Model-Based Trace Variant Analysis of Event Logs

'''

from itertools import combinations
from pm4py.algo.filtering.log.variants import variants_filter
from pm4py.objects.log.importer.xes import importer as import_xes
from pm4py.objects.petri.importer import importer as import_pnml
from da4py.TraCluSI import  createOverclustering
from da4py.main.analytics.amstc import samplingVariantsForAmstc
from pm4py.visualization.petrinet import factory as vizu
from pm4py.objects.log.util.log import project_traces
import numpy as np
from pm4py.objects.log.log import EventLog


def jacardIndex(dicoOfClustering1,dicoOfClustering2):
    '''
    computes the similarity between two clusterings results of the same dataset
    clustering1,clustering2 : clusterings, format output of AMSTC
    '''
    items=list(dicoOfClustering1.keys())
    n11=0
    n10=0
    n01=0
    for x1,x2 in combinations(items,2):
        x1_x2_in_c1 = True if dicoOfClustering1[x1]==dicoOfClustering1[x2] else False
        x1_x2_in_c2 = True if dicoOfClustering2[x1]==dicoOfClustering2[x2] else False
        if x1_x2_in_c1 and x1_x2_in_c2:
            n11+=1
        if (x1_x2_in_c1 and not x1_x2_in_c2):
            n10+=1
        if (x1_x2_in_c2 and not x1_x2_in_c1):
            n01+=1
    print(n11,"N11, pairs are clustered together")
    print(n10,"N10, pairs are clustered in C1 but not C2")
    print(n01,"N01, pairs are clustered in C2 but not C1")
    return n11/(n01+n10+n11)


########################################################
#                    MAIN PROGRAM                      #
########################################################


# read the file
net,m0,mf = import_pnml.apply("/Users/mboltenhagen/Documents/PhD/Josep&Thomas/markovian-accuracy/real-life-logs-models/im/2.pnml")
log  = import_xes.apply("/Users/mboltenhagen/Documents/PhD/Josep&Thomas/markovian-accuracy/real-life-logs-models/2.xes.gz")

# prepare an empty log for the clustered traces
clustered_traces = EventLog()

# launch the AMSTC method
print("########################################################")
print("#                         AMSTC                        #")
print("########################################################")
clustering = samplingVariantsForAmstc(net, m0, mf, log,5,15, 0, 7, 2 ,maxCounter=1,editDistance=True,silent_label="tau", debug=1)

# get a dict of my clustering, {trace:cluster number}
myClustering = {}

# for each cluster
for i in range (0,len(clustering)):
    # if there exists a centroid (net, m0, mf)
    if type(clustering[i][0]) is tuple:
        net1, m01, mf1 = clustering[i][0]
        # print it
        vizu.apply(net1, m01, mf1).view()
        log1 = clustering[i][1]
        # add the traces in the clustered one
        clustered_traces._list+=clustering[i][1]

        # create the dicto, this format has been used because it was easier
        for l in log1:
            for j in range (0,len(log._list)):
                if log._list[j].attributes["concept:name"]==l.attributes["concept:name"]:
                    myClustering[j]= i

# the Super Instance method requires a lit of sequences
traces1 = [' '.join(wordslist) for wordslist in project_traces(clustered_traces)]

# matches the good index cause we will compare indices in the Jaccard index
theirClustering ={}
for l in range (0,len(clustered_traces._list)):
    for j in range (0,len(log._list)):
        # find the good trace and get real index
        if log._list[j].attributes["concept:name"]==clustered_traces._list[l].attributes["concept:name"]:
            theirClustering[l]= j

# launch the Super Instance method
print("########################################################")
print("#                       TraCluS                        #")
print("########################################################")
TCSClustering = {}
# on the clustered traces and the same number of clusters
centers, classes = createOverclustering.cluster(traces1,len(clustering)-1)

# reshape the outputs
finallyTheirClustering={}
for l in range (0,len(clustered_traces._list)):
    finallyTheirClustering[theirClustering[l]]= classes[l]

# see their clustering
for i in range(0,len(clustering)-1):
    print(i,"=",np.count_nonzero(classes == i))

# see their centoids
for i in centers:
    print(traces1[i])

print("########################################################")
print("#                    Jaccard Index                     #")
print("########################################################")
print(jacardIndex(myClustering,finallyTheirClustering))
