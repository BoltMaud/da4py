import timeit

from pm4py.objects.petri.petrinet import PetriNet, Marking

from src.main.formulas import Or, And
from src.main import variablesGenerator as vg
from src.main.logToFormulas import log_to_SAT
from src.main.pnToFormulas import petri_net_to_SAT
import pysat.solvers as SATSolvers
from pysat.examples.rc2 import RC2
from pysat.formula import WCNF


SAT_SOLVERS=['cd','g3','g4','lgl','mcm','mcb','mpl','mc','m22','mgh']
SILENT_TRANSITION="tau"
WAIT_TRANSITION="w"
BOOLEAN_VAR_MARKING_PN="m_ip"
BOOLEAN_VAR_FIRING_TRANSITION_PN="tau_it"
BOOLEAN_VAR_TRACES_ACTIONS="lambda_jia"
BOOLEAN_VAR_EDIT_DISTANCE="djiid"

def alignmentEditDistance():
    return None

def antiAlignmentEditDistance():
    return None

def multiAlignmentEditDistance():
    return None

def generalAlignmentEditDistance(net, m0, mf, traces, size_of_run, silent_transition="tau",max_d=10):
    max_d+=1
    variables=vg.VariablesGenerator()
    net,wait_transition = add_wait_net(net)
    pn_formulas, places, transitions = petri_net_to_SAT(net, m0,mf,variables,size_of_run,label_m=BOOLEAN_VAR_MARKING_PN,label_t=BOOLEAN_VAR_FIRING_TRANSITION_PN)
    transitions.append(silent_transition)
    log_formulas,traces = log_to_SAT(traces,transitions,variables,size_of_run,wait_transition)
    variables.add(BOOLEAN_VAR_EDIT_DISTANCE,[(0, len(traces)),(0,size_of_run+1),(0,size_of_run+1),(0,max_d+1)])

    formulas = [pn_formulas,log_formulas]
    for j in range (0, len(traces)):
        formulas.append(initialisation(transitions,variables.getfunction(BOOLEAN_VAR_FIRING_TRANSITION_PN),
                                       variables.getfunction(BOOLEAN_VAR_TRACES_ACTIONS),
                                       variables.getfunction(BOOLEAN_VAR_EDIT_DISTANCE),j,
                                       size_of_run,wait_transition,max_d=max_d))
        formulas+=(recursionEditDistance(transitions,variables.getfunction(BOOLEAN_VAR_FIRING_TRANSITION_PN),
                                              variables.getfunction(BOOLEAN_VAR_TRACES_ACTIONS),
                                              variables.getfunction(BOOLEAN_VAR_EDIT_DISTANCE),j,size_of_run,wait_transition,max_d=max_d))

    nbVars=variables.iterator
    full_formulas = And([],[],formulas)

    cnf= full_formulas.clausesToCnf(nbVars)

    wcnf= WCNF()
    wcnf.extend(cnf)
    for j in range (0,len(traces)):
        for d in range (1,(max_d)+1):
            print(variables.getVarName(variables.getVarNumber(BOOLEAN_VAR_EDIT_DISTANCE,[j,size_of_run,size_of_run,d])))
            wcnf.append([variables.getVarNumber(BOOLEAN_VAR_EDIT_DISTANCE,[j,size_of_run,size_of_run,d])],weight=-10)
    from pysat.examples.rc2 import RC2
    with RC2(wcnf) as rc2:
        for model in rc2.enumerate():

            if(rc2.cost < 0):
                print(rc2.cost)
                for d in range (1,max_d+1):
                    if variables.getVarNumber(BOOLEAN_VAR_EDIT_DISTANCE,[0,size_of_run,size_of_run,d]) in model:
                        print("D =",d)
                run="<"
                word="<<"
                for var in model:
                    if var > 0 and variables.getVarName(var)!=None:
                        if variables.getVarName(var).startswith("tau"):
                            index= variables.getVarName(var).split("]")[0].split(",")[1]
                            i= variables.getVarName(var).split("[")[1].split(",")[0]
                            run+=" ("+i+", "+str(transitions[int(index)])+"),"
                    if var > 0 and variables.getVarName(var)!=None:
                        if variables.getVarName(var).startswith("lambda"):
                            index= variables.getVarName(var).split("]")[0].split(",")[2]
                            i= variables.getVarName(var).split("[")[1].split(",")[1]
                            word+=" ("+i+", "+str(transitions[int(index)])+"),"
                run+=">"
                word+=">>"
                print("RUN",run)
                print("WORD",word)
    '''for var in model :
        if var < 0:
            var*=-1
            if variables.getVarName(var)!=None and variables.getVarName(var).startswith("djiid"):
                print("-",variables.getVarName(var))
        else :
        if variables.getVarName(var)!=None and variables.getVarName(var).startswith("djiid"):
            print("+",variables.getVarName(var))'''


    return None


