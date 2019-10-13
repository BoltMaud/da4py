import sys

from da4py.main import formulas
from da4py.main.conformanceArtefacts import ConformanceArtefacts
from pm4py.objects.petri import importer
from pm4py.objects.log.importer.xes import factory as xes_importer
from pm4py.visualization.petrinet import factory as vizu


# USE : python3 testfile.py model log size_of_run max_d distance out_putfile

# import the model and the log with pm4py
net, m0, mf = importer.pnml.import_net(sys.argv[1])
log = xes_importer.import_log(sys.argv[2])

# visualize the model
#vizu.apply(net,m0,mf).view()

# create a conformanceArtefacts instance
artefacts= ConformanceArtefacts()
artefacts.setSize_of_run(int(sys.argv[3]))
artefacts.setMax_d(int(sys.argv[4]))
artefacts.setDistance_type(sys.argv[5])

# do some antiAlingment
artefacts.antiAlignment(net,m0,mf,log)

file = open(sys.argv[6],"w")
file.write(sys.argv[1]+";"+sys.argv[2]+";"+sys.argv[3]+";"+sys.argv[4]+";"+sys.argv[5]+";"+formulas.NB_VARS+";"+
           artefacts.getForumulaTime()+";"+artefacts.getTotalTime()+";"+artefacts.getRun())


