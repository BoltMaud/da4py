#!/usr/bin/env python
# -*- coding:utf-8 -*-
##
## treeRepair.py
##
##  Created on: June, 2020
##      Author: Boltenhagen Mathilde
##      E-mail: boltenhagen lsv . fr
##

'''
In this file, we consider Tree Petri net.
'''
from pm4py.algo.conformance.alignments import versions
from pm4py.algo.conformance.alignments import algorithm as alignments
from pm4py.objects import petri
from pm4py.objects.petri.petrinet import PetriNet
from pm4py.objects.log.util.log import project_traces
from copy import deepcopy

from da4py.main.conformanceChecking.conformanceArtefacts import ConformanceArtefacts
from pm4py.visualization.petrinet import factory as vizu



def apply(net,m0,mf,log):
    '''
    This function takes as input a tree like petri net and tries to get the optimal
    :param net: Petri net
    :param m0: initial Marking
    :param mf: final Marking
    :param log: Log
    :return: void
    '''
    # get the current fitness
    fitness= getFitness(net,m0,mf,log,10)
    # while critieria are not optimal
    while fitness != 0 :
        # get the actions that can be done on the net
        listOfActions=listOfPossibleActions(net,mf,log)
        iterOnListOfActions=iter(listOfActions)
        # while the loop doesn't stop, it means that we didn't get a GOOD repair
        while 1 :
            action = next(iterOnListOfActions)
            # don't try to remove the last transition
            if action[0]!=removeTransition or len(net.transitions)>1:
                # launch the action!
                actionHistory= action[0](net,m0,mf,action[1])
                print(">",action[0],action[1])
                # get the new fitness to compare with the old one
                newFitness=getFitness(net,m0,mf,log,10)
                if newFitness < fitness:
                    # if good, there are some little things to fully remove and we keep the modifications
                    if "ifNotCancelToDel" in actionHistory[-1]:
                        for a in actionHistory[-1]:
                            del a
                    break
                # otherwise, we cancel the modifications
                cancelAction(net,m0,mf,actionHistory)
        print("! > break for",action[0],action[1])
        input("")
        # this is the new fitness of the model
        fitness=newFitness


def listOfPossibleActions(net,mf,log):
    '''
    this function gives the list of the possible actions :
    - remove any transition
    - add a transition before a place
    - add a transition in a branch after a place
    :param net: Petri net (like a tree)
    :param mf: final Marking ('cause we don't want to add a transition in a branch after the final place)
    :param log: Log
    :return: List (function removeTransition, transition) or (function addTransition/addInBranchTransition, (place, label))
    '''
    actions= {(removeTransition,t) for t in net.transitions}
    letter=list(set([j for i in project_traces(log._list) for j in i]))
    for p in net.places:
        for l in letter:
            actions.add((addTransition,(l,p)))
            if p not in mf:
                actions.add((addInBranchTransition,(l,p)))
    return actions


