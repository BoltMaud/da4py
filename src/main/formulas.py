
from abc import ABCMeta, abstractmethod

NB_VARS=0

class Qbf_formula:
    '''
    abstract class
    Quantified boolean formulas
    '''
    __metaclass__ = metaclass=ABCMeta

    @abstractmethod
    def simplify(self):
        pass

    @abstractmethod
    def negation(self):
        pass

class Operator(Qbf_formula):
    '''
    && and || formulas
    '''
    def __init__(self, type, positiveVariables, negativeVariables, qbf_formulas):
        '''
        :param type (string) : "&&" or "||"
        :param positiveVariables (list of int)
        :param negatieVariables (list of int)
        :param qbf_formulas (list of QBF)
        '''
        self.type = type
        self.positiveVariables = positiveVariables
        self.negativeVariables = negativeVariables
        self.qbf_formulas = qbf_formulas

    def simplify(self):
        '''
        :return: QBF_formulas (only Operator)
        '''
        if len(self.qbf_formulas)==0 :
            return self
        if len(self.qbf_formulas)==1 and len(self.positiveVariables) == 0 and len(self.negativeVariables)==0:
            formula = self.qbf_formulas[0].simplify()
            return formula

        newQbflist = []
        for qbf in self.qbf_formulas:
            if qbf.type==self.type:
                self.negativeVariables+=qbf.negativeVariables
                self.positiveVariables+=qbf.positiveVariables
                newQbflist+=qbf.qbf_formulas
            else :
                newQbflist.append(qbf)
        simplifiedQbflist=[]
        for qbf in newQbflist:
            formula=qbf.simplify()
            simplifiedQbflist.append(formula)
        if self.type=="AND":
            formula=And(self.positiveVariables, self.negativeVariables, simplifiedQbflist)
            return formula
        if self.type=="OR":
            formula= Or(self.positiveVariables, self.negativeVariables, simplifiedQbflist)
            return formula

    def negation(self):
        newQbflist = [qbf.negation() for qbf in self.qbf_formulas]
        if self.type=="AND":
            return Or(self.negativeVariables,self.positiveVariables,newQbflist)
        if self.type=="OR":
            return And(self.negativeVariables,self.positiveVariables,newQbflist)

    @abstractmethod
    def distributeImplication(self,var):
        pass

    def clausesToCnf(self,nbVars):
        global NB_VARS
        NB_VARS=nbVars
        return self.aux_clausesToCnf()

    @abstractmethod
    def aux_clausesToCnf(self):
        pass

    def __repr__(self, variablesGenerator=None,time=0):
        if variablesGenerator ==None:
            return self.type + str(self.positiveVariables) + str(self.negativeVariables) + str(self.qbf_formulas)
        str_of_formulas=[ '\n' + q.__repr__(variablesGenerator, time+1) for q in self.qbf_formulas]
        str_of_positivesVariables = [variablesGenerator.getVarName(n) if variablesGenerator.getVarName(n) is not None else n for n in self.positiveVariables]
        str_of_negativeVariables = [variablesGenerator.getVarName(n) if variablesGenerator.getVarName(n) is not None else n for n in self.negativeVariables]
        return "\t"*time + self.type + "( ["\
               + ', '.join(str_of_positivesVariables) +"], ["\
               + ', '.join(str_of_negativeVariables)+"], "\
               + ' '.join(str_of_formulas) +")"

class And(Operator):
    def __init__(self, positiveVariables, negativeVariables, qbf_formulas):
        self.type = "AND"
        self.positiveVariables = positiveVariables
        self.negativeVariables = negativeVariables
        self.qbf_formulas = qbf_formulas

    def distributeImplication(self,var):
        temp = [Or([positiveVariable],[var],[]) for positiveVariable in self.positiveVariables]+ \
               [Or([],[negativeVariable,var],[]) for negativeVariable in self.negativeVariables]+\
               [Or([],[var],[formula]) for formula in self.qbf_formulas]
        self.qbf_formulas=temp
        self.positiveVariables = []
        self.negativeVariables = []

    def aux_clausesToCnf(self):
        dnfPositiveVariables =[]
        dnfNegativeVariables=[]
        for v in self.positiveVariables:
            dnfPositiveVariables.append([v])
        for v in self.negativeVariables:
            dnfNegativeVariables.append([v*-1])
        left = []
        for formula in self.qbf_formulas:
            cnf=formula.aux_clausesToCnf()
            left+= cnf
        return dnfPositiveVariables + dnfNegativeVariables + left


