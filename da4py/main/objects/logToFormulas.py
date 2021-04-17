#!/usr/bin/env python
# -*- coding:utf-8 -*-
##
## logToFormulas.py
##
##  Created on: September, 2019
##      Author: Boltenhagen Mathilde
##      E-mail: boltenhagen lsv . fr
##
##
'''
    This file contains the translation of a log to a Formula for :

    Scientific paper : _Encoding Conformance Checking Artefacts in SAT_
    By : Mathilde Boltenhagen, Thomas Chatain, Josep Carmona

    and a log to petri net for :

    Scientific paper : _Generalized Alignment-Based Trace Clustering of Process Behavior_
    By : Mathilde Boltenhagen, Thomas Chatain, Josep Carmona
'''
import time
from threading import Thread

from pm4py.objects import petri
from pm4py.objects.log.util.log import project_traces
#from pm4py.visualization.petrinet import factory as vizu
import numpy as np
from random import sample
BOOLEAN_VAR_TRACES_ACTIONS = "lambda_jia"
BOOLEAN_VAR_TRACES_MARKING= "m_jip"
WAIT_LABEL_TRACE="w"

NB_MAX_THREADS=50

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
    #traces=list(np.unique(traces_multiples))
    traces=traces_multiples
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
                        letterFound=True
                        positives.append(lambda_jia([j,i,transitions.index(a)]))
                    else :
                        negatives.append(lambda_jia([j,i,transitions.index(a)]))
    return And(positives,negatives,[]),traces


