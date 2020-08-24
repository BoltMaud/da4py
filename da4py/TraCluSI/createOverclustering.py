# -*- coding: utf-8 -*-
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cluster import KMeans
from scipy.spatial.distance import cdist
from sklearn import decomposition


'''
    Taken from http://processmining.be/traclusi/
    See README.md
'''

def closest_node(node, nodes):
    return cdist([node], nodes).argmin()

def cluster(traces,superinstances=50,pcaBool=True):
    """Create overclustering of logname.

    Keyword arguments:
    traces -- list of traces
    superinstances -- integer denoting the number of superinstances (default 50)
    pcaBool -- boolean denoting whether or not to use PCA reduction (default True)

    """

    texts= traces

    vectorizer = CountVectorizer(ngram_range=(1,3))
    X = vectorizer.fit_transform(texts)

    binair= (X>0).astype(int)
    pca = decomposition.TruncatedSVD(n_components=5)
    pca.fit(binair)
    Y = pca.transform(binair)

    if pcaBool: dataset=Y
    else: dataset=binair
    if pcaBool: PCAStrat= "PCA"
    else: PCAStrat="FullFeat"

    km = KMeans(n_clusters=superinstances, init='k-means++', max_iter=100, n_init=1)
    km.fit(dataset)

    closestToCenter = set()
    centers=km.cluster_centers_
    for center in centers:
        if pcaBool: superinstance=closest_node(center, dataset)
        else: superinstance= closest_node(center,dataset.toarray())
        closestToCenter.add(superinstance)

    return  closestToCenter, km.labels_
   
                       
        
     
    

