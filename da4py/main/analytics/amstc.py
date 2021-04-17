#!/usr/bin/env python
# -*- coding:utf-8 -*-
##
## amstc.py
##
##  Created on: December, 2019
##      Author: Boltenhagen Mathilde
##      E-mail: boltenhagen lsv . fr
##

'''

The amstc.py file implements the subnet based clustering presented in the following paper.

Scientific papers : _Generalized Alignment-Based Trace Clustering of Process Behavior_
                    _Model-based Trace Variants_
By : Mathilde Boltenhagen, Thomas Chatain, Josep Carmona

'''
import time
import itertools
import warnings
from copy import deepcopy

from pm4py.algo.filtering.log.variants.variants_filter import get_variants
from pm4py.objects import petri
from pm4py.objects.log.util.log import project_traces
#from pm4py.visualization.petrinet import factory as vizu
from pm4py.algo.conformance import alignments
from pm4py.objects.log.util import xes as xes_util
import editdistance

from da4py.main.utils.variablesGenerator import VariablesGenerator
from pm4py.objects.petri.petrinet import PetriNet, Marking
from pysat.examples.rc2 import RC2
from pysat.formula import WCNFPlus

from da4py.main.objects.logToFormulas import log_to_Petri_with_w
from da4py.main.utils.formulas import And, Or

BOOLEAN_VAR_J_IN_K="chi_jk"
BOOLEAN_VAR_TRACES_ACTIONS="lambda_jia"
BOOLEAN_VAR_CHI_MARKINGS="m_chijip"
BOOLEAN_VAR_CHI_TRANSITIONS="tau_chijia"
BOOLEAN_VAR_DIFF_m= "diffm_ji"
BOOLEAN_VAR_DIFF_l= "diffl_ji"
BOOLEAN_VAR_K_CONTAINS_T= "c_kt"
BOOLEAN_VAR_COMMON_T="common_kkt"
BOOLEAN_VAR_J_CLUSTERISED="inC_j"

WAIT_LABEL_TRACE="w"
WAIT_LABEL_MODEL="ww"

