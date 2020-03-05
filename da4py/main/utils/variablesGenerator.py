#!/usr/bin/env python
# -*- coding:utf-8 -*-
##
## variablesGenerator.py
##
##  Created on: September, 2019
##      Author: Boltenhagen Mathilde
##      E-mail: boltenhagen lsv . fr
##

'''

This file allows one to get an iterator and dictionary of boolean variables for SAT problems

-- Example of need :

cnf_formula=[]
for i in range (0,12):
    cnf_formula.append( [delta_i, lambda_i+1] )
    for j in range (0,2):
        cnf_formula.append([-sigma_ij])

Then one needs 12 detla_i variables with i in {0..11}, 12 lambda_i variables with i in {1..12} and 24 sigma_ij variables
with i in {0..11} and j in {0,1}. The VariablesGenerator class allows this.

variables = VariablesGenerator()
variables.add("delta",[(0,12)])
variables.add("lambda",[(1,13)])
variables.add("sigma",[(0,12),(0,2)])

To get delta_2 :
variables.getVarNumber("delta",[2])
> 3

To get sigma_5_1:
variables.getVarNumber("sigma",[5,1])
> 36

To know which variable is a number :
variables.getVarName(14)
> "lambda [ 3 ]"

To easly use the dictionnary of variables:
delta_i = variables.getfunction("delta")
delta_i([1])
> 0

'''


class VariablesGenerator:
    '''
    VariablesGenerator class creates an integer per variable with functions.
    Example : if one needs 5 "m" variables m1, m2, m3, m4, m5 then this class creates 1 2 3 4 5
    '''

    class Variable(object):
        '''
        A variable object is a set of boolean variables that share the same name.
        '''

        def __init__(self, function, min, max, listOfBoundaries):
            '''
            Each variable of the dictionary has :
            :param function: that takes as input a list of int and returns an int
            :param min: the minimal int that can return the function
            :param max: the maximal int that can return the function
            :param listOfBoundaries: the bounds of the variable (for example d_ij for i in {2..5} and j in {0..14},
            listOfBoundaries = [(2,6),(0,15)]
            '''
            self.function = function
            self.min = min
            self.max = max
            self.listOfBoundaries = listOfBoundaries

    def __init__(self):
        # set of variables
        self.set = {}
        # variables start at 1
        self.iterator = 1

    def add(self, name, listOfCouples):
        '''
        Add a set of boolean variables in the dictionary
        :param name (string) : name of the variables
        :param listOfCouples (int, int) : bounds of the variables
        :return (void) create a key "name" with a Variable object

        For example :
        > test=variablesGenerator()
        > test.add("m",[(0,4),(0,5),(0,8)])
        This creates 4*5*8 m variables.
        '''
        base = self.iterator

        def newfunction(listOfElements):
            '''
            Definition of Variable.function
            Every variable has a pre-defined function that returns an int from a list of indexes
            :param listOfElements (indexes) : in the previous example it could be [2,3,4]
            :return the value of the variables with those indexes (int)
            '''
            result = base
            # for each index
            for i in range(0, len(listOfElements)):
                # we get the initialisation of this index
                auxResult = (listOfElements[i] - listOfCouples[i][0])
                # for next index
                for c in range(i + 1, len(listOfCouples)):
                    # we get the couple
                    couple = listOfCouples[c]
                    auxResult *= (couple[1] - couple[0] - 1) + 1
                result += auxResult
            return result

        # creates the variable with its name, function, min, max, and boundaries
        self.set[name] = self.Variable(newfunction, self.iterator, -1, listOfCouples)
        self.iterator = self.set[name].function([(couple[1] - 1) for couple in listOfCouples]) + 1
        self.set[name].max = self.iterator

    def get(self, name, listOfElements):
        '''
        Returns int of the requested variable
        Example of use :
        > variables.getVarNumber("m",[0,4,2]) # to get m_0,4,2

        :param name (string): variable's name
        :param listOfElements (string): requested indexes
        :return (int): variable number
        '''
        return self.set[name].function(listOfElements)

    def getFunction(self, name):
        '''
        :param name (string) : name of the variable
        :return function of the variable
        '''
        return self.set[name].function

    def getMin(self, name):
        '''
        :param name (string) : name of the variable
        :return min int that can returns the function of this variable
        '''
        return self.set[name].min

    def getMax(self, name):
        '''
        :param name (string) : name of the variable
        :return max int that can returns the function of this variable
        '''
        return self.set[name].max

    def getVarName(self, number):
        '''
        Using for debugage
        :param number : int of a variable
        :return (string) name and indexes of this integer
        '''
        number -= 0
        for key in self.set:
            if number >= self.set[key].min and number < self.set[key].max:
                number -= self.set[key].min
                list_of_indexes = []
                for i in range(0, len(self.set[key].listOfBoundaries) - 1):
                    div = 1
                    for j in range(i + 1, len(self.set[key].listOfBoundaries)):
                        div *= (self.set[key].listOfBoundaries[j][1] - self.set[key].listOfBoundaries[j][0])
                    list_of_indexes.append(str(number // div + self.set[key].listOfBoundaries[i][0]))
                    number = number % div
                return key + " [" + ', '.join(list_of_indexes) + ", " + str(number+self.set[key].listOfBoundaries[-1][0]) + "]"

    def getAll(self,name):
        '''
        Get list of all variables of a name
        :param name (String)
        :return:  (list)
        '''
        return list(range (self.set[name].min,self.set[name].max))