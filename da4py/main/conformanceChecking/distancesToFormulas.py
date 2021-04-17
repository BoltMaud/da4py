#!/usr/bin/env python
# -*- coding:utf-8 -*-
##
## distancesToFormulas.py
##
##  Created on: September, 2019
##      Author: Boltenhagen Mathilde
##      E-mail: boltenhagen lsv . fr
##

'''

This file contains 6 formulas :
    -   the exact hamming distance
    -   the hamming with a reduction of the formula in the cas of multi-alignment
    -   the hamming with a reduction of the formula in the cas of anti-alignment
    -   the exact edit distance
    -   the edit distance with a reduction of the formula in the cas of multi-alignment
    -   the edit distance with a reduction of the formula in the cas of anti-alignment

2 generic functions (hamming_distance_per_trace_to_SAT and edit_distance_per_trace_to_SAT) are called by the ConformanceArtefacts
class. With the global variables (MULTI_ALIGNMENT, ANTI_ALIGNMENT and EXACT_ALIGNMENT), the generic functions call the right
specific functions. Three dictionaries are defined for that : DICT_OF_HAMMING_BODY, DICT_OF_EDIT_RECURSIONS and DICT_OF_EDIT_INIT.

Scientific paper : _Encoding Conformance Checking Artefacts in SAT_
By : Mathilde Boltenhagen, Thomas Chatain, Josep Carmona

'''
from threading import Thread
from da4py.main.utils.formulas import Or, And
import itertools

# our boolean formulas depends on variables, see our paper for more information
BOOLEAN_VAR_MARKING_PN = "m_ip"
BOOLEAN_VAR_FIRING_TRANSITION_PN = "tau_it"
BOOLEAN_VAR_TRACES_ACTIONS = "lambda_jia"
BOOLEAN_VAR_EDIT_DISTANCE = "djiid"
BOOLEAN_VAR_HAMMING_DISTANCE="dji"
BOOLEAN_VAR_HAMMING_SUP_AUX="supjd"

# some parallelism
NB_MAX_THREADS = 50

# the different artefacts, inputs of the generic functions
MULTI_ALIGNMENT = "multi"
ANTI_ALIGNMENT = "anti"
EXACT_ALIGNMENT = "exact"

def for_hamming_distance_aux_supd(artefact, vars, lenTraces, max_d, size_of_run):
    if artefact==MULTI_ALIGNMENT:
        return for_hamming_distance_aux_supd_multi(vars, lenTraces, max_d, size_of_run)
    else:
        return for_hamming_distance_aux_supd_anti(vars, lenTraces, max_d, size_of_run)

def for_hamming_distance_aux_supd_anti(variables,lenTraces,max_d,size_of_run):
    list_of_formula=[]
    list_to_size_of_run= list(range(1,size_of_run+1))
    not_d_or_and_diff=[]
    for j in range (0, lenTraces):
        for d in range(1,min(max_d + 1,size_of_run+1)):
            combinaisons_of_instants=list(itertools.combinations(list_to_size_of_run,d))
            and_sub_instants=[]
            for sub_list_of_instants in combinaisons_of_instants:
                instants_to_combine=[]
                for instant in list(sub_list_of_instants):
                    instants_to_combine.append(variables.get(BOOLEAN_VAR_HAMMING_DISTANCE, [j, instant]))
                and_sub_instants.append(And(instants_to_combine,[],[]))
            not_d_or_and_diff.append(Or([], [variables.get(BOOLEAN_VAR_HAMMING_SUP_AUX, [j, d])], and_sub_instants))
    list_of_formula.append(And([],[],not_d_or_and_diff))
    return list_of_formula

def for_hamming_distance_aux_supd_multi(vars, lenTraces, max_d, size_of_run):
    list_of_formula=[]
    list_to_size_of_run= list(range(1,size_of_run+1))
    not_d_or_and_diff=[]
    for j in range (0, lenTraces):
        for d in range(1,min(max_d + 1,size_of_run+1)):
            combinaisons_of_instants=list(itertools.combinations(list_to_size_of_run,d))
            and_sub_instants=[]
            for sub_list_of_instants in combinaisons_of_instants:
                instants_to_combine=[]
                for instant in list(sub_list_of_instants):
                    instants_to_combine.append(vars.get(BOOLEAN_VAR_HAMMING_DISTANCE, [j, instant]))
                and_sub_instants.append(Or([],instants_to_combine,[]))
            not_d_or_and_diff.append(Or([vars.get(BOOLEAN_VAR_HAMMING_SUP_AUX, [j, d])], [], [And([], [], and_sub_instants)]))
    list_of_formula.append(And([],[],not_d_or_and_diff))
    return list_of_formula