def recursionEditDistance(transitions, tau_it, lambda_jia, djiid,j, size_of_run,wait_transition,silent_transition="tau", max_d=10):
    formulas=[]
    print(size_of_run)
    for i_m in range (1, size_of_run):
        for i_t in range (1, size_of_run):
            for d in range (0, max_d):
                # letters are equals or i_m == "tau" : i_t+1 == i_m+1 => (d i_t i_m d <=> d i_t+1 i_m+1 d)
                letters_are_equals=Or([],[lambda_jia([j,i_t+1,transitions.index(wait_transition)])],[
                                    And([],[],
                                        [Or([],[tau_it([i_m+1,t]),lambda_jia([j,i_t+1,t])],[]) for t in (0,len(transitions))]
                                        ),
                                    And([djiid([j,i_m,i_t,d]),djiid([j,i_m+1,i_t+1,d])],[],[]),
                                    And([],[djiid([j,i_m,i_t,d]),djiid([j,i_m+1,i_t+1,d])],[])
                                ])
                formulas.append(letters_are_equals)

                # letters are diff : i_t+1 == i_m+1 => (d i_t i_m d <=> d i_t+1 i_m+1 d)
                letters_are_diff = Or([lambda_jia([j,i_t+1,transitions.index(wait_transition)]),
                                       tau_it([i_m+1,transitions.index(wait_transition)]),
                                       tau_it([i_m+1,transitions.index(silent_transition)])],
                                      [],
                                      [And([tau_it([i_m+1,t]),lambda_jia([j,i_t+1,t])],[],[]) for t in range (0,len(transitions))]+[
                                          And([],[djiid([j,i_m+1,i_t+1,d+1 ])],[Or([],[djiid([j,i_m+1,i_t,d]),djiid([j,i_m,i_t+1,d])],[])]),
                                          And([djiid([j,i_m+1,i_t+1,d+1 ]),djiid([j,i_m+1,i_t,d]),djiid([j,i_m,i_t+1,d])],[],[])
                                      ])
                formulas.append(letters_are_diff)

                # ( u_t == w and u_m <> w) => ( d i_m i_t d <=> d i_m+1 i_t d
                finish_run_of_model = Or([tau_it([i_m+1,transitions.index(wait_transition)])],[lambda_jia([j,i_t+1,transitions.index(wait_transition)])],[
                    And([djiid([j,i_m+1,i_t+1,d]),djiid([j,i_m+1,i_t,d])],[],[]),
                    And([],[djiid([j,i_m+1,i_t+1,d]),djiid([j,i_m+1,i_t,d])],[])
                ])
                formulas.append(finish_run_of_model)

                # ( u_m == w and u_t <> w) => ( d i_m i_t d <=> d i_m i_t+1 d
                finish_run_of_trace = Or([lambda_jia([j,i_t+1,transitions.index(wait_transition)])],[tau_it([i_m+1,transitions.index(wait_transition)])],[
                    And([djiid([j,i_m+1,i_t+1,d]),djiid([j,i_m,i_t+1,d])],[],[]),
                    And([],[djiid([j,i_m+1,i_t+1,d]),djiid([j,i_m,i_t+1,d])],[])
                ])
                formulas.append(finish_run_of_trace)

    return formulas


