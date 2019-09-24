from pysat.examples.rc2 import RC2
from pysat.solvers import Solver

class MinSATOverRC2:

    def __init__(self,wcnf=None,solver='g3'):
        self.solver=Solver(name=solver)
        self.factory=RC2(wcnf)

    def getSolutionForMinimalCost(self):
        cost=None
        optimalModel=None
        for model in self.factory.enumerate():
            if cost==None or self.factory.cost<cost:
                cost=self.factory.cost
                optimalModel=self.factory.model
        return model

    def getSolutionForMaximalCost(self):
        cost=None
        optimalModel=None
        for model in self.factory.enumerate():
            print("whut")
            if self.factory.cost!= 0:
                print(self.factory.cost)
            if cost==None or self.factory.cost>cost:
                cost=self.factory.cost
                optimalModel=self.factory.model
        return model