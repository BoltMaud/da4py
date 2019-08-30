
from formulas import And,Or


def is_run(n, pn, m_ip,lambda_ia,sigma):
    positives = [m_ip([0,m]) for m in pn.initialMarking]
    negatives = [m_ip([0,m]) for m in (pn.places-pn.initialMarking) ]
    formulas = [is_action(pn,i,m_ip,lambda_ia,sigma) for i in range(1,n+1)]
    run_of_pn = And(positives,negatives,formulas)
    return  run_of_pn

def is_action(pn, i, m_ip, lambda_ia, sigma):
    '''
    :param pn:
    :param i:
    :param m_ip:
    :param lambda_ia:
    :param sigma:
    :return: give action of instant i
    '''

    #only one action is true at instant i
    formulas= [Or([lambda_ia([i,a] for a in sigma)],[],[])]
    # if we have the action a, then we have the good marking and it fires
    for a in sigma:
        one_is_transitions=[]
        for transition in pn.transitions.items():
            if transition.label==a:
                one_is_transitions.append(is_transition(pn,transition,i,m_ip))
        formulas.append(Or([],[lambda_ia([i,a])],one_is_transitions))
    return And([],[],formulas)

def is_transition(pn,transition,i,m_ip):
    formulas=[]
    for place in pn.places.items():
        if place.id in transition.prePlaces and place.id in transition.postPlaces:
            formulas.append(And([m_ip([i,place.id]),m_ip([i-1,place.id])],[],[]))
        elif place.id in transition.prePlaces and place.id not in transition.postPlaces:
            formulas.append(And([m_ip([i-1,place.id])],[m_ip([i,place.id])],[]))
        elif place.id not in transition.prePlaces and place.id in transition.postPlaces:
            formulas.append(And([m_ip([i,place.id])],[m_ip([i-1,place.id])],[]))
        else :
            formulas.append(Or([],[],[And([m_ip([i,place.id]),m_ip([i-1,place.id])],[],[]),
                                      And([],[m_ip([i,place.id]),m_ip([i-1,place.id])],[])]))
    And([],[],formulas)