def hamming_distance_per_trace_to_SAT(artefact, transitions, silent_transitions, vars, nbTraces, size_of_run):
    '''
    Generic function that calls either bodyHammingDistance(), bodyHammingDistance_reducedForMultiAlignment() or
    bodyHammingDistance_reducedForAntiAlignment() depending on artefact value
    :param artefact (string) : one of the global variables (MULTI_ALIGNMENT, ANTI_ALIGNMENT and EXACT_ALIGNMENT)
    :param transitions (list) : the transitions
    :param silent_transitions (list) : the silent transitions
    :param variables (variablesGenerator) : to creates the variables numbers
    :param nbTraces (int) : number of traces
    :param size_of_run (int) : maximal size of run
    :return: formula
    '''
    vars.add(BOOLEAN_VAR_HAMMING_DISTANCE, [(0, nbTraces), (0, size_of_run + 1)])
    bodyFunction = DICT_OF_HAMMING_BODY[artefact]
    return bodyFunction(transitions, silent_transitions, vars, nbTraces, size_of_run)


def bodyHammingDistance(transitions, silent_transitions, vars, nbTraces, size_of_run):
    '''
    Exact formula of hamming distance.
    :param transitions (list) : the transitions
    :param silent_transitions (list) : the silent transitions
    :param variables (variablesGenerator) : to creates the variables numbers
    :param nbTraces (int) : number of traces
    :param size_of_run (int) : maximal size of run
    :return: formula
    '''
    formulas = []
    for j in range(0, nbTraces):
        for i in range(1, size_of_run + 1):
            for t in range(0, len(transitions)):
                if transitions[t] not in silent_transitions:
                    create_diff = Or([],
                                     [],
                                     [
                                         And([vars.get(BOOLEAN_VAR_FIRING_TRANSITION_PN, [i, t])], [], [
                                             Or([vars.get(BOOLEAN_VAR_TRACES_ACTIONS, [j, i, t]),
                                                 vars.get(BOOLEAN_VAR_HAMMING_DISTANCE, [j, i])], [], [])
                                         ]),
                                         And([], [vars.get(BOOLEAN_VAR_FIRING_TRANSITION_PN, [i, t]),
                                                  vars.get(BOOLEAN_VAR_TRACES_ACTIONS, [j, i, t]),
                                                  vars.get(BOOLEAN_VAR_HAMMING_DISTANCE, [j, i])], [])
                                     ])
                else:
                    create_diff = Or([], [vars.get(BOOLEAN_VAR_FIRING_TRANSITION_PN, [i, t]),
                                          vars.get(BOOLEAN_VAR_HAMMING_DISTANCE, [j, i])], [])
                formulas.append(create_diff)
    return formulas


def bodyHammingDistance_reducedForMultiAlignment(transitions, silent_transitions, vars, nbTraces, size_of_run):
    '''
    Reduced formula of hamming distance for multi-alignment
    :param transitions (list) : the transitions
    :param silent_transitions (list) : the silent transitions
    :param variables (variablesGenerator) : to creates the variables numbers
    :param nbTraces (int) : number of traces
    :param size_of_run (int) : maximal size of run
    :return: formula
    '''
    formulas = []
    for j in range(0, nbTraces):
        for i in range(1, size_of_run + 1):
            for t in range(0, len(transitions)):
                if transitions[t] not in silent_transitions:
                    # tau_i,t => (lamdba_i,a or diff_i )
                    create_diff = Or([vars.get(BOOLEAN_VAR_TRACES_ACTIONS, [j, i, t]),
                                      vars.get(BOOLEAN_VAR_HAMMING_DISTANCE, [j, i])],
                                     [vars.get(BOOLEAN_VAR_FIRING_TRANSITION_PN, [i, t])], [])
                else:
                    # tau_i,silent => not diff_i
                    create_diff = Or([], [vars.get(BOOLEAN_VAR_FIRING_TRANSITION_PN, [i, t]),
                                          vars.get(BOOLEAN_VAR_HAMMING_DISTANCE, [j, i])], [])
                formulas.append(create_diff)
    return formulas


