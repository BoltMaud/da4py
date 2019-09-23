from pm4py.objects.log.util.log import project_traces

from src.main.formulas import And


def log_to_SAT(traces_xes, transitions, variablesGenerator, size_of_run, wait_transition, label_l="lambda_jia"):
    traces = project_traces(traces_xes)
    print("IL Y A ",len(traces),"TRACES")
    variablesGenerator.add(label_l,[(0,len(traces)),(1,size_of_run+1),(0,len(transitions))])
    lambda_jia=variablesGenerator.getfunction(label_l)
    positives=[]
    negatives=[]
    for j in range (0,len(traces)):
        for i in range (1,size_of_run+1):
            if len(traces[j])<i:
                positives.append(lambda_jia([j,i,transitions.index(wait_transition)]))
                for a in transitions :
                    if a != wait_transition:
                        negatives.append(lambda_jia([j,i,transitions.index(a)]))
            else :
                for a in transitions:
                    if str(a)==traces[j][i-1]:
                        positives.append(lambda_jia([j,i,transitions.index(a)]))
                    else :
                        negatives.append(lambda_jia([j,i,transitions.index(a)]))

    return And(positives,negatives,[]),traces