def log_to_Petri_with_w(traces_xes, pn_transitions, vars, size_of_run, wait_transition_trace, wait_transition_model,
                        label_l=BOOLEAN_VAR_TRACES_ACTIONS, label_m=BOOLEAN_VAR_TRACES_MARKING,
                        max_nbTraces=None):
    '''
    This function transforms a log into a list of sequential petri net with wait transition that represents log moves.
    This function has subfunctions.
    :param traces_xes (Log)
    :param pn_transitions (list of Transitions)
    :param vars (VariablesGenerator) @see variablesGenerator.py
    :param size_of_run (int) : maximal size of run
    :param wait_transition_trace (Transition) : log moves
    :param wait_transition_model (Transition) : model moves
    :param label_l (optional, string) : name of boolean variables
    :param label_m (optional, string) : name of boolean variables
    :param max_nbTraces (optinal, string) : only top N traces
    :return:
    '''
    def is_run_for_j(j, size_of_run, places, pn_transitions, trace_transitions, m0, mf, m_ip, tau_it, reach_final):
        '''
        The is_run_for_j method creates run of centroid of trace j, i. e., alignment.
        :param j (int) : index of trace
        :param size_of_run (int): maximal size of the run
        :param places (list) : list of Places
        :param pn_transitions (list) : transitions of the model 'cause needed...
        :param trace_transitions (list) : transitions of the trace
        :param m0 (marking) : initial marking of trace
        :param mf (Marking) : final marking of trace
        :param m_ip (function) : marking boolean variables of the trace
        :param tau_it (function) : transitions boolean variables of the trace, @see variablesGenerator.
        :param reach_final (bool) : true or false to reach final marking
        :return:
        '''
        positives = [m_ip([j,0, places.index(m)]) for m in m0]
        if reach_final:
            [positives.append(m_ip([j,size_of_run,places.index(m)])) for m in mf]
        negatives = [m_ip([j,0, places.index(m)]) for m in places if m not in m0]
        formulas = [is_action_for_j(j, places, pn_transitions, trace_transitions, i, m_ip, tau_it) for i in range(1, size_of_run + 1)]
        run_of_pn = And(positives, negatives, formulas)
        return run_of_pn


    def is_action_for_j(j, trace_places, pn_transitions, trace_transitions, i, m_ip, tau_it):
        '''
        The is_action method used by is_run creates the formula of each instant. Which transition fired ?
        :param places (list) :
        :param pn_transitions (list) : we need all the alphabet to refuse transitions that aren't in trace
        :param trace_transitions (list) : transitions of the trace
        :param i (int) : instant in the run
        :param m_ip (function) : function to get the number of the boolean variables of the markings, see variablesGenerator.
        :param tau_it (function) : function to get the number of the boolean variables of the transitions, see variablesGenerator.
        :return:
        '''
        # only one transition is true at instant i
        # lazy comment : this verifies that alphabet is complet : all action not executed has to be taken into account
        or_formulas = []
        formulas = []
        label_transitions=[t.label for t in pn_transitions]
        copie_transitions=[t for t in pn_transitions]
        transitions_already_done=[]
        for t in trace_transitions:
            if t not in transitions_already_done:
                other_transitions_with_same_label=[]
                for t2 in trace_transitions:
                    if t2.label==t.label:
                        other_transitions_with_same_label.append(t2)
                        transitions_already_done.append(t2)
                if t.label in label_transitions:
                    index_of_t= label_transitions.index(t.label)
                else :
                    index_of_t=None# should never happen
                copie_transitions.remove(pn_transitions[(label_transitions.index(t.label))])
                or_formulas.append(And([tau_it([j,i, index_of_t])],[],[]))
                implication=[]
                for t2 in other_transitions_with_same_label:
                    implication.append(is_transition_for_j(j, trace_places, t2, i, m_ip))
                formulas.append(Or([], [tau_it([j,i, index_of_t])], implication))
        formulas.append(Or([],[],or_formulas))
        formulas.append(And([], [tau_it([j, i, pn_transitions.index(r)]) for r in copie_transitions], []))
        return And([], [], formulas)


    def is_transition_for_j(j, trace_places, trace_transition, i, m_ip):
        '''
        The is_transition_for_j method used by is_action_for_j creates the formula of a firing transition.
        Which marking is needed ?
        :param trace_places (list) :
        :param trace_transition (Transition) :
        :param i (int) : instant in the run
        :param m_ip (function) : function to get the number of the boolean variables of the markings, see variablesGenerator.
        :return:
        '''
        formulas = []
        prePlaces = [a.source for a in trace_transition.in_arcs]
        postPlaces = [a.target for a in trace_transition.out_arcs]
        for p in trace_places:
            if p in prePlaces and p in postPlaces:
                formulas.append(And([m_ip([j, i, trace_places.index(p)]), m_ip([j, i - 1, trace_places.index(p)])], [], []))
            elif p in prePlaces and p not in postPlaces:
                formulas.append(And([m_ip([j, i - 1, trace_places.index(p)])], [m_ip([j, i, trace_places.index(p)])], []))
            elif p not in prePlaces and p in postPlaces:
                formulas.append(And([m_ip([j, i, trace_places.index(p)])], [m_ip([j, i - 1, trace_places.index(p)])], []))
            elif p not in prePlaces and p not in postPlaces:
                formulas.append(Or([], [], [And([m_ip([j, i, trace_places.index(p)]), m_ip([j, i - 1, trace_places.index(p)])], [], []),
                                            And([], [m_ip([j, i, trace_places.index(p)]), m_ip([j, i - 1, trace_places.index(p)])], [])]))
        return And([], [], formulas)

    def create_pn_of_trace(j,size_of_run, trace, wait_transition_trace, wait_transition_model):
        '''
        Create sequential petri net of trace.
        :param j (int):
        :param trace (list) : list of words, labels
        :param wait_transition_trace (Transition) : log moves
        :param wait_transition_model (Transition) : model moves
        '''
        net_of_trace = petri.petrinet.PetriNet('L'+str(j))
        place_prec=petri.petrinet.PetriNet.Place(-1)
        net_of_trace.places.add(place_prec)
        m0 = petri.petrinet.Marking()
        m0[place_prec]=1
        for a in range (0,min(size_of_run, len(trace))):
            place_suiv=petri.petrinet.PetriNet.Place(a)
            net_of_trace.places.add(place_suiv)
            transition=petri.petrinet.PetriNet.Transition(trace[a]+str(a), trace[a])
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
        return m0, mf, net_of_trace

    # ......................................................................
    # here starts log_to_Petri_with_w function
    traces = list(project_traces(traces_xes))
    traces = sample(traces,max_nbTraces) if max_nbTraces!=None and len(traces)>max_nbTraces else traces

    # add boolean variables
    vars.add(label_l, [(0, len(traces)), (1, size_of_run + 1), (0, len(pn_transitions))])
    vars.add(label_m, [(0, len(traces)), (0, size_of_run + 1), (0, size_of_run + 1)])
    transitions = [t.label for t in pn_transitions]
    lambda_jia=vars.getFunction(label_l)
    marking_jia=vars.getFunction(label_m)

    # each trace becomes a sequential petri net with a wait transition representing the log moves
    listOfPns=[]
    for j in range(0,len(traces)):
        m0, mf, net_of_trace=create_pn_of_trace(j,size_of_run,traces[j],wait_transition_trace,wait_transition_model)
        #vizu.apply(net_of_trace,m0,mf).view()
        places = [p for p in net_of_trace.places]
        for t in net_of_trace.transitions:
            if t.label not in transitions:
                t.label=WAIT_LABEL_TRACE
        transitions_of_traces=[p for p in net_of_trace.transitions]
        # add alignment into formulas
        listOfPns.append(is_run_for_j(j,size_of_run, places, pn_transitions,transitions_of_traces, m0, mf, marking_jia,
                                      lambda_jia,True))

    return listOfPns,traces