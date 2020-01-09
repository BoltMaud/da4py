#!/usr/bin/env python
# -*- coding:utf-8 -*-
##
## amstc.py
##
##  Created on: December, 2019
##      Author: Boltenhagen Mathilde
##      E-mail: boltenhagen lsv . fr
##

#############################@ DRAFT CODING !!

'''

Please, notice that I know that this code is really bad. I hope to find the time to clarify it. I add this comment
to make sure that you understand that I know it but I am actually very busy...

The amstc.py file implements the subnet based clustering presented in the following paper.

Scientific paper : _Generalized Alignment-Based Trace Clustering of Process Behavior_
By : Mathilde Boltenhagen, Thomas Chatain, Josep Carmona

'''
import time
import itertools


from pm4py.objects import petri

from da4py.main.utils.variablesGenerator import VariablesGenerator
from pm4py.objects.petri.petrinet import PetriNet
from pysat.examples.rc2 import RC2
from pysat.formula import WCNF

from da4py.main.objects.logToFormulas import log_to_Petri_with_w
from da4py.main.objects.pnToFormulas import is_transition
from da4py.main.utils.formulas import And, Or

BOOLEAN_VAR_J_IN_K="chi_jk"
BOOLEAN_VAR_TRACES_ACTIONS="lambda_jia"
BOOLEAN_VAR_CHI_MARKINGS="m_chijip"
BOOLEAN_VAR_CHI_TRANSITIONS="tau_chijia"
BOOLEAN_VAR_diff_TRACE_CENTROIDS="diff_ji"
BOOLEAN_VAR_TRANSITION_IN_K="c_kt"
BOOLEAN_VAR_COMMON_T="common_kkt"
BOOLEAN_VAR_J_CLUSTERISED="inC_j"

WAIT_LABEL_TRACE="w"
WAIT_LABEL_MODEL="ww"


