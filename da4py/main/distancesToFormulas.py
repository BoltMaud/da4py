from threading import Thread
from da4py.main.formulas import Or, And

SILENT_TRANSITION = "tau"
WAIT_TRANSITION = "w"
BOOLEAN_VAR_MARKING_PN = "m_ip"
BOOLEAN_VAR_FIRING_TRANSITION_PN = "tau_it"
BOOLEAN_VAR_TRACES_ACTIONS = "lambda_jia"
BOOLEAN_VAR_EDIT_DISTANCE = "djiid"
WEIGHT_ON_CLAUSES_TO_REDUCE = -10
NB_MAX_THREADS = 50
MULTI_ALIGNMENT = "multi"
ANTI_ALIGNMENT = "anti"
EXACT_ALIGNMENT = "exact"

# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
# Here starts the dark code : code that should be commented/refactored ect
# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---

def hamming_distance_per_trace_to_SAT(artefact, transitions, silent_transitions, variables, nbTraces, size_of_run ):
    variables.add(BOOLEAN_VAR_EDIT_DISTANCE, [(0, nbTraces), (1, size_of_run + 1)])
    bodyFunction = DICT_OF_HAMMING_BODY[artefact]
    return bodyFunction(transitions, silent_transitions, variables, nbTraces, size_of_run)


def bodyHammingDistance(transitions, silent_transitions, variables, nbTraces, size_of_run):
    formulas = []
    for j in range(0, nbTraces):
        for i in range(1, size_of_run + 1):
            for t in range(0, len(transitions)):
                if transitions[t] not in silent_transitions:
                    create_diff = Or([],
                                     [],
                                     [
                                         And([variables.getVarNumber(BOOLEAN_VAR_FIRING_TRANSITION_PN, [i, t])], [], [
                                             Or([variables.getVarNumber(BOOLEAN_VAR_TRACES_ACTIONS, [j, i, t]),
                                                 variables.getVarNumber(BOOLEAN_VAR_EDIT_DISTANCE, [j, i])], [], [])
                                         ]),
                                         And([], [variables.getVarNumber(BOOLEAN_VAR_FIRING_TRANSITION_PN, [i, t]),
                                                  variables.getVarNumber(BOOLEAN_VAR_TRACES_ACTIONS, [j, i, t]),
                                                  variables.getVarNumber(BOOLEAN_VAR_EDIT_DISTANCE, [j, i])], [])
                                     ])
                else :
                    create_diff = Or([],[variables.getVarNumber(BOOLEAN_VAR_FIRING_TRANSITION_PN, [i, t]),
                           variables.getVarNumber(BOOLEAN_VAR_EDIT_DISTANCE, [j, i])],[])
                formulas.append(create_diff)
    return formulas


def bodyHammingDistance_reducedForMultiAlignment(transitions, silent_transitions,variables, nbTraces, size_of_run):
    formulas = []
    for j in range(0, nbTraces):
        for i in range(1, size_of_run + 1):
            for t in range(0, len(transitions)):
                if transitions[t] not in silent_transitions:
                    create_diff = Or([variables.getVarNumber(BOOLEAN_VAR_TRACES_ACTIONS, [j, i, t]),
                                     variables.getVarNumber(BOOLEAN_VAR_EDIT_DISTANCE, [j, i])],
                                   [variables.getVarNumber(BOOLEAN_VAR_FIRING_TRANSITION_PN, [i, t])], [])
                else :
                    create_diff = Or([],[variables.getVarNumber(BOOLEAN_VAR_FIRING_TRANSITION_PN, [i, t]),
                                         variables.getVarNumber(BOOLEAN_VAR_EDIT_DISTANCE, [j, i])],[])
                formulas.append(create_diff)
    return formulas


def bodyHammingDistance_reducedForAntiAlignment(transitions, silent_transitions,variables, nbTraces, size_of_run):
    formulas = []
    for j in range(0, nbTraces):
        for i in range(1, size_of_run + 1):
            for t in range(0, len(transitions)):
                if transitions[t] not in silent_transitions:
                    create_diff = Or([],[variables.getVarNumber(BOOLEAN_VAR_EDIT_DISTANCE, [j, i])],[
                                        Or([],
                                            [variables.getVarNumber(BOOLEAN_VAR_FIRING_TRANSITION_PN, [i, t]),
                                             variables.getVarNumber(BOOLEAN_VAR_TRACES_ACTIONS, [j, i, t]),],[])
                                    ])
                else :
                    create_diff = Or([],[variables.getVarNumber(BOOLEAN_VAR_FIRING_TRANSITION_PN, [i, t]),
                                                       variables.getVarNumber(BOOLEAN_VAR_EDIT_DISTANCE, [j, i])],[])
                formulas.append(create_diff)
    return formulas


