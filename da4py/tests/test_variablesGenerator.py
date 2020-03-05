from unittest import TestCase

from da4py.main.utils import variablesGenerator as vg

class TestVariablesGenerator(TestCase):
    '''
    This class aims at testing the variablesGenerator.py file
    '''
    vars=vg.VariablesGenerator()
    vars.add("a_ij",[(0,1),(3,6)])
    vars.add("b_ijk",[(2,5),(3,6),(0,1)])

    def test_add(self):
        '''
        Test if variables have been well added
        '''
        assert type(self.vars.set["a_ij"]) == vg.VariablesGenerator.Variable

    def test_get(self):
        '''
        Test if we get the right number of the variables
        '''
        number=1
        for i in range (0,1):
            for j in range (3,6):
                assert self.vars.get("a_ij",[i,j])==number
                number+=1
        for i in range (2,5):
            for j in range (3,6):
                for k in range (0,1):
                    assert self.vars.get("b_ijk",[i,j,k])==number
                    number+=1

    def test_getFunction(self):
        '''
        Test if we get the good function of a boolean variable
        '''
        functionToTest = self.vars.getFunction("a_ij")
        number=1
        for i in range (0,1):
            for j in range (3,6):
                assert functionToTest([i,j])==number
                number+=1
        functionToTest = self.vars.getFunction("b_ijk")
        for i in range (2,5):
            for j in range (3,6):
                for k in range (0,1):
                    assert functionToTest([i,j,k])==number
                    number+=1

    def test_getMin(self):
        '''
        Test if we get the good min of a variable
        '''
        assert self.vars.getMin("a_ij")==1
        assert self.vars.getMin("b_ijk")==4

    def test_getMax(self):
        '''
        Test if we get the good max of a variable
        '''
        assert self.vars.getMax("a_ij")==4
        assert self.vars.getMax("b_ijk")==13

    def test_getVarName(self):
        '''
        Test if get the right string output for debug
        '''
        assert self.vars.getVarName(2)=="a_ij [0, 4]"
        assert self.vars.getVarName(10)=="b_ijk [4, 3, 0]"

    def test_getAll(self):
        '''
        Test if getAll gives the list of variables of a boolean variable
        '''
        assert self.vars.getAll("b_ijk")==[4,5,6,7,8,9,10,11,12]
