>Author : Boltenhagen Mathilde<br>
>Date : 09.2019<br>
    
## INTRODUCTION 

This project implements **Process Mining** algorithms with  _SAT encodings_ to get optimal results in case of verification problems.
Boolean formulas are first created, then converted to CNF and solved with SAT solvers, thanks to  `pysat`.
This librairy used `pm4py` Objects. 

The project is a translation of the Ocaml version `darksider` created by Thomas Chatain and Mathilde Boltenhagen. 

### Scientific papers

- _Encoding Conformance Checking Artefacts in SAT_ by Mathilde Boltenhagen, Thomas Chatain, Josep Carmona <br>
- _Anti-alignments in conformance checking–the dark side of process models_ by Thomas Chatain, Josep Carmona

#### To be implemented soon

- (Ocaml version exists) _Generalized Alignment-Based Trace Clustering of Process Behavior_ by Mathilde Boltenhagen, Thomas Chatain, Josep Carmona
 
## ENVIRONNEMENT

 `python 3.7.x `
 
## USAGE

The librairie uses pm4py. 

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
Then an anti-alignment can be find by running : 
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


## ACKNOWLEDGEMENT 

Affiliations : LSV, CNRS, ENS Paris-Saclay, Inria, Université Paris-Saclay
