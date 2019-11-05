import sys
import os
from da4py.main import formulas
from da4py.main.conformanceArtefacts import ConformanceArtefacts
from pm4py.objects.petri import importer
from pm4py.objects.log.importer.xes import factory as xes_importer
from pm4py.visualization.petrinet import factory as vizu

outPutFileName="AA_artificialLog_2.csv"
for number in [1,2,3,4,5,6,7,8,12,13]:
    for distance in ["hamming","edit"]:
        model="artificial-logs-models/fig"+str(number)+".pnml"
        traces="artificial-logs-models/accepting-pns/artificial.xes"
        for run in [10]:
            for max_d in [20]:
                net, m0, mf = importer.pnml.import_net(model)
                log = xes_importer.import_log(traces)
                artefacts= ConformanceArtefacts()
                artefacts.setSilentLabel("tau")
                artefacts.setDistance_type(distance)
                artefacts.setSize_of_run(run)
                artefacts.setMax_d(max_d)
                # do some antiAlingment
                artefacts.antiAlignment(net,m0,mf,log)
                outPutFile=open(outPutFileName,"a")
                outPutFile.write(model+";")
                outPutFile.write("AA"+";")
                outPutFile.write(artefacts.getDistance_type()+";")
                outPutFile.write(str(run)+";")
                outPutFile.write(str(max_d)+";")
                outPutFile.write(str(artefacts.getPrecision())+";")
                outPutFile.write(str(artefacts.getTotalTime())+";"+str(formulas.NB_VARS)+";")
                outPutFile.write(artefacts.getRun()+";")
                outPutFile.close()


for number in [1,2,3,4,5,6,7,8,12]:
    model="artificial-logs-models/"+dir+"/"+str(number)+".pnml"
    traces="artificial-logs-models/accepting-pns/artificial.xes"
    outPutFile=open("adriano_artificialLog.txt","a")
    outPutFile.write("\n"+str(number))
    outPutFile.close()
    os.system("java -cp markovian-accuracy.jar:./lib/* au.edu.unimelb.services.ServiceProvider  MAC STA SPL "+traces+" "+model + "  3 > adriano_artificialLog.txt")



list_of_dirs=["im","shm","sm"]
outPutFileName="AA_realLog.csv"

for dir in list_of_dirs:
    for number in [1,2,3,4,5,6,7,8,9,10,11,12]:
        model="real-life-logs-models/"+dir+"/"+str(number)+".pnml"
        traces="real-life-logs-models/"+str(number)+".xes.gz"
        for distance in ["hamming","edit"]:
            for run in [10,15,20]:
                for max_d in [10,20]:
                    net, m0, mf = importer.pnml.import_net(model)
                    log = xes_importer.import_log(traces)
                    # create a conformanceArtefacts instance
                    artefacts= ConformanceArtefacts()
                    artefacts.setSilentLabel("tau")
                    artefacts.setDistance_type(distance)
                    artefacts.setSize_of_run(run)
                    artefacts.setMax_d(max_d)
                    # do some antiAlingment
                    artefacts.setMax_nbTraces(100)
                    artefacts.antiAlignment(net,m0,mf,log)
                    outPutFile=open(outPutFileName,"a")
                    outPutFile.write(model+";")
                    outPutFile.write("AA100"+";")
                    outPutFile.write(artefacts.getDistance_type()+";")
                    outPutFile.write(str(run)+";")
                    outPutFile.write(str(max_d)+";")
                    outPutFile.write(str(artefacts.getPrecision())+";")
                    outPutFile.write(str(artefacts.getTotalTime())+";"+str(formulas.NB_VARS)+";")
                    outPutFile.write(artefacts.getRun()+";")
                    outPutFile.write(artefacts.getDistanceOfAnti()+"\n")
                    outPutFile.close()

                    net, m0, mf = importer.pnml.import_net(model)
                    log = xes_importer.import_log(traces)
                    # create a conformanceArtefacts instance
                    artefacts= ConformanceArtefacts()
                    artefacts.setSilentLabel("tau")
                    artefacts.setDistance_type(distance)
                    artefacts.setSize_of_run(run)
                    artefacts.setMax_d(max_d)
                    # do some antiAlingment
                    artefacts.antiAlignment(net,m0,mf,log)
                    outPutFile=open(outPutFileName,"a")
                    outPutFile.write(model+";")
                    outPutFile.write("AA"+";")
                    outPutFile.write(artefacts.getDistance_type()+";")
                    outPutFile.write(str(run)+";")
                    outPutFile.write(str(max_d)+";")
                    outPutFile.write(str(artefacts.getPrecision())+";")
                    outPutFile.write(str(artefacts.getTotalTime())+";"+str(formulas.NB_VARS)+";")
                    outPutFile.write(artefacts.getRun()+";")
                    outPutFile.write(artefacts.getDistanceOfAnti()+"\n")
                    outPutFile.close()

for dir in list_of_dirs:
    for number in [1,2,3,4,5,6,7,8,9,10,11,12]:
        model="real-life-logs-models/"+dir+"/"+str(number)+".pnml"
        traces="real-life-logs-models/"+str(number)+".xes.gz"
        outPutFile=open("adriano_realLog.txt","a")
        outPutFile.write("\n"+str(number))
        outPutFile.close()
        os.system("java -cp markovian-accuracy.jar:./lib/* au.edu.unimelb.services.ServiceProvider  MAC STA SPL "+traces+" "+model + "  3 > adriano_realLog.txt")
