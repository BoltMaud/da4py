from pm4py.objects.log.util.log import project_traces
from pm4py.objects.petri.petrinet import PetriNet, Marking
from pm4py.objects.petri.utils import add_arc_from_to
from pm4py.visualization.petrinet import factory as vizu


def log_to_Pn(traces_xes,size_of_run):
    traces = project_traces(traces_xes)
    petri_of_traces=PetriNet()
    init, end=PetriNet.Place("init"),PetriNet.Place("end")
    [petri_of_traces.places.add(place) for place in [init, end]]
    prec=init
    for t in traces:
        prec=init
        for a in range (0,min(size_of_run,len(t))):
            transition=PetriNet.Transition(t[a]+str(a), t[a])
            petri_of_traces.transitions.add(transition)
            place_suiv=end if a in [size_of_run-1,len(t)-1]  else PetriNet.Place(t[a]+str(a))
            add_arc_from_to(transition, place_suiv, petri_of_traces)
            add_arc_from_to(prec, transition, petri_of_traces)
            prec=place_suiv
    m0=Marking().__add__({init:1})
    mf=Marking().__add__({end:1})
    return petri_of_traces,m0,mf