DICT_OF_HAMMING_BODY = {MULTI_ALIGNMENT: bodyHammingDistance_reducedForMultiAlignment,
                        ANTI_ALIGNMENT: bodyHammingDistance_reducedForAntiAlignment,
                        EXACT_ALIGNMENT: bodyHammingDistance}


def edit_distance_per_trace_to_SAT(artefact, transitions,silent_transitions, variables, nbTraces, size_of_run, wait_transition, max_d):
    initialisation_function=DICT_OF_EDIT_INIT[artefact]
    recursion_function = DICT_OF_EDIT_RECURSIONS[artefact]
    variables.add(BOOLEAN_VAR_EDIT_DISTANCE,
                  [(0, nbTraces), (0, size_of_run + 1), (0, size_of_run + 1), (0, max_d + 1)])
    formulas = []

    threads = []
    for i in range(0, NB_MAX_THREADS):
        process = Thread(target=aux_for_threading,
                         args=[formulas, recursion_function,initialisation_function, transitions, silent_transitions,variables, size_of_run, wait_transition,
                               max_d, i, nbTraces])
        process.start()
        threads.append(process)

    # We now pause execution on the main thread by 'joining' all of our started threads.
    for process in threads:
        process.join()

    return formulas


def aux_for_threading(formulas, recursion_function,initialisation_function, transitions,silent_transitions, variables, size_of_run, wait_transition, max_d, i,
                      nbTraces):
    for j in range(i, nbTraces, NB_MAX_THREADS):
        init = initialisation_function(transitions, silent_transitions,variables.getfunction(BOOLEAN_VAR_FIRING_TRANSITION_PN),
                              variables.getfunction(BOOLEAN_VAR_TRACES_ACTIONS),
                              variables.getfunction(BOOLEAN_VAR_EDIT_DISTANCE), j,
                              size_of_run, wait_transition, max_d)
        formulas.append(init)
        rec = recursion_function(transitions, silent_transitions,variables.getfunction(BOOLEAN_VAR_FIRING_TRANSITION_PN),
                                 variables.getfunction(BOOLEAN_VAR_TRACES_ACTIONS),
                                 variables.getfunction(BOOLEAN_VAR_EDIT_DISTANCE), j, size_of_run, wait_transition,
                                 max_d)

        formulas += (rec)
    return True


def initialisation_ReducedForMultiAlignment(transitions, silent_transitions,tau_it, lambda_jia, djiid, j, size_of_run, wait_transition, max_d):
    positives = []
    # diid is true for d = 0
    for i_m in range(0, size_of_run + 1):
        for i_t in range(0, size_of_run + 1):
            positives.append(djiid([j, i_m, i_t, 0]))

    # diid is false for 1 1 d and d >0
    negatives = [djiid([j, 0, 0, d]) for d in range(1, max_d + 1)]

    formulas = []
    for d in range(0, max_d):
        for i_m in range(0, size_of_run):
            # (i_m <> w and i_m <> tau ) <=> (d im+1 0 d+1 <=> d im 0 d )
            condition = [tau_it([i_m + 1, transitions.index(wait_transition)])]
            for st in silent_transitions :
                condition.append(tau_it([i_m + 1, transitions.index(st)]))
            this_condition = condition
            this_condition.append(djiid([j, i_m + 1, 0, d + 1]))
            i_t_null_and_i_m_cost = Or(this_condition, [djiid([j, i_m, 0, d])], [])
            formulas.append(i_t_null_and_i_m_cost)

            # (i_m == w or i_m == tau ) <=> (d im+1 0 d <= d im 0 d )
            i_t_null_and_i_m_dont_cost = Or([djiid([j, i_m + 1, 0, d])], [djiid([j, i_m, 0, d])], [
                                             And([],condition,[])
                                            ])
            formulas.append(i_t_null_and_i_m_dont_cost)
        for i_t in range(0, size_of_run):
            # i_t <> w <=> (d 0 it+1 d+1 <= d 0 it d )
            i_m_null_and_i_t_cost = Or(
                [lambda_jia([j, i_t + 1, transitions.index(wait_transition)]), djiid([j, 0, i_t + 1, d + 1])],
                [djiid([j, 0, i_t, d])], [])
            formulas.append(i_m_null_and_i_t_cost)
            # i_t == w <=> (d 0 it+1 d <= d 0 it d )
            i_m_null_and_i_t_dont_cost = Or([djiid([j, 0, i_t + 1, d])],
                                            [lambda_jia([j, i_t + 1, transitions.index(wait_transition)]),
                                             djiid([j, 0, i_t, d])], [])
            formulas.append(i_m_null_and_i_t_dont_cost)
    return And(positives, negatives, formulas)