def bodyHammingDistance_reducedForAntiAlignment(transitions, silent_transitions, vars, nbTraces, size_of_run):
    '''
    Reduced formula of hamming distance for anti-alignment
    :param transitions (list) : the transitions
    :param silent_transitions (list) : the silent transitions
    :param variables (variablesGenerator) : to creates the variables numbers
    :param nbTraces (int) : number of traces
    :param size_of_run (int) : maximal size of run
    :return: formula
    '''
    formulas = []
    for j in range(0, nbTraces):
        for i in range(1, size_of_run + 1):
            for t in range(0, len(transitions)):
                if transitions[t] not in silent_transitions:
                    # (tau_i,t and lambda_i,t ) => not diff_i
                    create_diff = Or([], [vars.get(BOOLEAN_VAR_HAMMING_DISTANCE, [j, i])], [
                        Or([],
                           [vars.get(BOOLEAN_VAR_FIRING_TRANSITION_PN, [i, t]),
                            vars.get(BOOLEAN_VAR_TRACES_ACTIONS, [j, i, t]), ], [])
                    ])
                else:
                    # tau_ti => not diff_i
                    create_diff = Or([], [vars.get(BOOLEAN_VAR_FIRING_TRANSITION_PN, [i, t]),
                                          vars.get(BOOLEAN_VAR_HAMMING_DISTANCE, [j, i])], [])
                formulas.append(create_diff)
    return formulas


# dictonary of functions used by the generic function hamming_distance_per_trace_to_SAT()
DICT_OF_HAMMING_BODY = {MULTI_ALIGNMENT: bodyHammingDistance_reducedForMultiAlignment,
                        ANTI_ALIGNMENT: bodyHammingDistance_reducedForAntiAlignment,
                        EXACT_ALIGNMENT: bodyHammingDistance}


def edit_distance_per_trace_to_SAT(artefact, transitions, silent_transitions, vars, nbTraces, size_of_run,
                                   wait_transition, max_d):
    '''
    Generic function of the edit distance.
    :param artefact (string) : one of the global variables (MULTI_ALIGNMENT, ANTI_ALIGNMENT and EXACT_ALIGNMENT)
    :param transitions (list) : the transitions
    :param silent_transitions (list) : the silent transitions
    :param variables (variablesGenerator) : to creates the variables numbers
    :param nbTraces (int) : number of traces
    :param size_of_run (int) : maximal size of run
    :param wait_transition (transition) : end of words
    :param max_d (int) : heuristic because formula are too large
    :return: formula
    '''
    # gets the right functions
    initialisation_function = DICT_OF_EDIT_INIT[artefact]
    recursion_function = DICT_OF_EDIT_RECURSIONS[artefact]
    # add djiid boolean variables. See paper _Encoding Conformance Checking Artefacts in SAT_ for more details
    vars.add(BOOLEAN_VAR_EDIT_DISTANCE,
             [(0, nbTraces), (0, size_of_run + 1), (0, size_of_run + 1), (0, max_d + 1)])

    # some simple parallelism
    formulas = []
    threads = []
    for i in range(0, NB_MAX_THREADS):
        process = Thread(target=aux_for_threading,
                         args=[formulas, recursion_function, initialisation_function, transitions, silent_transitions,
                               vars, size_of_run, wait_transition,
                               max_d, i, nbTraces])
        process.start()
        threads.append(process)
    for process in threads:
        process.join()

    return formulas


