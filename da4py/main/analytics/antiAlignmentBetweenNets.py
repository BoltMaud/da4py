import itertools

from pm4py.objects.petri.petrinet import PetriNet

from da4py.main.objects.pnToFormulas import petri_net_to_SAT
from da4py.main.utils import variablesGenerator as vg, formulas
from da4py.main.utils.formulas import Or, And
from da4py.main.utils.unSat2qbfReader import writeQDimacs, cadetOutputQDimacs, runCadet

BOOLEAN_VAR_MARKING_PN_1="m1_ip"
BOOLEAN_VAR_MARKING_PN_2="m2_ip"
BOOLEAN_VAR_FIRING_TRANSITION_PN_1="tau1_ia"
BOOLEAN_VAR_FIRING_TRANSITION_PN_2="tau2_ia"
BOOLEAN_VAR_DIFF1="diff_i1"
BOOLEAN_VAR_DIFF2="diff_i2"


def apply(net1, m01, mf1, net2, m02, mf2, size_of_run, d, silent_label=None):

    vars = vg.VariablesGenerator()
    w1=add_wait_net(net1,"w1")
    pn1_formula, pn1_places, pn1_transitions, pn1_silent_transitions=petri_net_to_SAT(net1, m01, mf1, vars,
                                                                                      size_of_run,
                                                                                      reach_final=True,
                                                                                      label_m=BOOLEAN_VAR_MARKING_PN_1,
                                                                                      label_t=BOOLEAN_VAR_FIRING_TRANSITION_PN_1,
                                                                                      silent_transition=silent_label)
    w2=add_wait_net(net2,"w2")
    pn2_formula, pn2_places, pn2_transitions, pn2_silent_transitions=petri_net_to_SAT(net2, m02, mf2, vars,
                                                                                      size_of_run,
                                                                                      reach_final=True,
                                                                                      label_m=BOOLEAN_VAR_MARKING_PN_2,
                                                                                      label_t=BOOLEAN_VAR_FIRING_TRANSITION_PN_2,
                                                                                      silent_transition=silent_label)

    dist_formulas = distanceNets(vars,size_of_run,vars.getFunction(BOOLEAN_VAR_FIRING_TRANSITION_PN_1),
                                 vars.getFunction(BOOLEAN_VAR_FIRING_TRANSITION_PN_2),pn1_transitions,pn2_transitions,w1,w2)

    maxDist_formulas=maxDistance(vars.getFunction(BOOLEAN_VAR_DIFF1),vars.getFunction(BOOLEAN_VAR_DIFF2),d,size_of_run)

    listOfForAll=vars.getAll(BOOLEAN_VAR_MARKING_PN_1)+vars.getAll(BOOLEAN_VAR_FIRING_TRANSITION_PN_1)
    listOfExist=vars.getAll(BOOLEAN_VAR_MARKING_PN_2)+vars.getAll(BOOLEAN_VAR_FIRING_TRANSITION_PN_2)+vars.getAll(BOOLEAN_VAR_DIFF1)+vars.getAll(BOOLEAN_VAR_DIFF2)
    full_formula=Or([],[],[pn1_formula.negation(),And([],[],[dist_formulas,maxDist_formulas,pn2_formula])])
    cnf=full_formula.operatorToCnf(vars.iterator)
    listOfExist+=list(range(vars.iterator,full_formula.nbVars))
    writeQDimacs(full_formula.nbVars,listOfForAll, listOfExist, cnf)
    runCadet()
    positives,negatives=cadetOutputQDimacs()
    for var in positives:
        if vars.getVarName(var) != None and vars.getVarName(var).startswith("tau1_ia"):
            print(vars.getVarName(var),pn1_transitions[int(vars.getVarName(var).split(", ")[1].split("]")[0])])
    print("....")
    for var in negatives:
        if vars.getVarName(var) != None  and vars.getVarName(var).startswith("tau1_ia"):
            print(vars.getVarName(var),pn1_transitions[int(vars.getVarName(var).split(", ")[1].split("]")[0])])


def add_wait_net(net,wait_label):
    '''
    Words don't have the same length. To compare them we add a "wait" transition at the end of the model and the
    traces.
    :return:
    '''
    wait_transition = PetriNet.Transition(wait_label, wait_label)
    net.transitions.add(wait_transition)
    return wait_transition


def distanceNets(vars,size_of_run, tau1,tau2,pn1_transitions,pn2_transitions,w1,w2):
    formula=[]
    vars.add(BOOLEAN_VAR_DIFF1,[(1,size_of_run+1)])
    vars.add(BOOLEAN_VAR_DIFF2,[(1,size_of_run+1)])
    for i in range (1,size_of_run+1):
        for t1 in pn1_transitions:
            if t1 != w1:
                listOfSameLabels=[tau2([i,pn2_transitions.index(t2)]) for t2 in pn2_transitions if t2.label==t1.label]
                listOfSameLabels.append(tau2([i,pn2_transitions.index(w2)]))
                formula.append(Or(listOfSameLabels,[tau1([i,pn1_transitions.index(t1)]) ],[And([vars.getFunction(BOOLEAN_VAR_DIFF1)([i]),
                                                                                                vars.getFunction(BOOLEAN_VAR_DIFF2)([i])],[],[])]))
                formula.append(Or([vars.getFunction(BOOLEAN_VAR_DIFF1)([i])],[tau2([i,pn2_transitions.index(w2)]),
                                                                              tau1([i,pn1_transitions.index(t1)])],[]))
            else :
                formula.append(Or([],[tau1([i,pn1_transitions.index(t1)]),tau2([i,pn2_transitions.index(w2)])],
                                  [And([vars.getFunction(BOOLEAN_VAR_DIFF1)([i]),vars.getFunction(BOOLEAN_VAR_DIFF2)([i])],[],[])]))
                formula.append(Or([vars.getFunction(BOOLEAN_VAR_DIFF2)([i])],[tau1([i,pn1_transitions.index(t1)])],[]))

    return And([],[],formula)


def maxDistance(diff1,diff2, max_d,size_of_run):
    formulas=[]
    list_to_size_of_run= list(range(1,size_of_run*2+1))
    max_distance=(size_of_run*2)- max_d
    # IDEA : there are at least max_distance number of false variables
    combinaisons_of_instants=list(itertools.combinations(list_to_size_of_run,max_distance))
    distFalseVariables=[]
    for instants in combinaisons_of_instants:
        list_distances=[]
        for i in instants:
            if i <=size_of_run :
                list_distances.append(diff1([i]))
            else :
                list_distances.append(diff2([i-size_of_run]))
        distFalseVariables.append(And([],list_distances,[]))
    formulas.append(Or([],[],distFalseVariables))
    return And([],[],formulas)