def initialisation_ReducedForAntiAlignment(transitions, silent_transitions,tau_it, lambda_jia, djiid, j, size_of_run, wait_transition, max_d):
    positives = []
    # diid is true for d = 0
    for i_m in range(0, size_of_run + 1):
        for i_t in range(0, size_of_run + 1):
            positives.append(djiid([j, i_m, i_t, 0]))

    # diid is false for 1 1 d and d >0
    negatives = [djiid([j, 0, 0, d]) for d in range(1, max_d + 1)]

    formulas = []
    for d in range(0, max_d):
        for i_m in range(0, size_of_run):
            # (i_m <> w and i_m <> tau ) <=> (d im+1 0 d+1 <=> d im 0 d )
            condition = [tau_it([i_m + 1, transitions.index(wait_transition)])]
            for st in silent_transitions :
                condition.append(tau_it([i_m + 1, transitions.index(st)]))
            this_condition = condition
            this_condition.append(djiid([j, i_m , 0, d ]))
            i_t_null_and_i_m_cost = Or(this_condition, [djiid([j, i_m+1, 0, d+1])], [])
            formulas.append(i_t_null_and_i_m_cost)

            # (i_m == w or i_m == tau ) <=> (d im+1 0 d <= d im 0 d )
            i_t_null_and_i_m_dont_cost = Or([djiid([j, i_m , 0, d])], [djiid([j, i_m+1, 0, d])], [
                                            And([],condition,[])
                                        ])
            formulas.append(i_t_null_and_i_m_dont_cost)
        for i_t in range(0, size_of_run):
            # i_t <> w <=> (d 0 it+1 d+1 <= d 0 it d )
            i_m_null_and_i_t_cost = Or(
                [lambda_jia([j, i_t + 1, transitions.index(wait_transition)]), djiid([j, 0, i_t , d ])],
                [djiid([j, 0, i_t+1, d+1])], [])
            formulas.append(i_m_null_and_i_t_cost)
            # i_t == w <=> (d 0 it+1 d <= d 0 it d )
            i_m_null_and_i_t_dont_cost = Or([djiid([j, 0, i_t , d])],
                                            [lambda_jia([j, i_t + 1, transitions.index(wait_transition)]),
                                             djiid([j, 0, i_t+1, d])], [])
            formulas.append(i_m_null_and_i_t_dont_cost)
    return And(positives, negatives, formulas)



