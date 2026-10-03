# Assessing Axes of Modularity

## Step 1: Find keywords indicative of axes

### Claude prompt
I have described axes for biological modularity in the note in https://docs.google.com/document/d/1j_K-iEQkwzShouvYjrA-3ZQmrQEGSdttTVT25FVTN2k/edit?usp=drive_link. I want to find which axes are referenced in the papers in the bibliography. Using the above mentioned note, propose keywords and/phrases that best characterize each axis described in the note. Use the examples cited in the note to construct these keywords and phrases. Choose 30 highly relevant papers to apply this classification scheme.

### Claude response

Keywords per axis (built from the note's examples)

* **Traits** 

  * References: lanternfish, marine microbes, mammalian backbone
  * keywords: trait(s), phenotypic/morphological integration, covariation/covariance, co-vary, morphometric, geometric morphometrics, landmarks, shape variation, evolutionary rate, disparity, skull/cranial, mandible, vertebra, backbone, skeletal, limbs, teeth, anatomical, phylogenetic comparative, phylogenetic signal, allometry, variational modularity, species composition, guild, community assembly, taxa
* **Networks**
  * References: Newman's network review, knockout gene network
  * Keywords: network, node, edge, link, graph, subgraph/subnetwork, community structure/detection, densely connected, hub, connector, clustering coefficient, degree distribution, scale-free, power-law, small-world, modularity Q, interaction network, protein–protein interaction, interactome, genetic interaction, co-expression/co-occurrence network, connectome, connectivity, Markov clustering, topology, wiring diagram, nestedness, between-module, keystone
* **Functions**
  * References: LRR synaptic proteins, ribosome-demand controller, miRNA→protein
  * Keywords: input/output, pathway, metabolic pathway, biosynthesis, enzyme, catalytic, reaction, gene/genetic/synthetic circuit, cassette, device, insulation, retroactivity, load, context-dependence, resource competition, ribosome, composability, plug-and-play, building block, reusable, protein complex, transcription, translation, expression, miRNA, signaling, decode, controller, feedback, combinatorial, glycolysis, co-essential, microcompartment
* **Evolutionary trajectory** (operator)
  * Keywords: evolution/evolve, phylogeny, lineage, speciation, duplication, selection, ontogeny, development, trajectory, radiation, domestication, "million years"
* **Hierarchy** (operator)
    * Keywords: hierarchical, nested, multiscale, multilevel, multilayer, levels of organization, sub-module, higher-order
  
## Papers Illustrating axes
I chose them from the 227 papers marked "Highly relevant", excluding your 9 examples. I preferred highly cited biological research papers with abstracts available and spread them across morphology, ecology, cell and systems biology, synthetic biology and neuroscience. The results are:

### Primary axis
11 Networks, 10 Functions, 9 Traits.
Two axes (hyper-module candidates): 17 papers. The clearest cases are:
  * plant traits analysed as graph nodes (geb.12996)
Drosophila metabolite traits whose modules match biochemical pathways (msab307)
  * brain network modules that each correspond to one cognitive function (pnas.1510619112)
  * gene co-expression modules traced through plant evolution (tpj.13502)
  * neuron types defined by combinations of gene families, an analogue of your LRR example (cell.2017.08.032)

## Evolutionary trajectory and Hierarchy
Evolutionary trajectory: 11 papers. Hierarchy: 8 papers.

* Keyword match: the keyword-count winner matched my primary label for 26 of 30. The 4 misses are papers whose wording is about function but whose method is a network (yeast regulatory modules, co-essential gene modules, co-expression phylogenomics, protein complexes). Keyword counts can't tell these apart.

## Issues with the scheme
The keyword counts never flagged a hyper module on their own. Combinations needed reading the paper, including your own example, the hierarchical metabolic networks paper (science.1073374), which scored as Networks only.
Network-built gene modules (co-essentiality, knockout screens) sit on the boundary between Networks and Functions. Your note puts the knockout example under Networks, so I followed that.
The combinatorial enzyme design paper (ade9434) fits the three axes poorly; its fragment modules are closer to the hierarchy operator.

## Files
* classify_axes.py: the keyword lists and the scoring script. Run it with python src/classify_axes.py --file dois.txt.
* axis_keyword_scores.csv: keyword counts and matched terms for each of the 30 papers. Re-running the script overwrites this file.
* axis_classification.csv: the classification for each paper (primary axis, second axis, evolution and hierarchy flags, a one-line reason), with the keyword result alongside.