def initialisation(transitions, tau_it, lambda_jia, djiid,j, size_of_run, wait_transition, silent_transition="tau",max_d=10):

    positives=[]
    # diid is true for d = 0
    for i_m in range (1,size_of_run+1):
        for i_t in range (1,size_of_run+1):
            positives.append(djiid([j,i_m,i_t,0]))

    # diid is false for 0 0 d and d >0
    negatives =[djiid([j,0,0, d]) for d in range (1,max_d+1)]

    formulas =[]
    for d in range (0, max_d):
        for i_m in range (1, size_of_run):
            # (i_m <> w and i_m <> tau ) <=> (d im+1 0 d+1 <=> d im 0 d )
            i_t_null_and_i_m_cost = Or([tau_it([i_m+1,transitions.index(silent_transition)]),
                                        tau_it([i_m+1, transitions.index(wait_transition)])],
                                        [],
                                        [
                                            And([djiid([j,i_m+1,0,d+1]),djiid([j,i_m,0,d])],[],[]),
                                            And([],[djiid([j,i_m+1,0,d+1]),djiid([j,i_m,0,d])],[])
                                        ])
            formulas.append(i_t_null_and_i_m_cost)

            # (i_m == w or i_m == tau ) <=> (d im+1 0 d+1 <=> d im 0 d )
            i_t_null_and_i_m_dont_cost = Or([],[],[
                                                And([],[tau_it([i_m+1,transitions.index(silent_transition)]),
                                                        tau_it([i_m+1, transitions.index(wait_transition)])],[]),
                                                And([djiid([j,i_m+1,0,d]),djiid([j,i_m,0,d])],[],[]),
                                                And([],[djiid([j,i_m+1,0,d]),djiid([j,i_m,0,d])],[])

                                            ])
            formulas.append(i_t_null_and_i_m_dont_cost)
        for i_t in range (0,size_of_run-1):
            # i_t <> w <=> (d 0 it+1 d+1 <=> d 0 it d )
            i_m_null_and_i_t_cost = Or([lambda_jia([j,i_t+1,transitions.index(wait_transition)])],[],[
                                        And([djiid([j,0,i_t,d]),djiid([j,0,i_t+1,d+1])],[],[]),
                                        And([],[djiid([j,0,i_t,d]),djiid([j,0,i_t+1,d+1])],[])
                                    ])
            formulas.append(i_m_null_and_i_t_cost)
            # i_t == w <=> (d 0 it+1 d+1 <=> d 0 it d )
            i_m_null_and_i_t_dont_cost = Or([],[lambda_jia([j,i_t+1,transitions.index(wait_transition)])],[
                                                And([djiid([j,0,i_t,d]),djiid([j,0,i_t+1,d])],[],[]),
                                                And([],[djiid([j,0,i_t,d]),djiid([j,0,i_t+1,d])],[])
                                         ])
            formulas.append(i_m_null_and_i_t_dont_cost)

    return And(positives,negatives,formulas)


def add_wait_net(net,wait_transition="w"):
    transition = PetriNet.Transition(wait_transition,wait_transition)
    for place in net.places:
        if len(place.out_arcs) == 0:
            arcIn=PetriNet.Arc(place,transition)
            arcOut=PetriNet.Arc(transition,place)
            net.arcs.add(arcIn)
            net.arcs.add(arcOut)
            transition.in_arcs.add(arcIn)
            transition.out_arcs.add(arcOut)
            place.out_arcs.add(arcIn)
            place.in_arcs.add(arcOut)
    net.transitions.add(transition)
    return net,transition
