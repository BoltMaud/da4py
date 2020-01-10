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

Scientific paper : _Generalized Alignment-Based Trace Clustering of Process Behavior_
By : Mathilde Boltenhagen, Thomas Chatain, Josep Carmona

'''
import time
import itertools

from da4py.main.utils.variablesGenerator import VariablesGenerator
from pm4py.objects.petri.petrinet import PetriNet
from pysat.examples.rc2 import RC2
from pysat.formula import WCNF

from da4py.main.objects.logToFormulas import log_to_Petri_with_w
from da4py.main.utils.formulas import And, Or

BOOLEAN_VAR_J_IN_K="chi_jk"
BOOLEAN_VAR_TRACES_ACTIONS="lambda_jia"
BOOLEAN_VAR_CHI_MARKINGS="m_chijip"
BOOLEAN_VAR_CHI_TRANSITIONS="tau_chijia"
BOOLEAN_VAR_DIFF= "diff_ji"
BOOLEAN_VAR_K_CONTAINS_T= "c_kt"
BOOLEAN_VAR_COMMON_T="common_kkt"
BOOLEAN_VAR_J_CLUSTERISED="inC_j"

WAIT_LABEL_TRACE="w"
WAIT_LABEL_MODEL="ww"

# some parallelism
NB_MAX_THREADS = 50

class Amstc:
    '''
    Alignment and Model Subnet-based Trace Clustering
    Creates clusters depending on subnets
    '''

    def __init__(self, pn, m0, mf, traces_xes, size_of_run, max_d, max_t, nb_clusters,silent_label=None):
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
        self.__transitions=list(pn.transitions)
        self.__places=list(pn.places)
        self.__nb_clusters=nb_clusters
        self.__silent_transititons=[t for t in self.__transitions if t.label==silent_label]
        # add wait transitions that represents log and model move for alignment
        self.__addWaitTransitions(pn,mf)
        self.__start=time.time()
        self.__createSATformula(pn, m0, mf, max_d, max_t,traces_xes)

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


    def __createSATformula(self, pn, m0, mf, max_d,max_t, traces_xes):
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
                                                               max_nbTraces=None)
        # creates the boolean variables for the next formulas
        self.__createBooleanVariables()
        # formula of centroids
        centroidsFormulasList = self.__createCentroids(m0)
        # formula that describes maximal distance
        diffTracesCentroids=self.__getDiffTracesCentroids(self.__vars.getFunction(BOOLEAN_VAR_CHI_TRANSITIONS),
                                                          self.__vars.getFunction(BOOLEAN_VAR_DIFF),
                                                          self.__vars.getFunction(BOOLEAN_VAR_TRACES_ACTIONS))
        # formula that create BOOLEAN_VAR_COMMON_T variables
        listOfCommonTransitions=self.__commonTransitions(self.__vars.getFunction(BOOLEAN_VAR_COMMON_T),
                                                         self.__vars.getFunction(BOOLEAN_VAR_K_CONTAINS_T))
        # formula that describes that a trace belongs to at most one cluster
        aClusterMax=self.__tracesInAClusterOnly(self.__vars.getFunction(BOOLEAN_VAR_J_CLUSTERISED),
                                                self.__vars.getFunction(BOOLEAN_VAR_J_IN_K))
        # formula that describes maximal number of transitions per centroids
        numberTransitionsPerCluster=self.__maxTransitionsPerCluster(self.__vars.getFunction(BOOLEAN_VAR_K_CONTAINS_T))

        # concat the formula
        full_formula = And([], [], log_to_PN_w_formula + centroidsFormulasList + diffTracesCentroids +
                            listOfCommonTransitions + aClusterMax + numberTransitionsPerCluster)
        # formula to cnf
        cnf = full_formula.operatorToCnf(self.__vars.iterator)

        # CNF is completed with minimisation and solved
        self.__createWCNFWithMinimization(cnf)

    def __createBooleanVariables(self):
        '''
        This function creates the boolean variables needed in this class.
        '''
        self.__vars.add(BOOLEAN_VAR_DIFF, [(0, len(self.__traces)), (1, self.__size_of_run + 1)])
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
        print("formulas", time.time()-self.__start)
        self.__wcnf = WCNF()
        self.__wcnf.extend(cnf)
        # most of the traces should be clustered
        self.__minimizingUnclusteredTraces()
        # minimizing BOOLEAN_VAR_COMMON_T variables
        self.__minimizingCommonTransitions()
        # minimizing BOOLEAN_VAR_diff_TRACE_CENTROIDS variables
        self.__minimizingDiff()
        # RC2 is a MaxSAT algorithm
        solver = RC2(self.__wcnf, solver="g4")
        solver.compute()
        self.__endComputationTime=time.time()
        self.__model = solver.model

    def __createCentroids(self,m0):
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

        def is_run_centroid(j, size_of_run,m0, m_jip, tau_jip, c_kt, chi_jk, nb_clusters, transitions, places ):
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
            negatives = [m_jip([j,0, places.index(m)]) for m in places if m not in m0]
            formulas = [is_action_centroid(j,places, transitions, i, m_jip, tau_jip, c_kt, chi_jk, nb_clusters)
                        for i in range(1, size_of_run + 1)]
            run_of_pn = And(positives, negatives, formulas)
            return run_of_pn

        # .....................................................................................
        # here starts __createCentroids function
        #todo parallelism
        centroidsFormulas=[]
        for j in range (0, len(self.__traces)):
            centroidOfJ=is_run_centroid(j, self.__size_of_run, m0,
                                        self.__vars.getFunction(BOOLEAN_VAR_CHI_MARKINGS),
                                        self.__vars.getFunction(BOOLEAN_VAR_CHI_TRANSITIONS),
                                        self.__vars.getFunction(BOOLEAN_VAR_K_CONTAINS_T),
                                        self.__vars.getFunction(BOOLEAN_VAR_J_IN_K),
                                        self.__nb_clusters, self.__transitions, self.__places)
            centroidIfClusterised=Or([], [self.__vars.get(BOOLEAN_VAR_J_CLUSTERISED, [j])], [centroidOfJ])
            centroidsFormulas.append(centroidIfClusterised)
        return centroidsFormulas

    def __getDiffTracesCentroids(self, chi_jia, diff_ji, lambda_jia):
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
                        diffjit=Or([],[chi_jia([j, i, t]), diff_ji([j, i])], [])
                    # chi_jia => lambda_jia or diff_ji
                    else :
                        diffjit=Or([diff_ji([j, i]),lambda_jia([j, i, t])],[chi_jia([j, i, t])], [])
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
        list_to_size_of_run= list(range(1,self.__size_of_run+1))
        max_distance=self.__size_of_run- self.__max_d
        # IDEA : there are at least max_distance number of false variables
        combinaisons_of_instants=list(itertools.combinations(list_to_size_of_run,max_distance))
        for j in range (0, len(self.__traces)):
            distFalseVariables=[]
            for instants in combinaisons_of_instants:
                distFalseVariables.append(And([],[self.__vars.get(BOOLEAN_VAR_DIFF, [j, i])
                                            for i in list(instants)],[]))
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

    def __maxTransitionsPerCluster(self, c_kt):
        '''
        This function uses self.__max_t that determines the maximal number of transition per centroid.
        Idea of the threshold : there are at least N transitions that aren't in centroid.
        :param formulas (list of formula to fill)
        :return: void
        '''
        # this function uses combinations of itertools to get all the combinations : this is better than parameter
        # at_most of pysat library
        listOfAnd=[]
        list_of_transitions_indexes= [t for t in range(0,len(self.__transitions))
                                        if self.__transitions[t]!=self.__wait_transition_model]
        max_tFalse=len(self.__transitions)- self.__max_t-1
        combinaisons_of_transtions=list(itertools.combinations(list_of_transitions_indexes,max_tFalse))
        for k in range (0, self.__nb_clusters):
            listOfAndNeg=[]
            for transitions_indexes in combinaisons_of_transtions:
                listOfAndNeg.append(And([],[c_kt([k, i])for i in list(transitions_indexes)],[]))
            listOfAnd.append(Or([],[],listOfAndNeg))
        return listOfAnd

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
                self.__wcnf.append([-1 * self.__vars.get(BOOLEAN_VAR_DIFF, [j, i])], 1)

    def __minimizingCommonTransitions(self):
        '''
        Fills WCNF formula with weights on BOOLEAN_VAR_COMMON_T variables
        '''
        for k1 in range (0,self.__nb_clusters):
            for transition in self.__transitions:
                t=self.__transitions.index(transition)
                for k2 in (k1+1,self.__nb_clusters):
                    self.__wcnf.append([-1 * self.__vars.get(BOOLEAN_VAR_COMMON_T, [k1, k2, t])], 1)

    def __minimizingUnclusteredTraces(self):
        '''
        Fills WCNF formula with weights on BOOLEAN_VAR_J_IN_K variables
        '''
        for j in range (0, len(self.__traces)):
            for k in range(0, len(self.__traces)):
                self.__wcnf.append([self.__vars.get(BOOLEAN_VAR_J_IN_K, [j, k])], 1)

    def getClustering(self):
        clusters={}
        traces={}
        trs={}
        clusterized=[]
        for var in self.__model:
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
            cluster=(set(clusters[i]),[])
            if i in traces:
                for j in traces[i]:
                    cluster[1].append([a for a in trs[int(j)]])
            clustering.append(cluster)

        unclusterized = [t for (i,t) in enumerate(self.__traces) if i not in clusterized]
        clustering.append(({"Unclusterized"},unclusterized))
        return  clustering

    def getTime(self):
        return self.__endComputationTime-self.__start




