from unittest import TestCase
from pm4py.objects.petri import importer
from pm4py.objects.log.importer.xes import factory as xes_importer
from da4py.main.conformanceChecking.conformanceArtefacts import ConformanceArtefacts


class TestConformanceArtefacts(TestCase):
    '''
    This class aims at testing conformanceArtefacts.py file.
    '''
    net, m0, mf = importer.factory.apply("../../examples/medium/model2.pnml")
    log = xes_importer.apply("../../examples/medium/model2.xes")
    artefacts=ConformanceArtefacts()

    def testAntiAlignmentEditDistance(self):
        '''
        Test anti-alignment with Edit Distance
        '''
        self.artefacts.setMax_d(14)
        self.artefacts.setSize_of_run(8)
        self.artefacts.antiAlignment(self.net, self.m0, self.mf,self.log)

        assert self.artefacts.getPrecision()== 0.7142857142857143
        assert len(self.artefacts.getRun())==8
        assert self.artefacts.getMinDistanceToRun()==4

    def testAntiAlignmentHammingDistance(self):
        '''
        Test anti-alignment with Hamming Distance
        '''
        self.artefacts=ConformanceArtefacts()
        self.artefacts.setMax_d(14)
        self.artefacts.setSize_of_run(8)
        self.artefacts.setDistance_type("hamming")
        self.artefacts.antiAlignment(self.net, self.m0, self.mf,self.log)

        assert self.artefacts.getPrecision()== 0.7142857142857143
        assert len(self.artefacts.getRun())==8
        assert self.artefacts.getMinDistanceToRun()==4

    def testAntiAlignmentSilentTransitions(self):
        '''
        Test anti-alignment with edit distance but another silent transition
        '''
        self.artefacts=ConformanceArtefacts()
        self.artefacts.setMax_d(14)
        self.artefacts.setSize_of_run(8)
        self.artefacts.setDistance_type("edit")
        self.artefacts.setSilentLabel("A")
        self.artefacts.antiAlignment(self.net, self.m0, self.mf,self.log)

        assert self.artefacts.getPrecision()== 0.7142857142857143
        assert 'n13' in self.artefacts.getRun()
        assert self.artefacts.getMinDistanceToRun()==4