class Amstc:
    '''
    Alignment and Model Subnet-based Trace Clustering
    Creates clusters based on subnets
    '''

    def __init__(self, pn, m0, mf, traces_xes, size_of_run, max_d, max_t, nb_clusters,silent_label="tau", nbTraces=20):
        '''
        Initialization of the object that directly launches the clustering
        :param pn (Petrinet)
        :param m0 (Marking) : initial marking
        :param mf (Marking) : final marking
        :param traces_xes (Log) : data
        :param size_of_run (int) : maximal studied size of run
        :param max_d (int) : distance maximal of the traces to their subnet centroids
        :param max_t (int) : maximal number of transitions in a subnet centroid
        :param nb_clusters (int) : maximal number of cluster
        :param silent_label (string) : non-cost label transition
        '''
        self.__max_d=max_d
        self.__max_t=max_t
        self.__size_of_run=size_of_run
        self.__copy_net(pn,m0,mf)
        self.__nb_clusters=nb_clusters
        self.__silent_transititons=[t for t in self.__transitions if  t.label is None or silent_label in t.label ]
        # add wait transitions that represents log and model move for alignment
        self.__addWaitTransitions(self.__pn,self.__mf)
        self.__start=time.time()
        self.__createSATformula(self.__pn, self.__m0, self.__mf, max_d, max_t,traces_xes,nbTraces)

    def __copy_net(self,pn, m0, mf):
        self.__pn=deepcopy(pn)
        self.__transitions=list(self.__pn.transitions)
        self.__places=list(self.__pn.places)
        self.__arcs=list(self.__pn.arcs)
        self.__m0=Marking()
        self.__mf=Marking()
        for p in self.__pn.places:
            for n in m0.keys():
                if n.name==p.name :
                    self.__m0[p]=1
            for n in mf.keys():
                if n.name==p.name:
                    self.__mf[p]=1

    def __addWaitTransitions(self, pn, mf):
        '''
        This function add 2 type of wait transitions :
            - log moves
            - model moves
        Those transitions cost.
        :param pn (Petrinet)
        :param mf (Marking)
        '''
        # creates the transitions with labels WAIT_LABEL_TRACE for log moves
        # and WAIT_LABEL_MODEL for model moves
        self.__wait_transition_trace=PetriNet.Transition(WAIT_LABEL_TRACE, WAIT_LABEL_TRACE)
        self.__wait_transition_model=PetriNet.Transition(WAIT_LABEL_MODEL, WAIT_LABEL_MODEL)
        final_places=[p for p in pn.places if p in mf]
        # WAIT_LABEL_MODEL is added in the Petrinet at the end of the
        # TODO I'm not sure here
        #petri.utils.add_arc_from_to(self.__wait_transition_model, final_places[0], pn)
        #petri.utils.add_arc_from_to(final_places[0],self.__wait_transition_model, pn)
        # add both transitions but notice that WAIT_LABEL_TRACE will be forbidden for the centroids
        self.__transitions.append(self.__wait_transition_trace)
        self.__transitions.append(self.__wait_transition_model)


    def __createSATformula(self, pn, m0, mf, max_d,max_t, traces_xes,nbTraces):
        '''
        This function creates and solve the SAT formula of the clustering problem.
        :param pn (Petrinet)
        :param m0 (Marking)
        :param mf (Marking)
        :param max_d (int)
        :param max_t (int)
        :param traces_xes (Log)
        '''
        # this object creates variable numbers of the SAT formula
        self.__vars=VariablesGenerator()
        # formula version of data event log
        log_to_PN_w_formula, self.__traces=log_to_Petri_with_w(traces_xes, self.__transitions, self.__vars,
                                                               self.__size_of_run, self.__wait_transition_trace,
                                                               self.__wait_transition_model,
                                                               label_l=BOOLEAN_VAR_TRACES_ACTIONS,
                                                               max_nbTraces=nbTraces)
        # creates the boolean variables for the next formulas
        self.__createBooleanVariables()
        # formula of centroids
        centroidsFormulasList = self.__createCentroids(m0,mf)
        # formula that describes maximal distance
        diffTracesCentroids=self.__getDiffTracesCentroids(self.__vars.getFunction(BOOLEAN_VAR_CHI_TRANSITIONS),
                                                          self.__vars.getFunction(BOOLEAN_VAR_DIFF_l),
                                                          self.__vars.getFunction(BOOLEAN_VAR_DIFF_m),
                                                          self.__vars.getFunction(BOOLEAN_VAR_TRACES_ACTIONS))

        # formula that create BOOLEAN_VAR_COMMON_T variables
        listOfCommonTransitions=self.__commonTransitions(self.__vars.getFunction(BOOLEAN_VAR_COMMON_T),
                                                         self.__vars.getFunction(BOOLEAN_VAR_K_CONTAINS_T))
        # formula that describes that a trace belongs to at most one cluster
        aClusterMax=self.__tracesInAClusterOnly(self.__vars.getFunction(BOOLEAN_VAR_J_CLUSTERISED),
                                                self.__vars.getFunction(BOOLEAN_VAR_J_IN_K))
        # concat the formula
        full_formula = And([], [], log_to_PN_w_formula + centroidsFormulasList + diffTracesCentroids +
                            listOfCommonTransitions + aClusterMax )
        # formula to cnf
        cnf = full_formula.operatorToCnf(self.__vars.iterator)

        # CNF is completed with minimisation and solved
        self.__createWCNFWithMinimization(cnf)

    def __createBooleanVariables(self):
        '''
        This function creates the boolean variables needed in this class.
        '''
        self.__vars.add(BOOLEAN_VAR_DIFF_m, [(0, len(self.__traces)), (1, self.__size_of_run + 1)])
        self.__vars.add(BOOLEAN_VAR_DIFF_l, [(0, len(self.__traces)), (1, self.__size_of_run + 1)])

        self.__vars.add(BOOLEAN_VAR_J_IN_K, [(0, len(self.__traces)), (0, self.__nb_clusters)])
        self.__vars.add(BOOLEAN_VAR_J_CLUSTERISED, [(0, len(self.__traces))])
        self.__vars.add(BOOLEAN_VAR_CHI_MARKINGS, [(0, len(self.__traces)), (0, self.__size_of_run + 1),
                                                   (0, len(self.__places))])
        self.__vars.add(BOOLEAN_VAR_CHI_TRANSITIONS, [(0, len(self.__traces)), (1, self.__size_of_run + 1),
                                                      (0, len(self.__transitions))])
        self.__vars.add(BOOLEAN_VAR_K_CONTAINS_T, [(0, self.__nb_clusters), (0, len(self.__transitions))])
        self.__vars.add(BOOLEAN_VAR_COMMON_T, [(0, self.__nb_clusters), (0, self.__nb_clusters),
                                               (0, len(self.__transitions))])


    def __createWCNFWithMinimization(self,cnf):
        '''
        This function creates the WCNF object and solves it.
        Variables are weighted, it's a MaxSAT problem.
        :param cnf (list)
        :return:
        '''
        # thanks to pysat library
        self.__wcnf = WCNFPlus()
        self.__wcnf.extend(cnf)
        # most of the traces should be clustered
        self.__minimizingUnclusteredTraces()
        # minimizing BOOLEAN_VAR_COMMON_T variables
        self.__minimizingCommonTransitions()
        # minimizing BOOLEAN_VAR_diff_TRACE_CENTROIDS variables
        self.__minimizingDiff()
        #
        self.__maxTransitionsPerClusterAtMost(self.__vars.getFunction(BOOLEAN_VAR_K_CONTAINS_T))
        # RC2 is a MaxSAT algorithm
        solver = RC2(self.__wcnf, solver="mc")
        solver.compute()
        self.__endComputationTime=time.time()
        self.__model = solver.model

    def __createCentroids(self,m0,mf):
        '''
        Create formula of the subnet centroids. There are one centroid per trace and transitions are affected to cluster.
        As the number of cluster is limited, centroid will naturally be joined : traces are clustered that way.
        Centroids finally are run of the model that allows alignments. When alignment are found, transitions go in
        clusters.
        Creates BOOLEAN_VAR_CHI_MARKINGS, BOOLEAN_VAR_CHI_TRANSITIONS, BOOLEAN_VAR_K_CONTAINS_T, BOOLEAN_VAR_J_IN_K
        boolean variables.
        This function has subfunctions because formula differ from normal petri nets (@see pnToFormula).
        :param m0 (Marking)
        '''
        def in_cluster_of_j(tr,c_kt, j, chi_jk,nb_clusters):
            '''
            Subfunction of __createCentroids. in_cluster_of_j function affects a transition to the cluster of the trace.
            :param tr (Transition)
            :param c_kt (function) : @see variablesGenerator.py, function c_kt(k,t) gets BOOLEAN_VAR_K_CONTAINS_T
            variables
            :param j (int) : index of the current trace
            :param chi_jk (function) : @see variablesGenerator.py, function chi_jk gets BOOLEAN_VAR_J_IN_K variables
            :param nb_clusters (int) : number of cluster
            :return:
            '''
            # BOOLEAN_VAR_J_IN_K => BOOLEAN_VAR_K_CONTAINS_T
            return And([],[],[Or([c_kt([k,tr])],[chi_jk([j,k])],[]) for k in range (0, nb_clusters)])

        def is_transition_centroid(j, places, tr, i, m_ip):
            '''
            This function verifies marking to fire transition of a centroid.
            :param j (int) : index of centroid
            :param places (list) : list of places
            :param tr (Transition) : transition that wants to fire
            :param i (int) : instant of firing
            :param m_ip (function) : @see @variablesGenerator.py function to get BOOLEAN_VAR_CHI_MARKINGS variables
            '''
            formulas = []
            prePlaces = [a.source for a in tr.in_arcs]
            postPlaces = [a.target for a in tr.out_arcs]
            # token game
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

        def is_action_centroid(j,places, transitions, i, m_jip, tau_jip, c_kt, chi_jk, nb_clusters):
            '''
            @see pnToFormula.py, is_action_centroid says if transition is fired.
            :param j (int) : index of trace
            :param places (list) : places of the petri net, indexes are important
            :param transitions (list) : transitions of the petri net, indexes are important
            :param i (int) : instant in the run of the centroid
            :param m_jip (function) : @see variablesGenerator.py, function chi_jk gets BOOLEAN_VAR_CHI_MARKINGS variables
            :param tau_jip (function) : @see variablesGenerator.py, function chi_jk gets BOOLEAN_VAR_CHI_TRANSITIONS
             variables
            :param c_kt (function) : @see variablesGenerator.py, function chi_jk gets BOOLEAN_VAR_K_CONTAINS_T variables
            :param chi_jk (function) : @see variablesGenerator.py, function chi_jk gets BOOLEAN_VAR_J_IN_K variables
            :param nb_clusters (int) : number of cluster
            :return:
            '''
            # a transition fires and only one
            aTransitionPerInstant=[And([tau_jip([j, i, t])],
                                       [tau_jip([j, i, t2])for t2 in range(len(transitions)) if t != t2],
                                       []) for t in range(len(transitions))]
            formulas=[Or([],[],aTransitionPerInstant)]

            # runs is_transition for the fired transition
            indexOfTraceWait=transitions.index(self.__wait_transition_trace)
            for t in range(len(transitions)):
                # WAIT_TRANSITION_TRACE is forbidden for centroid
                if t == indexOfTraceWait :
                    formulas.append(And([],[tau_jip([j, i, t])],[]))
                else :
                    formulas.append(Or([], [tau_jip([j, i, t])],
                                       [And([],[],
                                             [is_transition_centroid(j, places, transitions[t], i, m_jip),
                                              in_cluster_of_j(t, c_kt, j, chi_jk, nb_clusters)])]))
            return And([], [], formulas)

        def is_run_centroid(j, size_of_run,m0,mf, m_jip, tau_jip, c_kt, chi_jk, nb_clusters, transitions, places ):
            '''
            Initialization of centroids. There is a run per trace. This run represents alignment of the trace to the
            model. If trace is clusterised then transition of it run are containing in the centroid of its cluster.
            :param j (int) : index of trace
            :param size_of_run (int) : maximal size of the run, prefix
            :param m0 (Marking) : initial marking
            :param m_jip (function) : @see variablesGenerator.py, function chi_jk gets BOOLEAN_VAR_CHI_MARKINGS variables
            :param tau_jip (function) : @see variablesGenerator.py, function chi_jk gets BOOLEAN_VAR_CHI_TRANSITIONS
             variables
            :param c_kt (function) : @see variablesGenerator.py, function chi_jk gets BOOLEAN_VAR_K_CONTAINS_T variables
            :param chi_jk (function) : @see variablesGenerator.py, function chi_jk gets BOOLEAN_VAR_J_IN_K variables
            :param nb_clusters (int) : number of cluster
            :param transitions (list) : list of Transitions
            :param places (list) : list of Places
            :return:
            '''
            positives = [m_jip([j,0, places.index(m)]) for m in m0]
            for m in mf:
                positives.append(m_jip([j,size_of_run,places.index(m)]))
            negatives = [m_jip([j,0, places.index(m)]) for m in places if m not in m0]
            formulas = [is_action_centroid(j,places, transitions, i, m_jip, tau_jip, c_kt, chi_jk, nb_clusters)
                        for i in range(1, size_of_run + 1)]
            run_of_pn = And(positives, negatives, formulas)
            return run_of_pn

        # .....................................................................................
        # here starts __createCentroids function
        centroidsFormulas=[]
        for j in range (0, len(self.__traces)):
            centroidOfJ=is_run_centroid(j, self.__size_of_run, m0,mf,
                                        self.__vars.getFunction(BOOLEAN_VAR_CHI_MARKINGS),
                                        self.__vars.getFunction(BOOLEAN_VAR_CHI_TRANSITIONS),
                                        self.__vars.getFunction(BOOLEAN_VAR_K_CONTAINS_T),
                                        self.__vars.getFunction(BOOLEAN_VAR_J_IN_K),
                                        self.__nb_clusters, self.__transitions, self.__places)
            centroidIfClusterised=Or([], [self.__vars.get(BOOLEAN_VAR_J_CLUSTERISED, [j])], [centroidOfJ])
            centroidsFormulas.append(centroidIfClusterised)
        return centroidsFormulas

    def __getDiffTracesCentroids(self, chi_jia, diffl_ji, diffm_ji, lambda_jia):
        '''
        This function that defines the difference between the traces and its centroid and calls
        __maxDiffTracesCentroids().
        :param chi_jia (function)
        :param diff_ji (function)
        :param lambda_jia (function)
        :return: list of formula
        '''
        formulas=[]
        for j in range (0, len(self.__traces)):
            aDiffPerInstant=[]
            for i in range(1,self.__size_of_run+1):
                # for each instant, a transition is true and there is or not a diff
                for t in range(0,len(self.__transitions)):
                    # if silent transition : diffjit is false
                    if self.__transitions[t] in self.__silent_transititons:
                        indexOfWaitModel=self.__transitions.index(self.__wait_transition_model)
                        indexOfWaitTrace=self.__transitions.index(self.__wait_transition_trace)
                        diffjit=Or([diffl_ji([j, i]),lambda_jia([j,i,indexOfWaitModel]),
                                    lambda_jia([j,i,indexOfWaitTrace])],[chi_jia([j, i, t])], [])
                    # chi_jia => lambda_jia or diff_ji
                    elif self.__transitions[t]==self.__wait_transition_model:
                        diffjit=Or([diffl_ji([j, i]),lambda_jia([j, i, t])],[chi_jia([j, i, t])], [])
                    elif self.__transitions[t]==self.__wait_transition_trace:
                        diffjit=Or([diffm_ji([j, i])],[chi_jia([j, i, t])], [])
                    else :
                        indexOfWaitTrace=self.__transitions.index(self.__wait_transition_trace)
                        diffjit=Or([],[],[Or([lambda_jia([j, i, t])],
                                             [chi_jia([j, i, t])],[
                                             And([diffl_ji([j, i]),diffm_ji([j, i])],[],[])
                                             ]),
                                          And([diffm_ji([j, i]),lambda_jia([j,i,indexOfWaitTrace]),chi_jia([j, i, t])],
                                             [],[])
                                          ])
                    aDiffPerInstant.append(diffjit)
            diffPerJ=And([],[],aDiffPerInstant)
            formulas.append(diffPerJ)

        # then there is maximal number of diff :
        self.__maxDiffTracesCentroids(formulas)
        return formulas

    def __maxDiffTracesCentroids(self,formulas):
        '''
        This function uses self.__max_d that determines the maximal distance of the trace to its centroid.
        Idea of the threshold : there are at least N diff variables false per trace.
        :param formulas (list of formula to fill)
        :return: void
        '''
        # this function uses combinations of itertools to get all the combinations : this is better than parameter
        # at_most of pysat library
        list_to_size_of_run= list(range(1,(self.__size_of_run*2)+1))
        max_distance=(self.__size_of_run*2)- self.__max_d
        # IDEA : there are at least max_distance number of false variables
        combinaisons_of_instants=list(itertools.combinations(list_to_size_of_run,max_distance))
        for j in range (0, len(self.__traces)):
            distFalseVariables=[]
            for instants in combinaisons_of_instants:
                list_distances=[]
                for i in instants:
                    if i <=self.__size_of_run :
                        list_distances.append(self.__vars.get(BOOLEAN_VAR_DIFF_l, [j,i]))
                    else :
                        list_distances.append(self.__vars.get(BOOLEAN_VAR_DIFF_m, [j,(i-self.__size_of_run)]))
                distFalseVariables.append(And([],list_distances,[]))
            formulas.append(Or([],[],distFalseVariables))

    def __commonTransitions(self, common_kkt, ckt):
        '''
        When two clusters share a transition, BOOLEAN_VAR_COMMON_T are True.
        :paramc common_kkt (function)
        :param ckt (function)
        :return list of formula
        '''
        listOfCommunTransitionsFormulas=[]
        for k1 in range (0, self.__nb_clusters):
            for k2 in range(k1+1,self.__nb_clusters):
                for t in range(len(self.__transitions)):
                    # (c_k1t and c_k2t) => common_k1k2t
                    haveATransitionInCommon=Or([common_kkt([k1, k2, t])],
                                               [ckt([k1, t]), ckt([k2, t])],[])
                    listOfCommunTransitionsFormulas.append(haveATransitionInCommon)
        return listOfCommunTransitionsFormulas

    def __maxTransitionsPerClusterAtMost(self,c_kt):
        '''
        This function uses self.__max_t that determines the maximal number of transition per centroid.
        :return: void
        '''
        for k1 in range (0,self.__nb_clusters):
            self.__wcnf.append([[c_kt([k1,t])
                                 for t in range (0,len(self.__transitions))
                                 if self.__transitions[t]!=self.__wait_transition_model],self.__max_t],is_atmost=True)

    def __tracesInAClusterOnly(self, inC_j, chi_jk):
        '''
        Verifies that j is in a unique cluster or any
        :param inC_j (function)
        :param chi_jk (function)
        '''
        formulas=[]
        for j in range (0, len(self.__traces)):
            inCorNot=[]
            for k1 in range (0,self.__nb_clusters):
                # if in k1 then not in other k
                inCorNot.append(And([inC_j([j]), chi_jk([j, k1])],
                                        [chi_jk([j, k]) for k in range (0,self.__nb_clusters) if k!=k1], []))
            # if in any k, then not inC
            allKNot=[chi_jk([j, k]) for k in range(0, self.__nb_clusters)]
            allKNot.append(inC_j([j]))
            inCorNot.append(And([],allKNot,[]))
            formulas.append(Or([],[],inCorNot))
        return  formulas

    def __minimizingDiff(self):
        '''
        Fills WCNF formula with weights on BOOLEAN_VAR_DIFF variables
        '''
        for j in range (0, len(self.__traces)):
            for i in range(1,self.__size_of_run+1):
                self.__wcnf.append([-1 * self.__vars.get(BOOLEAN_VAR_DIFF_l, [j, i])], 2)
                self.__wcnf.append([-1 * self.__vars.get(BOOLEAN_VAR_DIFF_m, [j, i])], 2)

    def __minimizingCommonTransitions(self):
        '''
        Fills WCNF formula with weights on BOOLEAN_VAR_COMMON_T variables
        '''
        for k1 in range (0,self.__nb_clusters):
            for transition in self.__transitions:
                t=self.__transitions.index(transition)
                for k2 in (k1+1,self.__nb_clusters):
                    self.__wcnf.append([-1 * self.__vars.get(BOOLEAN_VAR_COMMON_T, [k1, k2, t])], 2)
                self.__wcnf.append([-1*self.__vars.get(BOOLEAN_VAR_K_CONTAINS_T,[k1,t])],1)

    def __minimizingUnclusteredTraces(self):
        '''
        Fills WCNF formula with weights on BOOLEAN_VAR_J_IN_K variables
        '''
        for j in range (0, len(self.__traces)):
            for k in range(0, len(self.__traces)):
                self.__wcnf.append([self.__vars.get(BOOLEAN_VAR_J_IN_K, [j, k])], 100)

    def getClustering(self):
        '''
        This function reads the result of the SAT problem. Very dirty function... sorry.
        From a Boolean solution of variables, find the informative ones and extract results.
        :return: a simple dictionary of list of letter and Petri nets (centroids)
        '''
        clusters={}
        traces={}
        trs={}
        clusterized=[]
        for var in self.__model:
            if self.__vars.getVarName(var) != None and self.__vars.getVarName(var).startswith("diff"):
                print(self.__vars.getVarName(var))
            if self.__vars.getVarName(var) != None and self.__vars.getVarName(var).startswith(
                    BOOLEAN_VAR_K_CONTAINS_T):
                k= self.__vars.getVarName(var).split("[")[1].split(",")[0]
                t=self.__transitions[int(self.__vars.getVarName(var).split("]")[0].split(",")[1])]
                if int(k) not in clusters.keys():
                    clusters[int(k)]=[]
                clusters[int(k)].append(t)
            elif self.__vars.getVarName(var) != None and self.__vars.getVarName(var).startswith(
                    BOOLEAN_VAR_J_IN_K):
                j= self.__vars.getVarName(var).split("[")[1].split(",")[0]
                clusterized.append(int(j))
                k=(self.__vars.getVarName(var).split("]")[0].split(",")[1])
                if int(k) not in traces.keys():
                    traces[int(k)]=[]
                traces[int(k)].append(j)
            elif self.__vars.getVarName(var) != None and self.__vars.getVarName(var).startswith(
                BOOLEAN_VAR_TRACES_ACTIONS):
                j= self.__vars.getVarName(var).split("[")[1].split(",")[0]
                i=(self.__vars.getVarName(var).split("]")[0].split(",")[1])
                a=(self.__vars.getVarName(var).split("]")[0].split(",")[2])
                if int(j) not in trs.keys():
                    trs[int(j)]=[]
                trs[int(j)].append(str(self.__transitions[int(a)]))

        clustering=[]
        for i in clusters:
            pn_i=PetriNet()
            for a in self.__arcs:
                if type(a.source) is PetriNet.Transition and a.source in clusters[i] :
                    p_i = a.target
                    t_i = a.source
                    if t_i not in pn_i.transitions:
                        pn_i.transitions.add(t_i)
                    if p_i not in pn_i.places:
                        pn_i.places.add(p_i)
                    a = petri.petrinet.PetriNet.Arc(t_i, p_i, 1)
                    pn_i.arcs.add(a)
                elif type(a.target) is PetriNet.Transition  and a.target in clusters[i]:
                    p_i = a.source
                    t_i = a.target
                    if t_i not in pn_i.transitions:
                        pn_i.transitions.add(t_i)
                    if p_i not in pn_i.places:
                        pn_i.places.add(p_i)
                    a = petri.petrinet.PetriNet.Arc(p_i, t_i, 1)
                    pn_i.arcs.add(a)
            pn_i_f=deepcopy(pn_i)
            m_i_0=Marking()
            m_i_f=Marking()
            for p in pn_i_f.places:
                for n in self.__m0.keys():
                    if n.name==p.name :
                        m_i_0[p]=1
                for n in self.__mf.keys():
                    if n.name==p.name:
                        m_i_f[p]=1
            cluster=((pn_i_f,m_i_0,m_i_f),[])
            if i in traces:
                for j in traces[i]:
                    cluster[1].append([a for a in trs[int(j)]])
            clustering.append(cluster)
        unclusterized = [t for (i,t) in enumerate(self.__traces) if i not in clusterized]
        clustering.append(({"Unclusterized"},unclusterized))
        return  clustering

    def getTime(self):
        return self.__endComputationTime-self.__start