def aux_for_threading(formulas, recursion_function, initialisation_function, transitions, silent_transitions, vars,
                      size_of_run, wait_transition, max_d, i,
                      nbTraces):
    '''
    Auxiliary function that does the parallelism and call the initialisation_function and recursion_function of the edit distance to create the formula.
    :param formulas (list) : list to fill
    :param recursion_function (fun) : name of the recursion function which depends on the artefact
    :param initialisation_function (fun) : name of the init function which depends on the artefact
    :param transitions (list) : list of transitions
    :param silent_transitions (list) : the silent transitions
    :param variables (variablesGenerator) : to creates the variables numbers
    :param nbTraces (int) : number of traces
    :param size_of_run (int) : maximal size of run
    :param wait_transition (transition) : end of words
    :param max_d (int) : heuristic because formula are too large
    :param i (int) : for parallelism
    :return:
    '''
    # each thread does some edit distance formula of some trace
    for j in range(i, nbTraces, NB_MAX_THREADS):
        init = initialisation_function(transitions, silent_transitions,
                                       vars.getFunction(BOOLEAN_VAR_FIRING_TRANSITION_PN),
                                       vars.getFunction(BOOLEAN_VAR_TRACES_ACTIONS),
                                       vars.getFunction(BOOLEAN_VAR_EDIT_DISTANCE), j,
                                       size_of_run, wait_transition, max_d)
        formulas.append(init)
        rec = recursion_function(transitions, silent_transitions,
                                 vars.getFunction(BOOLEAN_VAR_FIRING_TRANSITION_PN),
                                 vars.getFunction(BOOLEAN_VAR_TRACES_ACTIONS),
                                 vars.getFunction(BOOLEAN_VAR_EDIT_DISTANCE), j, size_of_run, wait_transition,
                                 max_d)

        formulas += (rec)
    return True


def initialisation_ReducedForMultiAlignment(transitions, silent_transitions, tau_it, lambda_jia, djiid, j, size_of_run,
                                            wait_transition, max_d):
    '''
    Initialisation of the edit distance reduced for multi-alignmet.
    This is the 3 first axioms of the _Encoding Conformance Checking Artefacts in SAT_ paper
    :param transitions (list) : list of transitions
    :param silent_transitions (list) : list of the silent transitions
    :param tau_it (fun) : function that returns the boolean variable number of the firing transition t at an instant i
    :param lambda_jia (fun) : function that returns the boolean variable number of the letter of trace j at instant i
    :param djiid (fun) : function that returns the boolean variable that says at instant i and i of we have d distance
    :param j (int) : jth trace
    :param size_of_run (int) : maximal size of a run
    :param wait_transition (transition) : to finish words
    :param max_d (int): heuristic
    :return: formula
    '''

    def t(transition):
        return transitions.index(transition)

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
            # (i_m <> w and i_m <> tau ) <=> (d im+1 0 d+1 <= d im 0 d )
            condition = [tau_it([i_m + 1, t(wait_transition)])]
            for st in silent_transitions:
                condition.append(tau_it([i_m + 1, t(st)]))
            this_condition = condition
            this_condition.append(djiid([j, i_m + 1, 0, d + 1]))
            i_t_null_and_i_m_cost = Or(this_condition, [djiid([j, i_m, 0, d])], [])
            formulas.append(i_t_null_and_i_m_cost)

            # (i_m == w or i_m == tau ) <=> (d im+1 0 d <= d im 0 d )
            i_t_null_and_i_m_dont_cost = Or([djiid([j, i_m + 1, 0, d])], [djiid([j, i_m, 0, d])], [
                And([], condition, [])
            ])
            formulas.append(i_t_null_and_i_m_dont_cost)

        for i_t in range(0, size_of_run):
            # i_t <> w <=> (d 0 it+1 d+1 <= d 0 it d )
            i_m_null_and_i_t_cost = Or([lambda_jia([j, i_t + 1, t(wait_transition)]), djiid([j, 0, i_t + 1, d + 1])],
                                       [djiid([j, 0, i_t, d])], [])
            formulas.append(i_m_null_and_i_t_cost)

            # i_t == w <=> (d 0 it+1 d <= d 0 it d )
            i_m_null_and_i_t_dont_cost = Or([djiid([j, 0, i_t + 1, d])],
                                            [lambda_jia([j, i_t + 1, t(wait_transition)]), djiid([j, 0, i_t, d])], [])
            formulas.append(i_m_null_and_i_t_dont_cost)

    return And(positives, negatives, formulas)


