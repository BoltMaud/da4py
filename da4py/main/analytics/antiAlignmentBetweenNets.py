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
BOOLEAN_VAR_DIFF1="diff_1i"
BOOLEAN_VAR_DIFF2="diff_2i"


def apply(net1, m01, mf1, net2, m02, mf2, size_of_run, d, silent_label=None):

    vars = vg.VariablesGenerator()
    we=add_wait_net_end(net1,"wf")
    w1=add_wait_net(net1,"wf")
    pn1_formula, pn1_places, pn1_transitions, pn1_silent_transitions=petri_net_to_SAT(net1, m01, mf1, vars,
                                                                                      size_of_run,
                                                                                      reach_final=True,
                                                                                      label_m=BOOLEAN_VAR_MARKING_PN_1,
                                                                                      label_t=BOOLEAN_VAR_FIRING_TRANSITION_PN_1,
                                                                                      silent_transition=silent_label)

    w2=add_wait_net(net2,"wf")
    pn2_formula, pn2_places, pn2_transitions, pn2_silent_transitions=petri_net_to_SAT(net2, m02, mf2, vars,
                                                                                      size_of_run,
                                                                                      reach_final=True,
                                                                                      label_m=BOOLEAN_VAR_MARKING_PN_2,
                                                                                      label_t=BOOLEAN_VAR_FIRING_TRANSITION_PN_2,
                                                                                      silent_transition=silent_label)
    dist_formulas = distanceNets(vars,size_of_run,vars.getFunction(BOOLEAN_VAR_FIRING_TRANSITION_PN_1),
                                 vars.getFunction(BOOLEAN_VAR_FIRING_TRANSITION_PN_2),pn1_transitions,pn2_transitions,w1,w2)

    maxDist_formulas=maxDistance(vars,vars.getFunction(BOOLEAN_VAR_DIFF1),vars.getFunction(BOOLEAN_VAR_DIFF2),d,size_of_run)
    notTooManyW=numberOfWaitInRun(vars,size_of_run,vars.getFunction(BOOLEAN_VAR_FIRING_TRANSITION_PN_1),pn1_transitions,w1,we)

    from pm4py.visualization.petrinet import factory as vizu
    #vizu.apply(net2,m02,mf2).view()
    listOfForAll=vars.getAll(BOOLEAN_VAR_MARKING_PN_1)+vars.getAll(BOOLEAN_VAR_FIRING_TRANSITION_PN_1)
    listOfExist=vars.getAll(BOOLEAN_VAR_MARKING_PN_2)+vars.getAll(BOOLEAN_VAR_FIRING_TRANSITION_PN_2)+vars.getAll(BOOLEAN_VAR_DIFF1)+vars.getAll(BOOLEAN_VAR_DIFF2)

    full_formula=Or([],[],[And([],[],[notTooManyW,pn1_formula]).negation(),And([],[],[dist_formulas,maxDist_formulas,pn2_formula])])
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

def add_wait_net_end(pn, wait_label):
    '''
    Words don't have the same length. To compare them we add a "wait" transition at the end of the model and the
    traces.
    :return:
    '''
    wait_transition = PetriNet.Transition(wait_label, wait_label)
    for place in pn.places:
        if len(place.out_arcs) == 0:
            arcIn = PetriNet.Arc(place, wait_transition)
            arcOut = PetriNet.Arc(wait_transition, place)
            pn.arcs.add(arcIn)
            pn.arcs.add(arcOut)
            wait_transition.in_arcs.add(arcIn)
            wait_transition.out_arcs.add(arcOut)
            place.out_arcs.add(arcIn)
            place.in_arcs.add(arcOut)
    pn.transitions.add(wait_transition)
    return wait_transition