def recursionEditDistance(transitions, silent_transitions,tau_it, lambda_jia, djiid, j, size_of_run, wait_transition, max_d):
    formulas = []
    for i_m in range(0, size_of_run):
        for i_t in range(0, size_of_run):
            for d in range(0, max_d):
                # letters are equals or i_m == "tau" : i_t+1 == i_m+1 => (d i_t i_m d <=> d i_t+1 i_m+1 d)

                condition = [tau_it([i_m + 1, transitions.index(st)]) for st in silent_transitions]
                letters_are_equals = Or([], [], [
                    And([], condition,
                        [Or([], [tau_it([i_m + 1, t]), lambda_jia([j, i_t + 1, t])], []) for t in
                         range(0, len(transitions))]
                        ),
                    And([djiid([j, i_m, i_t, d]), djiid([j, i_m + 1, i_t + 1, d])], [], []),
                    And([], [djiid([j, i_m, i_t, d]), djiid([j, i_m + 1, i_t + 1, d])], [])
                ])
                formulas.append(letters_are_equals)

                # letters are diff : i_t+1 == i_m+1 => (d i_t i_m d <=> d i_t+1 i_m+1 d)
                condition = [tau_it([i_m + 1, transitions.index(wait_transition)]),
                             lambda_jia([j, i_t + 1, transitions.index(wait_transition)])]
                for st in silent_transitions :
                    condition.append(tau_it([i_m + 1, transitions.index(st)]))

                list_of_letters_are_diff = [And([tau_it([i_m + 1, t]), lambda_jia([j, i_t + 1, t])], [], []) for
                                            t in range(0, len(transitions))]

                list_of_letters_are_diff.append(And([], [djiid([j, i_m + 1, i_t + 1, d + 1])], [Or([], [
                    djiid([j, i_m + 1, i_t, d]), djiid([j, i_m, i_t + 1, d])], [])]))
                list_of_letters_are_diff.append(And([djiid([j, i_m + 1, i_t + 1, d + 1]),
                                                     djiid([j, i_m + 1, i_t, d]), djiid([j, i_m, i_t + 1, d])], [],
                                                    []))
                letters_are_diff = Or(condition, [], list_of_letters_are_diff)
                formulas.append(letters_are_diff)

                # ( u_t == w and u_m <> w) => ( d i_m i_t d <=> d i_m+1 i_t d
                finish_run_of_model = Or([tau_it([i_m + 1, transitions.index(wait_transition)])],
                                         [lambda_jia([j, i_t + 1, transitions.index(wait_transition)])], [
                                             And([djiid([j, i_m + 1, i_t + 1, d]), djiid([j, i_m + 1, i_t, d])], [],
                                                 []),
                                             And([], [djiid([j, i_m + 1, i_t + 1, d]), djiid([j, i_m + 1, i_t, d])],
                                                 [])
                                         ])
                formulas.append(finish_run_of_model)

                # ( u_m == w and u_t <> w) => ( d i_m i_t d <=> d i_m i_t+1 d
                finish_run_of_trace = Or([lambda_jia([j, i_t + 1, transitions.index(wait_transition)])],
                                         [tau_it([i_m + 1, transitions.index(wait_transition)])], [
                                             And([djiid([j, i_m + 1, i_t + 1, d]), djiid([j, i_m, i_t + 1, d])], [],
                                                 []),
                                             And([], [djiid([j, i_m + 1, i_t + 1, d]), djiid([j, i_m, i_t + 1, d])],
                                                 [])
                                         ])

                formulas.append(finish_run_of_trace)

    return formulas


def recursionEditDistance__reducedForAntiAlignment(transitions, silent_transitions,tau_it, lambda_jia, djiid, j, size_of_run, wt, max_d):
    def t(transition):
        return transitions.index(transition)

    formulas = []
    for i_m in range(0, size_of_run):
        for i_t in range(0, size_of_run):
            for d in range(0, max_d):

                # letters are equals : i_m == "tau" or i_t+1 == i_m+1 => (d i_t i_m d <=> d i_t+1 i_m+1 d)
                letters_are_equals = Or([djiid([j, i_m, i_t, d + 1])],
                                        [djiid([j, i_m + 1, i_t + 1, d + 1])],
                                        [
                                            And([],
                                                [tau_it([i_m + 1, t(st)]) for st in silent_transitions],
                                                [Or([],
                                                    [tau_it([i_m + 1, t]), lambda_jia([j, i_t + 1, t])],
                                                    []) for t in range(0, len(transitions))
                                                 ])
                                        ])
                formulas.append(letters_are_equals)

                # letters are diff : i_t+1 == i_m+1 => (d i_t i_m d <=> d i_t+1 i_m+1 d)
                condition = [tau_it([i_m + 1, t(wt)]),
                             lambda_jia([j, i_t + 1, t(wt)])]
                for st in silent_transitions:
                    condition.append(tau_it([i_m + 1, t(st)]))

                and_in_this = [And([tau_it([i_m + 1, t]), lambda_jia([j, i_t + 1, t])], [], []) for
                               t in range(0, len(transitions))]
                and_in_this.append(And([djiid([j, i_m + 1, i_t, d]), djiid([j, i_m, i_t + 1, d])], [], []))

                letters_are_diff = Or(condition, [djiid([j, i_m + 1, i_t + 1, d + 1])], and_in_this
                                      )
                formulas.append(letters_are_diff)

                # ( u_t == w and u_m <> w) => ( d i_m i_t d <=> d i_m+1 i_t d
                finish_run_of_model = Or([tau_it([i_m + 1, t(wt)]), djiid([j, i_m + 1, i_t, d])],
                                         [lambda_jia([j, i_t + 1, t(wt)]), djiid([j, i_m + 1, i_t + 1, d])],
                                         [])
                formulas.append(finish_run_of_model)

                # ( u_m == w and u_t <> w) => ( d i_m i_t d <=> d i_m i_t+1 d
                finish_run_of_trace = Or([lambda_jia([j, i_t + 1, t(wt)]), djiid([j, i_m, i_t + 1, d])],
                                         [tau_it([i_m + 1, t(wt)]), djiid([j, i_m + 1, i_t + 1, d])], [])

                formulas.append(finish_run_of_trace)

    return formulas


