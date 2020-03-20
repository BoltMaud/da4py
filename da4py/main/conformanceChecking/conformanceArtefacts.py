#!/usr/bin/env python
# -*- coding:utf-8 -*-
##
## conformanceArtefacts.py
##
##  Created on: September, 2019
##      Author: Boltenhagen Mathilde
##      E-mail: boltenhagen lsv . fr
##

'''

The ConformanceArtefacts class is a factory class that can run the different artefacts:
    -   Multi-Alignment
    -   Anti-Alignment

Two distances are available with specific formula reduction for anti-alignment and multi-alignment. The exact formulas
are also implemented but shouldn't be used. They are presented for experimentations.

Scientific paper : _Encoding Conformance Checking Artefacts in SAT_
By : Mathilde Boltenhagen, Thomas Chatain, Josep Carmona

'''
import math
import time
from copy import deepcopy

import pandas as pd
from pm4py.objects.petri.petrinet import PetriNet, Marking
from pysat.examples.rc2 import RC2
from pysat.formula import WCNF
from da4py.main.conformanceChecking.distancesToFormulas import hamming_distance_per_trace_to_SAT, edit_distance_per_trace_to_SAT, \
    for_hamming_distance_aux_supd, levenshtein, hamming
from da4py.main.utils.formulas import And, Or
from da4py.main.objects.logToFormulas import log_to_SAT
from da4py.main.objects.pnToFormulas import petri_net_to_SAT
from da4py.main.utils import variablesGenerator as vg

# a wait transition is added to complete words, :see __add_wait_net()
WAIT_TRANSITION = "w"
SILENT_LABEL=None

# our boolean formulas depends on variables, see our paper for more information
BOOLEAN_VAR_MARKING_PN = "m_ip"
BOOLEAN_VAR_FIRING_TRANSITION_PN = "tau_it"
BOOLEAN_VAR_TRACES_ACTIONS = "lambda_jia"
BOOLEAN_VAR_EDIT_DISTANCE = "djiid"
BOOLEAN_VAR_HAMMING_DISTANCE="dji"
BOOLEAN_VAR_SUP = "supd"
BOOLEAN_VAR_HAMMING_SUP_AUX = "supjd"

# SAT solver allows to add weights on clauses to reduce or maximize
WEIGHT_ON_CLAUSES_TO_REDUCE = -10

# two distances are available
HAMMING_DISTANCE = "hamming"
EDIT_DISTANCE = "edit"

# three implementations have been created
MULTI_ALIGNMENT = "multi"
ANTI_ALIGNMENT = "anti"
EXACT_ALIGNMENT = "exact"


