import copy

from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.petri.importer import importer as petri_importer
from da4py.main.conformanceChecking.conformanceArtefacts import ConformanceArtefacts

'''
Observe that for this script, a slight modification of the code is requested:
- in da4py.main.conformanceChecking.conformanceArtefacts.ConformanceArtefacts 
-> comment the solving of the formula which is not required
-> modify return len(wncf.hard) in both multi-alignment and exact alignment class
'''


net, m0, mf = petri_importer.apply("../../examples/medium/model2.pnml")
log = xes_importer.apply("../../examples/medium/model2bis.xes")


# CHART 1 : increasing the number of traces
multi = []
exact = []
for i in range(0,110,10):
    print(i)
    log1 = copy.copy(log)

    log1._list = log._list[:i]
    artefacts = ConformanceArtefacts()
    artefacts.setDistance_type("edit")
    artefacts.setOptimizeSup(True)
    artefacts.setSize_of_run(10)
    artefacts.setMax_d(20)

    multi.append(artefacts.multiAlignment(net,m0,mf,log1))
    exact.append(artefacts.exactAlignment(net,m0,mf,log1))

print(multi)
print(exact)

# CHART 1 : increasing the size of run
multi = []
exact = []
log._list = log._list[:10]
for i in range(0, 11):
    print(i)

    artefacts = ConformanceArtefacts()
    artefacts.setDistance_type("edit")
    artefacts.setOptimizeSup(True)
    artefacts.setSize_of_run(i)
    artefacts.setMax_d(2*i)

    multi.append(artefacts.multiAlignment(net,m0,mf,log))
    exact.append(artefacts.exactAlignment(net,m0,mf,log))

print(multi)
print(exact)