import itertools

from da4py.main.objects.pnToFormulas import petri_net_to_SAT
from da4py.main.utils import variablesGenerator as vg, formulas
from da4py.main.utils.formulas import Or, And
from da4py.main.utils.unSat2qbfReader import writeQDimacs, cadetOutputQDimacs, runCadet

BOOLEAN_VAR_MARKING_PN_1="m1_ip"
BOOLEAN_VAR_MARKING_PN_2="m2_ip"
BOOLEAN_VAR_FIRING_TRANSITION_PN_1="tau1_ia"
BOOLEAN_VAR_FIRING_TRANSITION_PN_2="tau2_ia"
BOOLEAN_VAR_DIFF="diff_i"

def apply(net1, m01, mf1, net2, m02, mf2, size_of_run, d, silent_label=None):
    print("he")

    vars = vg.VariablesGenerator()

    pn1_formula, pn1_places, pn1_transitions, pn1_silent_transitions=petri_net_to_SAT(net1, m01, mf1, vars,
                                                                         size_of_run,
                                                                         reach_final=False,
                                                                         label_m=BOOLEAN_VAR_MARKING_PN_1,
                                                                         label_t=BOOLEAN_VAR_FIRING_TRANSITION_PN_1,
                                                                         silent_transition=silent_label)

    pn2_formula, pn2_places, pn2_transitions, pn2_silent_transitions=petri_net_to_SAT(net2, m02, mf2, vars,
                                                                                      size_of_run,
                                                                                      reach_final=False,
                                                                                      label_m=BOOLEAN_VAR_MARKING_PN_2,
                                                                                      label_t=BOOLEAN_VAR_FIRING_TRANSITION_PN_2,
                                                                                      silent_transition=silent_label)

    dist_formulas = distanceNets(vars,size_of_run,vars.getFunction(BOOLEAN_VAR_FIRING_TRANSITION_PN_1),
                 vars.getFunction(BOOLEAN_VAR_FIRING_TRANSITION_PN_2),pn1_transitions,pn2_transitions)

    maxDist_formulas=maxDistance(vars.getFunction(BOOLEAN_VAR_DIFF),d,size_of_run)

    listOfForAll=vars.getAll(BOOLEAN_VAR_MARKING_PN_1)+vars.getAll(BOOLEAN_VAR_FIRING_TRANSITION_PN_1)
    listOfExist=vars.getAll(BOOLEAN_VAR_MARKING_PN_2)+vars.getAll(BOOLEAN_VAR_FIRING_TRANSITION_PN_2)+vars.getAll(BOOLEAN_VAR_DIFF)
    full_formula=Or([],[],[pn1_formula.negation(),And([],[],[dist_formulas,maxDist_formulas,pn2_formula])])
    #full_formula=pn1_formula
    cnf=full_formula.operatorToCnf(vars.iterator)
    listOfExist+=list(range(vars.iterator,formulas.NB_VARS))
    writeQDimacs(formulas.NB_VARS,listOfForAll, listOfExist, cnf)
    runCadet()
    positives,negatives=cadetOutputQDimacs()
    for var in positives:
        if vars.getVarName(var) != None:
            print(var)
            print(vars.getVarName(var))
    print("....")
    for var in negatives:
        if vars.getVarName(var) != None:
            print(var)
            print(vars.getVarName(var))


def distanceNets(vars,size_of_run, tau1,tau2,pn1_transitions,pn2_transitions):
    formula=[]
    vars.add(BOOLEAN_VAR_DIFF,[(1,size_of_run+1)])
    for i in range (1,size_of_run+1):
        for t1 in pn1_transitions:
            listOfSameLabels=[tau2([i,pn2_transitions.index(t2)]) for t2 in pn2_transitions if t2.label==t1.label]
            formula.append(Or([vars.getFunction(BOOLEAN_VAR_DIFF)([i]),tau1([i,pn1_transitions.index(t1)]) ],
                           listOfSameLabels,[]))
    return And([],[],formula)

def maxDistance(delta, max_d,size_of_run):
    formulas=[]
    list_to_size_of_run= list(range(1,size_of_run+1))
    max_distance=(size_of_run)- max_d
    # IDEA : there are at least max_distance number of false variables
    combinaisons_of_instants=list(itertools.combinations(list_to_size_of_run,max_distance))
    distFalseVariables=[]
    for instants in combinaisons_of_instants:
        list_distances=[]
        for i in instants:
            list_distances.append(delta([i]))
        distFalseVariables.append(And([],list_distances,[]))
    formulas.append(Or([],[],distFalseVariables))
    return And([],[],formulas)