def samplingVariantsForAmstc(net, m0, mf, log,sample_size,size_of_run, max_d, max_t, m ,maxCounter=2,editDistance=True,silent_label="tau", debug=None):
    '''
    This function computes a AMSTC with a sampling method. See scientific paper : Model-based Trace Variants
    :param net (Petri) : process model
    :param m0 (Marking) : initial marking
    :param mf (Marking) : final marking
    :param log (Log) : log traces
    :param sample_size (int) : number of traces that will be used in the complete AMSTC
    :param size_of_run (int) : length of the run in the process model
    :param max_d (int) : maximal distance between centroids and traces
    :param max_t (int) : maximal number of transitions in a cluster
    :param m (int) : number of cluster
    :param maxCounter (int) : number of trials without results in the sampling method
    :param editDistance (bool) : use of edit distance between traces
    :param silent_label (string) : count 0 every transition that contains its substring
    :return:
    '''
    def logAlignToCluster(tuple_centroid, traces, variants,editDistance,max_d,counter):
        '''
        Private function of the sampling method with variants. From a centroid, cluster all the traces that
        can be aligned for a cost <= max_d
        :param tuple_centroid: (net, m0, mf)
        :param traces: list of log traces
        :param variants: dictionary of variants
        :param editDistance (boolean) : use or not the edit distance heuristic
        :param max_d (int): maximal distance between the traces and centroids (or casual distance !!)
        :param counter (int): number of trials
        :return:
        '''
        centroid, c_m0, c_mf= tuple_centroid
        traces_of_clusters=[]
        used_variants=[]
        cleaned_clustered_traces=[]
        for clustered in traces:
            # remove "w" and "ww" labels of SAT results
            cleaned_clustered_traces.append([x for x in clustered if x != WAIT_LABEL_TRACE and x!=WAIT_LABEL_MODEL])
        for l in variants:
            bool_clustered=False
            if editDistance:
                # format is not the same due to the SAT results
                transformed_l =list(map(lambda e: e[xes_util.DEFAULT_NAME_KEY], variants[l][0]))
                # align clustered traces and entire log traces with edit distance
                for clustered in cleaned_clustered_traces:
                    if editdistance.eval(clustered,transformed_l) <(max_d+1):
                        counter=-1
                        traces_of_clusters+=variants[l]
                        used_variants.append(l)
                        bool_clustered=True
                        break
            # align centroid and entire log with alignments
            if not bool_clustered:
                alignment=alignments.algorithm.apply(variants[l][0],centroid,c_m0,c_mf)
                if alignment['cost']< 10000*((max_d+1)):
                    counter=-1
                    traces_of_clusters+=variants[l]
                    used_variants.append(l)
        return traces_of_clusters,used_variants,cleaned_clustered_traces, counter

    # ---------------------------------------------------------------------------------------------------------------
    log=deepcopy(log)
    start,totalAlign = time.clock(), 0
    counter, nbOfIteration = 0, 0
    clusters=[]
    variants=get_variants(log)
    while len(log._list)>0 and counter<maxCounter:
        clustering = Amstc(net,m0,mf,log,size_of_run, max_d,max_t,m,nbTraces=sample_size,silent_label=silent_label)
        nbOfIteration+=1
        result=clustering.getClustering()

        if debug is not None:
            print("> Found",len(result)-1,"centroids")
            print(time.clock()-start)

        # if there is at least a clustered trace :
        if len(result)-1>0:
            for (tuple_centroid,traces) in result:
                if type (tuple_centroid) is tuple :

                    # launches logAlignToCluster function that uses trace variant alignments to cluster
                    startAlign=time.clock()
                    traces_of_clusters, used_variants,cleaned_clustered_traces, counter=\
                        logAlignToCluster(tuple_centroid, traces, variants,editDistance, max_d,counter)
                    totalAlign+=(time.clock()-startAlign)
                    for v in used_variants:
                        del variants[v]
                    log._list=list(set(log._list)-set(traces_of_clusters))

                    # create the cluster
                    if len(traces_of_clusters)>0:
                        clusters.append((tuple_centroid,traces_of_clusters))
            # if we found at least a good centroid
            if counter==-1:
                counter=0
            else:
                counter+=1
        else :
            counter+=1

    if debug is not None:
        print("This clustering has been found in ",nbOfIteration," iterations and "+str(time.clock()-start)+"secondes.")
        print(str(totalAlign)+" secondes have been used to align.")
        for (centroid, traces)in clusters:
            print(len(traces))
            if type(centroid) is tuple:
                net, m0,mf=centroid
                #vizu.apply(net, m0, mf).view()
                #input("enter..")
        print(len(log._list),"traces are unclustered.")
    clusters.append(("nc",log._list))
    return clusters