def initialisation_ReducedForAntiAlignment(transitions, silent_transitions, tau_it, lambda_jia, djiid, j, size_of_run,
                                           wait_transition, max_d):
    '''
   Initialisation of the edit distance reduced for anti-alignmet.
   This is the 3 first axioms of the _Encoding Conformance Checking Artefacts in SAT_ paper
   :param transitions (list) : list of transitions
   :param silent_transitions (list) : list of the silent transitions
   :param tau_it (fun) : function that returns the boolean variable number of the firing transition t at an instant i
   :param lambda_jia (fun) : function that returns the boolean variable number of the letter of trace j at instant i
   :param djiid (fun) : function that returns the boolean variable that says at instant i and i of we have d distance
   :param j (int) : jth trace
   :param size_of_run (int) : maximal size of a run
   :param wait_transition (transition) : to finish words
   :param max_d (int): heuristic
   :return: formula
   '''

    def t(transition):
        return transitions.index(transition)

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
            # (i_m <> w and i_m <> tau ) <=> (d im+1 0 d+1 => d im 0 d )
            condition = [tau_it([i_m + 1, t(wait_transition)])]
            for st in silent_transitions:
                condition.append(tau_it([i_m + 1, t(st)]))
            this_condition = condition
            this_condition.append(djiid([j, i_m, 0, d]))
            i_t_null_and_i_m_cost = Or(this_condition, [djiid([j, i_m + 1, 0, d + 1])], [])
            formulas.append(i_t_null_and_i_m_cost)

            # (i_m == w or i_m == tau ) <=> (d im+1 0 d => d im 0 d )
            i_t_null_and_i_m_dont_cost = Or([djiid([j, i_m, 0, d])], [djiid([j, i_m + 1, 0, d])], [
                And([], condition, [])
            ])
            formulas.append(i_t_null_and_i_m_dont_cost)

        for i_t in range(0, size_of_run):
            # i_t <> w <=> (d 0 it+1 d+1 => d 0 it d )
            i_m_null_and_i_t_cost = Or(
                [lambda_jia([j, i_t + 1, t(wait_transition)]), djiid([j, 0, i_t, d])],
                [djiid([j, 0, i_t + 1, d + 1])], [])
            formulas.append(i_m_null_and_i_t_cost)

            # i_t == w <=> (d 0 it+1 d => d 0 it d )
            i_m_null_and_i_t_dont_cost = Or([djiid([j, 0, i_t, d])],
                                            [lambda_jia([j, i_t + 1, t(wait_transition)]),
                                             djiid([j, 0, i_t + 1, d])], [])
            formulas.append(i_m_null_and_i_t_dont_cost)
    return And(positives, negatives, formulas)


def recursionEditDistance(transitions, silent_transitions, tau_it, lambda_jia, djiid, j, size_of_run, wait_transition,
                          max_d):
    '''
    Initialisation of the edit distance.
    This is the 2 lasts axioms of the _Encoding Conformance Checking Artefacts in SAT_ paper
    :param transitions (list) : list of transitions
    :param silent_transitions (list) : list of the silent transitions
    :param tau_it (fun) : function that returns the boolean variable number of the firing transition t at an instant i
    :param lambda_jia (fun) : function that returns the boolean variable number of the letter of trace j at instant i
    :param djiid (fun) : function that returns the boolean variable that says at instant i and i of we have d distance
    :param j (int) : jth trace
    :param size_of_run (int) : maximal size of a run
    :param wait_transition (transition) : to finish words
    :param max_d (int): heuristic
    :return: formula
    '''
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

                # letters are diff : i_t+1 <> i_m+1 => (d i_t i_m d <=> d i_t+1 i_m+1 d)
                condition = [tau_it([i_m + 1, transitions.index(wait_transition)]),
                             lambda_jia([j, i_t + 1, transitions.index(wait_transition)])]
                for st in silent_transitions:
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


