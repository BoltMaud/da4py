"""

"""
from abc import ABCMeta, abstractmethod
import warnings

class cnf_formula:
    def __init__(self, nbVars, listOfClauses):
        self.nbVars=nbVars
        self.listOfClauses=listOfClauses

    def cnfToDIMACS(self,file):
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
        PB_list=[]
        for (pos, neg) in self.listOfClauses:
            PB_geq([(1,p) for p in pos]+ [(-1,n) for n in neg],1-len(neg))
            #todo


class qbf_formula:
    __metaclass__ = metaclass=ABCMeta

    @abstractmethod
    def simplify(self):
        pass

    @abstractmethod
    def negation(self):
        pass

class NoQuantification(Exception):
    def __str__(self):
       return repr("No quantification allowed for this method")

class operator(qbf_formula):
    def __init__(self, type, positiveVariables, negatieVariables, qbf_formulas):
        self.type = type
        self.positiveVariables = positiveVariables
        self.negativeVariabes = negatieVariables
        self.qbf_formulas = qbf_formulas

    def simplify(self):
        if len(self.positiveVariables) == 0 and len(self.negativeVariabes)==0 and len(self.qbf_formulas)==1:
            return self.qbf_formulas[0].simplify()

    def simplify(self):
        super()
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

    def distributeImplication(self,var):
        raise NoQuantification

    def clausesToCnf(self,nbVars):
        raise NoQuantification

class And(operator):
    def __init__(self, positiveVariables, negatieVariables, qbf_formulas):
        self.type = "&&"
        self.positiveVariables = positiveVariables
        self.negativeVariabes = negatieVariables
        self.qbf_formulas = qbf_formulas

    def distributeImplication(self,var):
        self.positiveVariables = [Or(positiveVariable,[var],[]) for positiveVariable in self.positiveVariables]
        self.negativeVariabes = [Or([],[negativeVariable,var],[]) for negativeVariable in self.negativeVariabes]
        self.qbf_formulas = [Or([],[var],[formula]) for formula in self.qbf_formulas]

    def clausesToCnf(self,nbVars):
        dnfPositiveVariables = [([v],[]) for v in self.positiveVariables]
        dnfNegativeVariables = [([],[v]) for v in self.negativeVariabes]
        left = [ formula.clausesToCnf(nbVars) for formula in self.qbf_formulas]
        return cnf_formula(nbVars,dnfPositiveVariables + dnfNegativeVariables + left)


class Or(operator):
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
            return cnf_formula(nbVars+len(self.qbf_formulas),And([],[],implications).clausesToCnf(nbVars).append(dnf))

class pb_constraint :
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

class pb_formula:
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



class PB_leq(pb_constraint):
    def __init__(self,weightedVariables,threshold):
        self.type="<="
        self.weightedVariables=weightedVariables
        self.threshold=threshold

class PB_geq(pb_constraint):
    def __init__(self,weightedVariables,threshold):
        self.type=">="
        self.weightedVariables=weightedVariables
        self.threshold=threshold

class PB_eq(pb_constraint):
    def __init__(self,weightedVariables,threshold):
        self.type="="
        self.weightedVariables=weightedVariables
        self.threshold=threshold

class pb_objective:
    def __init__(self,weightedVariables):
        self.weightedVariables=weightedVariables







