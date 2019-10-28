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
import itertools
import time

from pm4py.objects.petri.petrinet import PetriNet
from pysat.examples.rc2 import RC2
from pysat.formula import WCNF

from da4py.main.distancesToFormulas import hamming_distance_per_trace_to_SAT, edit_distance_per_trace_to_SAT
from da4py.main.formulas import And, Or
from da4py.main.logToFormulas import log_to_SAT
from da4py.main.pnToFormulas import petri_net_to_SAT
from da4py.main import variablesGenerator as vg

# a wait transition is added to complete words, :see __add_wait_net()
WAIT_TRANSITION = "w"
SILENT_LABEL=None

# our boolean formulas depends on variables, see our paper for more information
BOOLEAN_VAR_MARKING_PN = "m_ip"
BOOLEAN_VAR_FIRING_TRANSITION_PN = "tau_it"
BOOLEAN_VAR_TRACES_ACTIONS = "lambda_jia"
BOOLEAN_VAR_EDIT_DISTANCE = "djiid"
BOOLEAN_VAR_HAMMING_DISTANCE="djd"
BOOLEAN_VAR_SUP = "supd"
BOOLEAN_VAR_SUP_AUX = "supjd"

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

    def __init__(self, distance=EDIT_DISTANCE, solver="g4"):
        '''
        Conformance artefact share some initialisation
        :param distance (string) : value = HAMMING_DISTANCE or EDIT_DISTANCE
        :param solver: one of the SAT solver of the librairy pysat
        '''
        self.__distance_type = distance
        self.__solver = solver
        self.__silent_label=SILENT_LABEL
        self.__max_nbTraces=None
        self.__optimizeSup=True

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
        self.__net = net
        # transforms the model and the log to SAT formulas
        initialisationFormulas, self.__wait_transition = self.__artefactsInitialisation(m0, mf, traces)

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
        self.__net = net
        # transforms the model and the log to SAT formulas
        initialisationFormulas, self.__wait_transition = self.__artefactsInitialisation(m0, mf, traces)

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
        initialisationFormulas, self.__wait_transition = self.__artefactsInitialisation(m0, mf, traces)
        distanceFormula = self.__compute_distance(EXACT_ALIGNMENT, self.__wait_transition)
        wncf = self.__createWncf(initialisationFormulas, distanceFormula, EXACT_ALIGNMENT)
        self.__solveWncf(wncf)
        return 0

    def __artefactsInitialisation(self, m0, mf, traces):
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
        # this variable (__variables) memorises the numbers of the boolean variables of the formula
        self.__variables = vg.VariablesGenerator()

        # we add a "wait" transition to complete the words
        self.__wait_transition = self.__add_wait_net()

        self.__start_time = time.time()
        # the model is translated to a formula
        pn_formula, places, self.__transitions, self.__silent_transitions = petri_net_to_SAT(self.__net, m0, mf, self.__variables,
                                                                  self.__size_of_run,
                                                                  label_m=BOOLEAN_VAR_MARKING_PN,
                                                                  label_t=BOOLEAN_VAR_FIRING_TRANSITION_PN,
                                                                   silent_transition=self.__silent_label)
        # the log is translated to a formula
        log_formula, traces = log_to_SAT(traces, self.__transitions, self.__variables, self.__size_of_run,
                                         self.__wait_transition,max_nbTraces=self.__max_nbTraces)
        self.__traces = traces
        return [pn_formula, log_formula], self.__wait_transition

    def __compute_distance(self, artefact, wait_transition):
        '''
        :param artefact: EXACT_ALIGNMENT or MULTI_ALIGNMENT or ANTI_ALIGNMENT, see globale variables
        :param wait_transition: see add_wait_transition
        :return: formulas of the distance
        '''
        if self.__distance_type == HAMMING_DISTANCE:
            return hamming_distance_per_trace_to_SAT(artefact, self.__transitions, self.__silent_transitions, self.__variables, len(self.__traces),
                                                     self.__size_of_run)
        elif self.__distance_type == EDIT_DISTANCE:
            return edit_distance_per_trace_to_SAT(artefact, self.__transitions, self.__silent_transitions, self.__variables, len(self.__traces),
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
        formulas = initialisationFormulas + distanceFormula + self.__to_minimize(artefactForMinimization)
        full_formula = And([], [], formulas)
        cnf = full_formula.operatorToCnf(self.__variables.iterator)
        wcnf = WCNF()
        wcnf.extend(cnf)
        wcnf = self.__createWeights(wcnf,artefactForMinimization)
        self.__formula_time = time.time()
        return wcnf

    def __createWeights(self,wcnf,artefactForMinimization):
        '''
        Add weights on variables. Depend on OptimizeSup and distance_type. If optimizeSup is true, then we do real anti
        alignment, otherwise we do MAX.
        :param wcnf: formula
        :param artefactForMinimization (string)
        :return:
        '''
        # weights of variables depends on artefact
        weightsOnVariables = -1 if artefactForMinimization != ANTI_ALIGNMENT else 1

        # real anti/multi
        if self.__optimizeSup==True :
            for d in range(0, self.__max_d ):
                wcnf.append([weightsOnVariables * self.__variables.getVarNumber(BOOLEAN_VAR_SUP,[d])],WEIGHT_ON_CLAUSES_TO_REDUCE)

        # MAX
        else :
            if self.__distance_type == EDIT_DISTANCE:
                for j in range(0, len(self.__traces)):
                    for d in range(1, self.__max_d + 1):
                        wcnf.append([weightsOnVariables * self.__variables.getVarNumber(BOOLEAN_VAR_EDIT_DISTANCE,
                                                                                       [j, self.__size_of_run,
                                                                                        self.__size_of_run, d])],
                                   WEIGHT_ON_CLAUSES_TO_REDUCE)

            # weighted variables for edit distance are d_j,i
            elif self.__distance_type == HAMMING_DISTANCE:
                for j in range(0, len(self.__traces)):
                    for i in range(1, self.__size_of_run + 1):
                        wcnf.append([weightsOnVariables * self.__variables.getVarNumber(BOOLEAN_VAR_HAMMING_DISTANCE, [j, i])],
                                    WEIGHT_ON_CLAUSES_TO_REDUCE)
        return wcnf

    def setOptimizeSup(self,bool):
        self.__optimizeSup=bool

    def __to_minimize(self,artefact):
        '''
        If we minimize SUP then we need to add some variables. Otherwise no.
        :param artefact:
        :return:
        '''
        # if we do max, then we don't have to add variables for distance
        if self.__optimizeSup==False :
            return []
        else :
            # create new variables SUPD
            self.__variables.add(BOOLEAN_VAR_SUP,[(0,self.__max_d+1)])
            list_of_formula=[]
            if self.__distance_type== EDIT_DISTANCE:
                if artefact == ANTI_ALIGNMENT:
                    for d in range (0, self.__max_d+1):
                        list_of_d=[]
                        for j in range(0, len(self.__traces)):
                            # delta_j1nnd and delta_j2nnd and ... delta_jlnnd
                            list_of_d.append(self.__variables.getVarNumber(BOOLEAN_VAR_EDIT_DISTANCE,[j,self.__size_of_run,self.__size_of_run,d]))
                        # not di or ( dji and dji ... dji)
                        not_di_or_list_of_and=Or([],[self.__variables.getVarNumber(BOOLEAN_VAR_SUP,[d])],[
                            And(list_of_d,[],[])])
                        list_of_formula.append(not_di_or_list_of_and)

                if artefact == MULTI_ALIGNMENT :
                    for d in range (0, self.__max_d + 1):
                        list_of_d=[]
                        for j in range(0, len(self.__traces)):
                            # not delta_j1nnd or not delta_j2nnd or ... not delta_jlnnd
                            list_of_d.append(self.__variables.getVarNumber(BOOLEAN_VAR_HAMMING_DISTANCE,[j,self.__size_of_run,self.__size_of_run,d]))
                        #  di or ( dji or dji ... dji)
                        not_di_or_list_of_and=Or([self.__variables.getVarNumber(BOOLEAN_VAR_SUP,[d])],list_of_d,[])
                        list_of_formula.append(not_di_or_list_of_and)
                return  list_of_formula
            else :
                # on crée les var SUP_AUX
                self.__variables.add(BOOLEAN_VAR_SUP_AUX,[(0,len(self.__traces)),(0,self.__max_d+1)])
                list_to_size_of_run= list(range(1,self.__size_of_run+1))
                not_d_or_and_diff=[]
                for j in range (0, len(self.__traces)):
                    for d in range(1,min(self.__max_d + 1,self.__size_of_run+1)):
                        combinaisons_of_instants=list(itertools.combinations(list_to_size_of_run,d))
                        and_sub_instants=[]
                        for sub_list_of_instants in combinaisons_of_instants:
                            instants_to_combine=[]
                            for instant in list(sub_list_of_instants):
                                instants_to_combine.append(self.__variables.getVarNumber(BOOLEAN_VAR_HAMMING_DISTANCE,[j,instant]))
                            and_sub_instants.append(And(instants_to_combine,[],[]))
                        not_d_or_and_diff.append(Or([],[self.__variables.getVarNumber(BOOLEAN_VAR_SUP_AUX,[j,d])],and_sub_instants))
                list_of_formula.append(And([],[],not_d_or_and_diff))

                for d in range (0, min(self.__max_d + 1,self.__size_of_run+1)):
                    list_of_d=[]
                    for j in range(0, len(self.__traces)):
                        # delta_j1nnd and delta_j2nnd and ... delta_jlnnd
                        list_of_d.append(self.__variables.getVarNumber(BOOLEAN_VAR_SUP_AUX,[j,d]))
                    # not di or ( dji and dji ... dji)
                    not_di_or_list_of_and=Or([],[self.__variables.getVarNumber(BOOLEAN_VAR_SUP,[d])],[
                                                And(list_of_d,[],[])])
                    list_of_formula.append(not_di_or_list_of_and)
                neg_for_hamming=[]
                for d in range (self.__size_of_run+1,self.__max_d + 1):
                    neg_for_hamming.append(self.__variables.getVarNumber(BOOLEAN_VAR_SUP,[d]))
                list_of_formula.append(And([],neg_for_hamming,[]))
                return list_of_formula

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

    def __solveWncf(self, wcnf):
        '''
        This method launches the SAT solver.
        :param wcnf: formulas
        :return:
        '''
        solver = RC2(wcnf, solver=self.__solver)
        solver.compute()
        end_solver = time.time()
        self.__model = solver.model
        self.__total_time=time.time()

    def __add_wait_net(self):
        '''
        Words don't have the same length. To compare them we add a "wait" transition at the end of the model and the
        traces.
        :return:
        '''
        wait_transition = PetriNet.Transition(WAIT_TRANSITION, WAIT_TRANSITION)
        for place in self.__net.places:
            if len(place.out_arcs) == 0:
                arcIn = PetriNet.Arc(place, wait_transition)
                arcOut = PetriNet.Arc(wait_transition, place)
                self.__net.arcs.add(arcIn)
                self.__net.arcs.add(arcOut)
                wait_transition.in_arcs.add(arcIn)
                wait_transition.out_arcs.add(arcOut)
                place.out_arcs.add(arcIn)
                place.in_arcs.add(arcOut)
        self.__net.transitions.add(wait_transition)
        return wait_transition

    def getRun(self):
        '''
        Returns a very simple string version of the multi or anti alignment
        :return (string) : output run
        '''
        try :
            run = "<"
            for var in self.__model:
                if self.__variables.getVarName(var) != None and self.__variables.getVarName(var).startswith(
                        BOOLEAN_VAR_FIRING_TRANSITION_PN):
                    index = self.__variables.getVarName(var).split("]")[0].split(",")[1]
                    i = self.__variables.getVarName(var).split("[")[1].split(",")[0]
                    run += " (" + i + ", " + str(self.__transitions[int(index)]) + ") "

            run += ">"
            return run
        except :
            raise Exception("Cannot get run because model doesn't exist. See if SAT formula returns True.")

    def getTracesWithDistances(self):
        '''
        Returns a very simple string version of the traces with their distance to the run
        :return:
        '''
        traces = ""
        for var in self.__model:
            if self.__variables.getVarName(var) != None and self.__variables.getVarName(var).startswith(
                    BOOLEAN_VAR_TRACES_ACTIONS):
                transition = self.__variables.getVarName(var).split("]")[0].split(",")[2]
                i = self.__variables.getVarName(var).split("[")[1].split(",")[1]
                if int(i) == 1:
                    traces += "\n"
                    lth_trace = self.__variables.getVarName(var).split("[")[1].split(",")[0]
                    max_d_of_l = self.__getMaxDistanceOfTrace(int(lth_trace))
                    traces+=str(lth_trace)+": [d="+str(max_d_of_l)+"]"
                traces += " (" + i + ", " + str(self.__transitions[int(transition)]) + ")"
        return traces

    def __getMaxDistanceOfTrace(self,l):
        '''
        Returns the maximal distance of the trace to the run
        :param l (int) : lth trace
        :return d (int)
        '''
        if self.__distance_type == EDIT_DISTANCE:
            max_d = 0
            for d in range(0, self.__max_d ):
                if self.__variables.getVarNumber(BOOLEAN_VAR_EDIT_DISTANCE,
                                                 [l, self.__size_of_run, self.__size_of_run, d]) in self.__model:
                    max_d = d
        if self.__distance_type == HAMMING_DISTANCE:
            max_d = 0
            for i in range(1, self.__size_of_run + 1):
                if self.__variables.getVarNumber(BOOLEAN_VAR_HAMMING_DISTANCE, [l, i]) in self.__model:
                    max_d += 1
        return max_d

    def getPrecision(self):
        # TODO ONLY FOR EDIT
        max_d=0
        for d in range (self.__max_d,-1,-1):
            if self.__variables.getVarNumber(BOOLEAN_VAR_SUP,[d]) in self.__model:
                max_d=d
                max_in_traces = len(max(self.__traces, key=len))
                max_in_model =  self.getRealSizeOfRun()
                max_len = max(max_in_traces,max_in_model)
                print(max_d)
                return float(1)-float(max_d)/float(max_len)

    def getRealSizeOfRun(self):
        i_wait=self.__transitions.index(self.__wait_transition)
        for i in range(self.__size_of_run,0,-1):
            if self.__variables.getVarNumber(BOOLEAN_VAR_FIRING_TRANSITION_PN,[i,i_wait]) not in self.__model:
                return i