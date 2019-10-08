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
 
## EXAMPLE OF USE 


 ```
  > from pm4py.objects.petri import importer
  > from pm4py.objects.log.importer.xes import factory as xes_importer
  > from da4py.src.main.conformanceArtefacts import ConformanceArtefacts
  
  # get the data with pm4py 
  > net, m0, mf = importer.pnml.import_net("./medium/CloseToM8.pnml")
  > log = xes_importer.import_log("./medium/CloseToM8.xes")

  # da4py has a common class for the different artefacts
  > artefacts =  ConformanceArtefacts(size_of_run = 6, max_d = 13)
  
  # launch a multi-alignment
  > artefacts.multiAlignment(net,m0,mf,log)

 ```

# FOLDERS 
<pre>
┬  
├ src : python code
├ examples : data and example files
└ ...
</pre>

## ACKNOWLEDGEMENT 

Affiliations : LSV, CNRS, ENS Paris-Saclay, Inria, Université Paris-Saclay