class ConformanceArtefacts:
    '''

    The ConformanceArtefacts class is a factory class that can run the different artefacts:
    -   Multi-Alignment
    -   Anti-Alignment
    ( and the exact distance )

    '''

    def __init__(self, distance=EDIT_DISTANCE, solver="g4",reachFinal=False):
        '''
        Conformance artefact share some initialisation
        :param distance (string) : value = HAMMING_DISTANCE or EDIT_DISTANCE
        :param solver: one of the SAT solver of the librairy pysat
        '''
        self.__distance_type = distance
        self.__solver = solver
        self.__silent_label=SILENT_LABEL
        self.__max_nbTraces=None
        self.__optimizeMin=True
        self.__reachFinal=reachFinal

    def multiAlignment(self, net, m0, mf, traces):
        '''
        The multiAlignment method takes a petri net and a log and compute the SAT formulas to get a run of the model
        that is the closest one to all the traces of the log.
        :param size_of_run (int) : maximal size of run, too limit the run when there are loops
        :param max_d (int) :
        :param net (Petrinet) : model
        :param m0 (marking) : initial marking
        :param mf (marking) : final marking
        :param traces (pm4py.objects.log) : traces
        :return:
        '''
        self.__artefact=MULTI_ALIGNMENT
        # transforms the model and the log to SAT formulas
        initialisationFormulas, self.__wait_transition = self.__artefactsInitialisation(net, m0, mf, traces)

        # computes the distance for multi-alignment
        distanceFormula = self.__compute_distance(MULTI_ALIGNMENT, self.__wait_transition)

        # solve the formulas
        wncf = self.__createWncf(initialisationFormulas, distanceFormula, MULTI_ALIGNMENT)
        self.__solveWncf(wncf)
        return 0

    def antiAlignment(self, net, m0, mf, traces):
        '''
        The antiAlignment method takes a petri net and a log and compute the SAT formulas to get a run of the model
        that is as far as possible to any traces of the log.
        :param net (Petrinet) : model
        :param m0 (marking) : initial marking
        :param mf (marking) : final marking
        :param traces (pm4py.objects.log) : traces
        :return:
        '''
        self.__artefact=ANTI_ALIGNMENT
        # transforms the model and the log to SAT formulas
        initialisationFormulas, self.__wait_transition = self.__artefactsInitialisation(net,m0, mf, traces)

        # computes the distance for multi-alignment
        distanceFormula = self.__compute_distance(ANTI_ALIGNMENT, self.__wait_transition)

        # solve the formulas
        wncf = self.__createWncf(initialisationFormulas, distanceFormula, ANTI_ALIGNMENT)
        self.__solveWncf(wncf)
        return 0

    def exactAlignment(self, net, m0, mf, traces):
        '''
        # TODO : be more precised
       The exactAlignment method takes a petri net and a log and compute the SAT formulas to get a run of the model
       that is the closest one to all the traces of the log. Notice that this function is presented for experimentation
       only.
       :param net (Petrinet) : model
       :param m0 (marking) : initial marking
       :param mf (marking) : final marking
       :param traces (pm4py.objects.log) : traces
       :param silent_transition (string) : transition with this label will not increase the distances
       :return:
       '''
        initialisationFormulas, self.__wait_transition = self.__artefactsInitialisation(net,m0, mf, traces)
        distanceFormula = self.__compute_distance(EXACT_ALIGNMENT, self.__wait_transition)
        wncf = self.__createWncf(initialisationFormulas, distanceFormula, EXACT_ALIGNMENT)
        self.__solveWncf(wncf)
        return 0

    def __artefactsInitialisation(self,net, m0, mf, traces):
        '''
        The initialisation of all the artefacts :
            - launches a VariablesGenerator to creates the variables numbers
            - translates the model into formulas
            - translates the log into formulas
        :param (marking) : initial marking
        :param mf (marking) : final marking
        :param traces (pm4py.objects.log) : traces
        :return:
        '''
        self.__copy_net(net,m0,mf)
        # this variable (__variables) memorises the numbers of the boolean variables of the formula
        self.__vars = vg.VariablesGenerator()

        # we add a "wait" transition to complete the words
        self.__wait_transition = self.__add_wait_net()

        self.__start_time = time.time()
        # the model is translated to a formula
        pn_formula, places, self.__transitions, self.__silent_transitions = petri_net_to_SAT(self.__pn, self.__m0, self.__mf, self.__vars,
                                                                                             self.__size_of_run,
                                                                                             self.__reachFinal,
                                                                                             label_m=BOOLEAN_VAR_MARKING_PN,
                                                                                             label_t=BOOLEAN_VAR_FIRING_TRANSITION_PN,
                                                                                             silent_transition=self.__silent_label)
        # the log is translated to a formula
        log_formula, traces = log_to_SAT(traces, self.__transitions, self.__vars, self.__size_of_run,
                                         self.__wait_transition, max_nbTraces=self.__max_nbTraces)
        self.__traces = traces
        return [pn_formula, log_formula], self.__wait_transition

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

    def __compute_distance(self, artefact, wait_transition):
        '''
        :param artefact: EXACT_ALIGNMENT or MULTI_ALIGNMENT or ANTI_ALIGNMENT, see globale variables
        :param wait_transition: see add_wait_transition
        :return: formulas of the distance
        '''
        if self.__distance_type == HAMMING_DISTANCE:
            return hamming_distance_per_trace_to_SAT(artefact, self.__transitions, self.__silent_transitions, self.__vars, len(self.__traces),
                                                     self.__size_of_run)
        elif self.__distance_type == EDIT_DISTANCE:
            return edit_distance_per_trace_to_SAT(artefact, self.__transitions, self.__silent_transitions, self.__vars, len(self.__traces),
                                                  self.__size_of_run,
                                                  self.__wait_transition, self.__max_d)
        else:
            raise Exception("Distance doesn't exist.")


    def __createWncf(self, initialisationFormulas, distanceFormula, artefactForMinimization):
        '''
        This method creates the wncf formulas with the weighted variables depending on the distance and artefact.
        :param initialisationFormulas: @see __artefactsInitialisation
        :param distanceFormula: @see __compute_distance
        :param artefactForMinimization: MULTI_ALIGNMENT or ANTI_ALIGNMENT or EXACT_ALIGNMENT
        :return:
        '''
        formulas = initialisationFormulas + distanceFormula + self.__sup_to_minimize(artefactForMinimization)
        full_formula = And([], [], formulas)
        cnf = full_formula.operatorToCnf(self.__vars.iterator)
        wcnf = WCNF()
        wcnf.extend(cnf)
        wcnf = self.__createWeights(wcnf,artefactForMinimization)
        self.__formula_time = time.time()
        return wcnf

    def __createWeights(self,wcnf,artefactForMinimization):
        '''
        Add weights on variables. Depend on optimizeMin and distance_type. If optimizeMin is true, then we do real anti
        alignment, otherwise we minimize/maximise the SUM of all the distances instead of the common minimal distance.
        Exemple :
        :param wcnf: formula
        :param artefactForMinimization (string)
        :return:
        '''
        # weights of variables depends on artefact
        weightsOnVariables = -1 if artefactForMinimization != ANTI_ALIGNMENT else 1

        # MIN real anti/multi
        if self.__optimizeMin==True :
            for d in range(0, self.__max_d ):
                wcnf.append([weightsOnVariables * self.__vars.get(BOOLEAN_VAR_SUP, [d])], WEIGHT_ON_CLAUSES_TO_REDUCE)
        # SUM
        else :
            if self.__distance_type == EDIT_DISTANCE:
                for j in range(0, len(self.__traces)):
                    for d in range(1, self.__max_d + 1):
                        wcnf.append([weightsOnVariables * self.__vars.get(BOOLEAN_VAR_EDIT_DISTANCE,
                                                                          [j, self.__size_of_run,
                                                                                        self.__size_of_run, d])],
                                   WEIGHT_ON_CLAUSES_TO_REDUCE)

            # weighted variables for edit distance are d_j,i
            elif self.__distance_type == HAMMING_DISTANCE:
                for j in range(0, len(self.__traces)):
                    for i in range(1, self.__size_of_run + 1):
                        wcnf.append([weightsOnVariables * self.__vars.get(BOOLEAN_VAR_HAMMING_DISTANCE, [j, i])],
                                    WEIGHT_ON_CLAUSES_TO_REDUCE)
        return wcnf

    def __solveWncf(self, wcnf):
        '''
        This method launches the SAT solver.
        :param wcnf: formulas
        :return:
        '''
        solver = RC2(wcnf, solver=self.__solver)
        solver.compute()
        end_solver = time.time()
        self.__model = solver.model if solver.model else None
        self.__total_time=time.time()

    def getPrecision(self):
        '''
        Formula : 1 - (distance/max length)
        :return (int)
        '''
        if self.__artefact==ANTI_ALIGNMENT:
            if self.__model is not None:
                try :
                    if self.__distance_type==EDIT_DISTANCE:
                        for d in range (self.__max_d,-1,-1):
                            if self.__vars.get(BOOLEAN_VAR_SUP, [d]) in self.__model:
                                return float(1)-float(d)/float(self.__max_d)
                    if self.__distance_type==HAMMING_DISTANCE:
                        for d in range (self.__size_of_run,-1,-1):
                            if self.__vars.get(BOOLEAN_VAR_SUP, [d]) in self.__model:
                                return float(1)-float(d)/float(self.__max_d)
                except:
                    raise Exception("Precision can only be computed with OptimizeSup to True.")
            else :
                return None
        else :
            raise Exception("Precision should be done with anti-alignment.")

    def getMinDistanceToRun(self):
        '''
        While artefact is computed, one may want to know what is the minimal distance of the run to the traces.
        :return (int)
        '''
        if self.__artefact==ANTI_ALIGNMENT:
            if self.__model is not None:
                if  self.__optimizeMin:
                    if self.__distance_type=="edit":
                        for d in range (0,self.__max_d+1):
                            if not self.__vars.get(BOOLEAN_VAR_SUP, [d]) in self.__model:
                                return d-1
                    else :
                        for d in range (0,self.__size_of_run):
                            if not self.__vars.get(BOOLEAN_VAR_SUP, [d]) in self.__model:
                                return d-1
                else :
                    # subfunction to get the good variables.
                    if self.__distance_type=="hamming":
                        def functionDistance(j,d):
                            return self.__vars.get(BOOLEAN_VAR_HAMMING_DISTANCE, [j, d])
                    else:
                        def functionDistance(j,d):
                            return self.__vars.get(BOOLEAN_VAR_EDIT_DISTANCE, [j, self.__size_of_run, self.__size_of_run, d])
                    # when one maximised the max, we check all the traces.
                    for d in range (0,self.__max_d):
                            for j in range(0,len(self.__traces)):
                                if functionDistance(j,d) not in self.__model:
                                    return d-1
            else:
                return None
        else :
            raise Exception("Not developed for multi-alignment.")

    def getRealSizeOfRun(self):
        '''
        As we complete run with "wait" transition, we need the real size of the run
        :return:
        '''
        if self.__model is not None:
            i_wait=self.__transitions.index(self.__wait_transition)
            for i in range(self.__size_of_run,0,-1):
                if self.__vars.get(BOOLEAN_VAR_FIRING_TRANSITION_PN, [i, i_wait]) not in self.__model:
                    return i
        else:
            return None

    def getRun(self,debug=False):
        '''
        Returns a very simple string version of the multi or anti alignment
        :param debug : to True return a string version with indices
        :return (string) : output run
        '''
        try :
            run = "<"
            run_list=[]
            for var in self.__model:
                if self.__vars.getVarName(var) != None and self.__vars.getVarName(var).startswith(
                        BOOLEAN_VAR_FIRING_TRANSITION_PN):
                    index = self.__vars.getVarName(var).split("]")[0].split(",")[1]
                    i = self.__vars.getVarName(var).split("[")[1].split(",")[0]
                    run += " (" + i + ", " + str(self.__transitions[int(index)]) + ") "
                    run_list.append(str(self.__transitions[int(index)]))
            run += ">"
            return run if debug else run_list
        except :
            raise Exception("Cannot get run because model doesn't exist. See if SAT formula returns True.")

    def getTracesWithDistances(self):
        '''
        Returns a very simple string version of the traces with their distance to the run
        :return:
        '''
        array_of_distance = [self.__getDistanceOfTrace(i) for i in range(0,len(self.__traces))]
        return (pd.DataFrame({"distance" :array_of_distance,"traces": self.__traces}))

    def fullRunOnly(self,bool=False):
        '''
        This function implies to choose to reach or not the final marking
        :param bool: reach final or not
        :return: void
        '''
        self.__reachFinal=bool

    def __getDistanceOfTrace(self,l):
        '''
        Returns the maximal distance of the trace to the run
        :param l (int) : lth trace
        :return d (int)
        '''
        # only work for max because reducting formulas allows distance boolean variables to be True
        if not self.__optimizeMin:
            if self.__distance_type == EDIT_DISTANCE:
                max_d = 0
                for d in range(0, self.__max_d ):
                    if self.__vars.get(BOOLEAN_VAR_EDIT_DISTANCE,
                                       [l, self.__size_of_run, self.__size_of_run, d]) in self.__model:
                        max_d = d

            if self.__distance_type == HAMMING_DISTANCE:
                max_d = 0
                for i in range(1, self.__size_of_run + 1):
                    if self.__vars.get(BOOLEAN_VAR_HAMMING_DISTANCE, [l, i]) in self.__model:
                        max_d += 1
            return max_d
        else:
            if self.__distance_type == EDIT_DISTANCE:
                return levenshtein(self.getRun(),self.__traces[l])
            else :
                return hamming(self.getRun(),self.__traces[l])

    def __sup_to_minimize(self,artefact):
        '''
        If we minimize SUP then we need to add some variables. Otherwise no.
        :param artefact:
        :return:
        '''
        # if we do max, then we don't have to add variables for distance
        if self.__optimizeMin==False :
            return []
        else :
            # create new variables SUPD
            self.__vars.add(BOOLEAN_VAR_SUP, [(0, self.__max_d + 1)])

            if self.__distance_type== EDIT_DISTANCE:
                def variables_edit_distance(j,d):
                    return self.__vars.get(BOOLEAN_VAR_EDIT_DISTANCE, [j, self.__size_of_run, self.__size_of_run, d])
                return self.__sup_to_minimize_with_distance_function(artefact,variables_edit_distance)

            elif self.__distance_type==HAMMING_DISTANCE:
                self.__vars.add(BOOLEAN_VAR_HAMMING_SUP_AUX, [(0, len(self.__traces)), (0, self.__max_d + 1)])
                def variables_edit_distance(j,d):
                    return self.__vars.get(BOOLEAN_VAR_HAMMING_SUP_AUX, [j, d])
                d_max_per_j = for_hamming_distance_aux_supd(artefact, self.__vars, len(self.__traces), self.__max_d, self.__size_of_run)
                return d_max_per_j+ self.__sup_to_minimize_with_distance_function(artefact,variables_edit_distance)

    def __sup_to_minimize_with_distance_function(self,artefact,variablesFunction):
        list_of_formula=[]
        if artefact == ANTI_ALIGNMENT:
            for d in range (0, self.__max_d+1):
                list_of_d=[]
                for j in range(0, len(self.__traces)):
                    # delta_j1nnd and delta_j2nnd and ... delta_jlnnd
                    list_of_d.append(variablesFunction(j,d))
                # not di or ( dji and dji ... dji)
                not_di_or_list_of_and=Or([], [self.__vars.get(BOOLEAN_VAR_SUP, [d])], [
                    And(list_of_d,[],[])])
                list_of_formula.append(not_di_or_list_of_and)

        if artefact == MULTI_ALIGNMENT :
            for d in range (0, self.__max_d + 1):
                list_of_d=[]
                for j in range(0, len(self.__traces)):
                    # not delta_j1nnd or not delta_j2nnd or ... not delta_jlnnd
                    list_of_d.append(variablesFunction(j,d))
                #  di or ( dji or dji ... dji)
                not_di_or_list_of_and=Or([self.__vars.get(BOOLEAN_VAR_SUP, [d])], [], [And([], list_of_d, [])])
                list_of_formula.append(not_di_or_list_of_and)
        return  list_of_formula

    def __add_wait_net(self):
        '''
        Words don't have the same length. To compare them we add a "wait" transition at the end of the model and the
        traces.
        :return:
        '''
        wait_transition = PetriNet.Transition(WAIT_TRANSITION, WAIT_TRANSITION)
        for place in self.__pn.places:
            if len(place.out_arcs) == 0:
                arcIn = PetriNet.Arc(place, wait_transition)
                arcOut = PetriNet.Arc(wait_transition, place)
                self.__pn.arcs.add(arcIn)
                self.__pn.arcs.add(arcOut)
                wait_transition.in_arcs.add(arcIn)
                wait_transition.out_arcs.add(arcOut)
                place.out_arcs.add(arcIn)
                place.in_arcs.add(arcOut)
        self.__pn.transitions.add(wait_transition)
        return wait_transition


    def setOptimizeSup(self,bool):
        self.__optimizeMin=bool

    def setSize_of_run(self,size):
        '''
        Sets the maximal size of the run
        :param size (int)
        '''
        self.__size_of_run=size

    def getSize_of_run(self):
        '''
        Gets the maximal size of the run
        :return (int)
        '''
        return self.__size_of_run

    def getMax_d(self):
        '''
        Gets the maximal distance computed, for Edit Distance only
        :return (int)
        '''
        return self.__max_d

    def setMax_d(self,max_d):
        '''
        Sets the maximal distance
        :param max_d:
        '''
        self.__max_d=max_d

    def setDistance_type(self,distance):
        self.__distance_type=distance

    def getDistance_type(self):
        return self.__distance_type

    def setMax_nbTraces(self,nb):
        self.__max_nbTraces=nb

    def setSilentLabel(self,label):
        self.__silent_label=label

    def getSilentLabel(self):
        return self.__silent_label

    def setSize_of_runAndMax_d(self,size,max_d):
        self.__size_of_run=size
        self.__max_d=max_d

    def getForumulaTime(self):
        return self.__formula_time-self.__start_time

    def getTotalTime(self):
        return self.__total_time-self.__start_time

    def getSizeOfLog(self):
        return len(self.__traces)


def getPrecision(net, m0,mf, log, epsilon):
    size_of_run=2
    end_loop = -1
    computeAntiAlignment=ConformanceArtefacts()
    while (size_of_run > end_loop ):
        size_of_run+=1
        computeAntiAlignment.setSize_of_run(size_of_run)
        computeAntiAlignment.setMax_d(size_of_run*2)
        computeAntiAlignment.antiAlignment(net,m0,mf,log)
        aa = computeAntiAlignment.getRun()
        print(aa)
        while 'w' in aa:
            aa.remove('w')
        m = (computeAntiAlignment.getMinDistanceToRun()/(len(aa)+7)) / (1+epsilon)**(len(aa))
        print(m)
        if m > 0 :
            end_loop = math.floor(math.log((1+epsilon)**(len(aa)))/math.log((1+epsilon)))
        else :
            end_loop = m
        print(size_of_run,computeAntiAlignment.getMinDistanceToRun(), "|", m,end_loop )

    print(computeAntiAlignment.getRun())
