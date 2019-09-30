import time

from pm4py.objects.petri.petrinet import PetriNet, Marking

from src.main.formulas import Or, And
from src.main import variablesGenerator as vg
from src.main.logToFormulas import log_to_SAT
from src.main.pnToFormulas import petri_net_to_SAT
from pysat.examples.rc2 import RC2
from pm4py.visualization.petrinet import factory as vizu
from pysat.formula import WCNF

import multiprocessing as mp
from functools import partial
from threading import Thread

SAT_SOLVERS = ['cd', 'g3', 'g4', 'lgl', 'mcm', 'mcb', 'mpl', 'mc', 'm22', 'mgh']
SILENT_TRANSITION = "tau"
WAIT_TRANSITION = "w"
BOOLEAN_VAR_MARKING_PN = "m_ip"
BOOLEAN_VAR_FIRING_TRANSITION_PN = "tau_it"
BOOLEAN_VAR_TRACES_ACTIONS = "lambda_jia"
BOOLEAN_VAR_EDIT_DISTANCE = "djiid"
WEIGHT_ON_CLAUSES_TO_REDUCE = -10
NB_MAX_THREADS=50


def alignmentEditDistance(net, m0, mf, traces, size_of_run, silent_transition="tau", max_d=10, solver_name='g4'):
    solution, variables, transitions, traces = generalAlignmentEditDistance(net, m0, mf, traces, size_of_run,
                                                                            anti_alignment=False,
                                                                            silent_transition="tau", max_d=10,
                                                                            solver_name='g4')

    run = "<"
    word = ""
    for var in solution:
        if variables.getVarName(var) != None and variables.getVarName(var).startswith("tau"):
            index = variables.getVarName(var).split("]")[0].split(",")[1]
            i = variables.getVarName(var).split("[")[1].split(",")[0]
            run += " (" + i + ", " + str(transitions[int(index)]) + "),"
        if var > 0 and variables.getVarName(var) != None:
            if variables.getVarName(var).startswith("lambda"):
                index = variables.getVarName(var).split("]")[0].split(",")[2]
                i = variables.getVarName(var).split("[")[1].split(",")[1]
                if int(i) == 1:
                    word += "\n"
                word += " (" + i + ", " + str(transitions[int(index)]) + "),"

    run += ">"
    print("RUN", run)
    print("WORDS", word)

    for l in range(0, len(traces)):
        max = 0
        for d in range(0, max_d + 1):
            if variables.getVarNumber(BOOLEAN_VAR_EDIT_DISTANCE, [l, size_of_run, size_of_run, d]) in solution:
                max = d
        print(l, " :", max)

    return None


def antiAlignmentEditDistance():
    return None


def multiAlignmentEditDistance():
    return None


def generalAlignmentEditDistance(net, m0, mf, traces, size_of_run, anti_alignment=False, silent_transition="tau",
                                 max_d=10, solver_name='g4'):
    variables = vg.VariablesGenerator()
    net, wait_transition = add_wait_net(net)

    start = time.time()

    pn_formula, places, transitions = petri_net_to_SAT(net, m0, mf, variables, size_of_run,
                                                       label_m=BOOLEAN_VAR_MARKING_PN,
                                                       label_t=BOOLEAN_VAR_FIRING_TRANSITION_PN)
    log_formula, traces = log_to_SAT(traces, transitions, variables, size_of_run, wait_transition)
    distances_formula = edit_distance_per_trace_to_SAT(transitions, variables, len(traces), size_of_run,
                                                       wait_transition, max_d)

    formulas = [pn_formula, log_formula] + distances_formula
    full_formula = And([], [], formulas)
    cnf = full_formula.clausesToCnf(variables.iterator)

    wcnf = WCNF()
    wcnf.extend(cnf)

    weight_for_anti_alignment = -1 if not anti_alignment else 1
    for d in range(1, max_d + 1):
        wcnf.append([weight_for_anti_alignment * variables.getVarNumber(BOOLEAN_VAR_EDIT_DISTANCE,
                                                                        [0, size_of_run, size_of_run, d])],
                    WEIGHT_ON_CLAUSES_TO_REDUCE)

    formula_time = time.time()
    print("Construction de la formule =", formula_time - start)

    solver = RC2(wcnf, solver=solver_name)
    solver.compute()
    end_solver = time.time()
    print("Solve  =", end_solver - formula_time)
    model = solver.model

    return model, variables, transitions, traces


def edit_distance_per_trace_to_SAT(transitions, variables, nbTraces, size_of_run, wait_transition, max_d):
    variables.add(BOOLEAN_VAR_EDIT_DISTANCE,
                  [(0, nbTraces), (0, size_of_run + 1), (0, size_of_run + 1), (0, max_d + 1)])
    formulas = []

    threads = []
    for i in range (0,NB_MAX_THREADS):
        process = Thread(target=aux_for_threading,
                         args=[formulas, transitions, variables, size_of_run, wait_transition, max_d, i,nbTraces])
        process.start()
        threads.append(process)

    # We now pause execution on the main thread by 'joining' all of our started threads.
    for process in threads:
        process.join()

    return formulas


