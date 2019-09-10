
from abc import ABCMeta, abstractmethod

class Cnf_formula:
    '''
    Conjunctive normal form formulas
    @:param nbVars (int) : number of variables
    @:param listOfClauses [([pos1, pos2 ...],[neg1, neg2..]), ([pos1, pos2 ...],[neg1, neg2..])] (list of couples of list) :
    list of clauses, each clause is a couple of two lists of variables : positive and negative
    '''
    def __init__(self, nbVars, listOfClauses):
        self.nbVars=nbVars
        self.listOfClauses=listOfClauses

    def cnfToDIMACS(self,file):
        '''
        write the clauses in a dimacs file
        :param file (string) : name
        :return (void)
        '''
        writer=open(file,"w")
        writer.write("p cnf "+self.nbVars+ " "+len(self.listOfClauses)+"\n")
        for (pos, neg ) in self.listOfClauses:
            for p in pos :
                writer.write(p +" ")
            for n in neg :
                writer.write(n*(-1)+ " ")
            writer.write(0+"\n")
        writer.close()

    def cnfToPb(self):
        '''
        Pb formulas have weights
        :return PB_list (list of >= formulas)
        '''
        PB_list=[]
        for (pos, neg) in self.listOfClauses:
            # weight = 1 if positive, weight = - 1 if negative and sum is greater of equal to 1-negatives
            PB_list.append(PB_geq([(1,p) for p in pos]+ [(-1,n) for n in neg],1-len(neg)))
        return  PB_list


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
    def __init__(self, type, positiveVariables, negatieVariables, qbf_formulas):
        '''
        :param type (string) : "&&" or "||"
        :param positiveVariables (list of int)
        :param negatieVariables (list of int)
        :param qbf_formulas (list of QBF)
        '''
        self.type = type
        self.positiveVariables = positiveVariables
        self.negativeVariabes = negatieVariables
        self.qbf_formulas = qbf_formulas

    def simplify(self):
        '''
        :return: QBF_formulas (only Operator)
        '''
        if len(self.positiveVariables) == 0 and len(self.negativeVariabes)==0 and len(self.qbf_formulas)==1:
            return self.qbf_formulas[0].simplify()
        newQbflist = [qbf.simplify() for qbf in self.qbf_formulas]
        if len(self.qbf_formulas) == 1 and self.qbf_formulas[0].type == "&&":
            self.positiveVariables = self.qbf_formulas[0].positiveVariables + self.positiveVariables
            self.negativeVariabes = self.qbf_formulas[0].negativeVariables + self.negativeVariabes
        if self.type=="&&":
            return And(self.positiveVariables, self.negativeVariabes, newQbflist).simplify()
        if self.type=="||":
            return Or(self.positiveVariables, self.negativeVariabes, newQbflist).simplify()

    def negation(self):
        newQbflist = [qbf.negation() for qbf in self.qbf_formulas]
        if self.type=="&&":
            return Or(self.negativeVariabes,self.positiveVariables,newQbflist)
        if self.type=="||":
            return And(self.negativeVariabes,self.positiveVariables,newQbflist)

    @abstractmethod
    def distributeImplication(self,var):
        pass

    @abstractmethod
    def clausesToCnf(self,nbVars):
        pass

class And(Operator):
    def __init__(self, positiveVariables, negatieVariables, qbf_formulas):
        self.type = "&&"
        self.positiveVariables = positiveVariables
        self.negativeVariabes = negatieVariables
        self.qbf_formulas = qbf_formulas

    def distributeImplication(self,var):
        self.qbf_formulas = [Or(positiveVariable,[var],[]) for positiveVariable in self.positiveVariables]+ \
                            [Or([],[negativeVariable,var],[]) for negativeVariable in self.negativeVariabes]+\
                            [Or([],[var],[formula]) for formula in self.qbf_formulas]
        self.positiveVariables = []
        self.negativeVariabes = []

    def clausesToCnf(self,nbVars):
        dnfPositiveVariables = [([v],[]) for v in self.positiveVariables]
        dnfNegativeVariables = [([],[v]) for v in self.negativeVariabes]
        left = [ formula.clausesToCnf(nbVars) for formula in self.qbf_formulas]
        return Cnf_formula(nbVars,dnfPositiveVariables + dnfNegativeVariables + left)


class Or(Operator):
    def __init__(self, positiveVariables, negatieVariables, qbf_formulas):
        self.type = "||"
        self.positiveVariables = positiveVariables
        self.negativeVariabes = negatieVariables
        self.qbf_formulas = qbf_formulas

    def distributeImplication(self,var):
        self.negativeVariabes.append(var)

    def clausesToCnf(self,nbVars):
        if len(self.qbf_formulas)==1 and self.qbf_formulas[0].type == "||":
            return Or(self.positiveVariables,self.negativeVariabes,self.qbf_formulas[0]).clausesToCnf(nbVars)
        else:
            dnf = (self.positiveVariables+ [i for i in range (nbVars+1, len(self.qbf_fomulas))] , self.negativeVariabes)
            implications=[]
            for i in range (1,len(self.qbf_formulas)+1):
                implications.append(self.qbf_formulas[i].distributeImplication(nbVars+1+i))
            return Cnf_formula(nbVars+len(self.qbf_formulas),And([],[],implications).clausesToCnf(nbVars).append(dnf))

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







