import sys
import os
from da4py.main import formulas
from da4py.main.conformanceArtefacts import ConformanceArtefacts
from pm4py.objects.petri import importer
from pm4py.objects.log.importer.xes import factory as xes_importer
from pm4py.visualization.petrinet import factory as vizu
from pm4py.algo.conformance.alignments.versions import state_equation_a_star

traces="/Users/mboltenhagen/Downloads/Hospital_log.xes.gz"
model="/Users/mboltenhagen/Documents/PhD/Josep&Thomas/markovian-accuracy/artificial-logs-models/fig1.pnml"

log = xes_importer.import_log(traces)
from pm4py.algo.discovery.inductive import factory as inductive_miner
net, im, fm = inductive_miner.apply(log)
vizu.apply(net, im, fm).view()

from pm4py.algo.conformance.alignments import factory as align_factory

alignments = align_factory.apply(log, net, im, fm)

for a in alignments:
    print(a)

print(state_equation_a_star.get_best_worst_cost(net, im,fm))


# calculer la fitness (5 points)

# changer les poids (2 points)

# calculer un multi-alignment (2 points)

# calculer un anti-alignment (2 points)

# tester et expliquer la distance de hamming (1 point)

# tester et expliquer max (1 point)

# data real : créer un model et calculer sa fitness/précision sur des données réelles (6 points)

