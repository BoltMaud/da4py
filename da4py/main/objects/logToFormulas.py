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
'''
    This file contains the translation of a log to a Formula.

    Scientific paper : _Encoding Conformance Checking Artefacts in SAT_
    By : Mathilde Boltenhagen, Thomas Chatain, Josep Carmona
'''
import time

from pm4py.objects import petri
from pm4py.objects.log.util.log import project_traces
from pm4py.visualization.petrinet import factory as vizu
import numpy as np
BOOLEAN_VAR_TRACES_ACTIONS = "lambda_jia"
BOOLEAN_VAR_TRACES_MARKING= "m_jip"


from da4py.main.utils.formulas import And, Or


def log_to_SAT(traces_xes, transitions, variablesGenerator, size_of_run, wait_transition, label_l=BOOLEAN_VAR_TRACES_ACTIONS,max_nbTraces=None):
    '''
    This method returns the formulas of the Log.
    :param traces_xes:
    :param transitions (list)
    :param variablesGenerator (variablesGenerator) : to add the new boolean variables
    :param size_of_run (int) : to complete smaller words with "wait" transitions
    :param wait_transition (transition) : the "wait" transition
    :param label_l (string) : name of the boolean variables of the log
    :return:
    '''
    traces_multiples = project_traces(traces_xes)
    print("traces m",traces_multiples)
    traces=list(np.unique(traces_multiples))
    print("uniques",traces)
    traces = traces[:max_nbTraces] if max_nbTraces!=None else traces
    variablesGenerator.add(label_l,[(0,len(traces)),(1,size_of_run+1),(0,len(transitions))])
    lambda_jia=variablesGenerator.getFunction(label_l)
    positives=[]
    negatives=[]
    for j in range (0,len(traces)):
        for i in range (1,size_of_run+1):
            if len(traces[j])<(i):
                positives.append(lambda_jia([j,i,transitions.index(wait_transition)]))
                for a in transitions :
                    if a != wait_transition:
                        negatives.append(lambda_jia([j,i,transitions.index(a)]))
            else :
                for a in transitions:
                    if str(a)==traces[j][i-1]:
                        positives.append(lambda_jia([j,i,transitions.index(a)]))
                    else :
                        negatives.append(lambda_jia([j,i,transitions.index(a)]))

    return And(positives,negatives,[]),traces


def log_to_Petri_with_w(traces_xes, ttransitions, variablesGenerator, size_of_run, wait_transition_trace,wait_transition_model, label_l=BOOLEAN_VAR_TRACES_ACTIONS,label_m=BOOLEAN_VAR_TRACES_MARKING,max_nbTraces=None):
    def is_run_for_j(j,size_of_run, places, transitions,transitions_of_traces, m0, mf, m_ip, tau_it,reach_final):
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
        positives = [m_ip([j,0, places.index(m)]) for m in m0]
        if reach_final:
            [positives.append(m_ip([j,size_of_run,places.index(m)])) for m in mf]
        negatives = [m_ip([j,0, places.index(m)]) for m in places if m not in m0]
        formulas = [is_action_for_j(j,places, transitions,transitions_of_traces, m0, i, m_ip, tau_it) for i in range(1, size_of_run + 1)]
        run_of_pn = And(positives, negatives, formulas)
        return run_of_pn


    def is_action_for_j(j,places, transitions, transitions_of_traces, m0, i, m_ip, tau_it):
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
        formulas = []
        copie_transitions=[t for t in transitions]
        transitions_already_done=[]
        for t in transitions_of_traces:
            if t not in transitions_already_done:
                other_transitions_with_same_label=[]
                for t2 in transitions_of_traces:
                    if t2.label==t.label:
                        other_transitions_with_same_label.append(t2)
                        transitions_already_done.append(t2)
                index_of_t= transitions.index(t.label)
                copie_transitions.remove(t.label)
                or_formulas.append(And([tau_it([j,i, index_of_t])],[],[]))
                implication=[]
                for t2 in other_transitions_with_same_label:
                    implication.append(is_transition_for_j(j,places, t2, i, m_ip))
                formulas.append(Or([], [tau_it([j,i, index_of_t])], implication))
        formulas.append(Or([],[],or_formulas))
        formulas.append(And([],[tau_it([j,i, transitions.index(r)]) for r in copie_transitions],[]))
        return And([], [], formulas)


    def is_transition_for_j(j,places, transition, i, m_ip):
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
                formulas.append(And([m_ip([j,i, places.index(p)]), m_ip([j,i - 1, places.index(p)])], [], []))
            elif p in prePlaces and p not in postPlaces:
                formulas.append(And([m_ip([j,i - 1, places.index(p)])], [m_ip([j,i, places.index(p)])], []))
            elif p not in prePlaces and p in postPlaces:
                formulas.append(And([m_ip([j,i, places.index(p)])], [m_ip([j,i - 1, places.index(p)])], []))
            elif p not in prePlaces and p not in postPlaces:
                formulas.append(Or([], [], [And([m_ip([j,i, places.index(p)]), m_ip([j,i - 1, places.index(p)])], [], []),
                                            And([], [m_ip([j,i, places.index(p)]), m_ip([j,i - 1, places.index(p)])], [])]))
        return And([], [], formulas)

    traces_multiples = project_traces(traces_xes)
    traces=list(traces_multiples)
    traces=traces[:12]
    print("he ouie",len(traces))
    traces = traces[:max_nbTraces] if max_nbTraces!=None else traces
    variablesGenerator.add(label_l,[(0,len(traces)),(1,size_of_run+1),(0,len(ttransitions))])
    variablesGenerator.add(label_m,[(0,len(traces)),(0,size_of_run+1),(0,len(ttransitions))])
    transitions = [t.label for t in ttransitions]
    lambda_jia=variablesGenerator.getFunction(label_l)
    marking_jia=variablesGenerator.getFunction(label_m)
    listOfPns=[]
    for t in range(0,len(traces)):
        places=[]
        net_of_trace = petri.petrinet.PetriNet('L'+str(t))
        place_prec=petri.petrinet.PetriNet.Place(-1)
        net_of_trace.places.add(place_prec)
        m0 = petri.petrinet.Marking()
        m0[place_prec]=1
        for a in range (0,len(traces[t])):
            place_suiv=petri.petrinet.PetriNet.Place(a)
            net_of_trace.places.add(place_suiv)
            transition=petri.petrinet.PetriNet.Transition(traces[t][a]+str(a), traces[t][a])
            net_of_trace.transitions.add(transition)
            petri.utils.add_arc_from_to(transition, place_suiv, net_of_trace)
            petri.utils.add_arc_from_to(place_prec,transition,net_of_trace)
            place_prec=place_suiv
        mf = petri.petrinet.Marking()
        net_of_trace.transitions.add(wait_transition_trace)
        net_of_trace.transitions.add(wait_transition_model)
        petri.utils.add_arc_from_to(wait_transition_model, place_prec, net_of_trace)
        petri.utils.add_arc_from_to(place_prec,wait_transition_model, net_of_trace)
        mf[place_prec]=1
        places = [p for p in net_of_trace.places]
        transitions_of_traces=[p for p in net_of_trace.transitions]
        #vizu.apply(net_of_trace,m0,mf).view()
        listOfPns.append(is_run_for_j(t,size_of_run, places, transitions,transitions_of_traces, m0, mf, marking_jia, lambda_jia,False))

    return listOfPns,traces