def recursionEditDistance_reducedForMultiAlignment(transitions,silent_transitions, tau_it, lambda_jia, djiid, j, size_of_run,
                                                   wait_transition, max_d):
    formulas = []
    for i_m in range(0, size_of_run):
        for i_t in range(0, size_of_run):
            for d in range(0, max_d):
                # letters are equals or i_m == "tau" : i_t+1 == i_m+1 => (d i_t i_m d <=> d i_t+1 i_m+1 d)
                condition = [
                    tau_it([i_m + 1, transitions.index(st)]) for st in silent_transitions]
                letters_are_equals = Or([djiid([j, i_m + 1, i_t + 1, d])], [djiid([j, i_m, i_t, d])], [
                    And([], condition,
                        [Or([], [tau_it([i_m + 1, t]), lambda_jia([j, i_t + 1, t])], []) for t in
                         range(0, len(transitions))]
                        )])
                formulas.append(letters_are_equals)

                # letters are diff : i_t+1 == i_m+1 => (d i_t i_m d <=> d i_t+1 i_m+1 d)
                condition = [tau_it([i_m + 1, transitions.index(wait_transition)]),
                             lambda_jia([j, i_t + 1, transitions.index(wait_transition)])]
                for st in silent_transitions :
                    condition.append(tau_it([i_m + 1, transitions.index(st)]))

                condition.append(djiid([j, i_m + 1, i_t + 1, d + 1]))
                letters_are_diff = Or(condition, [djiid([j, i_m + 1, i_t, d]), djiid([j, i_m, i_t + 1, d])],
                                      [And([tau_it([i_m + 1, t]), lambda_jia([j, i_t + 1, t])], [], []) for
                                       t in range(0, len(transitions))])
                formulas.append(letters_are_diff)

                # ( u_t == w and u_m <> w) => ( d i_m i_t d <=> d i_m+1 i_t d
                finish_run_of_model = Or(
                    [tau_it([i_m + 1, transitions.index(wait_transition)]), djiid([j, i_m + 1, i_t + 1, d])],
                    [lambda_jia([j, i_t + 1, transitions.index(wait_transition)]), djiid([j, i_m + 1, i_t, d])],
                    [])
                formulas.append(finish_run_of_model)

                # ( u_m == w and u_t <> w) => ( d i_m i_t d <=> d i_m i_t+1 d
                finish_run_of_trace = Or(
                    [lambda_jia([j, i_t + 1, transitions.index(wait_transition)]), djiid([j, i_m + 1, i_t + 1, d])],
                    [tau_it([i_m + 1, transitions.index(wait_transition)]), djiid([j, i_m, i_t + 1, d])], [])

                formulas.append(finish_run_of_trace)
    return formulas


DICT_OF_EDIT_RECURSIONS = {MULTI_ALIGNMENT: recursionEditDistance_reducedForMultiAlignment,
                           ANTI_ALIGNMENT: recursionEditDistance__reducedForAntiAlignment,
                           EXACT_ALIGNMENT: recursionEditDistance}
DICT_OF_EDIT_INIT= {MULTI_ALIGNMENT: initialisation_ReducedForMultiAlignment,
                    ANTI_ALIGNMENT: initialisation_ReducedForAntiAlignment,
                    EXACT_ALIGNMENT: initialisation_ReducedForMultiAlignment}