def removeTransition(net,m0,mf,t):
    '''
    Remove transition t
    There are some specificities for branches:
    - if the place before the transition is the final place and has several out_arcs then we do nothing, sorry
    - if the place before the transition is the final place but has only one out_arc then we can remove the transition
    and this place
    - otherwise, when the transition is not attached to the end place, we remove the place which is after the transition
    :param net:Petri net (tree like)
    :param m0:Marking
    :param mf:Making
    :param t: Transition
    :return: history is a list of repair items that should be recorded to be canceled (draft version?)
    '''
    history=[]
    previousPlace = next(iter(t.in_arcs)).source
    nextPlace = next(iter(t.out_arcs)).target
    if nextPlace in mf:
        # if the next place is the end place, then there are some specificities
        if len(nextPlace.in_arcs) > 1:
            # if the place has many in arcs, we do nothing, sorry
            if len(previousPlace.out_arcs)>1:
                return history
            # otherwise we can remove the place before the transition and the corresponding arcs
            else :
                newArc = petri.utils.add_arc_from_to(next(iter(previousPlace.in_arcs)).source,nextPlace,net)
                history.append({"action":"addArc","arc":newArc,"source":newArc.source,"target":newArc.target})
                history.append({"action":"delArc","source":t,"target":nextPlace})
                afterT = next(iter(t.out_arcs))
                del afterT
                history.append({"action":"delArc","source":previousPlace,"target":t})
                beforeT = next(iter(t.in_arcs))
                del beforeT
                history.append({"action":"delArc","source":next(iter(previousPlace.in_arcs)).source,"target":previousPlace})
                beforeP = next(iter(previousPlace.in_arcs))
                del beforeP
                history.append({"action":"delTransition","t":t})
                petri.utils.remove_transition(net,t)
                t.in_arcs.clear()
                t.out_arcs.clear()
                history.append({"action":"delPlace","p":previousPlace})
                petri.utils.remove_place(net,previousPlace)
                previousPlace.out_arcs.clear()
                previousPlace.in_arcs.clear()
                history.append({"ifNotCancelToDel":None})
                return history
        else :
            # if the end place has only one out arc, then we just modify which place is the end place
            history.append({"action":"delmf","place":nextPlace})
            history.append({"action":"addmf","place":previousPlace})
            del mf[nextPlace]
            mf[previousPlace]=1
    for nextArc in nextPlace.out_arcs:
        # for each outArc of the future removed place, put into the previousPlace
        newArc = petri.utils.add_arc_from_to(previousPlace,nextArc.target,net)
        history.append({"action":"addArc","arc":newArc,"source":previousPlace,"target":nextArc.target})
        history.append({"action":"delArc","source":nextArc.source,"target":nextArc.target})
        del nextArc
    history.append({"action":"delTransition","t":t})
    petri.utils.remove_transition(net,t)
    t.in_arcs.clear()
    t.out_arcs.clear()
    history.append({"action":"delPlace","p":nextPlace})
    petri.utils.remove_place(net,nextPlace)
    nextPlace.out_arcs.clear()
    nextPlace.in_arcs.clear()
    history.append({"action":"delArc","source":t, "target":nextPlace})
    history.append({"action":"delArc","source":previousPlace, "target":t})
    history.append({"ifNotCancelToDel":[t,previousPlace]})
    return history

def cancelAction(net,m0,mf, history):
    '''
    From the list of history, we cancel the actions ie we do the contrary.
    Don't touch the last item because it's for removing fully some items
    :param net: Petri net (tree like)
    :param m0: Marking
    :param mf: Marking
    :param history:  history is a list of repair items that should be recorded to be canceled (draft version?)
    :return: void
    '''
    for a in history[:-1]:
        if a["action"]=="delArc":
            petri.utils.add_arc_from_to(a["source"],a["target"],net)
        elif a["action"]=="addArc":
            net.arcs.remove(a["arc"])
            a["source"].out_arcs.remove(a["arc"])
            a["target"].in_arcs.remove(a["arc"])
        elif a["action"]=="delTransition":
            net.transitions.add(a["t"])
        elif a["action"]=="delPlace":
            net.places.add(a["p"])
        elif a["action"]=="addTransition":
            net.transitions.remove(a["transition"])
            del a["transition"]
        elif a["action"]=="addPlace":
            net.places.remove(a["place"])
            del a["place"]
        elif a["action"]=="delm0":
            m0[a["place"]]=1
        elif a["action"]=="addm0":
            del m0[a["place"]]
        elif a["action"]=="delmf":
            mf[a["place"]]=1
        elif a["action"]=="addmf":
            del mf[a["place"]]

