class Place :
    def __init__(self,id):
        self.id = id

class Transition :
    def __init__(self,label,prePlaces,postPlaces):
        self.label=label
        self.prePlaces=prePlaces
        self.postPlaces=postPlaces

class Petri_net:
    def __init__(self, placesList, transitionsList, m0=None, mf=None):
        self.placesList=placesList
        self.transitionsList=transitionsList
        self.m0=m0
        self.mf=mf

    def add_ww(self):
        self.transitionsList.append(Transition("ww",[],[]))
        