def aux_for_threading(formulas, transitions, variables, size_of_run, wait_transition, max_d, i, nbTraces):

    for j in range (i,nbTraces,NB_MAX_THREADS):
        print(j)
        init = initialisation(transitions, variables.getfunction(BOOLEAN_VAR_FIRING_TRANSITION_PN),
                              variables.getfunction(BOOLEAN_VAR_TRACES_ACTIONS),
                              variables.getfunction(BOOLEAN_VAR_EDIT_DISTANCE), j,
                              size_of_run + 1, wait_transition, max_d=max_d)
        formulas.append(init)

        rec = recursionEditDistance(variables, transitions, variables.getfunction(BOOLEAN_VAR_FIRING_TRANSITION_PN),
                                    variables.getfunction(BOOLEAN_VAR_TRACES_ACTIONS),
                                    variables.getfunction(BOOLEAN_VAR_EDIT_DISTANCE), j, size_of_run + 1, wait_transition,
                                    max_d=max_d)

        formulas += (rec)

    return True


def recursionEditDistance(variables, transitions, tau_it, lambda_jia, djiid, j, size_of_run, wait_transition,
                          silent_transition="tau", max_d=10):
    formulas = []
    for i_m in range(0, size_of_run - 1):
        for i_t in range(0, size_of_run - 1):
            for d in range(0, max_d - 1):
                # letters are equals or i_m == "tau" : i_t+1 == i_m+1 => (d i_t i_m d <=> d i_t+1 i_m+1 d)

                condition = [
                    tau_it([i_m + 1, transitions.index(silent_transition)])] if silent_transition in transitions else []
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
                if silent_transition in transitions:
                    condition.append(tau_it([i_m + 1, transitions.index(silent_transition)]))

                list_of_letters_are_diff = [And([tau_it([i_m + 1, t]), lambda_jia([j, i_t + 1, t])], [], []) for
                                            t in range(0, len(transitions))]
                
                list_of_letters_are_diff.append(And([], [djiid([j, i_m + 1, i_t + 1, d + 1])], [Or([], [
                    djiid([j, i_m + 1, i_t, d]), djiid([j, i_m, i_t + 1, d])], [])]))
                list_of_letters_are_diff.append(And([djiid([j, i_m + 1, i_t + 1, d + 1]),
                                                     djiid([j, i_m + 1, i_t, d]), djiid([j, i_m, i_t + 1, d])], [],
                                                    []))
                letters_are_diff = Or(condition,[],list_of_letters_are_diff)
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


def initialisation(transitions, tau_it, lambda_jia, djiid, j, size_of_run, wait_transition, silent_transition="tau",
                   max_d=10):
    positives = []
    # diid is true for d = 0
    for i_m in range(0, size_of_run):
        for i_t in range(0, size_of_run):
            positives.append(djiid([j, i_m, i_t, 0]))

    # diid is false for 1 1 d and d >0
    negatives = [djiid([j, 0, 0, d]) for d in range(1, max_d)]

    formulas = []
    for d in range(0, max_d - 1):
        for i_m in range(0, size_of_run - 1):
            # (i_m <> w and i_m <> tau ) <=> (d im+1 0 d+1 <=> d im 0 d )
            condition = [tau_it([i_m + 1, transitions.index(wait_transition)])]
            if silent_transition in transitions:
                condition.append(tau_it([i_m + 1, transitions.index(silent_transition)]))
            i_t_null_and_i_m_cost = Or(condition, [], [
                    And([djiid([j, i_m + 1, 0, d + 1]), djiid([j, i_m, 0, d])], [], []),
                    And([], [djiid([j, i_m + 1, 0, d + 1]), djiid([j, i_m, 0, d])], [])
                ])
            formulas.append(i_t_null_and_i_m_cost)

            # (i_m == w or i_m == tau ) <=> (d im+1 0 d+1 <=> d im 0 d )
            i_t_null_and_i_m_dont_cost = Or([], [], [
                    And([], condition, []),
                    And([djiid([j, i_m + 1, 0, d]), djiid([j, i_m, 0, d])], [], []),
                    And([], [djiid([j, i_m + 1, 0, d]), djiid([j, i_m, 0, d])], [])
                ])
            formulas.append(i_t_null_and_i_m_dont_cost)
        for i_t in range(0, size_of_run - 1):
            # i_t <> w <=> (d 0 it+1 d+1 <=> d 0 it d )
            i_m_null_and_i_t_cost = Or([lambda_jia([j, i_t + 1, transitions.index(wait_transition)])], [], [
                    And([djiid([j, 0, i_t, d]), djiid([j, 0, i_t + 1, d + 1])], [], []),
                    And([], [djiid([j, 0, i_t, d]), djiid([j, 0, i_t + 1, d + 1])], [])
                ])
            formulas.append(i_m_null_and_i_t_cost)
            # i_t == w <=> (d 0 it+1 d+1 <=> d 0 it d )
            i_m_null_and_i_t_dont_cost = Or([], [lambda_jia([j, i_t + 1, transitions.index(wait_transition)])], [
                    And([djiid([j, 0, i_t, d]), djiid([j, 0, i_t + 1, d])], [], []),
                    And([], [djiid([j, 0, i_t, d]), djiid([j, 0, i_t + 1, d])], [])
                    ])
            formulas.append(i_m_null_and_i_t_dont_cost)

    return And(positives, negatives, formulas)


def add_wait_net(net, wait_transition="w"):
    transition = PetriNet.Transition(wait_transition, wait_transition)
    for place in net.places:
        if len(place.out_arcs) == 0:
            arcIn = PetriNet.Arc(place, transition)
            arcOut = PetriNet.Arc(transition, place)
            net.arcs.add(arcIn)
            net.arcs.add(arcOut)
            transition.in_arcs.add(arcIn)
            transition.out_arcs.add(arcOut)
            place.out_arcs.add(arcIn)
            place.in_arcs.add(arcOut)
    net.transitions.add(transition)
    return net, transition