def samplingForAmstc(net, m0, mf, log,sample_size,size_of_run, max_d, max_t, m ,maxCounter=2,editDistance=True,silent_label="tau"):
    '''
    DEPRECATED FUNCTION!! It is still just available for the experiment of the paper Model based trace variants
    '''
    warnings.warn("This function is Deprecated. Please use samplingVariantsForAmstc().", DeprecationWarning,stacklevel=2)
    start=time.time()
    totalAlign=0
    clusters=[]
    counter=0
    nbOfIteration=0
    while len(log._list)>0 and counter<maxCounter:
        clustering = Amstc(net,m0,mf,log,size_of_run, max_d,max_t,m,nbTraces=sample_size,silent_label=silent_label)
        nbOfIteration+=1
        result=clustering.getClustering()
        print("> Found",len(result)-1,"centroids")
        print(time.time()-start)
        # if there is at least a clustered trace :
        if len(result)-1>0:
            for (tuple_centroid,traces) in result:
                if type (tuple_centroid) is tuple :

                    centroid, c_m0, c_mf= tuple_centroid
                    traces_of_clusters=[]
                    cleaned_clustered_traces=[]

                    startAlign=time.time()
                    for clustered in traces:
                        cleaned_clustered_traces.append([x for x in clustered if x != WAIT_LABEL_TRACE and x!=WAIT_LABEL_MODEL])
                    for l in log._list:
                        bool_clustered=False
                        if editDistance:
                            transformed_l =list(map(lambda e: e[xes_util.DEFAULT_NAME_KEY], l))
                            for clustered in cleaned_clustered_traces:
                                if editdistance.eval(clustered,transformed_l) <(max_d+1):
                                    counter=-1
                                    traces_of_clusters.append(l)
                                    bool_clustered=True
                                    break
                        if not bool_clustered:
                            alignment=alignments.algorithm.apply(l,centroid,c_m0,c_mf)
                            if alignment['cost']< 10000*((max_d+1)):
                                counter=-1
                                traces_of_clusters.append(l)
                    totalAlign+=(time.time()-startAlign)
                    log._list=list(set(log._list)-set(traces_of_clusters))

                    if len(traces_of_clusters)>0:
                        clusters.append((tuple_centroid,traces_of_clusters))

            # if we found at least a good centroid
            if counter==-1:
                counter=0
            else:
                counter+=1
        else :
            counter+=1
    print("This clustering has been found in ",nbOfIteration," iterations and "+str(time.time()-start)+"secondes.")
    print(str(totalAlign)+" secondes have been used to align.")
    for (centroid, traces)in clusters:
        print(len(traces))
    print(len(log._list),"traces are unclustered.")



