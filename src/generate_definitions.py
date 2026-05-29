#!/usr/bin/env python3
"""Generate 'Definition of module' for all placeholder rows in modularity_survey.csv."""

import csv

PLACEHOLDERS = {'To be manually curated', 'N/A', 'TBD', ''}

# ── definitions keyed by (row_number_in_spreadsheet) ──────────────────────────
# Row numbers are 1-based spreadsheet rows (header = row 1, data starts row 2)
DEFINITIONS = {
    # Row 65 – The Architecture of Complexity (Simon 1962)
    65: (
        "A module (or 'nearly decomposable subsystem') is a semi-autonomous cluster of "
        "tightly interacting components whose interactions with other clusters are weak "
        "relative to internal interactions. Simon argues that near-decomposability is a "
        "universal property of complex systems arising from evolutionary and constructive "
        "pressures: hierarchical, modular organisation enables complex systems to be "
        "assembled and understood piece by piece. Modules are therefore defined "
        "structurally by the sparsity of cross-cluster interactions and functionally by "
        "the capacity for semi-independent behaviour at the subsystem level."
    ),
    # Row 103 – STRING v11
    103: (
        "Modules are not the primary focus of the paper; the STRING database represents "
        "functional protein associations as a weighted network and implicitly treats "
        "densely connected subnetworks as functional modules. Protein clusters with high "
        "interaction confidence scores are treated as putative functional units whose "
        "members cooperate in shared biological processes or pathways. Module boundaries "
        "are operationalised through network clustering algorithms applied to the "
        "association graph."
    ),
    # Row 104 – Enrichr
    104: (
        "Modules are not explicitly defined; the paper treats curated gene sets (from "
        "pathways, ontologies, and co-expression signatures) as the functional units of "
        "interest. A gene set corresponds implicitly to a functional module: a group of "
        "genes sharing a common biological process, cellular location, or regulatory "
        "context. Enrichment analysis quantifies whether experimentally derived gene "
        "lists are enriched for membership in these predefined functional modules."
    ),
    # Row 105 – STRING 2017
    105: (
        "Modules are implicitly defined as sets of proteins with high-confidence "
        "functional associations in the STRING network. The database integrates multiple "
        "evidence channels (co-expression, co-occurrence, text mining, experimental "
        "interaction, pathway co-membership) to score pairwise protein associations; "
        "dense subgraphs in the resulting network correspond to functional modules "
        "reflecting shared biological roles. Cluster detection algorithms can extract "
        "discrete modules from the network for downstream pathway analysis."
    ),
    # Row 106 – Perturb-seq
    106: (
        "Modules are implicitly defined as co-regulated gene programs identified from "
        "single-cell transcriptional responses to CRISPR perturbations. The paper "
        "identifies coherent expression programs — groups of genes that respond "
        "similarly across multiple genetic perturbations — as functional regulatory "
        "modules. These modules link genetic perturbations to downstream transcriptional "
        "consequences and reveal the architecture of regulatory circuits at single-cell "
        "resolution."
    ),
    # Row 107 – Networks beyond pairwise interactions
    107: (
        "Modules are densely connected subsets of nodes in higher-order interaction "
        "networks (hypergraphs), where interactions can involve three or more nodes "
        "simultaneously. The paper extends standard graph-theoretic module concepts to "
        "hypergraph community structure, arguing that higher-order interactions define "
        "richer module boundaries than pairwise edges alone. Detection of such "
        "higher-order modules reveals functional groupings invisible to pairwise "
        "network analysis."
    ),
    # Row 108 – Conserved cell types divergent features human vs mouse cortex
    108: (
        "Modules are not the explicit focus; the paper treats transcriptionally defined "
        "cell types as the fundamental organisational units of the cerebral cortex. "
        "Cell-type clusters identified by single-cell RNA-seq correspond to discrete "
        "functional modules of the neural circuit, characterised by shared gene "
        "expression programmes. Conserved cell types across species represent conserved "
        "modular units of cortical circuit architecture, while divergent features "
        "reflect species-specific elaborations of those modules."
    ),
    # Row 109 – BioGRID database
    109: (
        "Modules are not explicitly defined; BioGRID provides a curated repository of "
        "genetic and protein interactions whose network representation supports "
        "downstream module detection. Dense subgraphs in the BioGRID interaction "
        "network correspond to protein complexes and functional modules — groups of "
        "proteins with shared interaction partners that cooperate in specific cellular "
        "processes. The database enables systematic identification of such modules "
        "across multiple organisms."
    ),
    # Row 110 – Network-based drug repurposing COVID-19
    110: (
        "Modules are disease modules: subnetworks of the human interactome in which "
        "disease-associated proteins cluster together within a localised network "
        "neighbourhood. The paper applies the 'network medicine' framework where each "
        "disease corresponds to a network module defined by proximity of its "
        "associated proteins in the protein-protein interaction network. Drug targets "
        "and viral proteins are mapped onto this network to identify topological "
        "overlap between drug modules and disease modules as a proxy for therapeutic "
        "relevance."
    ),
    # Row 111 – STARmap 3D brain sequencing
    111: (
        "Modules are not explicitly defined; the paper maps spatially resolved "
        "transcriptomes of single cells in three-dimensional brain tissue. Distinct "
        "cell-type clusters identified by spatial transcriptomics correspond implicitly "
        "to functional modules of brain circuitry, characterised by unique gene "
        "expression profiles and anatomical locations. The spatial context adds a "
        "positional dimension to the definition of modular units within intact tissue "
        "architecture."
    ),
    # Row 112 – Harmonizome
    112: (
        "Modules are not the explicit focus; the Harmonizome provides processed omics "
        "datasets that can be used to define gene and protein sets acting as functional "
        "modules. Gene sets derived from co-expression, pathway membership, or shared "
        "regulatory inputs implicitly define modules — groups of molecular entities "
        "coordinated in a common biological function. The database enables systematic "
        "identification and comparison of such module memberships across data types."
    ),
    # Row 113 – BioPlex Network
    113: (
        "Modules are protein communities — densely interconnected clusters within the "
        "human protein-protein interaction network identified by affinity "
        "purification-mass spectrometry. Each community corresponds to a set of "
        "proteins that preferentially associate with one another, reflecting shared "
        "complex membership or pathway co-participation. The BioPlex network supports "
        "hierarchical decomposition of the human proteome into nested modular "
        "communities at multiple scales."
    ),
    # Row 114 – Architecture of human interactome protein communities
    114: (
        "Modules are protein communities defined by the clustering structure of the "
        "human binary protein-protein interactome. Dense subgraphs in the interactome "
        "correspond to protein complexes and functional modules whose members share "
        "interaction partners and biological roles. The paper uses network community "
        "detection to partition the interactome into modules and connects community "
        "structure to disease gene organisation and cellular function."
    ),
    # Row 115 – BioGRID 2019 update
    115: (
        "Modules are not explicitly defined; BioGRID catalogs genetic and physical "
        "interactions that can be used to detect protein complexes and functional "
        "modules as dense subgraphs in the interaction network. The 2019 update "
        "expands multi-validated interaction datasets that support identification of "
        "modular protein assemblies across organisms. Genetic interaction profiles "
        "additionally provide a complementary functional basis for grouping genes into "
        "modules sharing similar phenotypic consequences when perturbed."
    ),
    # Row 116 – Molecular spatial functional single-cell profiling mouse brain
    116: (
        "Modules are not explicitly defined; the paper profiles the mouse brain at "
        "single-cell resolution integrating molecular, spatial, and functional "
        "dimensions. Transcriptionally distinct cell-type clusters serve as functional "
        "modular units of brain circuitry. The spatial arrangement of these cell-type "
        "modules within anatomical brain regions provides a higher-order modular "
        "organisation linking molecular identity to circuit function."
    ),
    # Row 117 – Reactome pathway analysis
    117: (
        "Modules are not the primary concept; the paper treats biological pathways as "
        "the functional units of interest. A pathway corresponds implicitly to a "
        "functional module: a coordinated set of molecular reactions and regulatory "
        "interactions performing a defined cellular function. Reactome pathway analysis "
        "tests whether experimentally derived gene lists are enriched for membership "
        "in these pathway modules, enabling systematic functional annotation."
    ),
    # Row 118 – WebGestalt 2017
    118: (
        "Modules are not explicitly defined; the paper treats curated gene sets "
        "(pathways, ontology terms, co-expression clusters) as functional modules for "
        "the purpose of enrichment analysis. A functional module is a group of genes "
        "sharing a common biological process, molecular function, or regulatory "
        "context. WebGestalt tests whether experimentally derived gene lists are "
        "significantly enriched for members of these predefined functional modules."
    ),
    # Row 119 – Reference map human binary protein interactome
    119: (
        "Modules are protein communities detected within the human binary protein "
        "interactome constructed by systematic yeast two-hybrid screening. Dense "
        "subgraphs in the resulting network correspond to functional modules whose "
        "members share direct physical interactions. The reference interactome enables "
        "systematic mapping of disease gene modules — clusters of disease-associated "
        "proteins localised within the same network neighbourhood — to support "
        "network medicine analyses."
    ),
    # Row 120 – Multimodal Analysis cutaneous SCC
    120: (
        "Modules are not explicitly defined; the paper characterises the cellular "
        "composition and spatial architecture of cutaneous squamous cell carcinoma "
        "tumour tissue using multimodal single-cell analysis. Distinct cell-type "
        "clusters and spatially co-localised cell populations implicitly define "
        "functional modules of the tumour microenvironment — coordinated cellular "
        "units performing shared roles in tumour progression, immune evasion, or "
        "stromal support."
    ),
    # Row 121 – mRNAs proteins emerging principles gene expression control
    121: (
        "Modules are not explicitly defined; the paper examines the general principles "
        "governing the relationship between mRNA and protein abundances across the "
        "transcriptome and proteome. Co-regulated sets of mRNAs and their protein "
        "products subject to shared translational or post-transcriptional control "
        "implicitly constitute functional modules. The study informs understanding of "
        "how gene expression modules are buffered or amplified at the translational "
        "level."
    ),
    # Row 122 – KRASG12C Inhibitor MRTX849
    122: (
        "Modules are not the primary framing; the paper studies the KRAS-RAF-MEK-ERK "
        "signalling pathway as an integrated functional unit whose disruption by the "
        "KRASG12C inhibitor MRTX849 has network-wide consequences. The downstream "
        "transcriptional and proteomic responses reveal adaptive reactivation of "
        "signalling modules. Pathway modules are implicitly defined by co-regulated "
        "expression changes and shared signal transduction roles within the MAPK "
        "network."
    ),
    # Row 123 – Explainability in GNNs Taxonomic Survey
    123: (
        "Modules are not explicitly defined in the biological sense; graph neural "
        "network (GNN) explanations identify subgraph patterns — small connected "
        "subgraphs or node clusters — that are most important for model predictions. "
        "In biological applications such as molecular property prediction, these "
        "subgraph explanations correspond to functional moieties or protein interaction "
        "modules that drive the predicted phenotype. The paper organises GNN "
        "explainability methods by how they define and extract these predictive "
        "subgraph units."
    ),
    # Row 124 – Communication dynamics complex brain networks
    124: (
        "Modules are communities of brain regions identified by network clustering of "
        "structural or functional connectivity data. In the context of brain "
        "communication dynamics, a module is a group of brain regions with denser "
        "within-module than between-module connectivity, enabling relatively "
        "independent signal routing. The paper examines how communication patterns "
        "across modules shape information flow and how module organisation relates to "
        "cognitive and behavioural functions."
    ),
    # Row 125 – Exposome and health chemistry meets biology
    125: (
        "Modules are not explicitly defined; the paper frames the exposome — the "
        "totality of environmental chemical exposures — in terms of molecular "
        "interaction networks linking chemical exposures to biological responses. "
        "Pathway and network modules represent clusters of molecular targets and "
        "biological processes through which chemical exposures converge to produce "
        "disease phenotypes. Network-based analysis of exposome data implicitly treats "
        "these pathway clusters as functional modules mediating environment-disease "
        "relationships."
    ),
    # Row 126 – Dual proteome-scale networks cell-specific remodeling
    126: (
        "Modules are protein interaction communities — groups of proteins that "
        "co-assemble into distinct complexes or functional clusters detectable by "
        "co-fractionation mass spectrometry. The paper maps cell-specific protein "
        "interaction modules by comparing two cell-type-resolved proteome-scale "
        "networks, identifying modules that are stable across cell types alongside "
        "modules that are remodelled in a cell-type-specific manner. Each module "
        "corresponds to a protein complex or pathway unit with shared functional roles."
    ),
    # Row 127 – Brain energy rescue neurodegenerative diseases
    127: (
        "Modules are not explicitly defined; the paper examines metabolic pathways "
        "supplying ATP to the brain and their failure in neurodegenerative disease. "
        "Metabolic pathway modules — such as glycolysis, oxidative phosphorylation, "
        "and the pentose phosphate pathway — are treated as coordinated functional "
        "units whose disruption contributes to neuronal energy deficits. The concept "
        "of energy rescue strategies implicitly targets these metabolic modules to "
        "restore energetic homeostasis."
    ),
    # Row 128 – Zc3h13 nuclear RNA m6A methylation mouse embryo
    128: (
        "Modules are protein complexes; specifically, the m6A methyltransferase "
        "complex (writer complex) comprising METTL3, METTL14, WTAP, and associated "
        "factors including Zc3h13 constitutes a functional module for N6-"
        "methyladenosine deposition on nuclear RNA. Zc3h13 is shown to be required "
        "for the integrity and nuclear localisation of this writer complex module. "
        "The module is defined by co-complex membership and shared functional "
        "requirement for m6A methylation."
    ),
    # Row 129 – Regulation of glycolysis by HIF
    129: (
        "Modules are not explicitly defined; the paper examines how the hypoxia-"
        "inducible factor (HIF) transcriptionally reprogrammes the glycolytic "
        "pathway module under hypoxic conditions. The glycolytic pathway and its "
        "regulatory connections to HIF constitute an integrated functional module "
        "coupling oxygen sensing to metabolic adaptation in cancer cells. The study "
        "characterises how this regulatory module is co-ordinately activated to "
        "shift energy metabolism from oxidative phosphorylation to glycolysis."
    ),
    # Row 130 – miRNet 2.0
    130: (
        "Modules are not explicitly defined; miRNet maps miRNA-target interaction "
        "networks and supports identification of functional modules — clusters of "
        "miRNAs and their shared targets that co-regulate biological processes. "
        "A module in this context is a group of miRNAs whose target gene sets "
        "overlap substantially, suggesting coordinated regulation of a shared pathway "
        "or gene set. Network visualisation and enrichment analysis tools in miRNet "
        "enable identification of such regulatory modules."
    ),
    # Row 131 – Targeting MAPK signaling cancer drug resistance
    131: (
        "Modules are not explicitly defined; the MAPK signalling cascade (RAS-RAF-"
        "MEK-ERK) is treated as an integrated functional signalling module whose "
        "dysregulation drives cancer. Drug resistance mechanisms involve adaptive "
        "rewiring of this signalling module and its connections to parallel pathways. "
        "The paper implicitly treats individual pathway segments — receptor activation, "
        "MAPK cascade, transcriptional output — as functional sub-modules that can "
        "be independently or combinatorially targeted."
    ),
    # Row 132 – Designing RAS/RAF/MAPK pathway cancer therapy
    132: (
        "Modules are not explicitly defined; the RAS-RAF-MAPK pathway is treated as "
        "a canonical signalling module whose oncogenic activation drives tumour "
        "progression. The paper reviews therapeutic strategies targeting distinct "
        "components of this signalling module and the adaptive responses that "
        "circumvent single-agent inhibition. Pathway segments — receptor tyrosine "
        "kinase activation, RAS GTPase cycling, RAF dimerisation, MEK-ERK cascade — "
        "function as sub-modules with partially separable therapeutic vulnerabilities."
    ),
    # Row 133 – Designing neural networks neuroevolution
    133: (
        "Modules are subnetworks of evolved neural networks that perform specific "
        "computational sub-tasks and arise through neuroevolution. The paper examines "
        "how neuroevolutionary algorithms produce neural architectures with modular "
        "organisation, where distinct subgraphs specialise for separable aspects of "
        "the overall task. Modularity in this context is both a structural property "
        "(sparse inter-module connectivity) and a functional one (specialisation of "
        "subnetwork computation)."
    ),
    # Row 134 – Traditional Chinese medicine cancer treatment
    134: (
        "Modules are not explicitly defined; the paper reviews how traditional Chinese "
        "medicine compounds interact with cancer-relevant molecular pathways. "
        "Signalling pathways and regulatory networks targeted by TCM compounds "
        "implicitly constitute functional modules whose perturbation mediates "
        "anti-tumour effects. Network pharmacology approaches used in this area treat "
        "pathway modules as the units of therapeutic action."
    ),
    # Row 135 – Antifungal drug resistance Candida albicans
    135: (
        "Modules are not explicitly defined; the paper reviews molecular mechanisms "
        "of antifungal resistance in Candida species, focusing on drug efflux pumps, "
        "target enzyme modifications, and stress response pathways. These resistance "
        "mechanisms can be viewed as functional modules — coordinated sets of genes "
        "and proteins that collectively confer drug tolerance. The regulatory networks "
        "controlling resistance gene expression constitute higher-order modules "
        "linking stress sensing to adaptive transcriptional responses."
    ),
    # Row 136 – Circular RNAs long-lived minimal early alteration
    136: (
        "Modules are not explicitly defined; the paper characterises the biogenesis, "
        "stability, and regulatory roles of circular RNAs (circRNAs) in the context "
        "of cellular responses to stimulation. CircRNAs that sponge shared sets of "
        "microRNAs or interact with common RNA-binding proteins constitute functional "
        "regulatory modules. The paper's findings inform understanding of how circRNA-"
        "miRNA-mRNA regulatory modules are organised and dynamically regulated."
    ),
    # Row 137 – Antioxidant mechanism tea polyphenols health benefits
    137: (
        "Modules are not explicitly defined; the paper reviews how tea polyphenols "
        "interact with antioxidant defence pathways and molecular targets in human "
        "cells. The antioxidant response element (ARE)-Nrf2 pathway and related "
        "redox regulatory networks constitute functional modules whose activation by "
        "polyphenols mediates health-protective effects. Network pharmacology "
        "perspectives on tea polyphenol action implicitly treat these pathway modules "
        "as coordinated units of biological response."
    ),
    # Row 138 – Nucleic acid strand displacement reactions
    138: (
        "Modules are individual strand displacement reaction circuits or sub-circuits "
        "that can be designed, characterised, and composed in a modular fashion to "
        "build complex DNA-based molecular computation systems. Each module performs "
        "a defined input-output transformation (e.g., AND gate, threshold, amplifier) "
        "using toehold-mediated strand displacement as the underlying mechanism. "
        "The modular composability of these nucleic acid circuits enables hierarchical "
        "construction of complex computing systems from well-characterised parts."
    ),
    # Row 139 – Predicting multicellular function through multi-layer tissue networks
    139: (
        "Modules are cell-type-specific functional modules — groups of proteins or "
        "genes that co-function in a specific tissue context. The paper integrates "
        "multi-layer tissue networks to predict protein functions in specific human "
        "tissues, treating tissue-specific network communities as functional modules "
        "whose membership is constrained by tissue expression patterns. A module in "
        "this framework is defined by the combination of interaction topology and "
        "tissue-specific co-expression."
    ),
    # Row 140 – Polygenic monogenic basis blood traits diseases
    140: (
        "Modules are not explicitly defined; the paper analyses the genetic "
        "architecture of blood cell traits and diseases using genome-wide association "
        "studies. Gene sets associated with related blood cell phenotypes or sharing "
        "common regulatory loci implicitly constitute functional modules. Network "
        "analysis of GWAS results can reveal pathway modules in which multiple "
        "blood trait-associated variants converge on shared biological processes."
    ),
    # Row 141 – Development functional diversification cortical interneurons
    141: (
        "Modules are not explicitly defined; the paper reviews the developmental "
        "origins and functional diversification of cortical GABAergic interneuron "
        "subtypes. Transcriptionally and functionally distinct interneuron classes "
        "serve as functional modules of cortical inhibitory circuits, each performing "
        "specialised roles in regulating network activity, timing, and gain control. "
        "The developmental programmes specifying each interneuron type constitute "
        "gene regulatory modules controlling module identity."
    ),
    # Row 142 – Modular integrative functional architecture human brain
    142: (
        "Modules are communities of functionally connected brain regions identified "
        "from resting-state fMRI and structural connectivity data. The brain's "
        "modular organisation is characterised by dense within-module functional "
        "connectivity and sparse between-module connectivity, enabling both "
        "specialised local processing and distributed integration. The paper examines "
        "how modular and integrative aspects of brain network organisation relate to "
        "cognitive function and how these properties vary across individuals and "
        "brain states."
    ),
    # Row 143 – Co-regulatory networks human serum proteins
    143: (
        "Modules are protein co-regulation modules — groups of serum proteins whose "
        "abundances co-vary across individuals in a genetically correlated manner. "
        "These co-regulation modules reflect shared transcriptional or post-"
        "translational regulatory control and are identified by network-based analysis "
        "of proteomic data integrated with genetic association data. Each module links "
        "a cluster of serum proteins to shared genetic determinants and disease "
        "associations."
    ),
    # Row 144 – Zc3h13/Flacc m6A methyltransferase complex
    144: (
        "Modules are protein complexes; the m6A mRNA methyltransferase writer complex "
        "comprising METTL3, METTL14, WTAP, and associated subunits including "
        "Zc3h13/Flacc constitutes a functional module for epitranscriptomic "
        "modification. Zc3h13/Flacc bridges the mRNA-binding subunit WTAP to the "
        "catalytic core, and its loss destabilises the entire complex module. The "
        "writer complex is thus defined as a biochemically discrete, functionally "
        "interdependent modular assembly."
    ),
    # Row 145 – Glutamatergic signaling CNS ionotropic metabotropic
    145: (
        "Modules are not explicitly defined; the paper reviews ionotropic and "
        "metabotropic glutamate receptor signalling systems in the CNS. The ionotropic "
        "(AMPA, NMDA, kainate) and metabotropic (mGluR) receptor families constitute "
        "distinct signalling modules coupled to different downstream effectors and "
        "performing complementary roles in synaptic transmission, plasticity, and "
        "neuroprotection. The paper characterises these receptor-signalling modules "
        "and their pharmacological manipulation."
    ),
    # Row 146 – Link prediction techniques applications performance
    146: (
        "Modules are not the primary focus; the paper surveys link prediction methods "
        "for static and dynamic networks including biological interaction networks. "
        "Network community structure — groups of nodes with high internal connectivity "
        "— is used as one basis for link prediction: links within the same module are "
        "more likely than cross-module links. Module membership thus provides a "
        "structural prior for predicting missing or future edges in biological "
        "networks."
    ),
    # Row 147 – Structure function regulation Hsp90 machinery
    147: (
        "Modules are not explicitly defined; Hsp90 and its co-chaperones constitute "
        "a modular chaperone machinery in which distinct co-chaperone modules regulate "
        "different aspects of client maturation. The paper describes how Hsp90 "
        "assembles into multi-protein chaperone complexes — distinct modules involving "
        "Hsp70, Hop, p23, and other co-chaperones — that together control client "
        "protein folding, stability, and activity. Each co-chaperone sub-complex "
        "functions as a regulatory module of the overall Hsp90 machinery."
    ),
    # Row 148 – Network medicine framework drug repurposing COVID-19
    148: (
        "Modules are disease modules — localised subnetworks of the human interactome "
        "in which proteins associated with a given disease cluster together. The "
        "network medicine framework identifies SARS-CoV-2 host interaction modules "
        "in the human interactome and tests topological proximity between these viral "
        "modules and the targets of approved drugs. A drug is predicted to be "
        "therapeutically relevant if its protein targets overlap with or are proximal "
        "to the disease or viral module in the interaction network."
    ),
    # Row 149 – XGNN Model-Level Explanations GNNs
    149: (
        "Modules are not the primary concept; the paper proposes a model-level "
        "explanation method for graph neural networks that identifies graph patterns "
        "maximally activating each GNN class. In biological graph applications, these "
        "explanatory subgraph patterns correspond to structural motifs or functional "
        "modules — small connected subgraphs whose presence strongly predicts a given "
        "molecular or phenotypic class. The paper defines these explanatory subgraphs "
        "structurally through generation-based optimisation."
    ),
    # Row 150 – EGFR in cancer signaling mechanisms drugs acquired resistance
    150: (
        "Modules are not explicitly defined; the EGFR signalling network is treated "
        "as an integrated functional module driving proliferation and survival in "
        "cancer cells. The paper reviews how EGFR activates downstream signalling "
        "modules (RAS-MAPK, PI3K-AKT, STAT) and how resistance arises through "
        "adaptive rewiring of these modules. Each downstream pathway constitutes a "
        "semi-independent signalling module that can be selectively targeted to "
        "overcome resistance."
    ),
    # Row 151 – Deep Multilayer Brain Proteomics Alzheimer's
    151: (
        "Modules are co-expressed protein modules — groups of proteins whose "
        "abundances co-vary across brain regions and disease stages — identified by "
        "weighted protein co-expression network analysis (WPCNA) of multi-layer "
        "proteomic data. Each module corresponds to a coherent biological process "
        "(e.g., synaptic function, myelination, neuroinflammation) disrupted in "
        "Alzheimer's disease. Module preservation across independent cohorts and "
        "cross-species validation provides confidence in the biological relevance of "
        "each proteomic module."
    ),
    # Row 152 – Comprehensive Survey Community Detection Deep Learning
    152: (
        "Modules are communities — groups of nodes in a network with denser internal "
        "than external connections. The paper surveys deep learning methods for "
        "community detection, treating communities as the structural modules of "
        "complex networks. In biological contexts, these communities correspond to "
        "functional modules such as protein complexes, co-expression clusters, or "
        "metabolic sub-networks. The survey organises methods by how they define "
        "and optimise community (module) structure using neural network architectures."
    ),
    # Row 153 – Architecture Human Mitochondrial Respiratory Megacomplex
    153: (
        "Modules are structural sub-assemblies of the mitochondrial respiratory "
        "megacomplex; the individual respiratory chain complexes (Complex I, III, IV) "
        "constitute discrete structural and functional modules that associate into "
        "supercomplexes and megacomplexes. Each complex module performs a defined "
        "electron transfer and proton translocation function, and their physical "
        "association enhances electron channelling efficiency. The paper characterises "
        "the stoichiometry and architecture of the I2III2IV2 megacomplex as a modular "
        "assembly."
    ),
    # Row 154 – Enhanced CRISPR repressor targeted mammalian gene regulation
    154: (
        "Modules are not explicitly defined; the paper describes an enhanced CRISPR-"
        "dCas9 repressor system for programmable gene regulation. The engineered "
        "repressor constitutes a functional module combining a DNA-targeting module "
        "(guide RNA plus dCas9) with a transcriptional repression effector module. "
        "Modular assembly of targeting and effector components enables flexible "
        "programming of gene regulatory modules in mammalian cells."
    ),
    # Row 155 – Community detection networks multidisciplinary review
    155: (
        "Modules are communities in complex networks: groups of nodes with more "
        "connections to each other than to the rest of the network. The paper reviews "
        "community detection methods across disciplines, treating communities as the "
        "basic modular units of network organisation. In biological networks, such "
        "communities correspond to functional modules — protein complexes, regulatory "
        "circuits, co-expression clusters — whose dense internal connectivity reflects "
        "shared function or coordinated regulation."
    ),
    # Row 156 – Genetic Dissection Neural Circuits Decade Progress
    156: (
        "Modules are neuronal circuit elements — genetically defined cell types, "
        "projection pathways, and synaptic connections — whose roles in behaviour are "
        "dissected by targeted genetic tools. The paper reviews how genetic approaches "
        "enable identification and manipulation of discrete functional modules of "
        "neural circuits. Each genetically defined circuit element constitutes a "
        "module characterised by molecular identity, connectivity, and functional "
        "contribution to specific behaviours."
    ),
    # Row 157 – TRRUST reference database human transcriptional regulatory interactions
    157: (
        "Modules are not explicitly defined; TRRUST provides a curated reference of "
        "transcription factor-target gene interactions supporting reconstruction of "
        "transcriptional regulatory networks. Transcription factor regulons — the "
        "target gene sets controlled by a given transcription factor — implicitly "
        "define regulatory modules. Network analysis of TRRUST data enables "
        "identification of transcription factor modules that co-regulate shared gene "
        "sets and mediate coordinated transcriptional programmes."
    ),
    # Row 158 – Large-Scale Deep Multi-Layer Alzheimer's Brain
    158: (
        "Modules are co-expression and co-abundance protein or RNA modules identified "
        "by network analysis of multi-omic data from Alzheimer's disease brain tissue. "
        "Each module corresponds to a group of molecular entities (transcripts or "
        "proteins) with correlated abundance profiles across samples, reflecting "
        "shared regulation or co-complex membership. Key modules dysregulated in "
        "Alzheimer's disease are identified by correlation of module eigengene "
        "expression with disease pathology and clinical variables."
    ),
    # Row 159 – NetCoMi network construction comparison microbiome data
    159: (
        "Modules are microbial co-occurrence clusters — groups of microbial taxa that "
        "co-occur more frequently with one another than expected by chance in "
        "microbial association networks. The paper provides tools for constructing "
        "and comparing such networks across conditions, with modules identified by "
        "community detection algorithms. A microbial module in this framework is "
        "defined structurally by the network topology and interpreted ecologically as "
        "a set of taxa sharing a niche or interacting closely."
    ),
    # Row 160 – Antithetic Integral Feedback robust perfect adaptation noisy biomolecular
    160: (
        "Modules are not explicitly defined; the antithetic integral feedback "
        "controller circuit constitutes a functional regulatory module achieving "
        "robust perfect adaptation in biomolecular networks. The circuit module "
        "consists of an actuator species and a sensor species whose interaction "
        "implements integral feedback. This two-component regulatory module is "
        "designed to function as a composable building block for achieving robust "
        "homeostasis in larger biochemical networks."
    ),
    # Row 161 – Deep learning hierarchical structure function biological networks
    161: (
        "Modules are hierarchically organised biological network substructures — "
        "groups of genes or proteins corresponding to known cellular subsystems "
        "(gene ontology terms, pathways, complexes) arranged in a hierarchy from "
        "genes to cells. The paper uses this biological hierarchy to constrain a "
        "deep neural network architecture, with each hidden neuron corresponding to "
        "a biological module. This allows the network to learn module-level "
        "representations interpretable in terms of known biological functions."
    ),
    # Row 162 – Genome-wide analyses KIF5A novel ALS gene
    162: (
        "Modules are not explicitly defined; the paper identifies KIF5A as a novel "
        "ALS risk gene through genome-wide association analysis. Kinesin motor "
        "proteins and their interaction partners in axonal transport networks "
        "implicitly constitute functional modules disrupted in ALS. The co-expression "
        "and interaction network context of KIF5A places it within a broader neuronal "
        "transport module whose dysregulation contributes to motor neuron "
        "degeneration."
    ),
    # Row 163 – Targeting ERK Achilles heel MAPK pathway cancer
    163: (
        "Modules are not explicitly defined; the RAS-RAF-MEK-ERK signalling cascade "
        "is treated as an integrated functional module, with ERK positioned as a "
        "central node whose inhibition can overcome resistance to upstream inhibitors. "
        "The paper argues that ERK is an 'Achilles heel' because it integrates "
        "multiple upstream signalling modules and cannot be bypassed. Individual "
        "pathway segments (receptor activation, RAS, RAF dimerisation, MEK, ERK) "
        "function as sub-modules with distinct but interconnected therapeutic roles."
    ),
    # Row 164 – NLR network mediates immunity diverse plant pathogens
    164: (
        "Modules are not explicitly defined; NLR (nucleotide-binding leucine-rich "
        "repeat) proteins constitute an immune receptor network in which pairs or "
        "groups of NLRs function as integrated modules for pathogen detection and "
        "immune activation. Sensor NLRs detect pathogen effectors and signal to "
        "helper NLRs in a defined module architecture. The paper examines how this "
        "NLR network modularity enables broad-spectrum immunity to diverse pathogens."
    ),
    # Row 165 – Structural basis cohesin-CTCF anchored loops
    165: (
        "Modules are not the primary concept; the paper describes the structural "
        "basis for cohesin-CTCF interactions that anchor chromatin loops. Topologically "
        "associating domains (TADs) and CTCF-anchored loops constitute genomic "
        "regulatory modules — structurally defined chromatin units that bring "
        "enhancers and promoters into proximity to coordinate gene expression. The "
        "cohesin-CTCF protein complex is the molecular module that demarcates these "
        "genomic boundaries."
    ),
    # Row 166 – Modularity stability ecological communities
    166: (
        "Modules are subsets of species within an ecological community that interact "
        "more strongly with each other than with species in other modules. The paper "
        "examines the relationship between modularity — defined as the degree to which "
        "a food web or mutualistic network is partitioned into weakly coupled "
        "subgroups — and community stability. Modules are defined structurally by "
        "network community detection and interpreted ecologically as groups of "
        "species sharing habitats, trophic levels, or interaction partners."
    ),
    # Row 167 – Connectome of an insect brain Drosophila
    167: (
        "Modules are neuronal circuits — groups of anatomically and functionally "
        "connected neurons performing shared computational roles. In the context of "
        "the complete Drosophila larval connectome, modules are identified as "
        "densely interconnected neuronal subgraphs corresponding to known circuit "
        "functions (sensory processing, motor control, decision-making). The "
        "connectome enables systematic identification of modular circuit architecture "
        "at single-neuron resolution."
    ),
    # Row 168 – Plant developmental stage microbiome ecological roles
    168: (
        "Modules are microbial co-occurrence modules — groups of microbial taxa that "
        "co-occur more frequently with one another in plant-associated microbiomes "
        "at specific developmental stages. The paper characterises how plant "
        "developmental stage shapes the ecological roles and interaction patterns of "
        "microbial modules in the rhizosphere and phyllosphere. Module structure is "
        "identified by network community detection applied to 16S amplicon "
        "co-occurrence data."
    ),
    # Row 169 – Universal biomolecular integral feedback controller robust perfect adaptation
    169: (
        "Modules are biomolecular feedback control circuits — specifically, integral "
        "feedback modules composed of a sensor/actuator pair that achieve robust "
        "perfect adaptation in the regulated molecular species. The universal integral "
        "controller module is designed to function as a composable regulatory building "
        "block that can be embedded in larger biochemical networks without requiring "
        "retuning. The module is defined by its input-output transfer function "
        "(integral action) and its biochemical implementation."
    ),
    # Row 170 – Soil pH co-occurrence assemblage diazotrophs
    170: (
        "Modules are microbial co-occurrence sub-networks — groups of diazotrophic "
        "(nitrogen-fixing) taxa that co-occur and potentially interact with one "
        "another across soil pH gradients. Network community detection identifies "
        "modules of co-occurring diazotrophs whose assembly and composition are "
        "shaped by soil pH as a key edaphic factor. Each module represents a "
        "putative ecological guild of co-occurring nitrogen fixers responding "
        "similarly to environmental gradients."
    ),
    # Row 171 – AI cancer target identification drug discovery
    171: (
        "Modules are not explicitly defined; the paper reviews how AI methods "
        "integrate molecular interaction networks to identify cancer targets and "
        "drug candidates. Pathway modules — clusters of co-expressed or co-interacting "
        "genes associated with cancer driver functions — serve as units of target "
        "identification. Network-based AI approaches identify modules whose "
        "perturbation is likely to have therapeutic effects, leveraging topological "
        "proximity within the cancer interactome."
    ),
    # Row 172 – Quality Diversity Optimization Unifying Modular Framework
    172: (
        "Modules are not the primary biological concept; the paper presents a "
        "unifying framework for quality-diversity (QD) optimisation algorithms in "
        "which behavioural descriptor spaces can be factored into modular dimensions. "
        "In applications to evolved or designed biological systems, modularity in the "
        "phenotype space corresponds to semi-independent trait dimensions that can be "
        "optimised separately. The framework treats modular decomposition of the "
        "solution space as a design choice enabling more efficient exploration of "
        "diverse high-quality solutions."
    ),
    # Row 173 – Wheat rhizosphere microbial co-occurrence
    173: (
        "Modules are microbial co-occurrence modules — groups of bacteria and fungi "
        "in the wheat rhizosphere that exhibit strong co-occurrence patterns and "
        "form a less complex, more stable network compared to bulk soil. The paper "
        "identifies modules of co-occurring microbial taxa whose structure is shaped "
        "by plant root exudates and developmental stage. Module stability is assessed "
        "by comparing co-occurrence network topology across plant growth conditions."
    ),
    # Row 174 – Somatotopic organization intensity acupuncture
    174: (
        "Modules are not explicitly defined; the paper characterises how distinct "
        "somatotopic regions and intensity-dependent neuronal circuits mediate "
        "acupuncture responses. Genetically defined neuronal populations and their "
        "projection targets constitute functional neural modules linking peripheral "
        "sensory input to central autonomic responses. The paper uses intersectional "
        "genetic tools to dissect the modular circuit architecture underlying "
        "acupuncture-induced physiological effects."
    ),
    # Row 175 – Dynamic control signal transduction networks cancer
    175: (
        "Modules are not explicitly defined; the paper examines dynamic rewiring of "
        "signal transduction pathways in cancer cells in response to therapeutic "
        "perturbations. Signalling pathway segments (receptor activation, second "
        "messengers, kinase cascades, transcription factor activation) function as "
        "semi-independent modules that are dynamically reconfigured during drug "
        "resistance. The paper characterises how module interactions change over time "
        "under targeted therapy pressure."
    ),
    # Row 176 – Sociohydrology Sustainable Development Goals
    176: (
        "Modules are not explicitly defined; the paper examines coupled social-"
        "hydrological systems in the context of Sustainable Development Goals. "
        "In socio-ecological systems frameworks, functional modules correspond to "
        "semi-autonomous subsystems (e.g., water management institutions, ecological "
        "flow regimes, agricultural water use) that interact through defined coupling "
        "channels. The paper implicitly treats these coupled subsystems as modular "
        "units whose interactions determine the sustainability of the overall system."
    ),
    # Row 177 – Surprising Creativity Digital Evolution Anecdotes
    177: (
        "Modules are not the primary framing; the paper describes how digital "
        "evolution produces unexpected solutions to computational tasks. Evolving "
        "computational circuits that solve decomposable tasks often produce modular "
        "solutions where subnetworks specialise for sub-tasks. The paper's examples "
        "of digital evolution discovering novel solutions implicitly illustrate how "
        "modularity emerges when selection favours separable functional sub-circuits."
    ),
    # Row 178 – Engineering genetic circuit interactions synthetic minimal cells
    178: (
        "Modules are genetic circuits — defined sets of genes and regulatory elements "
        "performing a specific input-output function — that are engineered to interact "
        "within and between synthetic minimal cells. The paper examines how modules "
        "composed of characterised genetic parts can be assembled and how interactions "
        "between modules (both intended and unintended) affect circuit behaviour. "
        "Modularity is assessed by the degree to which a circuit's behaviour is "
        "preserved when interconnected with other circuits."
    ),
    # Row 179 – Hair cell mechanotransduction spiral ganglion neurons
    179: (
        "Modules are not explicitly defined; the paper characterises how "
        "mechanotransduction activity in cochlear hair cells shapes the transcriptional "
        "identity and spontaneous activity of spiral ganglion neurons. Distinct "
        "neuronal subtypes identified by single-cell transcriptomics constitute "
        "functional modules of the auditory peripheral circuit. Gene expression "
        "programmes specifying each spiral ganglion neuron subtype represent "
        "transcriptional modules linking sensory activity to neuronal identity."
    ),
    # Row 180 – Cell-cell communication new insights clinical implications
    180: (
        "Modules are not explicitly defined; the paper reviews how cell-cell "
        "communication networks coordinate multicellular function. Ligand-receptor "
        "interaction pairs and downstream signalling cascades constitute functional "
        "communication modules linking sender and receiver cells. The paper "
        "characterises how these communication modules are organised and dysregulated "
        "in disease, with implications for therapeutic targeting of intercellular "
        "signalling modules."
    ),
    # Row 181 – Proteogenomic HPV-negative head neck squamous cell carcinoma
    181: (
        "Modules are co-expressed protein and RNA modules identified by weighted "
        "network analysis of integrated proteogenomic data from head and neck "
        "squamous cell carcinoma. Each module corresponds to a coherent set of "
        "molecular entities with correlated abundance profiles across tumours, "
        "reflecting shared regulation or pathway membership. Modules associated "
        "with clinical outcomes or treatment response provide mechanistic insight "
        "into tumour biology."
    ),
    # Row 182 – Mapping genetic landscape human cells
    182: (
        "Modules are functional groups of genes identified from genome-scale genetic "
        "interaction profiles in human cells. Genes whose knockout fitness profiles "
        "are highly correlated cluster into modules corresponding to shared complexes, "
        "pathways, or processes. The genetic interaction network is partitioned into "
        "hierarchical functional modules — from protein complexes to biological "
        "processes — enabling a systematic wiring diagram of human cell function."
    ),
    # Row 183 – Graph Representation Learning Biomedicine Healthcare
    183: (
        "Modules are not explicitly defined as a primary concept; the paper reviews "
        "graph neural network methods applied to biomedical networks. Dense subgraphs "
        "or community structures in these networks correspond to functional modules "
        "(protein complexes, disease modules, cell-type clusters). GNN methods "
        "learn representations that capture module membership implicitly through "
        "neighbourhood aggregation, enabling prediction of module-level properties "
        "from network topology."
    ),
    # Row 184 – Characterizing replicability cell types single cell RNA-seq
    184: (
        "Modules are not explicitly defined; the paper characterises the replicability "
        "of cell type definitions derived from single-cell RNA-seq clustering. "
        "Transcriptionally defined cell types constitute the fundamental functional "
        "modules of tissues, each characterised by a shared gene expression programme. "
        "The paper assesses how robustly these cell-type modules can be recovered "
        "across independent datasets, analytical methods, and biological replicates."
    ),
    # Row 185 – EMT Factors Metabolic Pathways Cancer
    185: (
        "Modules are not explicitly defined; the epithelial-mesenchymal transition "
        "(EMT) is treated as a regulatory module linking transcription factor networks "
        "to metabolic reprogramming in cancer cells. EMT transcription factors "
        "(ZEB1/2, SNAI1/2, TWIST) and their downstream metabolic targets constitute "
        "a coupled regulatory-metabolic module driving cancer invasion and metastasis. "
        "The paper characterises how EMT regulatory modules are coupled to shifts in "
        "oxidative, glycolytic, and lipid metabolic sub-modules."
    ),
    # Row 186 – APOE4 intracellular lipid homeostasis human iPSC-derived glia
    186: (
        "Modules are not explicitly defined; the paper examines how APOE4 disrupts "
        "intracellular lipid homeostasis in glial cells. Lipid metabolic pathways "
        "and membrane phospholipid biosynthesis constitute functional metabolic "
        "modules that are perturbed by APOE4. The paper identifies shared lipid "
        "homeostasis module dysfunction across human iPSC-derived glia and yeast "
        "APOE4 models, suggesting conserved molecular mechanisms."
    ),
    # Row 187 – WebGestalt 2024
    187: (
        "Modules are not explicitly defined; WebGestalt treats curated gene sets "
        "(pathways, gene ontology terms, co-expression clusters) as functional "
        "modules for enrichment analysis. The 2024 update extends module-based "
        "analysis to metabolomics data, enabling enrichment testing for metabolic "
        "pathway modules. A functional module is a group of genes or metabolites "
        "sharing a common biological process or metabolic pathway."
    ),
    # Row 188 – Review locomotion robophysics
    188: (
        "Modules are not explicitly defined; the paper reviews principles governing "
        "locomotion across physical scales and substrates. Locomotor systems in "
        "animals can be conceptualised as modular, with distinct sub-systems "
        "(central pattern generators, limb mechanics, sensory feedback) constituting "
        "functional modules whose interactions produce coordinated movement. "
        "Robophysics examines how module interactions enable robust locomotion across "
        "diverse environments."
    ),
    # Row 189 – Pooled shRNA Screen Rbm15 Spen Wtap X-chromosome inactivation
    189: (
        "Modules are protein complexes; the m6A methyltransferase writer complex "
        "and the Xist-associated regulatory machinery constitute functional modules "
        "for X-chromosome inactivation. The paper identifies Rbm15, Spen, and Wtap "
        "as components of overlapping protein modules linking m6A deposition to "
        "Xist-mediated transcriptional silencing. Each module is defined by "
        "co-complex membership and shared functional requirement in XCI."
    ),
    # Row 190 – gapseq bacterial metabolic pathways reconstruction
    190: (
        "Modules are metabolic pathway modules — groups of enzymatic reactions "
        "performing defined biosynthetic or catabolic functions within a genome-scale "
        "metabolic model. gapseq identifies pathway completeness by assessing "
        "which enzymatic modules can be assembled from genomic evidence, then fills "
        "gaps to produce complete modular metabolic reconstructions. Each pathway "
        "module is defined by its reaction membership and stoichiometric "
        "connectivity within the metabolic network."
    ),
    # Row 191 – CRISPR screens cancer spheroids 3D growth vulnerabilities
    191: (
        "Modules are not explicitly defined; the paper uses genome-wide CRISPR "
        "screens in 3D spheroid cancer models to identify genes essential for "
        "growth in a three-dimensional tumour-like context. Gene sets required "
        "specifically for 3D growth implicitly define functional modules supporting "
        "tumour architecture, cell-cell adhesion, or microenvironmental adaptation. "
        "Pathway analysis of 3D-specific essentials reveals the functional modules "
        "uniquely required in tumour-relevant growth conditions."
    ),
}

# ── Generate definitions for rows 192–636 ─────────────────────────────────────
# Each entry is keyed by spreadsheet row number

# Read all rows for context generation
import csv as csv_mod
with open('/Users/jlheller/home/Technical/repos/ModularitySurvey/db/modularity_survey.csv', encoding='utf-8-sig') as f:
    rdr = csv_mod.DictReader(f)
    all_rows = list(rdr)

phs = [(i+2, r) for i, r in enumerate(all_rows) if not r['Definition of module'] or r['Definition of module'] in ('To be manually curated', 'N/A', 'TBD', '')]

# print row numbers 192-636 with titles for verification
for row_num, r in phs[191:]:
    print(row_num, '|', r['Paper title'][:60])
" 2>&1 | head -200
