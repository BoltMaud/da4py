from src.main.formulas import Or, And


def alignmentEditDistance():
    return None

def antiAlignmentEditDistance():
    return None

def multiAlignmentEditDistance():
    return None

def generalAlignmentEditDistance(net, traces, ):
    return None


def recursionEditDistance(transitions, tau_it, lambda_ia, diid, size_of_run,wait_transition="w",silent_transition="tau", max_d=10):
    formulas=[]
    for i_m in range (0, size_of_run-1):
        for i_t in range (0, size_of_run-1):
            for d in range (0, max_d-1):
                # letters are equals or i_m == "tau" : i_t+1 == i_m+1 => (d i_t i_m d <=> d i_t+1 i_m+1 d)
                letters_are_equals=Or([],[lambda_ia([i_t+1,transitions.index(wait_transition)])],[
                                    And([],[],
                                        [Or([],[tau_it([i_m+1,t]),lambda_ia([i_t+1,t])],[]) for t in (0,len(transitions))]
                                        ),
                                    And([diid([i_m,i_t,d]),diid([i_m+1,i_t+1,d])],[],[]),
                                    And([],[diid([i_m,i_t,d]),diid([i_m+1,i_t+1,d])],[])
                                ])
                formulas.append(letters_are_equals)

                # letters are diff : i_t+1 == i_m+1 => (d i_t i_m d <=> d i_t+1 i_m+1 d)
                letters_are_diff = Or([lambda_ia([i_t+1,transitions.index(wait_transition)]),
                                       tau_it([i_m+1,transitions.index(wait_transition)]),
                                       tau_it([i_m+1,transitions.index(silent_transition)])],
                                      [],
                                      [And([tau_it([i_m+1,t]),lambda_ia([i_t+1,t])],[],[]) for t in range (0,len(transitions))]+[
                                          And([],[diid([i_m+1,i_t+1,d+1 ])],[Or([],[diid([i_m+1,i_t,d])],[diid([i_m,i_t+1,d])])]),
                                          And([diid([i_m+1,i_t+1,d+1 ]),diid([i_m+1,i_t,d])],[diid([i_m,i_t+1,d])],[],[])
                                      ])
                formulas.append(letters_are_diff)

                

def initialisation(transitions, tau_it, lambda_ia, diid, size_of_run, silent_transition="tau", wait_transition="w", max_d=10):

    positives=[]
    # diid is true for d = 0
    for i_m in range (0,size_of_run+1):
        for i_t in range (0,size_of_run+1):
            positives.append(diid([i_m,i_t,0]))

    # diid is false for 0 0 d and d >0
    negatives =[diid([0,0, d]) for d in range (1,max_d+1)]

    formulas =[]

    for d in range (0, max_d-1):
        for i_m in range (0, size_of_run-1):
            # (i_m <> w and i_m <> tau ) <=> (d im+1 0 d+1 <=> d im 0 d )
            i_t_null_and_i_m_cost = Or([tau_it([i_m+1,transitions.index(silent_transition)]),
                                        tau_it([i_m+1, transitions.index(wait_transition)])],
                                        [],
                                        [
                                            And([diid([i_m+1,0,d+1]),diid([i_m,0,d])],[],[]),
                                            And([],[diid([i_m+1,0,d+1]),diid([i_m,0,d])],[])
                                        ])
            formulas.append(i_t_null_and_i_m_cost)

            # (i_m == w or i_m == tau ) <=> (d im+1 0 d+1 <=> d im 0 d )
            i_t_null_and_i_m_dont_cost = Or([],[],[
                                                And([],[tau_it([i_m+1,transitions.index(silent_transition)]),
                                                        tau_it([i_m+1, transitions.index(wait_transition)])],[]),
                                                And([diid([i_m+1,0,d]),diid([i_m,0,d])],[],[]),
                                                And([],[diid([i_m+1,0,d]),diid([i_m,0,d])],[])

                                            ])
            formulas.append(i_t_null_and_i_m_dont_cost)
        for i_t in range (0,size_of_run-1):
            # i_t <> w <=> (d 0 it+1 d+1 <=> d 0 it d )
            i_m_null_and_i_t_cost = Or([lambda_ia([i_t+1,transitions.index(wait_transition)])],[],[
                                        And([diid([0,i_t,d]),diid([0,i_t+1,d+1])],[],[]),
                                        And([],[diid([0,i_t,d]),diid([0,i_t+1,d+1])],[])
                                    ])
            formulas.append(i_m_null_and_i_t_cost)
            # i_t == w <=> (d 0 it+1 d+1 <=> d 0 it d )
            i_m_null_and_i_t_dont_cost = Or([],[lambda_ia([i_t+1,transitions.index(wait_transition)])],[
                                                And([diid([0,i_t,d]),diid([0,i_t+1,d])],[],[]),
                                                And([],[diid([0,i_t,d]),diid([0,i_t+1,d])],[])
                                         ])
            formulas.append(i_m_null_and_i_t_dont_cost)

    return And(positives,negatives,formulas)