def addTransition(net,m0,mf,labelAndPlace):
    '''
    add ARC+PLACE+ARC+TRANSITION in a net before nextPlace
    :param net:
    :param label:
    :param nextPlace:
    :return:
    '''
    label, nextPlace=labelAndPlace
    history=[]
    newPlace = petri.utils.add_place(net, label+"place")
    if nextPlace == next(iter(m0)):
        history.append({"action":"delm0","place":nextPlace})
        history.append({"action":"addm0","place":newPlace})
        del m0[nextPlace]
        m0[newPlace]=1
    history.append({"action":"addPlace","place":newPlace})
    newTransition = petri.utils.add_transition(net, label+"transition",label)
    history.append({"action":"addTransition","transition":newTransition})
    newArc = petri.utils.add_arc_from_to(newPlace,newTransition,net)
    history.append({"action":"addArc","arc":newArc,"source": newPlace,"target":newTransition})
    toDel=[]
    for inArc in nextPlace.in_arcs:
        newArc=petri.utils.add_arc_from_to(inArc.source,newPlace,net)
        history.append({"action":"addArc","arc":newArc,"source": inArc.source,"target":newPlace})
        history.append({"action":"delArc","arc":inArc,"source": inArc.source,"target": inArc.target})
        inArc.source.out_arcs.remove(inArc)
        net.arcs.remove(inArc)
        toDel.append(inArc)
    nextPlace.in_arcs.clear()
    newArc=petri.utils.add_arc_from_to(newTransition,nextPlace,net)
    history.append({"action":"addArc","arc":newArc,"source": newTransition,"target":nextPlace})
    history.append({"ifNotCancelToDel":toDel})
    return history

def addInBranchTransition(net, m0, mf,labelAndPlace):
    '''
    add a new branch from the place to the endplace
    :param net:
    :param m0:
    :param mf:
    :param labelAndPlace:
    :return:
    '''
    history=[]
    label, prevPlace=labelAndPlace
    newTransition = petri.utils.add_transition(net, label+"transition",label)
    history.append({"action":"addTransition","transition":newTransition})
    newArc=petri.utils.add_arc_from_to(prevPlace,newTransition,net)
    history.append({"action":"addArc","arc":newArc,"source": prevPlace,"target":newTransition})
    endPlace= next(iter(mf))
    newArc=petri.utils.add_arc_from_to(newTransition,endPlace,net)
    history.append({"action":"addArc","arc":newArc,"source": newTransition,"target":endPlace})
    history.append({"ifNotCancelToDel":None})
    return history


def getFitness(net,m0,mf,log,size_of_run):
    '''
    Prefix-aware fitness
    :param net:
    :param m0:
    :param mf:
    :param log:
    :param size_of_run:
    :return:
    '''
    sum=0
    for l in log._list:
        model_cost_function = dict()
        sync_cost_function = dict()
        for t in net.transitions:
            if t.label is not None:
                model_cost_function[t]=2**(len(l)+size_of_run-getIndexOfT(t,m0))
            sync_cost_function[t]=0
        trace_cost_function = dict()
        for a in range (0,len(l)):
            trace_cost_function[a]=2**(len(l)+size_of_run-a)
        parameters = {}
        parameters[alignments.Variants.VERSION_STATE_EQUATION_A_STAR.value.Parameters.PARAM_MODEL_COST_FUNCTION] = model_cost_function
        parameters[alignments.Variants.VERSION_STATE_EQUATION_A_STAR.value.Parameters.PARAM_SYNC_COST_FUNCTION] = sync_cost_function
        parameters[alignments.Variants.VERSION_STATE_EQUATION_A_STAR.value.Parameters.PARAM_TRACE_COST_FUNCTION] = trace_cost_function
        ali = alignments.apply(l, net, m0, mf, parameters=parameters, variant=versions.dijkstra_no_heuristics)
        if ali == None:
            vizu.apply(net, m0, mf).view()
        sum+=ali['cost']
    return sum

def getIndexOfT(t,initial_marking):
    '''
    From a transition to the initial marking, count distance. Work for tree petri net only.
    :param t: Transition
    :param initial_marking: Marking
    :return: int
    '''
    d=1
    initialPlace=next(iter(initial_marking))
    if initialPlace!=t:
        previousPlace=next(iter(t.in_arcs)).source
        d+=1
        while(previousPlace!=initialPlace):
            transTemp=next(iter(previousPlace.in_arcs)).source
            previousPlace=next(iter(transTemp.in_arcs)).source
            d+=1
    return d

def getPrecision(net,m0,mf,log,size_of_run):
    aa=ConformanceArtefacts()
    aa.setSize_of_run(size_of_run)
    aa.setMax_d(2*size_of_run)
    aa.antiAlignment(net, m0,mf, log)
    p = aa.getMinDistanceToRun()
    return aa.getPrecision()