class Or(Operator):
    def __init__(self, positiveVariables, negativeVariables, qbf_formulas):
        self.type = "OR"
        self.positiveVariables = positiveVariables
        self.negativeVariables = negativeVariables
        self.qbf_formulas = qbf_formulas

    def getpositiveVariables(self):
        return self.positiveVariables

    def getnegativeVariables(self):
        return self.negativeVariables

    def distributeImplication(self,var):
        self.negativeVariables.append(var)

    def aux_clausesToCnf(self):
        if len(self.qbf_formulas)==1 and self.qbf_formulas[0].type == "OR" and len(self.qbf_formulas[0].getpositiveVariables())==0\
                and len(self.qbf_formulas[0].getnegativeVariables())==0:
           clauses = Or(self.positiveVariables,self.negativeVariables,self.qbf_formulas[0].qbf_formulas).aux_clausesToCnf()
           return  clauses
        else:
            global NB_VARS
            newVariables = []
            for numVariable in range (NB_VARS, NB_VARS+len(self.qbf_formulas)):
                newVariables.append(numVariable)
            dnf = self.positiveVariables+ newVariables + [v*-1 for v in self.negativeVariables]
            for i in range (0,len(self.qbf_formulas)):
                # distribute implication
                if self.qbf_formulas[i].type=="OR":
                    self.qbf_formulas[i].negativeVariables=self.qbf_formulas[i].negativeVariables+[NB_VARS+i]
                else :
                    var=NB_VARS+i
                    newListOfFormulas=[]
                    for positiveVariable in self.qbf_formulas[i].positiveVariables:
                        newListOfFormulas.append(Or([positiveVariable],[var],[]))
                    for negativeVariable in self.qbf_formulas[i].negativeVariables:
                        newListOfFormulas.append(Or([],[negativeVariable,var],[]))
                    for formula in self.qbf_formulas[i].qbf_formulas:
                        newListOfFormulas.append(Or([],[var],[formula]))
                    self.qbf_formulas[i].qbf_formulas=newListOfFormulas
                    self.qbf_formulas[i].negativeVariables=[]
                    self.qbf_formulas[i].positiveVariables=[]
            NB_VARS+=len(self.qbf_formulas)
            if len(self.qbf_formulas)==0:
                return [dnf]
            else :
                clauses = And([],[],self.qbf_formulas).aux_clausesToCnf()
                clauses.append(dnf)
                return clauses

class Pb_constraint :
    def __init__(self,type,weightedVariables,threshold):
        self.type=type
        self.weightedVariables=weightedVariables
        self.threshold=threshold
        self.nbVariables= len(weightedVariables)

    def __str__(self):
        result=""
        for ( weight, variable ) in self.weightedVariables:
            result+=weight +" x"+ variable+" ";
        result+=self.type + " " +self.threshold+"\n"
        return result

class Pb_formula:
    def __init__(self,listOfContraints,nbVars,pbObjective=[]):
        self.listOfConstraints=listOfContraints
        self.pbObjective= pbObjective
        self.nbVariables=nbVars

    def pbformulaToOpb(self,file,pbSolver):
        if pbSolver in ["sat4j"]:
            self.nbVariables+=1
        writer=open(file,"w")
        writer.write("* #variable= "+self.nbVariables+ " #constraint= "+len(self.listOfConstraints)+"\n")
        writer.write("min: ")
        for ( weight, variable ) in self.pbObjective:
            writer.write(weight +" x"+ variable+" ")
        for constraint in self.listOfConstraints:
            writer.write(constraint.toString())
        writer.close()

class PB_leq(Pb_constraint):
    def __init__(self,weightedVariables,threshold):
        self.type="<="
        self.weightedVariables=weightedVariables
        self.threshold=threshold

class PB_geq(Pb_constraint):
    def __init__(self,weightedVariables,threshold):
        self.type=">="
        self.weightedVariables=weightedVariables
        self.threshold=threshold

class PB_eq(Pb_constraint):
    def __init__(self,weightedVariables,threshold):
        self.type="="
        self.weightedVariables=weightedVariables
        self.threshold=threshold

class Pb_objective:
    def __init__(self,weightedVariables):
        self.weightedVariables=weightedVariables







