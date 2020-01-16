import sys
import time
from pm4py.objects import petri
from pm4py.objects.log.log import EventStream
from pm4py.objects.petri import importer, check_soundness
from pm4py.objects.log.importer.xes import factory as xes_importer
# import the model and the log with pm4py
from pm4py.objects.petri.petrinet import PetriNet, Marking
import pm4py.algo.conformance.alignments.factory as alignments

from da4py.main.analytics.amstc import Amstc

net, m0, mf = importer.factory.apply("<>")
from pm4py.visualization.petrinet import factory as vizu
#vizu.apply(net,m0,mf).view()
log = xes_importer.apply("<>")

#cost=alignments.apply_trace(log._list[0],net,m0,mf)
from pm4py import util
from pm4py.objects import log as log_lib
start=time.time()
clusters=[]
log._list=log._list[:100]
counter=0
nbOfIteration=0
while len(log._list)>0 and counter<2:
    clustering = Amstc(net,m0,mf,log,16, 2,16,3,nbTraces=10)
    nbOfIteration+=1
    result=clustering.getClustering()
    print("> Found",len(result)-1,"centroids")
    new_clustered_traces=[]
    # if there is at least a clustered trace :
    if len(result[-1][1])!=10:
        for (tuple_centroid,traces) in result:
            if type (tuple_centroid) is tuple :
                centroid, c_m0, c_mf= tuple_centroid
                #vizu.apply(centroid,c_m0,c_mf).view()
                #print(traces)
                #input("Press Enter to continue...")
                if check_soundness.check_relaxed_soundness_net_in_fin_marking(centroid,c_m0,c_mf):
                    traces_of_clusters=[]
                    for l in log._list:
                        ali=alignments.apply_trace(l,centroid,c_m0,c_mf)
                        cost=ali['cost']
                        if cost< 10000*5:
                            print(cost,ali)
                            counter=-1
                            new_clustered_traces.append(l)
                            traces_of_clusters.append(l)
                    if len(traces_of_clusters)>0:
                        clusters.append((tuple_centroid,traces_of_clusters))
                    else :
                        print("Clustering raté")
                        print(traces)
                        centroid, c_m0, c_mf= tuple_centroid
                        vizu.apply(centroid,c_m0,c_mf).view()
                        input("On appuie!!")
                        counter+=1
                else :
                    print("This model is not sound")
                    #input("Press Enter to continue...")

        # if we found at least a good centroid
        if counter==-1:
            print("Empty?",len(new_clustered_traces))
            print("NbTraces:(AV)", len(log._list))
            log._list=list(set(log._list)-set(new_clustered_traces))
            print("NbTraces:(AP)",len(log._list))
            counter=0
    else :
        print("Clustering raté")
        counter+=1

print("This clustering has been found in ",nbOfIteration," iterations.")
for (centroid, traces)in clusters:
    c, m0, mf=centroid
    vizu.apply(c,m0,mf).view()
    print(len(traces))

print(time.time()-start)