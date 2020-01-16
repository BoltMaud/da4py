from da4py.main.analytics.amstc import Amstc

PATH = "/Users/mboltenhagen/Documents/PhD/recherche/BPI2015"
from pm4py.objects.log.exporter.xes import factory as xes_exporter
from pm4py.objects.log.importer.xes import factory as xes_importer





from pm4py.objects.log.log import EventLog
from pm4py.objects.log.log import Trace


'''
for n in range (1,6):
    log_m1 = xes_importer.apply(PATH+"/BPIC15_"+str(n)+"f.xes.gz")
    sub_log_m1 = EventLog()

    for t in log_m1:
        sub_trace=Trace()
        sub_trace._set_attributes(t.attributes)
        for e in t._list:
            if len(e['concept:name'].split("_"))>1 and  e['concept:name'].split("_")[2][0]=='0':
                if len(e['concept:name'].split("_"))>3:
                    e['concept:name']=e['concept:name'][:-2]
                sub_trace.append(e)
        sub_log_m1.append(sub_trace)
    xes_exporter.apply(sub_log_m1,PATH+"/BPIC15_"+str(n)+"s.xes")
'''

from pm4py.objects.petri import importer
net, m0, mf = importer.factory.apply(PATH+"/ILP_based.pnml")
log_m1 = xes_importer.apply(PATH+"/BPIC15_1s.xes")
clustering = Amstc(net,m0,mf,log_m1,4, 2,4,3)
print("Runtime",clustering.getTime())
for (centroid,traces) in clustering.getClustering():
    print(centroid, traces)