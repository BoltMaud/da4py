
import re

class Place :
    def __init__(self,id):
        self.id = id

class Transition :
    def __init__(self,label,prePlaces,postPlaces):
        self.label=label
        self.prePlaces=prePlaces
        self.postPlaces=postPlaces

class Petri_net_for_PM:
    def __init__(self, placesList=[], transitionsList=[], m0=[], mf=[]):
        self.placesList=placesList
        self.transitionsList=transitionsList
        self.m0=m0
        self.mf=mf #TODO

    def add_ww(self):
        self.transitionsList.append(Transition("ww",[],[]))

    #TODO final marking
    def fromFile(self,file):
        reader=open(file,"r")
        for line in reader :
            if line.startswith("place"):
                place=Place(re.sub("[^0-9]", line.split(" ")[1]))
                self.placesList.append(place)
                if line.split(" ").length > 2:
                    self.m0.append(place)
            if line.startswith("transition"):
                label = line.split(" ")[1]
                prePlaces = [Place(id) for id in line.split("in")[1].split("out")[0].split(" ")]
                postPlaces =[Place(id) for id in line.split("out")[1].split(" ")]
                self.transitionsList.append(Transition(label,prePlaces,postPlaces))
            else :
                raise Exception