def numberOfWaitInRun(vars,size_of_run, tau1,pn1_transitions,w1,we):
    list_to_size_of_run= list(range(1,size_of_run*2+1))
    minw1=int((size_of_run)/2)
    # IDEA : there are at least max_distance number of w1 variables to false
    combinaisons_of_instants=list(itertools.combinations(list_to_size_of_run,minw1))
    w1ToTrue=[]
    for instants in combinaisons_of_instants:
        listOfW1ToTrue=[]
        for i in instants:
            if i <=int(size_of_run):
                listOfW1ToTrue.append(tau1([i,pn1_transitions.index(w1)]))
            else :
                listOfW1ToTrue.append(tau1([i-int(size_of_run),pn1_transitions.index(we)]))
        w1ToTrue.append(And(listOfW1ToTrue,[],[]))
    return Or([],[],w1ToTrue)


def distanceNets(vars,size_of_run, tau1,tau2,pn1_transitions,pn2_transitions,w1,w2):
    formula=[]
    vars.add(BOOLEAN_VAR_DIFF1,[(1,size_of_run+1)])
    vars.add(BOOLEAN_VAR_DIFF2,[(1,size_of_run+1)])

    for i in range (1,size_of_run+1):
        for t1 in pn1_transitions:
            '''
            listOfSameLabels=[tau2([i,pn2_transitions.index(t2)]) for t2 in pn2_transitions if t2.label==t1.label]
            listOfSameLabels.append(vars.getFunction(BOOLEAN_VAR_DIFF)([i]))
            formula.append(Or(listOfSameLabels,[tau1([i,pn1_transitions.index(t1)]) ],[]))

            '''
            if t1 != w1:
                listOfSameLabels=[tau2([i,pn2_transitions.index(t2)]) for t2 in pn2_transitions if t2.label==t1.label]
                listOfSameLabels.append(tau2([i,pn2_transitions.index(w2)]))
                formula.append(Or(listOfSameLabels,[tau1([i,pn1_transitions.index(t1)]) ],[And([vars.getFunction(BOOLEAN_VAR_DIFF1)([i]),
                                                                                            vars.getFunction(BOOLEAN_VAR_DIFF2)([i])],[],[])]))
                formula.append(Or([vars.getFunction(BOOLEAN_VAR_DIFF1)([i])],[tau2([i,pn2_transitions.index(w2)]),
                                                                          tau1([i,pn1_transitions.index(t1)])],[]))
            else :
                formula.append(Or([vars.getFunction(BOOLEAN_VAR_DIFF2)([i]),tau2([i,pn2_transitions.index(w2)])],
                                  [tau1([i,pn1_transitions.index(t1)])],[]))

    return And([],[],formula)


def maxDistance(vars,diff1,diff2, max_d,size_of_run):
    list_to_size_of_run= list(range(1,size_of_run*2+1))
    max_distance=size_of_run*2-max_d
    # IDEA : there are at least max_distance number of false variables
    combinaisons_of_instants=list(itertools.combinations(list_to_size_of_run,max_distance))
    distFalseVariables=[]
    for instants in combinaisons_of_instants:
        list_distances=[]
        for i in instants:
            if i <=size_of_run:
                list_distances.append(diff1([i]))
            else :
                list_distances.append(diff2([i-size_of_run]))
        distFalseVariables.append(And([],list_distances,[]))
    return Or([],[],distFalseVariables)

def maxDistance2(vars,diff1,diff2, max_d,size_of_run):
    list_to_size_of_run= list(range(1,size_of_run*2+1))
    max_distance=max_d
    # IDEA : there are at least max_distance number of false variables
    combinaisons_of_instants=list(itertools.combinations(list_to_size_of_run,max_distance))
    distFalseVariables=[]
    for instants in combinaisons_of_instants:
        list_distances=[]
        for i in instants:
            if i <=size_of_run:
                list_distances.append(diff1([i]))
            else :
                list_distances.append(diff2([i-size_of_run]))
        list_distances2=[]
        for i in range(1,size_of_run*2+1):
            if i not in instants:
                if i <=size_of_run:
                    list_distances2.append(diff1([i]))
                else :
                    list_distances2.append(diff2([i-size_of_run]))

        distFalseVariables.append(Or([],list_distances,[And([],list_distances2,[])]))
    return Or([],[],distFalseVariables)