class Amstc:

    def __init__(self, pn, m0, mf, traces_xes, size_of_run, max_d, max_t, nb_clusters,silent_label=None):
        self.__max_d=max_d
        self.__max_t=max_t
        self.__size_of_run=size_of_run
        self.__transitions=list(pn.transitions)
        self.__places=list(pn.places)
        self.__wait_transition_trace=PetriNet.Transition(WAIT_LABEL_TRACE, WAIT_LABEL_TRACE)
        self.__wait_transition_model=PetriNet.Transition(WAIT_LABEL_MODEL, WAIT_LABEL_MODEL)
        final_places=[p for p in pn.places if p in mf]
        petri.utils.add_arc_from_to(self.__wait_transition_model, final_places[0], pn)
        petri.utils.add_arc_from_to(final_places[0],self.__wait_transition_model, pn)
        self.__silent_transititons=[t for t in self.__transitions if t.label==silent_label]
        self.__transitions.append(self.__wait_transition_trace)
        self.__transitions.append(self.__wait_transition_model)

        self.__nb_clusters=nb_clusters
        self.__start=time.time()
        self.__createSATformula( pn, m0, mf, max_d, max_t,traces_xes)

    def __createSATformula(self, pn, m0, mf, max_d,max_t, traces_xes):
        self.__variablesGenerator=VariablesGenerator()
        log_to_PN_w_formula, self.__traces=log_to_Petri_with_w(traces_xes, self.__transitions, self.__variablesGenerator,
                                                  self.__size_of_run,self.__wait_transition_trace,self.__wait_transition_model,
                                                  label_l=BOOLEAN_VAR_TRACES_ACTIONS,
                                                  max_nbTraces=None)

        centroidsFormulasList = self.__createCentroids(m0)
        diffTracesCentroids=self.__getDiffTracesCentroids()
        listOfCommonTransitions=self.__interClustersDistance()
        aClusterMax=self.__TraceInAClusterOnly()
        numberTransitionsPerCluster=self.__maxTransitionsPerCluster(max_t)

        full_formula = And([], [], log_to_PN_w_formula+centroidsFormulasList+diffTracesCentroids+listOfCommonTransitions+aClusterMax+numberTransitionsPerCluster)
        cnf = full_formula.operatorToCnf(self.__variablesGenerator.iterator)
        self.__wcnf = WCNF()
        self.__wcnf.extend(cnf)
        self.__minimizingUnclusteredTraces()
        self.__minimizingCommonTransitions(max_t)
        self.__minimizingDiff(max_d)
        solver = RC2(self.__wcnf, solver="g4")
        solver.compute()
        print(time.time()-self.__start)
        self.__model = solver.model

    def __createCentroids(self,m0):
        def in_cluster_of_j(tr,c_kt, j, chi_jk,nb_clusters):
            t=self.__transitions.index(tr)
            tinK=[Or([c_kt([k,t])],[chi_jk([j,k])],[]) for k in range (0, nb_clusters)]
            return And([],[],tinK)

        def is_action_centroid(j,places, transitions, m0, i, m_jip, tau_jip, c_kt, chi_jk, nb_clusters):
            or_formulas = []
            for t in transitions:
                or_formulas.append(And([tau_jip([j,i, transitions.index(t)])],[tau_jip([j,i, transitions.index(t2)])
                                                                             for t2 in transitions if t != t2],[]))
            formulas=[Or([],[],or_formulas)]
            for t in transitions:
                if t==self.__wait_transition_trace:
                    formulas.append(And([],[tau_jip([j,i, transitions.index(t)])],[]))
                else :
                    formulas.append(Or([], [tau_jip([j,i, transitions.index(t)])], [
                    And([],[],[is_transition_centroid(j,places, t, i, m_jip),
                               in_cluster_of_j(t,c_kt,j,chi_jk,nb_clusters)])]))
            return And([], [], formulas)

        def is_transition_centroid(j,places, transition, i, m_ip):
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

        def is_run_centroid(j, size_of_run,m0, m_jip, tau_jip, c_kt, chi_jk, nb_clusters, transitions, places ):
            positives = [m_jip([j,0, places.index(m)]) for m in m0]
            negatives = [m_jip([j,0, places.index(m)]) for m in places if m not in m0]
            formulas = [is_action_centroid(j,places, transitions, m0, i, m_jip, tau_jip, c_kt, chi_jk, nb_clusters)
                        for i in range(1, size_of_run + 1)]
            run_of_pn = And(positives, negatives, formulas)
            return run_of_pn

        self.__variablesGenerator.add(BOOLEAN_VAR_J_IN_K,[(0,len(self.__traces)),(0,self.__nb_clusters)])
        self.__variablesGenerator.add(BOOLEAN_VAR_J_CLUSTERISED,[(0,len(self.__traces))])
        self.__variablesGenerator.add(BOOLEAN_VAR_CHI_MARKINGS,[(0,len(self.__traces)),(0,self.__size_of_run+1),(0,len(self.__places))])
        self.__variablesGenerator.add(BOOLEAN_VAR_CHI_TRANSITIONS,[(0,len(self.__traces)),(1,self.__size_of_run+1),(0,len(self.__transitions))])
        self.__variablesGenerator.add(BOOLEAN_VAR_TRANSITION_IN_K,[(0,self.__nb_clusters),(0,len(self.__transitions))])
        centroidsFormulas=[]

        for j in range (0, len(self.__traces)):
            centroidOfJ=is_run_centroid(j,self.__size_of_run,m0,self.__variablesGenerator.getfunction(BOOLEAN_VAR_CHI_MARKINGS),
                                self.__variablesGenerator.getfunction(BOOLEAN_VAR_CHI_TRANSITIONS),
                                self.__variablesGenerator.getfunction(BOOLEAN_VAR_TRANSITION_IN_K),
                                self.__variablesGenerator.getfunction(BOOLEAN_VAR_J_IN_K),
                                self.__nb_clusters,self.__transitions,self.__places)
            centroidIfClusterised=Or([],[self.__variablesGenerator.getVarNumber(BOOLEAN_VAR_J_CLUSTERISED,[j])],[centroidOfJ])
            centroidsFormulas.append(centroidIfClusterised)
        return centroidsFormulas

    def __getDiffTracesCentroids(self):
        self.__variablesGenerator.add(BOOLEAN_VAR_diff_TRACE_CENTROIDS,[(0,len(self.__traces)),(1,self.__size_of_run+1)])
        listOfAnd=[]
        listOfOr=[]
        for j in range (0, len(self.__traces)):
            for i in range(1,self.__size_of_run+1):
                for t in range(0,len(self.__transitions)):
                    if self.__transitions[t] in self.__silent_transititons:
                        diffjit=Or([],
                                   [self.__variablesGenerator.getVarNumber(BOOLEAN_VAR_CHI_TRANSITIONS,[j,i,t]),
                                    self.__variablesGenerator.getVarNumber(BOOLEAN_VAR_diff_TRACE_CENTROIDS,[j,i])],[])
                    else :
                        diffjit=Or([self.__variablesGenerator.getVarNumber(BOOLEAN_VAR_diff_TRACE_CENTROIDS,[j,i]),
                                    self.__variablesGenerator.getVarNumber(BOOLEAN_VAR_TRACES_ACTIONS,[j,i,t])],
                                   [self.__variablesGenerator.getVarNumber(BOOLEAN_VAR_CHI_TRANSITIONS,[j,i,t])],[])
                    listOfOr.append(diffjit)
            diffPerJ=And([],[],listOfOr)
            listOfAnd.append(diffPerJ)

        list_to_size_of_run= list(range(1,self.__size_of_run+1))
        max_distance=self.__size_of_run- self.__max_d
        combinaisons_of_instants=list(itertools.combinations(list_to_size_of_run,max_distance))
        for j in range (0, len(self.__traces)):
            listOfAndNeg=[]
            for instants in combinaisons_of_instants:
                listOfAndNeg.append(And([],[self.__variablesGenerator.getVarNumber(BOOLEAN_VAR_diff_TRACE_CENTROIDS,[j,i])
                                        for i in list(instants)],[]))
            listOfAnd.append(Or([],[],listOfAndNeg))
        return listOfAnd

    def __minimizingDiff(self,max_d):
        #for j in range (0,len(self.__traces)):
        #    listOfDiff=[self.__variablesGenerator.getVarNumber(BOOLEAN_VAR_diff_TRACE_CENTROIDS,[j,i]) for i in range  (1,self.__size_of_run+1)]
        #    self.__wcnf.append([listOfDiff,max_d],is_atmost=True)
            #for i in range (1,self.__size_of_run+1):
                #indexOfWait=self.__transitions.index(self.__wait_transition)
                #self.__wcnf.append([-1*self.__variablesGenerator.getVarNumber(BOOLEAN_VAR_TRACES_ACTIONS,[j,i,indexOfWait])],1)
        for j in range (0, len(self.__traces)):
            for i in range(1,self.__size_of_run+1):
                self.__wcnf.append([-1*self.__variablesGenerator.getVarNumber(BOOLEAN_VAR_diff_TRACE_CENTROIDS,[j,i])],1)

    def __interClustersDistance(self):
        self.__variablesGenerator.add(BOOLEAN_VAR_COMMON_T,[(0,self.__nb_clusters),(0,self.__nb_clusters),(0,len(self.__transitions))])
        listOfCommunTransitionsFormulas=[]
        for k1 in range (0, self.__nb_clusters):
            for k2 in range(k1+1,self.__nb_clusters):
                for t in self.__transitions:
                    indexOfT=self.__transitions.index(t)
                    haveATransitionInCommon=Or([self.__variablesGenerator.getVarNumber(BOOLEAN_VAR_COMMON_T,[k1,k2,indexOfT])],
                       [self.__variablesGenerator.getVarNumber(BOOLEAN_VAR_TRANSITION_IN_K,[k1,indexOfT]),
                        self.__variablesGenerator.getVarNumber(BOOLEAN_VAR_TRANSITION_IN_K,[k2,indexOfT])],[])
                    listOfCommunTransitionsFormulas.append(haveATransitionInCommon)
        return listOfCommunTransitionsFormulas


    def __TraceInAClusterOnly(self):
        listOfFormula=[]
        for j in range (0, len(self.__traces)):
            listOfAndNeg=[]
            for k1 in range (0,self.__nb_clusters):
                listOfAndNeg.append(And([self.__variablesGenerator.getVarNumber(BOOLEAN_VAR_J_CLUSTERISED,[j]),
                                         self.__variablesGenerator.getVarNumber(BOOLEAN_VAR_J_IN_K,[j,k1])],
                                        [self.__variablesGenerator.getVarNumber(BOOLEAN_VAR_J_IN_K,[j,k])
                                            for k in range (0,self.__nb_clusters) if k!=k1],[]))

            allKNot=[self.__variablesGenerator.getVarNumber(BOOLEAN_VAR_J_IN_K,[j,k]) for k in range(0,self.__nb_clusters)]
            allKNot.append(self.__variablesGenerator.getVarNumber(BOOLEAN_VAR_J_CLUSTERISED,[j]))
            listOfAndNeg.append(And([],allKNot,[]))
            listOfFormula.append(Or([],[],listOfAndNeg))
        return  listOfFormula

    def __minimizingUnclusteredTraces(self):
        for j in range (0, len(self.__traces)):
            for k in range(0, len(self.__traces)):
                self.__wcnf.append([self.__variablesGenerator.getVarNumber(BOOLEAN_VAR_J_IN_K,[j,k])],1)

    def __maxTransitionsPerCluster(self,max_t):
        listOfAnd=[]
        list_of_transitions_indexes= [t for t in range(0,len(self.__transitions)) if self.__transitions[t]!=self.__wait_transition_model]
        max_tFalse=len(self.__transitions)- max_t-1
        print("xxx",max_tFalse)
        combinaisons_of_transtions=list(itertools.combinations(list_of_transitions_indexes,max_tFalse))
        for k in range (0, self.__nb_clusters):
            listOfAndNeg=[]
            for transitions_indexes in combinaisons_of_transtions:
                listOfAndNeg.append(And([],[self.__variablesGenerator.getVarNumber(BOOLEAN_VAR_TRANSITION_IN_K,[k,i])
                                            for i in list(transitions_indexes)],[]))
            listOfAnd.append(Or([],[],listOfAndNeg))
        return listOfAnd

    def __minimizingCommonTransitions(self,max_t):
        for k1 in range (0,self.__nb_clusters):
            #self.__wcnf.append([[self.__variablesGenerator.getVarNumber(BOOLEAN_VAR_TRANSITION_IN_K,[k1,t])
            #                     for t in range (0,len(self.__transitions))
            #                     if self.__transitions[t]!=self.__wait_transition_model],max_t],is_atmost=True)
            for transition in self.__transitions:
                t=self.__transitions.index(transition)
                #self.__wcnf.append([-1*self.__variablesGenerator.getVarNumber(BOOLEAN_VAR_TRANSITION_IN_K,[k1,t])],1)
                for k2 in (k1+1,self.__nb_clusters):
                    self.__wcnf.append([-1*self.__variablesGenerator.getVarNumber(BOOLEAN_VAR_COMMON_T,[k1,k2,t])],1)


    def testPrint(self):
        clusters={}
        traces={}
        trs={}
        print(self.__transitions)
        for var in self.__model:
            print(self.__variablesGenerator.getVarName(var)) if self.__variablesGenerator.getVarName(var) is not None else None
            if self.__variablesGenerator.getVarName(var) != None and self.__variablesGenerator.getVarName(var).startswith(
                    BOOLEAN_VAR_TRANSITION_IN_K):
                k= self.__variablesGenerator.getVarName(var).split("[")[1].split(",")[0]
                t=self.__transitions[int(self.__variablesGenerator.getVarName(var).split("]")[0].split(",")[1])]
                if int(k) not in clusters.keys():
                    clusters[int(k)]=[]
                clusters[int(k)].append(t)
            if self.__variablesGenerator.getVarName(var) != None and self.__variablesGenerator.getVarName(var).startswith(
                    BOOLEAN_VAR_J_IN_K):
                j= self.__variablesGenerator.getVarName(var).split("[")[1].split(",")[0]
                k=(self.__variablesGenerator.getVarName(var).split("]")[0].split(",")[1])
                if int(k) not in traces.keys():
                    traces[int(k)]=[]
                traces[int(k)].append(j)
            if self.__variablesGenerator.getVarName(var) != None and self.__variablesGenerator.getVarName(var).startswith(
                BOOLEAN_VAR_TRACES_ACTIONS):
                j= self.__variablesGenerator.getVarName(var).split("[")[1].split(",")[0]
                i=(self.__variablesGenerator.getVarName(var).split("]")[0].split(",")[1])
                a=(self.__variablesGenerator.getVarName(var).split("]")[0].split(",")[2])
                if int(j) not in trs.keys():
                    trs[int(j)]=[]
                trs[int(j)].append('('+i+'-'+str(self.__transitions[int(a)])+')')
        for i in clusters:
            print(clusters[i])
            if i in traces:
                for j in traces[i]:
                    print([a for a in trs[int(j)]])
            print()
        print(self.__traces)





