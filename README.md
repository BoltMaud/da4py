>Author : Boltenhagen Mathilde with Thomas Chatain and Josep Carmona<br>
>Date : 09.2019<br>
    
## INTRODUCTION 

This project implements **Process Mining** algorithms with  _SAT encodings_ to get optimal results for verification problems.
Boolean formulas are first created, then converted into CNF form and solved with SAT solvers, thanks to  `pysat`.
This librairy used `pm4py` Objects. 

The project is a translation of the Ocaml version `darksider` created by Thomas Chatain and Mathilde Boltenhagen. 

### Scientific papers

- _Encoding Conformance Checking Artefacts in SAT_ by Mathilde Boltenhagen, Thomas Chatain, Josep Carmona <br>
- _Anti-alignments in conformance checking–the dark side of process models_ by Thomas Chatain, Josep Carmona
- _Generalized Alignment-Based Trace Clustering of Process Behavior_ by Mathilde Boltenhagen, Thomas Chatain, Josep Carmona
 
## ENVIRONNEMENT & INSTALLATION

 `python 3.7.x `
 
 Simply run : 
 `pip install da4py`
 
 (https://pypi.org/project/da4py/0.0.1/)

 
## USAGE

The librairy uses pm4py. 

```python
pm4py.objects.petri import importer
pm4py.objects.log.importer.xes import factory as xes_importer
from da4py.src.main.conformanceArtefacts import ConformanceArtefacts  
# get the data with pm4py 
model, m0, mf = importer.pnml.import_net('<PATH_TO_MODEL>')
traces = xes_importer.import_log('<PATH_TO_LOG>')
```
### Anti-alignment
> Formal definition : 
> Given a finite collection $L$ of log traces and a model $N$, an anti-alignment is a run $u \in Runs(N)$ which maximizes its distance $\min_{\sigma \in L} dist(\sigma,u)$ to the log. 



This launches the main module. This object, the model and the traces must be reloaded for each experimentation. This is an issue that will be fix soon. 
```python
artefacts = ConformanceArtefacts()
```
We can to set the size of the anti-alignment we want (usefull for prefix) : 
```python
artefacts.setSize_of_run(10)
```
For execution times or memory problems, we can set the maximum number of difference that will be tried. 
```python
artefacts.setMax_d(10)
```

Two types of distances are available : 
- Hamming distance
- Edit distance

```python
artefacts.setDistance_type("edit")
```
Then an anti-alignment can be found by running : 
```python
artefacts.antiAlignment(model,m0,mf,traces)
print(artefacts.getRun())
print(artefacts.getTracesWithDistances())
```

### Precision 
Then we can compute precision :
```python
print(artefacts.getPrecision())
```

### Other features 

One can add silent transition label that will not cost in the distances :
```python
artefacts.setSilentLabel("tau")
```

We can also compute sum instead of min :
```python
artefacts.setOptimizeMin(False)
```

### Multi-alignment
The same features (not precision) also work for multi-alignment: 
```python
model, m0, mf = importer.pnml.import_net('<PATH_TO_MODEL>')
traces = xes_importer.import_log('<PATH_TO_LOG>')
artefacts = ConformanceArtefacts()
artefacts.setSilentLabel("tau")
artefacts.setDistance_type("hamming")
artefacts.setOptimizeMin(True)
artefacts.setSize_of_run(10)
artefacts.setMax_d(10)

# run a multi-Alignment
artefacts.multiAlignment(model,m0,mf,traces)
print(artefacts.getRun())
print(artefacts.getTracesWithDistances())
```

## AMSTC 

AMSTC is a trace clustering method that allows one to extract subnet centroids from a process model. The input is then 
a log and a model and it outputs a set of subnets and associated clustered traces. The method is implemented in SAT but a sampling method allows to run large logs.
```python
# process model
model, m0, mf = importer.pnml.import_net('examples/medium/model2.pnml')

# log traces
traces = xes_importer.import_log('examples/medium/model2.xes')

# sampleSize : number of traces that are used in the sampling method
sampleSize= 5 

# sizeOfRun : maximal length requested to compute alignment 
sizeOfRun = 8

# maxNbC : maximal number of transitions per cluster to avoid to get a unique centroid
maxNbC = 5

# m : number of cluster that will be searching at each AMSTC of the sampling method. Understand that more than m cluster can 
be returned. 
m = 2

# maxCounter : as this is a sampling method, maxCounter is the number of fails of AMSTC before the sampling method stops
# silent_label : every transition that contains this string will not cost in alignment
clustering=samplingVariantsForAmstc(net,m0,mf,log,sampleSize,sizeOfRun,maxD,maxNbC,m,maxCounter=1,silent_label="tau")
```

The clustering can then be used like : 
```python
from pm4py.visualization.petrinet import factory as vizu

for (centroid, traces) in clustering:
    if type(centroid) is tuple:
        net, m0,mf=centroid
        vizu.apply(net, m0, mf).view()
        print(traces)
```

## SAT Encoding & Formula Shapes
The tool first constructs SAT formulas using operator classes AND and OR of da4py.utils.formulas.py. Those formulas are fully described in the published related papers. 
```
AND( [], [], 
	AND( [m_ip [0, 0]], [m_ip [0, 1]], 
		AND( [], [], 
			OR( [], [], 
				AND( [tau_it [1, 0]], [tau_it [1, 1], tau_it [1, 2]], ) 
				AND( [tau_it [1, 1]], [tau_it [1, 0], tau_it [1, 2]], ) 
				AND( [tau_it [1, 2]], [tau_it [1, 0], tau_it [1, 1]], )) 
			OR( [], [tau_it [1, 0]], 
				AND( [], [], 
					OR( [], [], 
						AND( [m_ip [1, 0], m_ip [0, 0]], [], ) 
						AND( [], [m_ip [1, 0], m_ip [0, 0]], )) 
					AND( [m_ip [1, 1], m_ip [0, 1]], [], ))) 
                    ...
```
Then, the formula is translated to a WCNF form which is solved with `pysat` library.
```
[[2], [-1], [7, -82], [-8, -82], [-9, -82], [8, -83], [82, 83, 84], [3, -86]...]
```


## ACKNOWLEDGEMENT 

Affiliations : LSV, CNRS, ENS Paris-Saclay, Inria, Université Paris-Saclay