def recursionEditDistance__reducedForAntiAlignment(transitions, silent_transitions, tau_it, lambda_jia, djiid, j,
                                                   size_of_run, wt, max_d):
    '''
    Initialisation of the edit distance reduced for anti-alignment.
    This is the 2 lasts axioms of the _Encoding Conformance Checking Artefacts in SAT_ paper
    :param transitions (list) : list of transitions
    :param silent_transitions (list) : list of the silent transitions
    :param tau_it (fun) : function that returns the boolean variable number of the firing transition t at an instant i
    :param lambda_jia (fun) : function that returns the boolean variable number of the letter of trace j at instant i
    :param djiid (fun) : function that returns the boolean variable that says at instant i and i of we have d distance
    :param j (int) : jth trace
    :param size_of_run (int) : maximal size of a run
    :param wait_transition (transition) : to finish words
    :param max_d (int): heuristic
    :return: formula
    '''

    def t(transition):
        return transitions.index(transition)

    formulas = []
    for i_m in range(0, size_of_run):
        for i_t in range(0, size_of_run):
            for d in range(0, max_d):

                # letters are equals : i_m == "tau" or i_t+1 == i_m+1 => (d i_t i_m d <= d i_t+1 i_m+1 d)
                letters_are_equals = Or([djiid([j, i_m, i_t, d + 1])],
                                        [djiid([j, i_m + 1, i_t + 1, d + 1])],
                                        [
                                            And([],
                                                [],
                                                [Or([],
                                                    [tau_it([i_m + 1, t]), lambda_jia([j, i_t + 1, t])],
                                                    []) for t in range(0, len(transitions))
                                                 ])
                                        ])
                formulas.append(letters_are_equals)

                # letters are diff : i_t+1 <> i_m+1 and not (silent or w) => (d i_t i_m d <= d i_t+1 i_m+1 d)
                condition = [tau_it([i_m + 1, t(wt)]), lambda_jia([j, i_t + 1, t(wt)])]
                for st in silent_transitions:
                    condition.append(tau_it([i_m + 1, t(st)]))
                and_in_this = [And([tau_it([i_m + 1, t]), lambda_jia([j, i_t + 1, t])], [], []) for
                               t in range(0, len(transitions))]
                and_in_this.append(And([djiid([j, i_m + 1, i_t, d]), djiid([j, i_m, i_t + 1, d])], [], []))
                letters_are_diff = Or(condition, [djiid([j, i_m + 1, i_t + 1, d + 1])], and_in_this)
                formulas.append(letters_are_diff)

                # ( u_t == w and u_m <> w) => ( d i_m i_t d <= d i_m+1 i_t d
                finish_run_of_model = Or([tau_it([i_m + 1, t(wt)]), djiid([j, i_m + 1, i_t, d])],
                                         [lambda_jia([j, i_t + 1, t(wt)]), djiid([j, i_m + 1, i_t + 1, d])],
                                         [])
                formulas.append(finish_run_of_model)

                # ( (u_m == w ou u_m=tau )and u_t <> w) => ( d i_m i_t d <= d i_m i_t+1 d
                condition=[tau_it([i_m + 1, t(wt)])]
                for st in silent_transitions:
                    condition.append(tau_it([i_m + 1, t(st)]))
                finish_run_of_trace = Or([lambda_jia([j, i_t + 1, t(wt)]), djiid([j, i_m, i_t + 1, d])],
                                         [ djiid([j, i_m + 1, i_t + 1, d])], [
                                      And([], condition,[])
                                         ])
                formulas.append(finish_run_of_trace)

    return formulas


