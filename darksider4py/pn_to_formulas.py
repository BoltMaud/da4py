from darksider4py.formulas import Or, And
import sys

from darksider4py import variablesGenerator as vg

sys.path.append('../pm4py-source')
from pm4py.objects.petri import importer
from pm4py.objects.petri.common import final_marking, initial_marking


def is_run(size_of_run, places, transitions, m0, m_ip,tau_it):
    positives = [m_ip([0,places.index(m)]) for m in m0]
    negatives = [m_ip([0,places.index(m)]) for m in places if m not in m0]
    formulas = [is_action(places, transitions, m0,i,m_ip,tau_it) for i in range(1,size_of_run)]
    run_of_pn = And(positives,negatives,formulas)
    return  run_of_pn

def is_action(places, transitions, m0, i, m_ip, tau_it):
    '''
    :param pn:
    :param i:
    :param m_ip:
    :param tau_it:
    :param sigma:
    :return: give action of instant i
    '''
    #only one transition is true at instant i
    formulas= [Or([tau_it([i,transitions.index(t)]) for t in transitions],[],[])]
    # if transition t fires at instant i, then we have the good marking
    for t in transitions:
        formulas.append(Or([],[tau_it([i,transitions.index(t)])],is_transition(places,t,i,m_ip)))
    return And([],[],formulas)

def is_transition(places,transition,i,m_ip):
    formulas=[]
    prePlaces=[ a.source for a in transition.in_arcs ]
    postPlaces=[a.target for a in transition.out_arcs]

    for p in places:
        if p in prePlaces and p in postPlaces:
            formulas.append(And([m_ip([i,places.index(p)]),m_ip([i-1,places.index(p)])],[],[]))
        elif p in prePlaces and p not in postPlaces:
            formulas.append(And([m_ip([i-1,places.index(p)])],[m_ip([i,places.index(p)])],[]))
        elif p not in prePlaces and p in postPlaces:
            formulas.append(And([m_ip([i,places.index(p)])],[m_ip([i-1,places.index(p)])],[]))
        else :
            formulas.append(Or([],[],[And([m_ip([i,places.index(p)]),m_ip([i-1,places.index(p)])],[],[]),
                                      And([],[m_ip([i,places.index(p)]),m_ip([i-1,places.index(p)])],[])]))
    And([],[],formulas)

def petri_net_to_SAT(net, m0, mf, variablesGenerator, size_of_run, label_m="m_ip", label_t="tau_it"):
    '''
    This function returns the SAT formulas of a petrinet given label of variables, size_of_run
    :param net: petri net of the librairie pm4py
    :param m0: initial marking
    :param mf: final marking
    :param variablesgenerator: @see darksider4py.variablesGenerator
    :param label_m (string) : name of marking boolean variables per instant i and place p
    :param label_t (string) : name of place boolean variables per instant i and transition t
    :param size_of_run (int) : max instant i
    :param sigma (list of char) : transition name
    :return: a boolean formulas
    '''
    # we need a ordered list to get int per place/transition (for the variablesgenerator)
    transitions=[t for t in net.transitions]
    places=[p for p in net.places]

    # we create the number of variables needed for the markings
    variablesGenerator.add(label_m, [(0,size_of_run),(0,len(places)-1)])

    # we create the number of variables needed for the transitions
    variablesGenerator.add(label_t, [(0,size_of_run-1),(0,len(transitions)-1)])
    return is_run(size_of_run, places, transitions,m0,variablesGenerator.get(label_m),variablesGenerator.get(label_t))


net, m0, mf = importer.pnml.import_net("../examples/example.pnml")
variables=vg.variablesGenerator()
petri_net_to_SAT(net, m0,mf,variables,10)




