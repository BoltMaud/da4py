#!/usr/bin/env python
# -*- coding:utf-8 -*-
##
## variablesGenerator.py
##
##  Created on: September, 2019
##      Author: Boltenhagen Mathilde
##      E-mail: boltenhagen lsv . fr
##
##
##  Translation of Darksider in Ocaml by Thomas Chatain
##

'''

This file contains the translation of a Petrinet to a Formula.
Scientific paper : _Alignment-based trace clustering_

'''

from da4py.main.utils.formulas import Or, And

def is_run(size_of_run, places, transitions, m0, mf, m_ip, tau_it,reach_final,space_between_fired):
    '''
    The is_run method allows one to create the boolean paths of the petri net.
    :param size_of_run (int): maximal size of the run
    :param places (list) :
    :param transitions (list) :
    :param m0 (marking) : initial marking
    :param m_ip (marking) : final marking
    :param tau_it (function) : function to get the number of the boolean variables, see variablesGenerator.
    :param reach_final (bool) : true or false to reach final marking
    :return:
    '''
    positives = [m_ip([0, places.index(m)]) for m in m0]
    if reach_final:
        positives+=[m_ip([size_of_run,places.index(m)]) for m in mf]
    negatives = [m_ip([0, places.index(m)]) for m in places if m not in m0]
    formulas = [is_action(places, transitions, m0, i, m_ip, tau_it,space_between_fired) for i in range(space_between_fired, size_of_run + 1,space_between_fired)]
    run_of_pn = And(positives, negatives, formulas)
    return run_of_pn


def is_action(places, transitions, m0, i, m_ip, tau_it,space_between_fired):
    '''
    The is_action method used by is_run creates the formula of each instant. Which transition fired ?
    :param places (list) :
    :param transitions (list) :
    :param m0 (marking) : initial marking
    :param i (int) : instant in the run
    :param m_ip (function) : function to get the number of the boolean variables of the markings, see variablesGenerator.
    :param tau_it (function) : function to get the number of the boolean variables of the transitions, see variablesGenerator.
    :return:
    '''
    # only one transition is true at instant i
    or_formulas = []
    for t in transitions:
        or_formulas.append(And([tau_it([i, transitions.index(t)])],[tau_it([i, transitions.index(t2)]) for t2 in transitions if t != t2],[]))
    formulas=[Or([],[],or_formulas)]
    # if transition t fires at instant i, then we have the good marking
    for t in transitions:
        formulas.append(Or([], [tau_it([i, transitions.index(t)])], [is_transition(places, t, i, m_ip,space_between_fired)]))
    return And([], [], formulas)


def is_transition(places, transition, i, m_ip,space_between_fired):
    '''
    The is_transition method used by is_action creates the formula of a firing transition. Which marking is needed ?
    :param places (list) :
    :param transitions (list) :
    :param i (int) : instant in the run
    :param m_ip (function) : function to get the number of the boolean variables of the markings, see variablesGenerator.
    :return:
    '''
    formulas = []
    prePlaces = [a.source for a in transition.in_arcs]
    postPlaces = [a.target for a in transition.out_arcs]

    for p in places:
        if p in prePlaces and p in postPlaces:
            formulas.append(And([m_ip([i, places.index(p)]), m_ip([i - space_between_fired, places.index(p)])], [], []))
        elif p in prePlaces and p not in postPlaces:
            formulas.append(And([m_ip([i - space_between_fired, places.index(p)])], [m_ip([i, places.index(p)])], []))
        elif p not in prePlaces and p in postPlaces:
            formulas.append(And([m_ip([i, places.index(p)])], [m_ip([i - space_between_fired, places.index(p)])], []))
        elif p not in prePlaces and p not in postPlaces:
            formulas.append(Or([], [], [And([m_ip([i, places.index(p)]), m_ip([i - space_between_fired, places.index(p)])], [], []),
                                        And([], [m_ip([i, places.index(p)]), m_ip([i - space_between_fired, places.index(p)])], [])]))
    return And([], [], formulas)


def petri_net_to_SAT(net, m0, mf, variablesGenerator, size_of_run, reach_final, label_m="m_ip", label_t="tau_it",
                     silent_transition=None,transitions=None,space_between_fired=1):
    '''
    This function returns the SAT formulas of a petrinet given label of variables, size_of_run
    :param net: petri net of the librairie pm4py
    :param m0: initial marking
    :param mf: final marking
    :param variablesgenerator: @see darksider4py.variablesGenerator
    :param label_m (string) : name of marking boolean variables per instant i and place p
    :param label_t (string) : name of place boolean variables per instant i and transition t
    :param size_of_run (int) : max instant i
    :param reach_final (bool) : True for reaching final marking
    :param sigma (list of char) : transition name
    :return: a boolean formulas
    '''

    # we need a ordered list to get int per place/transition (for the variablesgenerator)
    if transitions is None :
        transitions = [t for t in net.transitions]
    silent_transitions=[t for t in net.transitions if t.label==silent_transition]
    places = [p for p in net.places]

    # we create the number of variables needed for the markings
    variablesGenerator.add(label_m, [(0, size_of_run + 1), (0, len(places))])

    # we create the number of variables needed for the transitions
    variablesGenerator.add(label_t, [(1, size_of_run + 1), (0, len(transitions))])

    return (is_run(size_of_run, places, transitions, m0, mf, variablesGenerator.getFunction(label_m),
                   variablesGenerator.getFunction(label_t), reach_final,space_between_fired), places, transitions, silent_transitions)