def recursionEditDistance_reducedForMultiAlignment(transitions, silent_transitions, tau_it, lambda_jia, djiid, j,
                                                   size_of_run,
                                                   wait_transition, max_d):
    '''
    Initialisation of the edit distance reduced for multi-alignment.
    This is the 2 lasts axioms of the _Encoding Conformance Checking Artefacts in SAT_ paper
    :param transitions (list) : list of transitions
    :param silent_transitions (list) : list of the silent transitions
    :param tau_it (fun) : function that returns the boolean variable number of the firing transition t at an instant i
    :param lambda_jia (fun) : function that returns the boolean variable number of the letter of trace j at instant i
    :param djiid (fun) : function that returns the boolean variable that says at instant i and i of we have d distance
    :param j (int) : jth trace
    :param size_of_run (int) : maximal size of a run
    :param wait_transition (transition) : to finish words
    :param max_d (int): heuristic
    :return: formula
    '''

    def t(transition):
        return transitions.index(transition)

    formulas = []
    for i_m in range(0, size_of_run):
        for i_t in range(0, size_of_run):
            for d in range(0, max_d):
                # letters are equals i_t+1 == i_m+1 => (d i_t i_m d => d i_t+1 i_m+1 d)
                letters_are_equals = Or([djiid([j, i_m + 1, i_t + 1, d+1])], [djiid([j, i_m, i_t, d+1])],
                                        [And([], [],
                                             [Or([], [tau_it([i_m + 1, t]), lambda_jia([j, i_t + 1, t])], []) for t in
                                              range(0, len(transitions))]
                                             )])
                formulas.append(letters_are_equals)

                # letters are diff : i_t+1 == i_m+1 => (d i_t i_m d => d i_t+1 i_m+1 d)
                condition = [tau_it([i_m + 1, t(wait_transition)]), lambda_jia([j, i_t + 1, t(wait_transition)])]
                for st in silent_transitions:
                    condition.append(tau_it([i_m + 1, t(st)]))
                condition.append(djiid([j, i_m + 1, i_t + 1, d + 1]))
                letters_are_diff = Or(condition,
                                      [djiid([j, i_m + 1, i_t, d]), djiid([j, i_m, i_t + 1, d])],
                                      [And([tau_it([i_m + 1, t]), lambda_jia([j, i_t + 1, t])], [], []) for
                                       t in range(0, len(transitions))])
                formulas.append(letters_are_diff)

                # ( u_t == w and u_m <> w) => ( d i_m i_t d => d i_m+1 i_t d
                finish_run_of_model = Or([tau_it([i_m + 1, t(wait_transition)]), djiid([j, i_m + 1, i_t + 1, d])],
                                         [lambda_jia([j, i_t + 1, t(wait_transition)]), djiid([j, i_m + 1, i_t, d])],
                                         [])
                formulas.append(finish_run_of_model)

                # ( u_m == w and u_t <> w) => ( d i_m i_t d => d i_m i_t+1 d
                condition=[tau_it([i_m + 1, t(wait_transition)])]
                for st in silent_transitions:
                    condition.append(tau_it([i_m + 1, t(st)]))
                finish_run_of_trace = Or(
                    [lambda_jia([j, i_t + 1, t(wait_transition)]), djiid([j, i_m + 1, i_t + 1, d])],
                    [ djiid([j, i_m, i_t + 1, d])], [
                        And([], condition,[])
                    ])
                formulas.append(finish_run_of_trace)
    return formulas

# dictonary of functions used by the generic function edit_distance_per_trace_to_SAT()
DICT_OF_EDIT_RECURSIONS = {MULTI_ALIGNMENT: recursionEditDistance_reducedForMultiAlignment,
                           ANTI_ALIGNMENT: recursionEditDistance__reducedForAntiAlignment,
                           EXACT_ALIGNMENT: recursionEditDistance}
DICT_OF_EDIT_INIT = {MULTI_ALIGNMENT: initialisation_ReducedForMultiAlignment,
                     ANTI_ALIGNMENT: initialisation_ReducedForAntiAlignment,
                     EXACT_ALIGNMENT: initialisation_ReducedForMultiAlignment}


def levenshtein(s, t):
    if len(s) == 0 :
        return len(t)
    if len(t) == 0 :
        return len(s)
    if s[-1] in ["w",None,"tau"] or "tau" in s[-1] or "skip" in s[-1]:
        return levenshtein(s[:-1], t)
    if t[-1] in ["w",None,"tau"]  or "tau" in s[-1] or "skip" in s[-1]:
        return levenshtein(s, t[:1])
    if s[-1] == t[-1] :
        return levenshtein(s[:-1], t[:-1])
    else:
        return min(levenshtein(s[:-1], t)+1,
               levenshtein(s, t[:-1])+1)

def hamming(s,t):
    if len(s) == 0 :
        while "w" in t: t.remove("w")
        return len(t)
    if len(t) == 0 :
        while "w" in s: s.remove("w")
        return len(s)
    if s[0] == t[0] or s[0] in ["tau",None] or t[0] in ["tau",None] or  "tau"in s[0] or "skip" in s[0]:
        return hamming(s[1:], t[1:])
    else:
        return hamming(s[1:], t[1:])+1