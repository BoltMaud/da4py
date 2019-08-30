from darksider4py import petrinet as pn

class NetSystem(pn.PetriNet):
    def __init__(self):
        super()
        self.initialMarking=[]
        self.finalMarking=[]

    def NetSystemFromPNML(self,filename):
        result=pn.parse_pnml_file(filename)[0]
        self.transitions=result.transitions
        self.places=result.places
        self.id=result.id
        self.edges=result.edges
        for (id,place) in self.places.items() :
            if place.marking==1:
                self.initialMarking.append(place.id)
        self.getFinalMarking()

    def getFinalMarking(self):
        allPrePlaces=[]
        for (id,transition) in self.transitions.items():
            for p in transition.prePlaces :
                if p.id not in allPrePlaces:
                    allPrePlaces.append(p.id)
        checkedTransitions=[]
        for (id,transition) in self.transitions.items():
            for p in transition.postPlaces:
                if p.id not in allPrePlaces and transition.id not in checkedTransitions:
                    self.finalMarking.append(p.id)
                checkedTransitions.append(transition.id)




sys = NetSystem()
sys.NetSystemFromPNML("../examples/example.pnml")






