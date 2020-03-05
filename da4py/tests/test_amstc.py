from unittest import TestCase

from numpy import sort
from pm4py.objects.petri import importer
from pm4py.objects.log.importer.xes import factory as xes_importer

from da4py.main.analytics.amstc import Amstc, samplingVariantsForAmstc


class TestAmstc(TestCase):
    '''
    This class aims at testing amstc.py file.
    '''
    net, m0, mf = importer.factory.apply("../../examples/medium/model2.pnml")
    log = xes_importer.apply("../../examples/medium/model2.xes")

    def testSamplingVariantsForAmstcDistanceZero(self):
        '''
        Test classical clustering of Generalized Alignment-based Trace Clustering
        '''
        sampleSize=9
        sizeOfRun=8
        maxD=0
        maxNbC=5
        m=2
        clustering=samplingVariantsForAmstc(self.net,self.m0,self.mf,self.log,\
                                            sampleSize,sizeOfRun,maxD,maxNbC,m,maxCounter=1,silent_label="tau")
        assert len(clustering)==4
        size_of_clusters=sort([len(list) for (centroid,list) in clustering ])
        assert ([2,2,2,3]==size_of_clusters).all()


    def testSamplingVariantsForAmstcDistanceTwo(self):
        '''
        Test other parameters
        :return:
        '''
        sampleSize=9
        sizeOfRun=8
        maxD=2
        maxNbC=5
        m=2
        clustering=samplingVariantsForAmstc(self.net,self.m0,self.mf,self.log, \
                                            sampleSize,sizeOfRun,maxD,maxNbC,m,maxCounter=1,silent_label="tau")
        assert len(clustering)==3
        size_of_clusters=sort([len(list) for (centroid,list) in clustering ])
        assert ([1,3,5]==size_of_clusters).all()