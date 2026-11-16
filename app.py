import json
import os
import zipfile
from html import escape
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import numpy as np
import plotly.graph_objects as go
import streamlit as st
try:
 st.sidebar.page_link("pages/2_Elder_Care_Help.py", label="🤝 Elder Care Help (बुज़ुर्गों की देखभाल)")
except Exception:
 pass

import streamlit.components.v1 as components


def clean_html_markup(raw_html: str) -> str:
    return "".join(
        line.strip() for line in raw_html.splitlines() if line.strip()
    )


ANATOMICAL_FUNCTION_ROLES = (
    ("corticospinal", "Carries descending voluntary-movement signals to spinal motor neurons."),
    ("substantia nigra", "Modulates movement through dopaminergic basal-ganglia circuits."),
    ("striatum", "Selects and scales movement through basal-ganglia circuits."),
    ("hippocampus", "Supports episodic memory formation and spatial navigation."),
    ("thalamus", "Relays information and coordinates communication with the cortex."),
    ("cerebellum", "Coordinates balance, posture, timing, and motor learning."),
    ("brainstem", "Supports arousal and essential autonomic functions."),
    ("vessel", "Supplies brain tissue and helps regulate cerebral perfusion."),
    ("insular", "Integrates interoception, salience, and connected executive networks."),
    ("motor cortex", "Plans and initiates voluntary movement through descending motor pathways."),
    ("frontal", "Supports executive function, planning, and voluntary action."),
    ("temporal", "Supports hearing, language, and memory processing."),
    ("parietal", "Integrates somatic sensation and spatial attention."),
    ("cortex", "Supports higher-order cognition, perception, and voluntary action."),
)


def functional_role_for_name(anatomy_name: str) -> str:
    lowered_name = anatomy_name.lower()
    matched_roles = dict.fromkeys(
        role
        for token, role in ANATOMICAL_FUNCTION_ROLES
        if token in lowered_name
    )
    return " ".join(matched_roles) or "Supports specialized neural processing."


DISEASE_DATA = {
    "Healthy Control": {
        "genes": "Standard Human DNA (Normal Baseline)",
        "protein": "Intact Native Protein Structure (Ubiquitin)",
        "pdb_id": "1UBQ",
        "short_region": "Whole Brain Equilibrium",
        "gene_and_misfolding": (
            "Wild-type genes produce proteins that generally adopt their "
            "functional conformations. Molecular chaperones support folding, "
            "while ubiquitin-proteasome and autophagy-lysosomal pathways help "
            "clear damaged or misfolded proteins and maintain proteostasis."
        ),
        "target_region": (
            "Whole-brain reference: cerebral cortex, subcortical nuclei, "
            "midbrain, cerebellum, brainstem, and cerebral vasculature."
        ),
        "core_impact": (
            "Reference state for coordinated movement, memory, executive "
            "function, sleep-wake regulation, and cerebrovascular health."
        ),
        "foci": [],
        "camera_eye": {"x": 1.45, "y": 1.45, "z": 1.05},
        "rgb": (100, 116, 139),
        "hex": "#64748B",
    },
    "Huntington's Disease": {
        "genes": "HTT",
        "protein": "Huntingtin",
        "pdb_id": "4FE8",
        "short_region": "Striatum (Basal Ganglia) & Cortex",
        "gene_and_misfolding": (
            "An expanded CAG repeat in HTT adds an abnormally long "
            "polyglutamine segment to huntingtin. This stretch destabilizes the "
            "protein and favors sticky, beta-rich assemblies; soluble oligomers "
            "and larger aggregates can interfere with gene regulation, energy "
            "handling, and the transport that keeps neurons supplied."
        ),
        "target_region": (
            "Medium spiny neurons in the caudate and putamen are lost early, "
            "disrupting the basal-ganglia circuits that select and smooth "
            "movement. The reason these cells are especially vulnerable is "
            "not fully resolved; connected cerebral cortex is affected as the "
            "disease advances."
        ),
        "core_impact": (
            "As striatal control of movement circuits weakens, movements can "
            "become involuntary and jerky (chorea). Damage to connected "
            "cognitive and emotional networks brings difficulty planning, "
            "memory changes, irritability, depression, and increasing support "
            "needs."
        ),
        "foci": [
            {"dir": [0.35, 0.45, 0.35], "radius": 0.56, "primary": True, "label": "Striatum & Cerebral Cortex"},
            {"dir": [-0.35, 0.45, 0.35], "radius": 0.56, "primary": False, "label": "Contralateral Striatum"},
        ],
        "camera_eye": {"x": 1.35, "y": 1.55, "z": 1.05},
        "rgb": (225, 29, 72),
        "hex": "#E11D48",
    },
    "Familial Alzheimer's Disease": {
        "genes": "APP, PSEN1, PSEN2",
        "protein": "Amyloid-beta (Aβ42) & Hyperphosphorylated Tau",
        "pdb_id": "2M4J",
        "short_region": "Hippocampus & Cerebral Cortex",
        "gene_and_misfolding": (
            "Pathogenic variants in APP or the presenilin genes PSEN1 and "
            "PSEN2 can shift amyloid precursor protein processing toward "
            "longer, stickier amyloid-beta peptides. These peptides assemble "
            "into oligomers and plaques; the resulting cellular stress is "
            "linked to tau becoming abnormally modified, detaching from "
            "microtubules, and forming tangles that impair neuronal transport."
        ),
        "target_region": (
            "Entorhinal cortex and hippocampal memory circuits are often "
            "affected early, followed by wider association cortex. Injury to "
            "these densely connected circuits interrupts the encoding and "
            "retrieval of new experiences before atrophy becomes widespread."
        ),
        "core_impact": (
            "When hippocampal circuits can no longer reliably form new "
            "memories, recent conversations and events are easily lost. As "
            "cortical networks are drawn in, confusion, disorientation, "
            "language and problem-solving difficulties, and loss of "
            "independence become more pronounced."
        ),
        "foci": [
            {"dir": [0.85, -0.15, -0.10], "radius": 0.62, "primary": True, "label": "Hippocampus & Temporal Cortex"},
            {"dir": [-0.85, -0.15, -0.10], "radius": 0.62, "primary": False, "label": "Contralateral Temporal Cortex"},
        ],
        "camera_eye": {"x": 1.65, "y": 0.85, "z": 0.95},
        "rgb": (234, 88, 12),
        "hex": "#EA580C",
    },
    "Familial Parkinson's Disease": {
        "genes": "SNCA, LRRK2, PRKN",
        "protein": "Alpha-synuclein (Lewy bodies)",
        "pdb_id": "1XQ8",
        "short_region": "Substantia Nigra (Midbrain)",
        "gene_and_misfolding": (
            "SNCA variants or extra gene copies can increase or destabilize "
            "alpha-synuclein, encouraging it to assemble into beta-rich "
            "oligomers and Lewy pathology. LRRK2 variants alter kinase "
            "signaling, while PRKN variants impair mitochondrial quality "
            "control; these are distinct routes to neuronal stress, and not "
            "every genetic form is defined by Lewy bodies."
        ),
        "target_region": (
            "Dopamine-producing neurons in the substantia nigra pars compacta "
            "are especially vulnerable to oxidative and metabolic stress. "
            "Their long projections supply the striatum, so their loss "
            "depletes dopamine across a movement-control circuit."
        ),
        "core_impact": (
            "With less dopamine reaching the striatum, the brain has trouble "
            "initiating and scaling movement. Patients may develop resting "
            "tremor, stiffness, slowed movement, and a shuffling or unstable "
            "gait."
        ),
        "foci": [
            {"dir": [0.0, -0.45, -0.75], "radius": 0.54, "primary": True, "label": "Substantia Nigra (Midbrain)"},
        ],
        "camera_eye": {"x": 1.45, "y": -1.35, "z": 0.85},
        "rgb": (126, 34, 206),
        "hex": "#7E22CE",
    },
    "Familial Amyotrophic Lateral Sclerosis (ALS)": {
        "genes": "SOD1, TARDBP, FUS, C9orf72",
        "protein": "TDP-43, SOD1, or FUS",
        "pdb_id": "2C9V",
        "short_region": "Motor Cortex, Brainstem, & Spinal Cord",
        "gene_and_misfolding": (
            "SOD1 variants can destabilize the enzyme and expose surfaces that "
            "promote misfolding. TARDBP and FUS variants can disturb RNA-"
            "binding proteins and their movement between nucleus and "
            "cytoplasm; C9orf72 repeat expansions can produce toxic RNA and "
            "repeat-derived proteins. These different mechanisms converge on "
            "cellular stress rather than one identical aggregate."
        ),
        "target_region": (
            "Upper motor neurons in the motor cortex and lower motor neurons "
            "in brainstem and spinal cord are affected. Their exceptionally "
            "long axons must maintain distant muscle connections, making "
            "transport and energy failures especially damaging."
        ),
        "core_impact": (
            "As motor neurons lose their connections to muscle, weakness "
            "spreads from clumsiness or muscle twitching to loss of voluntary "
            "control and paralysis. Bulbar involvement can impair speech and "
            "swallowing; weakness of breathing muscles can make respiration "
            "increasingly difficult."
        ),
        "foci": [
            {"dir": [0.25, 0.15, 0.90], "radius": 0.54, "primary": True, "label": "Motor Cortex & Brainstem"},
            {"dir": [-0.25, 0.15, 0.90], "radius": 0.54, "primary": False, "label": "Contralateral Motor Cortex"},
            {"dir": [0.0, -0.35, -0.85], "radius": 0.50, "primary": False, "label": "Spinal Motor Pathways"},
        ],
        "camera_eye": {"x": 1.45, "y": 1.15, "z": 1.25},
        "rgb": (2, 132, 199),
        "hex": "#0284C7",
    },
    "Genetic Frontotemporal Dementia (FTD)": {
        "genes": "MAPT, GRN, C9orf72",
        "protein": "Tau or TDP-43",
        "pdb_id": "5O3L",
        "short_region": "Frontal & Temporal Lobes",
        "gene_and_misfolding": (
            "MAPT variants can alter tau splicing or weaken its normal "
            "microtubule association, allowing abnormal tau to accumulate. "
            "GRN loss and many C9orf72 repeat expansions instead disrupt "
            "cellular pathways associated with TDP-43 mislocalization and "
            "aggregation. These distinct proteinopathies undermine the "
            "maintenance of frontal and temporal neurons."
        ),
        "target_region": (
            "Prefrontal, orbitofrontal, and anterior temporal networks are "
            "preferentially affected, with patterns that vary by genetic "
            "cause. These regions support social judgment, motivation, "
            "behavior, and language, so their injury can change personality "
            "before memory is prominently affected."
        ),
        "core_impact": (
            "Damage to frontal control networks can reduce empathy, weaken "
            "social inhibition, and alter motivation or judgment. When "
            "language-dominant temporal networks are involved, word-finding, "
            "speech production, or comprehension progressively falter."
        ),
        "foci": [
            {"dir": [0.35, 0.85, 0.20], "radius": 0.60, "primary": True, "label": "Frontal & Temporal Lobes"},
            {"dir": [-0.35, 0.85, 0.20], "radius": 0.60, "primary": False, "label": "Contralateral Frontal Lobe"},
            {"dir": [0.75, 0.25, -0.25], "radius": 0.52, "primary": False, "label": "Temporal Lobe"},
            {"dir": [-0.75, 0.25, -0.25], "radius": 0.52, "primary": False, "label": "Contralateral Temporal Lobe"},
        ],
        "camera_eye": {"x": 1.35, "y": 1.55, "z": 0.95},
        "rgb": (190, 24, 93),
        "hex": "#BE185D",
    },
    "Genetic Prion Diseases (e.g., Familial CJD, FFI)": {
        "genes": "PRNP",
        "protein": "Prion protein (PrPSc)",
        "pdb_id": "1QLX",
        "short_region": "Cerebral Cortex, Thalamus, & Cerebellum",
        "gene_and_misfolding": (
            "Pathogenic PRNP variants can make cellular prion protein less "
            "stable and more likely to adopt the beta-rich PrPSc shape. "
            "PrPSc can template neighboring prion proteins to refold, "
            "allowing misfolding to propagate through tissue and trigger "
            "rapid neuronal injury."
        ),
        "target_region": (
            "Prion injury can involve cerebral cortex, thalamus, and "
            "cerebellum; the pattern depends on the PRNP variant and syndrome. "
            "Loss of cortical and thalamic neurons disrupts cognition and "
            "sleep regulation, while cerebellar injury undermines balance."
        ),
        "core_impact": (
            "As templated misfolding spreads, function can decline rapidly: "
            "cortical injury causes dementia, cerebellar injury causes "
            "unsteadiness, and some variants disrupt thalamic sleep circuits "
            "so profoundly that fatal familial insomnia develops."
        ),
        "foci": [
            {"dir": [0.0, -0.80, -0.35], "radius": 0.58, "primary": True, "label": "Cerebellum, Thalamus & Cortex"},
            {"dir": [0.40, 0.10, 0.65], "radius": 0.52, "primary": False, "label": "Cerebral Cortex"},
            {"dir": [-0.40, 0.10, 0.65], "radius": 0.52, "primary": False, "label": "Contralateral Cortex"},
        ],
        "camera_eye": {"x": 1.35, "y": -1.45, "z": 0.95},
        "rgb": (22, 163, 74),
        "hex": "#16A34A",
    },
    "Spinocerebellar Ataxias (SCAs)": {
        "genes": "ATXN1, ATXN2, ATXN3, etc.",
        "protein": "Ataxin proteins (Polyglutamine aggregates)",
        "pdb_id": "1YZB",
        "short_region": "Cerebellum & Brainstem",
        "gene_and_misfolding": (
            "In several SCA subtypes, expanded CAG repeats lengthen the "
            "polyglutamine tract in an ataxin protein. The enlarged segment "
            "can destabilize the fold, promote aggregation, and interfere "
            "with the protein's normal interactions; the precise mechanism "
            "depends on the affected ATXN gene."
        ),
        "target_region": (
            "Cerebellar Purkinje cells, deep cerebellar nuclei, and connected "
            "brainstem pathways are vulnerable. These circuits continually "
            "compare intended with actual movement, so their loss erodes "
            "balance and fine motor timing."
        ),
        "core_impact": (
            "As cerebellar timing signals degrade, walking becomes unsteady "
            "and precise movements overshoot or miss their targets. The same "
            "coordination failure can make speech slurred and balance "
            "increasingly difficult."
        ),
        "foci": [
            {"dir": [0.0, -0.85, -0.50], "radius": 0.62, "primary": True, "label": "Cerebellum & Brainstem"},
        ],
        "camera_eye": {"x": 1.25, "y": -1.55, "z": 0.85},
        "rgb": (13, 148, 136),
        "hex": "#0D9488",
    },
    "Familial Cerebral Amyloid Angiopathy (CAA)": {
        "genes": "APP, CST3",
        "protein": "Amyloid-beta (Aβ40/42) or Cystatin C",
        "pdb_id": "1G96",
        "short_region": "Cerebral Blood Vessels",
        "gene_and_misfolding": (
            "Certain APP variants alter amyloid-beta production, while CST3 "
            "variants can destabilize cystatin C. The resulting proteins are "
            "more prone to assemble into amyloid deposits within vessel "
            "walls, where they replace structural support rather than "
            "forming only tissue plaques."
        ),
        "target_region": (
            "Amyloid accumulates in cortical and leptomeningeal vessel walls. "
            "As deposits disrupt the muscular and elastic layers that normally "
            "reinforce these vessels, the affected arteries become fragile "
            "and prone to leakage or rupture."
        ),
        "core_impact": (
            "Fragile vessels can leak small amounts of blood or rupture, "
            "causing cerebral microbleeds or a lobar hemorrhagic stroke. "
            "Depending on the injured area, a patient may experience sudden "
            "weakness, numbness, language problems, or stepwise cognitive "
            "decline."
        ),
        "foci": [
            {"dir": [0.45, 0.35, 0.75], "radius": 0.58, "primary": True, "label": "Cerebral Blood Vessels"},
            {"dir": [-0.45, -0.45, 0.70], "radius": 0.58, "primary": False, "label": "Contralateral Cerebral Vessels"},
        ],
        "camera_eye": {"x": 1.35, "y": -1.45, "z": 1.05},
        "rgb": (217, 119, 6),
        "hex": "#D97706",
    },
}

DISEASE_FEATURES = {
    "Healthy Control": {
        "wt_pdb_id": "1UBQ",
        "wt_protein": "Intact Native Protein Structure (Ubiquitin)",
        "stages": {
            1: "Baseline homeostasis: normal protein folding and synaptic function.",
            2: "Stable neural networks with ongoing protein quality control.",
            3: "Healthy reference anatomy; no disease progression is represented.",
        },
        "mutations": {
            "Intact Native Protein (Healthy Baseline)": {
                "res": None,
                "dna": "Standard Human DNA (Normal Baseline)",
                "effect": (
                    "100% functional native conformation with zero toxic "
                    "aggregation."
                ),
            }
        },
    },
    "Huntington's Disease": {
        "wt_pdb_id": "3IO4",
        "wt_protein": "Wild-Type Huntingtin Exon 1",
        "stage_foci": [
            {"dir": [0.0, 0.70, 0.55], "radius": 0.52, "min_stage": 2},
            {"dir": [0.0, 0.15, 0.85], "radius": 0.56, "min_stage": 3},
        ],
        "stages": {
            1: "Early striatal involvement; subtle motor, cognitive, or mood changes may emerge.",
            2: "Greater striatal and connected network involvement with more evident motor and executive symptoms.",
            3: "Wider cortical and subcortical involvement with substantial functional impairment.",
        },
        "mutations": {
            "HTT CAG repeat expansion": {
                "res": "25-45",
                "dna": "Expanded CAG tract in HTT",
                "effect": "Expanded polyglutamine huntingtin can misfold and aggregate.",
            },
            "Huntingtin N-terminal region": {
                "res": "13-17",
                "dna": "N-terminal huntingtin region",
                "effect": "Illustrative locus in the N-terminal region associated with altered aggregation behavior.",
            },
        },
    },
    "Familial Alzheimer's Disease": {
        "wt_pdb_id": "1IYT",
        "wt_protein": "Reference Amyloid-beta Peptide",
        "stage_foci": [
            {"dir": [0.55, -0.55, 0.45], "radius": 0.54, "min_stage": 2},
            {"dir": [-0.55, -0.55, 0.45], "radius": 0.54, "min_stage": 2},
            {"dir": [0.0, 0.75, 0.45], "radius": 0.62, "min_stage": 3},
        ],
        "stages": {
            1: "Early medial temporal and memory-network involvement.",
            2: "Spread through limbic and association networks with increasing cognitive symptoms.",
            3: "Widespread cortical involvement and substantial loss of independence.",
        },
        "mutations": {
            "APP Arctic variant (E22G)": {
                "res": "22",
                "dna": "APP E693G (Aβ E22G)",
                "effect": "An amyloid-beta variant associated with altered aggregation propensity.",
            },
            "APP Iowa variant (D23N)": {
                "res": "23",
                "dna": "APP D694N (Aβ D23N)",
                "effect": "An amyloid-beta variant associated with altered fibril formation.",
            },
            "Amyloid-beta C-terminal region": {
                "res": "31-40",
                "dna": "Amyloid processing region",
                "effect": "Illustrative peptide region; this is not a patient-specific sequence variant.",
            },
        },
    },
    "Familial Parkinson's Disease": {
        "wt_pdb_id": "2KKW",
        "wt_protein": "Reference Alpha-synuclein",
        "stage_foci": [
            {"dir": [0.35, 0.20, 0.15], "radius": 0.52, "min_stage": 2},
            {"dir": [-0.35, 0.20, 0.15], "radius": 0.52, "min_stage": 2},
            {"dir": [0.0, 0.55, 0.65], "radius": 0.58, "min_stage": 3},
        ],
        "stages": {
            1: "Early brainstem or olfactory-network involvement in some staging models.",
            2: "Substantia nigra and midbrain involvement with motor symptoms.",
            3: "Broader cortical and connected-network involvement in advanced disease.",
        },
        "mutations": {
            "SNCA A53T variant": {
                "res": "53",
                "dna": "SNCA c.157G>A",
                "effect": "A pathogenic alpha-synuclein variant associated with familial Parkinson's disease.",
            },
            "SNCA E46K variant": {
                "res": "46",
                "dna": "SNCA c.136G>A",
                "effect": "A pathogenic alpha-synuclein variant associated with altered aggregation.",
            },
            "SNCA A30P variant": {
                "res": "30",
                "dna": "SNCA c.88G>C",
                "effect": "A pathogenic alpha-synuclein variant associated with altered membrane interaction.",
            },
        },
    },
    "Familial Amyotrophic Lateral Sclerosis (ALS)": {
        "wt_pdb_id": "1SPD",
        "wt_protein": "Reference Cu/Zn Superoxide Dismutase",
        "stage_foci": [
            {"dir": [0.0, -0.35, -0.85], "radius": 0.50, "min_stage": 2},
            {"dir": [0.0, 0.55, 0.65], "radius": 0.56, "min_stage": 3},
        ],
        "stages": {
            1: "Early focal motor-neuron involvement with weakness or cramps.",
            2: "Progression across motor pathways, potentially involving bulbar function.",
            3: "Widespread motor-system impairment, including respiratory pathways.",
        },
        "mutations": {
            "SOD1 A4V variant": {
                "res": "4",
                "dna": "SOD1 c.14C>T",
                "effect": "A SOD1 variant associated with familial ALS and protein instability.",
            },
            "SOD1 G93A variant": {
                "res": "93",
                "dna": "SOD1 c.281G>C",
                "effect": "A commonly studied SOD1 variant associated with altered protein folding.",
            },
            "SOD1 H46R variant": {
                "res": "46",
                "dna": "SOD1 c.137A>G",
                "effect": "A variant affecting a copper-binding residue in SOD1.",
            },
        },
    },
    "Genetic Frontotemporal Dementia (FTD)": {
        "wt_pdb_id": "2MZ7",
        "wt_protein": "Reference Tau Structure",
        "stage_foci": [
            {"dir": [0.75, 0.25, -0.25], "radius": 0.52, "min_stage": 2},
            {"dir": [-0.75, 0.25, -0.25], "radius": 0.52, "min_stage": 2},
            {"dir": [0.0, 0.30, 0.75], "radius": 0.56, "min_stage": 3},
        ],
        "stages": {
            1: "Early frontal or anterior temporal network involvement.",
            2: "Progressive involvement of frontal and temporal association networks.",
            3: "Broader cortical and subcortical network involvement.",
        },
        "mutations": {
            "MAPT P301L variant": {
                "res": "301",
                "dna": "MAPT c.902C>T",
                "effect": "A tau variant associated with inherited frontotemporal degeneration.",
            },
            "MAPT V337M variant": {
                "res": "337",
                "dna": "MAPT c.1009G>A",
                "effect": "A tau variant associated with familial frontotemporal dementia.",
            },
        },
    },
    "Genetic Prion Diseases (e.g., Familial CJD, FFI)": {
        "wt_pdb_id": "1QM0",
        "wt_protein": "Cellular Prion Protein Reference",
        "stage_foci": [
            {"dir": [0.40, 0.10, 0.65], "radius": 0.52, "min_stage": 2},
            {"dir": [-0.40, 0.10, 0.65], "radius": 0.52, "min_stage": 2},
            {"dir": [0.0, 0.65, 0.45], "radius": 0.60, "min_stage": 3},
        ],
        "stages": {
            1: "Early syndrome-dependent involvement, which may include thalamic or cerebellar features.",
            2: "Progressive spread of prion-associated pathology through connected neural systems.",
            3: "Widespread neurological impairment in advanced disease.",
        },
        "mutations": {
            "PRNP E200K variant": {
                "res": "200",
                "dna": "PRNP c.598G>A",
                "effect": "A pathogenic prion-protein variant associated with familial CJD.",
            },
            "PRNP D178N variant": {
                "res": "178",
                "dna": "PRNP c.532G>A",
                "effect": "A pathogenic variant associated with fatal familial insomnia in a specific genetic context.",
            },
            "PRNP P102L variant": {
                "res": "102",
                "dna": "PRNP c.305C>T",
                "effect": "A pathogenic variant associated with Gerstmann-Sträussler-Scheinker disease.",
            },
        },
    },
    "Spinocerebellar Ataxias (SCAs)": {
        "wt_pdb_id": "1WG3",
        "wt_protein": "Reference Ataxin Domain Structure",
        "stage_foci": [
            {"dir": [0.40, -0.75, -0.45], "radius": 0.50, "min_stage": 2},
            {"dir": [-0.40, -0.75, -0.45], "radius": 0.50, "min_stage": 2},
            {"dir": [0.0, -0.40, -0.85], "radius": 0.54, "min_stage": 3},
        ],
        "stages": {
            1: "Early cerebellar dysfunction with balance or eye-movement symptoms.",
            2: "Progressive cerebellar involvement with gait, coordination, or speech difficulties.",
            3: "Advanced cerebellar and brainstem involvement with substantial mobility impairment.",
        },
        "mutations": {
            "ATXN1 polyglutamine expansion": {
                "res": "570-590",
                "dna": "Expanded CAG tract in ATXN1",
                "effect": "Expanded polyglutamine ataxin-1 is associated with altered protein behavior.",
            },
            "Ataxin domain region": {
                "res": "615-625",
                "dna": "Ataxin domain region",
                "effect": "Illustrative domain region; it is not a specific patient variant.",
            },
        },
    },
    "Familial Cerebral Amyloid Angiopathy (CAA)": {
        "wt_pdb_id": "3GAX",
        "wt_protein": "Reference Cystatin C Structure",
        "stage_foci": [
            {"dir": [-0.45, -0.45, 0.70], "radius": 0.52, "min_stage": 2},
            {"dir": [0.0, -0.75, 0.45], "radius": 0.58, "min_stage": 3},
        ],
        "stages": {
            1: "Early vascular amyloid deposition, which may be clinically silent.",
            2: "Increasing vessel-wall involvement and possible transient neurological symptoms.",
            3: "Advanced vessel fragility with risk of intracerebral hemorrhage.",
        },
        "mutations": {
            "CST3 L68Q variant": {
                "res": "68",
                "dna": "CST3 p.Leu68Gln",
                "effect": "A cystatin C variant associated with hereditary cerebral amyloid angiopathy.",
            },
            "Cystatin C domain-swapping region": {
                "res": "55-59",
                "dna": "Cystatin C structural region",
                "effect": "Illustrative structural region; it is not a specific patient variant.",
            },
        },
    },
}

for condition, features in DISEASE_FEATURES.items():
    DISEASE_DATA[condition].update(features)
    DISEASE_DATA[condition]["foci"].extend(features.get("stage_foci", []))

CAMERA_PRESETS = {
    "Auto (Pathology Focus)": None,
    "Anterior (Front)": {"x": 0.0, "y": 1.85, "z": 0.15},
    "Lateral (Side)": {"x": 1.85, "y": 0.0, "z": 0.15},
    "Superior (Top)": {"x": 0.0, "y": 0.15, "z": 1.95},
    "Posterior (Back)": {"x": 0.0, "y": -1.85, "z": 0.15},
}


def format_gene_links(gene_text: str) -> str:
    if "Wild-Type" in gene_text or "Standard Human DNA" in gene_text:
        return escape(gene_text)
    tokens = [token.strip() for token in gene_text.split(",")]
    links = []
    for token in tokens:
        if token.lower() == "etc.":
            links.append(escape(token))
            continue
        url = (
            "https://www.ncbi.nlm.nih.gov/gene/?term="
            + quote(f"{token}[sym] AND human[orgn]")
        )
        links.append(
            f"<a class='clinical-link' href='{url}' target='_blank' "
            f"rel='noopener noreferrer'>{escape(token)} ↗</a>"
        )
    return ", ".join(links)


def format_pdb_link(pdb_id: str) -> str:
    return (
        f"<a class='clinical-link pdb-badge' href='https://www.rcsb.org/structure/"
        f"{quote(pdb_id)}' target='_blank' rel='noopener noreferrer'>"
        f"PDB ID: {escape(pdb_id)} ↗</a>"
    )


@st.cache_data(show_spinner=False)
def load_mesh(mesh_directory: str) -> tuple[np.ndarray, np.ndarray]:
    """Load, triangulate, and normalize an OBJ mesh from disk or a ZIP archive."""
    obj_path = Path(mesh_directory) / "brain_mesh.obj"
    zip_path = Path(mesh_directory) / "brain_mesh.zip"
    vertices = []
    triangles = []

    def parse_obj_lines(lines, source: str) -> None:
        for line_number, line in enumerate(lines, start=1):
            fields = line.split()
            if not fields or fields[0].startswith("#"):
                continue
            if fields[0] == "v":
                if len(fields) < 4:
                    raise ValueError(f"Invalid vertex at line {line_number} in {source}")
                vertices.append([float(value) for value in fields[1:4]])
            elif fields[0] == "f":
                if len(fields) < 4:
                    raise ValueError(f"Invalid face at line {line_number} in {source}")
                face = []
                for field in fields[1:]:
                    vertex_index = int(field.split("/", 1)[0])
                    face.append(
                        vertex_index - 1
                        if vertex_index > 0
                        else len(vertices) + vertex_index
                    )
                for index in range(1, len(face) - 1):
                    triangles.append([face[0], face[index], face[index + 1]])

    if obj_path.is_file():
        with obj_path.open(encoding="utf-8") as obj_file:
            parse_obj_lines(obj_file, str(obj_path))
        source = str(obj_path)
    elif zip_path.is_file():
        with zipfile.ZipFile(zip_path) as archive:
            obj_files = sorted(
                name
                for name in archive.namelist()
                if name.lower().endswith(".obj") and "__macosx/" not in name.lower()
            )
            if not obj_files:
                raise FileNotFoundError(
                    f"Found `{zip_path}`, but it contains no usable OBJ mesh."
                )
            obj_name = next(
                (name for name in obj_files if Path(name).name == "brain_mesh.obj"),
                obj_files[0],
            )
            with archive.open(obj_name) as obj_file:
                parse_obj_lines(
                    (line.decode("utf-8") for line in obj_file),
                    f"{zip_path}:{obj_name}",
                )
        source = f"{zip_path}:{obj_name}"
    else:
        raise FileNotFoundError(
            f"Could not find `brain_mesh.obj` or `brain_mesh.zip` in `{mesh_directory}`."
        )

    if not vertices or not triangles:
        raise ValueError(f"No usable vertices or faces found in {source}")

    vertex_array = np.asarray(vertices, dtype=np.float32)
    triangle_array = np.asarray(triangles, dtype=np.int32)
    if not np.isfinite(vertex_array).all():
        raise ValueError(f"Non-finite vertex coordinate in {source}")
    if triangle_array.min() < 0 or triangle_array.max() >= len(vertex_array):
        raise ValueError(f"Face index outside the vertex range in {source}")
    bounds_min = vertex_array.min(axis=0)
    bounds_max = vertex_array.max(axis=0)
    center = (bounds_min + bounds_max) / 2
    scale = np.max(bounds_max - bounds_min) / 2
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError(f"Cannot normalize degenerate OBJ mesh in {source}")
    normalized_vertices = (vertex_array - center) / scale
    return normalized_vertices, triangle_array


def render_molecule_viewer(
    pdb_id, color_hex, height=450, viewer_id="mol-main", highlight_res=None
):
    residue_selector = ""
    mapping_note = ""
    viewer_height = height + 15
    if highlight_res is not None:
        residue_parts = highlight_res.split("-", 1)
        if not all(part.isdigit() for part in residue_parts):
            raise ValueError(f"Invalid residue selector: {highlight_res}")
        start = int(residue_parts[0])
        end = int(residue_parts[-1])
        if start < 1 or end < start or end - start > 1000:
            raise ValueError(f"Invalid residue range: {highlight_res}")
        residues = json.dumps(list(range(start, end + 1)))
        mapping_context = (
            "core "
            if pdb_id.upper() == "5O3L" and start <= 301 <= end
            else ""
        )
        mapping_note = (
            f"""
    <div id="{viewer_id}-mapping-note" style="min-height: 16px; margin: 3px 6px 0; color: #475569; font: 12px Arial, sans-serif;"></div>
    """
        )
        viewer_height = height + 35
        residue_selector = f"""
            const requestedResidues = {residues};
            const resolvedResidues = Array.from(new Set(
                viewer.selectedAtoms({{}})
                    .map(atom => Number(atom.resi))
                    .filter(Number.isInteger)
            ));
            const resolvedSet = new Set(resolvedResidues);
            let markerResidues = requestedResidues.filter(
                residue => resolvedSet.has(residue)
            );
            if (markerResidues.length === 0 && resolvedResidues.length > 0) {{
                const targetResidue = requestedResidues.reduce(
                    (total, residue) => total + residue, 0
                ) / requestedResidues.length;
                const nearestResidue = resolvedResidues.reduce(
                    (nearest, residue) =>
                        Math.abs(residue - targetResidue) <
                        Math.abs(nearest - targetResidue) ? residue : nearest,
                    resolvedResidues[0]
                );
                markerResidues = [nearestResidue];
                document.getElementById("{viewer_id}-mapping-note").textContent =
                    "(mapped to nearest resolved {mapping_context}residue " +
                    nearestResidue + ")";
            }} else if (markerResidues.length === 0) {{
                document.getElementById("{viewer_id}-mapping-note").textContent =
                    "(no resolved residues are available for this structure)";
            }}
            if (markerResidues.length > 0) {{
                viewer.addStyle({{resi: markerResidues}}, {{
                    sphere: {{color: "#FFD700", radius: 1.45}},
                    stick: {{color: "#FF003C", radius: 0.35}}
                }});
            }}
        """
    html_code = f"""
    <div id="{viewer_id}" class="protein-viewer-frame" style="height: {height}px; width: 99%; box-sizing: border-box; position: relative; border-top: 3px solid {color_hex}; border-radius: 12px; border-right: 1px solid #E2E8F0; border-bottom: 1px solid #E2E8F0; border-left: 1px solid #E2E8F0; background-color: #F8FAFC;"></div>
    {mapping_note}
    <script>
        function initializeMoleculeViewer() {{
            const element = document.getElementById('{viewer_id}');
            if (!element || !window.$3Dmol) {{
                return;
            }}
            const viewer = $3Dmol.createViewer(
                element, {{ backgroundColor: '#F8FAFC' }}
            );
            $3Dmol.download("pdb:{pdb_id}", viewer, {{}}, function() {{
                viewer.setStyle({{}}, {{cartoon: {{color: 'spectrum'}}}});
                {residue_selector}
                window.requestAnimationFrame(function() {{
                    viewer.zoomTo();
                    viewer.zoom(1.35);
                    viewer.render();
                }});
            }});
        }}
    </script>
    <script async src="https://3Dmol.org/build/3Dmol-min.js" onload="initializeMoleculeViewer()"></script>
    """
    components.html(html_code, height=viewer_height)


def build_anatomical_structure_mesh(
    structure_name: str,
    bounds: np.ndarray,
    color: str,
    opacity: float = 0.95,
    scale: float = 1.0,
    stage: int = 1,
) -> go.Mesh3d:
    """Build an illustrative, closed internal structure mesh within OBJ bounds."""
    bounds = np.asarray(bounds, dtype=float)
    if bounds.shape != (2, 3) or not np.isfinite(bounds).all():
        raise ValueError("Structure bounds must be a finite array with shape (2, 3).")
    spans = bounds[1] - bounds[0]
    if np.any(spans <= 0):
        raise ValueError("Structure bounds must have positive spans on all axes.")
    if not 0.0 < scale <= 1.5:
        raise ValueError(f"Invalid anatomical structure scale: {scale}")
    if not 0.0 < opacity <= 1.0:
        raise ValueError(f"Invalid anatomical structure opacity: {opacity}")

    center = (bounds[0] + bounds[1]) / 2.0
    half_spans = spans / 2.0
    structure_vertices: list[np.ndarray] = []
    structure_faces: list[np.ndarray] = []
    structure_key = structure_name.lower()
    deep_structures = {
        "hippocampus",
        "striatum",
        "thalamus",
        "substantia_nigra_brainstem",
    }
    is_deep_structure = structure_key in deep_structures
    if is_deep_structure:
        scale *= 0.55

    def to_mesh_space(local_vertices: np.ndarray) -> np.ndarray:
        bounded_vertices = (
            np.clip(local_vertices, -0.599, 0.599)
            if is_deep_structure
            else local_vertices
        )
        mapped = bounded_vertices * half_spans
        return mapped + center

    def append_ellipsoid(
        local_center: tuple[float, float, float],
        radii: tuple[float, float, float],
    ) -> None:
        latitude_count = 18
        longitude_count = 32
        latitudes = np.linspace(
            -np.pi / 2, np.pi / 2, latitude_count
        )[1:-1]
        longitudes = np.linspace(
            0, 2 * np.pi, longitude_count, endpoint=False
        )
        cx, cy, cz = local_center
        rx, ry, rz = (radius * scale for radius in radii)
        rings = np.asarray(
            [
                [
                    (
                        cx + rx * np.cos(latitude) * np.cos(longitude),
                        cy + ry * np.cos(latitude) * np.sin(longitude),
                        cz + rz * np.sin(latitude),
                    )
                    for longitude in longitudes
                ]
                for latitude in latitudes
            ],
            dtype=float,
        )
        local_vertices = np.vstack(
            (
                np.asarray([[cx, cy, cz - rz]]),
                rings.reshape(-1, 3),
                np.asarray([[cx, cy, cz + rz]]),
            )
        )
        offset = sum(len(part) for part in structure_vertices)
        ring_start = offset + 1
        south_pole = offset
        north_pole = offset + len(local_vertices) - 1
        faces = []

        for column in range(longitude_count):
            next_column = (column + 1) % longitude_count
            faces.append(
                [south_pole, ring_start + next_column, ring_start + column]
            )

        for row in range(len(latitudes) - 1):
            current_start = ring_start + row * longitude_count
            next_start = current_start + longitude_count
            for column in range(longitude_count):
                next_column = (column + 1) % longitude_count
                a = current_start + column
                b = current_start + next_column
                c = next_start + column
                d = next_start + next_column
                faces.extend(([a, b, c], [b, d, c]))

        last_ring_start = ring_start + (len(latitudes) - 1) * longitude_count
        for column in range(longitude_count):
            next_column = (column + 1) % longitude_count
            faces.append(
                [north_pole, last_ring_start + column, last_ring_start + next_column]
            )

        structure_vertices.append(to_mesh_space(local_vertices))
        structure_faces.append(np.asarray(faces, dtype=np.int32))

    def append_tube(
        path: tuple[tuple[float, float, float], ...],
        radius: float,
    ) -> None:
        control_points = np.asarray(path, dtype=float)
        if (
            control_points.ndim != 2
            or control_points.shape[1] != 3
            or len(control_points) < 2
            or not np.isfinite(control_points).all()
        ):
            raise ValueError("Anatomical tube paths must contain at least two 3D points.")
        points = []
        samples_per_segment = 8
        for index in range(len(control_points) - 1):
            p0 = control_points[max(index - 1, 0)]
            p1 = control_points[index]
            p2 = control_points[index + 1]
            p3 = control_points[min(index + 2, len(control_points) - 1)]
            for t in np.linspace(0.0, 1.0, samples_per_segment, endpoint=False):
                points.append(
                    0.5
                    * (
                        2 * p1
                        + (-p0 + p2) * t
                        + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t**2
                        + (-p0 + 3 * p1 - 3 * p2 + p3) * t**3
                    )
                )
        points.append(control_points[-1])
        points = np.asarray(points, dtype=float)
        tangents = np.gradient(points, axis=0)
        ring_count = 16
        angles = np.linspace(0, 2 * np.pi, ring_count, endpoint=False)
        rings = []
        for point, tangent in zip(points, tangents):
            tangent_norm = np.linalg.norm(tangent)
            if tangent_norm == 0:
                raise ValueError("Anatomical tube path contains a zero-length tangent.")
            tangent = tangent / tangent_norm
            reference = np.asarray(
                [0.0, 0.0, 1.0]
                if abs(tangent[2]) < 0.85
                else [0.0, 1.0, 0.0]
            )
            normal = np.cross(tangent, reference)
            normal /= np.linalg.norm(normal)
            binormal = np.cross(tangent, normal)
            rings.append(
                [
                    point
                    + scale
                    * radius
                    * (np.cos(angle) * normal + np.sin(angle) * binormal)
                    for angle in angles
                ]
            )
        ring_vertices = np.asarray(rings, dtype=float).reshape(-1, 3)
        local_vertices = np.vstack((ring_vertices, points[0], points[-1]))
        offset = sum(len(part) for part in structure_vertices)
        faces = []
        for row in range(len(points) - 1):
            current_start = offset + row * ring_count
            next_start = current_start + ring_count
            for column in range(ring_count):
                next_column = (column + 1) % ring_count
                a = current_start + column
                b = current_start + next_column
                c = next_start + column
                d = next_start + next_column
                faces.extend(([a, b, c], [b, d, c]))
        start_cap = offset + len(ring_vertices)
        end_cap = start_cap + 1
        last_ring_start = offset + (len(points) - 1) * ring_count
        for column in range(ring_count):
            next_column = (column + 1) % ring_count
            faces.append([start_cap, offset + next_column, offset + column])
            faces.append(
                [
                    end_cap,
                    last_ring_start + column,
                    last_ring_start + next_column,
                ]
            )
        structure_vertices.append(to_mesh_space(local_vertices))
        structure_faces.append(np.asarray(faces, dtype=np.int32))

    if structure_key == "hippocampus":
        for side in (-1, 1):
            append_tube(
                (
                    (side * 0.22, 0.08, -0.27),
                    (side * 0.29, -0.02, -0.37),
                    (side * 0.28, -0.16, -0.45),
                    (side * 0.20, -0.28, -0.40),
                ),
                0.045,
            )
    elif structure_key == "striatum":
        for side in (-1, 1):
            append_tube(
                (
                    (side * 0.18, 0.36, 0.10),
                    (side * 0.26, 0.28, 0.18),
                    (side * 0.31, 0.15, 0.12),
                    (side * 0.31, 0.02, 0.00),
                    (side * 0.27, -0.10, -0.12),
                ),
                0.050,
            )
            append_ellipsoid(
                (side * 0.43, 0.02, -0.06),
                (0.14, 0.18, 0.17),
            )
    elif structure_key == "thalamus":
        for side in (-1, 1):
            append_ellipsoid(
                (side * 0.13, -0.04, -0.12),
                (0.12, 0.15, 0.16),
            )
    elif structure_key == "substantia_nigra_brainstem":
        append_tube(
            (
                (0.0, -0.10, -0.12),
                (0.0, -0.10, -0.30),
                (0.0, -0.14, -0.50),
                (0.0, -0.19, -0.53),
            ),
            0.085,
        )
        for side in (-1, 1):
            append_ellipsoid(
                (side * 0.095, -0.02, -0.35),
                (0.075, 0.10, 0.075),
            )
    elif structure_key == "insular_frontostriatal":
        for side in (-1, 1):
            append_ellipsoid(
                (side * 0.40, 0.08, -0.02),
                (0.13, 0.18, 0.17),
            )
            append_tube(
                (
                    (side * 0.22, 0.24, 0.10),
                    (side * 0.31, 0.17, 0.06),
                    (side * 0.40, 0.08, -0.02),
                ),
                0.035,
            )
    else:
        raise ValueError(f"Unknown anatomical structure: {structure_name}")

    all_vertices = np.concatenate(structure_vertices, axis=0)
    all_faces = np.concatenate(structure_faces, axis=0)
    display_names = {
        "substantia_nigra_brainstem": "Substantia Nigra & Brainstem",
        "insular_frontostriatal": "Insular & Frontostriatal Zones",
    }
    clean_name = display_names.get(
        structure_key, structure_key.replace("_", " ").title()
    )
    role_text = functional_role_for_name(clean_name)
    return go.Mesh3d(
        x=all_vertices[:, 0],
        y=all_vertices[:, 1],
        z=all_vertices[:, 2],
        i=all_faces[:, 0],
        j=all_faces[:, 1],
        k=all_faces[:, 2],
        color=color,
        opacity=opacity,
        flatshading=False,
        lighting={"ambient": 0.55, "diffuse": 0.8, "specular": 0.4, "roughness": 0.25},
        name=clean_name,
        hovertemplate=f"<b>{clean_name}</b><br>Stage {stage} Localization<br>{role_text}<extra></extra>",
        showlegend=False,
    )


def compute_anatomical_pathology_mask(
    vertices: np.ndarray,
    disorder_key: str,
    stage_label: str,
) -> np.ndarray:
    """Return smooth bilateral cortical-lobe selections for a disease stage."""
    points = np.asarray(vertices, dtype=float)
    if points.ndim != 2 or points.shape[1] != 3 or len(points) == 0:
        raise ValueError("Brain vertices must be a non-empty array with shape (n, 3).")
    if not np.isfinite(points).all():
        raise ValueError("Brain vertices must contain only finite coordinates.")

    minima = points.min(axis=0)
    spans = np.where(points.max(axis=0) == minima, 1.0, points.max(axis=0) - minima)
    normalized = 2.0 * (points - minima) / spans - 1.0
    xn, yn, zn = normalized.T
    ax = np.abs(xn - np.median(xn))
    anterior_y = yn
    empty = np.zeros(len(points), dtype=bool)

    text_key = disorder_key.lower()
    stage_text = stage_label.lower()
    if any(token in text_key for token in ("healthy", "control", "equilibrium")):
        return empty
    if any(token in stage_text for token in ("stage 3", "advanced", "late")):
        stage = 3
    elif any(token in stage_text for token in ("stage 2", "intermediate", "moderate")):
        stage = 2
    else:
        stage = 1

    def lobe(
        x_center: float,
        y_center: float,
        z_center: float,
        radius_x: float,
        radius_y: float,
        radius_z: float,
    ) -> np.ndarray:
        return (
            ((ax - x_center) / radius_x) ** 2
            + ((anterior_y - y_center) / radius_y) ** 2
            + ((zn - z_center) / radius_z) ** 2
        ) <= 1.0

    frontal = lobe(0.52, 0.46, 0.26, 0.53, 0.55, 0.78)
    temporal = lobe(0.54, 0.00, -0.24, 0.49, 0.50, 0.50)
    parietal = lobe(0.51, -0.36, 0.30, 0.50, 0.45, 0.63)
    occipital = lobe(0.43, -0.70, 0.16, 0.46, 0.32, 0.53)
    motor = lobe(0.51, 0.08, 0.70, 0.40, 0.24, 0.34)
    premotor = lobe(0.51, 0.34, 0.58, 0.43, 0.32, 0.42)
    cerebellar_surface = lobe(0.43, -0.60, -0.57, 0.48, 0.34, 0.34)
    cerebellar_stage1 = lobe(0.43, -0.60, -0.57, 0.36, 0.25, 0.25)
    brainstem_surface = lobe(0.12, -0.12, -0.74, 0.24, 0.32, 0.34)
    brainstem_stage2 = lobe(0.12, -0.12, -0.74, 0.18, 0.24, 0.25)

    if any(token in text_key for token in ("angiopathy", "caa", "vascular", "cystatin")):
        lobar_surface = zn > -0.35
        anterior_limit = (-0.65, -0.18, 0.52)[stage - 1]
        return lobar_surface & (anterior_y < anterior_limit)
    if any(token in text_key for token in ("frontotemporal", "ftd", "pick", "mapt")):
        anterior_temporal = lobe(
            0.54, 0.08, -0.24, 0.49, 0.39, 0.50
        ) & (anterior_y > -0.22)
        return frontal | anterior_temporal
    if any(token in text_key for token in ("alzheimer", "hippocamp", "entorhinal")):
        if stage == 1:
            return empty
        if stage == 2:
            return temporal | parietal
        return temporal | parietal | frontal
    if any(token in text_key for token in ("prion", "prnp", "cjd", "ffi")):
        hindbrain_surface = cerebellar_surface | brainstem_surface
        if stage == 1:
            return hindbrain_surface
        if stage == 2:
            return hindbrain_surface | occipital | parietal
        return hindbrain_surface | frontal | temporal | parietal | occipital
    if any(token in text_key for token in ("parkinson", "lewy", "synuclein", "substantia", "nigra")):
        if stage < 3:
            return empty
        return frontal | motor
    if any(token in text_key for token in ("als", "amyotrophic", "sod1", "tdp-43", "fusz")):
        if stage < 3:
            return motor
        return motor | premotor
    if any(token in text_key for token in ("huntington", "striat", "caudate", "putamen", "basal ganglia", "htt")):
        if stage < 3:
            return empty
        return frontal | parietal
    if any(token in text_key for token in ("ataxia", "cerebell", "sca", "purkinje")):
        if stage == 1:
            return cerebellar_stage1
        if stage == 2:
            return cerebellar_surface | brainstem_stage2
        return cerebellar_surface | brainstem_surface
    return empty


def anatomical_structures_for_condition(
    disorder_key: str, stage: int
) -> list[tuple[str, float]]:
    """Return internal structure meshes and progression scales for a condition."""
    key = disorder_key.lower()
    if any(token in key for token in ("healthy", "control", "equilibrium")):
        return []
    if any(token in key for token in ("huntington", "striat", "caudate", "putamen", "basal ganglia", "htt")):
        structures = [("striatum", (0.74, 0.88, 1.0)[stage - 1])]
        if stage >= 2:
            structures.append(
                ("insular_frontostriatal", (0.72, 0.88)[stage - 2])
            )
        return structures
    if any(token in key for token in ("parkinson", "lewy", "synuclein", "substantia", "nigra")):
        structures = [
            ("substantia_nigra_brainstem", (0.70, 0.88, 1.0)[stage - 1])
        ]
        if stage >= 2:
            structures.append(("striatum", (0.70, 0.92)[stage - 2]))
        return structures
    if any(token in key for token in ("alzheimer", "hippocamp", "entorhinal")):
        return [("hippocampus", (0.72, 0.88, 1.0)[stage - 1])]
    if any(token in key for token in ("prion", "prnp", "cjd", "ffi")):
        scale = (0.72, 0.88, 1.0)[stage - 1]
        return [("thalamus", scale)]
    if any(token in key for token in ("ataxia", "cerebell", "sca", "purkinje")):
        return []
    if any(token in key for token in ("als", "amyotrophic", "sod1", "tdp-43", "fusz")):
        if stage >= 2:
            return [("substantia_nigra_brainstem", (0.72, 0.90)[stage - 2])]
        return []
    if any(token in key for token in ("frontotemporal", "ftd", "pick", "mapt")):
        if stage == 3:
            return [("striatum", 0.78)]
    return []


@st.cache_data(show_spinner=False)
def retain_largest_face_components(
    faces: np.ndarray,
    face_mask: np.ndarray,
    vertex_count: int,
    component_count: int = 2,
) -> np.ndarray:
    """Keep the largest connected patches in a selected surface-face mask."""
    selected_face_indices = np.flatnonzero(face_mask)
    if len(selected_face_indices) == 0:
        return face_mask.copy()

    parent = np.arange(vertex_count, dtype=np.int32)
    component_size = np.ones(vertex_count, dtype=np.int32)

    def find(vertex_index: int) -> int:
        while parent[vertex_index] != vertex_index:
            parent[vertex_index] = parent[parent[vertex_index]]
            vertex_index = int(parent[vertex_index])
        return vertex_index

    def union(first_vertex: int, second_vertex: int) -> None:
        first_root = find(first_vertex)
        second_root = find(second_vertex)
        if first_root == second_root:
            return
        if component_size[first_root] < component_size[second_root]:
            first_root, second_root = second_root, first_root
        parent[second_root] = first_root
        component_size[first_root] += component_size[second_root]

    selected_faces = faces[selected_face_indices]
    for first_vertex, second_vertex, third_vertex in selected_faces:
        union(int(first_vertex), int(second_vertex))
        union(int(second_vertex), int(third_vertex))

    face_roots = np.fromiter(
        (find(int(face[0])) for face in selected_faces),
        dtype=np.int32,
        count=len(selected_faces),
    )
    roots, face_counts = np.unique(face_roots, return_counts=True)
    largest_roots = roots[np.argsort(face_counts)[-component_count:]]

    filtered_mask = np.zeros_like(face_mask, dtype=bool)
    filtered_mask[selected_face_indices] = np.isin(face_roots, largest_roots)
    return filtered_mask


def build_brain_figure(
    vertices: np.ndarray,
    faces: np.ndarray,
    condition_info: dict,
    camera_override: Optional[dict] = None,
    height: int = 450,
    uirevision: str = "brain",
    stage: int = 2,
    *,
    disorder_key: str,
    stage_label: str,
) -> go.Figure:
    x, y, z = vertices.T

    if stage not in (1, 2, 3):
        raise ValueError(f"Invalid disease stage: {stage}")
    pathology_vertices = compute_anatomical_pathology_mask(
        vertices, disorder_key, stage_label
    )
    highlighted = np.all(pathology_vertices[faces], axis=1)
    condition_key = disorder_key.lower()
    if any(
        token in condition_key
        for token in ("angiopathy", "caa", "vascular", "cystatin")
    ):
        component_count = 4
    elif any(
        token in condition_key
        for token in (
            "prion",
            "prnp",
            "cjd",
            "ffi",
            "ataxia",
            "cerebell",
            "sca",
            "purkinje",
        )
    ):
        component_count = 6
    else:
        component_count = 2
    highlighted = retain_largest_face_components(
        faces, highlighted, len(vertices), component_count=component_count
    )
    target_faces = faces[highlighted]
    bounds = np.vstack((vertices.min(axis=0), vertices.max(axis=0)))
    internal_traces = [
        build_anatomical_structure_mesh(
            structure_name,
            bounds,
            condition_info["hex"],
            opacity=0.95,
            scale=scale,
            stage=stage,
        )
        for structure_name, scale in anatomical_structures_for_condition(
            disorder_key, stage
        )
    ]
    is_als_condition = any(
        token in condition_key
        for token in ("amyotrophic", "familial als", "(als)")
    )
    for trace in internal_traces:
        if is_als_condition and trace.name == "Substantia Nigra & Brainstem":
            trace.name = "Corticospinal Tract & Brainstem"
            role_text = functional_role_for_name(trace.name)
            trace.hovertemplate = f"<b>{trace.name}</b><br>Stage {stage} Localization<br>{role_text}<extra></extra>"

    primary_focus = next(
        (focus for focus in condition_info["foci"] if focus.get("primary")), None
    )
    target_label = (
        primary_focus["label"]
        if primary_focus is not None
        else condition_info["short_region"]
    )
    default_eye = condition_info.get("camera_eye", {"x": 1.45, "y": 1.45, "z": 1.05})
    camera = {
        "center": {"x": 0, "y": 0, "z": 0},
        "eye": camera_override or default_eye,
        "up": {"x": 0, "y": 0, "z": 1},
    }

    light_position = {"x": 120, "y": 180, "z": 160}
    traces = [
        go.Mesh3d(
            x=x, y=y, z=z,
            i=faces[:, 0], j=faces[:, 1], k=faces[:, 2],
            color="#CBD5E1", opacity=0.20, flatshading=False,
            lighting={"ambient": 0.6, "diffuse": 0.5, "specular": 0.1},
            lightposition=light_position,
            hoverinfo="skip", name="Glass Cortex",
        )
    ]
    if len(target_faces):
        cortical_role = functional_role_for_name(target_label)
        traces.append(
            go.Mesh3d(
                x=x, y=y, z=z,
                i=target_faces[:, 0], j=target_faces[:, 1], k=target_faces[:, 2],
                color=condition_info["hex"], opacity=0.90, flatshading=False,
                lighting={
                    "ambient": 0.65,
                    "diffuse": 0.75,
                    "specular": 0.3,
                    "roughness": 0.15,
                    "fresnel": 0.25,
                },
                lightposition=light_position,
                name="Cortical Pathology",
                hovertemplate=f"<b>{target_label}</b><br>Stage {stage} Localization<br>{cortical_role}<extra></extra>",
            )
        )
    traces.extend(internal_traces)

    figure = go.Figure(data=traces)
    is_healthy = any(
        token in disorder_key.lower()
        for token in ("healthy", "control", "equilibrium")
    )
    badge_text = (
        f"<b>HEALTHY BASELINE:</b> {target_label.upper()}"
        if is_healthy
        else (
            f"<span style='color:{condition_info['hex']}'>●</span> "
            f"<b>ACTIVE TARGET:</b> {target_label.upper()} "
            f"· STAGE {stage}"
        )
    )
    figure.add_annotation(
        xref="paper",
        yref="paper",
        x=0.03,
        y=0.93,
        text=badge_text,
        showarrow=False,
        xanchor="left",
        yanchor="top",
        align="left",
        bgcolor="rgba(15,23,42,0.88)",
        bordercolor="rgba(255,255,255,0.18)",
        borderwidth=1,
        borderpad=8,
        font={"color": "#F8FAFC", "size": 10, "family": "Arial"},
    )
    figure.update_layout(
        uirevision=uirevision,
        scene={
            "xaxis": {"visible": False},
            "yaxis": {"visible": False},
            "zaxis": {"visible": False},
            "aspectmode": "data",
            "bgcolor": "#F8FAFC",
            "camera": camera,
        },
        hoverlabel={
            "bgcolor": "#0F172A",
            "bordercolor": "#38BDF8",
            "font": {"color": "#F8FAFC", "size": 12, "family": "Inter, Arial, sans-serif"},
        },
        paper_bgcolor="#F8FAFC",
        plot_bgcolor="#F8FAFC",
        margin={"l": 0, "r": 0, "b": 0, "t": 0},
        height=height,
        showlegend=False,
    )
    return figure


# Auto-unzip the 3D brain mesh to bypass GitHub's 25MB file limit
base_dir = os.path.dirname(os.path.abspath(__file__))
zip_path = os.path.join(base_dir, "brain_mesh.zip")
obj_path = os.path.join(base_dir, "brain_mesh.obj")

if not os.path.exists(obj_path) and os.path.exists(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(base_dir)

st.set_page_config(
    page_title="Atlas of Neurodegenerative Diseases",
    layout="wide",
    page_icon="🧬",
)

# === MODE_SWITCH_START ===
import streamlit as st
if 'active_app_module' not in st.session_state:
    st.session_state.active_app_module = 'atlas'

st.sidebar.markdown("""
<style>
    [data-testid="stSidebarNav"] { display: none !important; }
    .nav-hdr {
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
        font-size: 1.2rem !important;
        font-weight: 800 !important;
        color: #0F172A !important;
        letter-spacing: -0.02em !important;
        margin: 2px 0 2px 0 !important;
    }
    .nav-sub {
        font-family: 'Plus Jakarta Sans', 'Noto Sans Devanagari', sans-serif !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        color: #64748B !important;
        margin: 0 0 10px 0 !important;
    }
    /* Allow text wrapping and flexible height so text never overflows the button */
    section[data-testid="stSidebar"] div.stButton > button {
        width: 100% !important;
        border-radius: 14px !important;
        min-height: 52px !important;
        height: auto !important;
        padding: 0.5rem 0.6rem !important;
        font-family: 'Plus Jakarta Sans', 'Noto Sans Devanagari', sans-serif !important;
        font-size: 0.85rem !important;
        font-weight: 800 !important;
        white-space: normal !important;
        line-height: 1.3 !important;
        margin-bottom: 8px !important;
        transition: all 0.15s ease !important;
    }
    section[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25) !important;
    }
    section[data-testid="stSidebar"] div.stButton > button[kind="secondary"] {
        background: #FFFFFF !important;
        color: #0F172A !important;
        border: 1.5px solid #CBD5E1 !important;
    }
</style>
<div class="nav-hdr">Clinical Workspace</div>
<div class="nav-sub">Select Active Module:</div>
""", unsafe_allow_html=True)

if st.sidebar.button(
    "🧠 3D Clinical Atlas",
    use_container_width=True,
    type="primary" if st.session_state.active_app_module == "atlas" else "secondary",
    key="nav_btn_atlas"
):
    st.session_state.active_app_module = "atlas"
    st.rerun()

if st.sidebar.button(
    "🤝 Elder Care • बुज़ुर्गों की देखभाल",
    use_container_width=True,
    type="primary" if st.session_state.active_app_module == "elder" else "secondary",
    key="nav_btn_elder"
):
    st.session_state.active_app_module = "elder"
    st.rerun()

st.sidebar.markdown("<hr style='margin: 10px 0 16px 0; border: none; border-top: 1.5px solid #E2E8F0;'>", unsafe_allow_html=True)

if st.session_state.active_app_module != "elder":
    import os as _os, sys as _sys
    if _os.path.dirname(_os.path.abspath(__file__)) not in _sys.path:
        _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    import importlib, tracker_utils  # type: ignore
    importlib.reload(tracker_utils)
    try:
        tracker_utils.render_sidebar_tracker("atlas")
    except TypeError:
        tracker_utils.render_sidebar_tracker()
if st.session_state.active_app_module == "elder":
    exec(open("pages/2_Elder_Care_Help.py", encoding="utf-8").read(), globals())
    st.stop()
# === MODE_SWITCH_END ===






st.markdown(
    """
    <style>
        div[data-testid="stHtml"], div.stHtml, iframe {
            width: 100% !important;
            min-width: 100% !important;
            display: block !important;
            border: none !important;
        }
        .stApp {
            background: #FFFFFF;
            color: #334155;
            font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }
        .block-container {
            padding-top: 4.5rem !important;
            padding-bottom: 3rem !important;
        }
        header[data-testid="stHeader"] {
            background: rgba(255, 255, 255, 0.92);
            backdrop-filter: blur(6px);
        }
        a.clinical-link {
            color: #005EB8 !important;
            text-decoration: none;
            font-weight: 600;
            border-bottom: 1px dotted #005EB8;
        }
        a.clinical-link:hover {
            color: #002D72 !important;
            border-bottom-style: solid;
        }
        div[data-testid="stPlotlyChart"] {
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 4px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(15, 23, 42, 0.06);
        }
        .top-brand-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 12px;
            width: 100%;
            box-sizing: border-box;
            margin: 4px 0 18px;
            padding: 14px 20px;
            border: 1px solid rgba(104, 172, 229, 0.35);
            border-bottom: 3px solid #38BDF8;
            border-radius: 10px;
            background: linear-gradient(135deg, #002D72 0%, #0A192F 100%);
            color: #FFFFFF;
        }
        .top-brand-title {
            color: #FFFFFF !important;
            font-size: 0.76rem;
            font-weight: 750;
            letter-spacing: 0.11em;
        }
        .top-brand-badge {
            padding: 6px 10px;
            border: 1px solid rgba(203, 160, 82, 0.65);
            border-radius: 999px;
            background: rgba(203, 160, 82, 0.12);
            color: #F4D58D !important;
            font-size: 0.7rem;
            font-weight: 750;
            letter-spacing: 0.08em;
        }
        .hatch-divider {
            height: 0;
            margin-bottom: 22px;
            border-bottom: 1px solid #E2E8F0;
            background: none;
        }
        .main-serif-title {
            margin: 0 0 6px;
            color: #002D72 !important;
            font: 700 clamp(2rem, 4vw, 2.5rem)/1.12 "Merriweather", "Playfair Display", Georgia, serif;
            word-break: normal;
            overflow-wrap: normal;
        }
        .category-tag {
            margin-bottom: 18px;
            color: #1D4ED8 !important;
            font-size: 1.08rem;
            font-weight: 600;
        }
        .lead-explanation {
            max-width: 1050px;
            margin: 0 0 28px;
            color: #334155 !important;
            font-size: 1.02rem;
            line-height: 1.75;
        }
        .clinical-heading {
            margin-bottom: 12px;
            overflow: visible;
            color: #0F172A !important;
            font: 700 1.25rem/1.25 Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            min-height: 36px;
            display: flex;
            align-items: flex-end;
        }
        .clinical-sub {
            margin-bottom: 12px;
            overflow: visible;
            color: #475569 !important;
            font-size: 0.92rem;
            font-weight: 500;
            min-height: 28px;
            line-height: 1.35;
            display: flex;
            align-items: center;
            flex-wrap: wrap;
        }
        .clinical-card {
            height: 100%;
            padding: 18px 20px;
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-top: 3px solid #0F172A;
            border-radius: 12px;
            color: #334155;
            min-height: 320px;
            box-sizing: border-box;
            box-shadow: 0 4px 20px rgba(15, 23, 42, 0.06);
        }
        .clinical-card h4 {
            margin: 0 0 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #CBD5E1;
            color: #0F172A !important;
            font: 700 1.05rem/1.4 Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }
        .clinical-card p {
            margin-bottom: 10px;
            color: #334155 !important;
            font-size: 0.94rem;
            line-height: 1.6;
        }
        .clinical-label {
            color: #0F172A !important;
            font-weight: 700;
        }
        [data-testid="stSidebar"] {
            background: #F4F6F9 !important;
            border-right: 1px solid #E2E8F0;
        }
        .sidebar-heading {
            margin-bottom: 12px;
            color: #0F172A !important;
            font: 700 1.25rem Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }
        .sidebar-box {
            margin-bottom: 12px;
            padding: 12px 14px;
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-left: 3px solid #005EB8;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(15, 23, 42, 0.04);
        }
        .sidebar-box-title {
            color: #005EB8 !important;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.4px;
            text-transform: uppercase;
        }
        .sidebar-box-value {
            color: #334155 !important;
            font-size: 0.92rem;
            line-height: 1.45;
        }
        .stage-banner, .mutation-pill {
            margin-top: 10px;
            padding: 12px 14px;
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-left: 3px solid #2563EB;
            border-radius: 12px;
            color: #334155;
            font-size: 0.9rem;
            line-height: 1.5;
            box-shadow: 0 4px 20px rgba(15, 23, 42, 0.04);
        }
        .clinical-legend-card {
            margin-top: 10px;
            padding: 14px 16px;
            background: #FFFFFF;
            border: 1px solid #DCE5EF;
            border-top: 3px solid #68ACE5;
            border-radius: 14px;
            box-shadow: 0 4px 18px rgba(15, 23, 42, 0.05);
        }
        .clinical-legend-heading {
            margin-bottom: 10px;
            color: #002D72 !important;
            font-size: 0.82rem;
            font-weight: 800;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }
        .telemetry-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 9px;
        }
        .telemetry-item {
            min-width: 0;
            padding: 10px 11px;
            border: 1px solid #E5EAF1;
            border-radius: 10px;
            background: #F8FAFC;
        }
        .telemetry-label {
            display: block;
            margin-bottom: 5px;
            color: #64748B !important;
            font-size: 0.66rem;
            font-weight: 800;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }
        .telemetry-value {
            display: flex;
            align-items: flex-start;
            gap: 7px;
            color: #1E293B !important;
            font-size: 0.82rem;
            font-weight: 600;
            line-height: 1.4;
            overflow-wrap: anywhere;
        }
        .telemetry-swatch {
            display: inline-block;
            flex: 0 0 11px;
            width: 11px;
            height: 11px;
            margin-top: 3px;
            border: 1px solid rgba(15, 23, 42, 0.18);
            border-radius: 50%;
        }
        .telemetry-note {
            margin-top: 10px;
            padding: 10px 12px;
            border-left: 3px solid #CBA052;
            border-radius: 8px;
            background: #FFFBEB;
            color: #475569 !important;
            font-size: 0.82rem;
            line-height: 1.5;
        }
        .clinical-legend-card .stage-banner {
            margin-top: 10px;
        }
        .clinical-focus-card {
            margin-bottom: 8px;
            padding: 2px;
        }
        .clinical-focus-active {
            margin: 8px 0 12px;
            color: #1E293B !important;
            font-size: 0.88rem;
            font-weight: 650;
            line-height: 1.45;
        }
        .clinical-focus-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 10px;
        }
        .clinical-focus-kicker {
            color: #1D4ED8 !important;
            font-size: 0.7rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .clinical-focus-title {
            margin-top: 2px;
            color: #0F172A !important;
            font-size: 0.98rem;
            font-weight: 750;
        }
        .clinical-focus-stage {
            flex: 0 0 auto;
            padding: 6px 10px;
            border-radius: 999px;
            background: #002D72;
            color: #FFFFFF !important;
            font-size: 0.72rem;
            font-weight: 750;
        }
        .clinical-focus-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 8px;
        }
        .clinical-focus-entry {
            padding: 10px 11px;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            background: #FFFFFF;
        }
        .clinical-focus-structure {
            margin-bottom: 4px;
            color: #002D72 !important;
            font-size: 0.82rem;
            font-weight: 750;
        }
        .clinical-focus-role {
            color: #334155 !important;
            font-size: 0.79rem;
            line-height: 1.45;
        }
        .protein-header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 10px;
        }
        .protein-header .clinical-heading {
            margin-bottom: 6px;
        }
        .protein-header .clinical-sub {
            margin-bottom: 0;
        }
        a.pdb-badge {
            flex: 0 0 auto;
            display: inline-flex;
            align-items: center;
            margin-top: 3px;
            padding: 7px 10px;
            border: 1px solid #BFDBFE;
            border-radius: 999px;
            background: #EFF6FF;
            color: #1D4ED8 !important;
            font-size: 0.8rem;
            font-weight: 700;
            text-decoration: none;
        }
        .baseline-chip {
            display: inline-flex;
            margin: 2px 0 10px;
            padding: 7px 11px;
            border: 1px solid #BBF7D0;
            border-radius: 999px;
            background: #F0FDF4;
            color: #166534;
            font-size: 0.85rem;
            font-weight: 650;
        }
        .protein-viewer-frame {
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(15, 23, 42, 0.08);
        }
        div[data-baseweb="select"] > div {
            min-height: 44px;
            border-color: #CBD5E1 !important;
            border-radius: 10px !important;
        }
        div[data-testid="stSelectbox"] [data-testid="stWidgetLabel"],
        div[data-testid="stSelectbox"] [data-testid="stWidgetLabel"] p {
            min-height: 1.4rem;
            padding-top: 2px;
            overflow: visible !important;
            line-height: 1.4 !important;
        }
        div[data-baseweb="select"]:focus-within > div,
        div[data-baseweb="select"] > div:focus-within {
            border-color: #2563EB !important;
            box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.16) !important;
        }
        div[data-baseweb="select"] [role="combobox"],
        div[data-baseweb="popover"] [role="option"] {
            white-space: normal !important;
            text-overflow: clip !important;
        }
        input:focus-visible, button:focus-visible, [role="radio"]:focus-visible {
            outline: 2px solid #2563EB !important;
            outline-offset: 2px;
            box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.14) !important;
        }
        @media (max-width: 640px) {
            .telemetry-grid {
                grid-template-columns: minmax(0, 1fr);
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

lead_explanation = " ".join(
    (
        "Every thought, memory, and movement depends on billions of proteins folding into precise three-dimensional shapes.",
        "When genetic mutations or thermodynamic stress cause these proteins to misfold, they clump together into toxic aggregates that spread across specific networks of the brain.",
        "This interactive clinical atlas maps the journey from a single mutated amino acid to macroscopic brain atrophy—connecting 3D molecular structures directly to the regions and functions of the human nervous system they impact.",
    )
)
hero_html = f"""
    <div class="top-brand-bar">
        <div class="top-brand-title">NEUROGENETICS & STRUCTURAL BRAIN INITIATIVE</div>
        <div class="top-brand-badge">3D CLINICAL & MOLECULAR ATLAS</div>
    </div>
    <div class="hatch-divider"></div>
    <div class="main-serif-title">Atlas of Neurodegenerative Diseases</div>
    <div class="category-tag">Mapping Genetic Mutations and Protein Misfolding Across the 3D Human Brain</div>
    <div class="lead-explanation">{lead_explanation}</div>
"""
st.markdown(clean_html_markup(hero_html), unsafe_allow_html=True)

st.sidebar.markdown(
    "<div class='sidebar-heading'>Directory Filter</div>",
    unsafe_allow_html=True,
)
selected_condition = st.sidebar.selectbox(
    "Select Disorder:", tuple(DISEASE_DATA)
)
info = DISEASE_DATA[selected_condition]
first_disease_stage = "Stage 1: Early / Initial Localization"
healthy_stage_label = "Baseline: Intact Cortical & Subcortical Homeostasis"
if "last_selected_condition" not in st.session_state:
    st.session_state.last_selected_condition = selected_condition
elif st.session_state.last_selected_condition != selected_condition:
    st.session_state["disease_progression"] = first_disease_stage
    st.session_state.last_selected_condition = selected_condition
compare_healthy = False
if selected_condition != "Healthy Control":
    compare_healthy = st.sidebar.checkbox("Compare with Healthy Control")

linked_genes_html = format_gene_links(info["genes"])

st.sidebar.markdown("---")
st.sidebar.markdown(
    f"""
    <div class="sidebar-box">
        <div class="sidebar-box-title">Key Gene(s)</div>
        <div class="sidebar-box-value">{linked_genes_html}</div>
    </div>
    <div class="sidebar-box">
        <div class="sidebar-box-title">Protein Reference</div>
        <div class="sidebar-box-value">{escape(info['protein'])}</div>
    </div>
    <div class="sidebar-box">
        <div class="sidebar-box-title">Primary Brain Region</div>
        <div class="sidebar-box-value">{escape(info['short_region'])}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

control_camera, control_protein_view = st.columns((0.58, 0.42), gap="medium")
with control_camera:
    selected_preset = st.radio(
        "3D Brain Camera Angle:",
        tuple(CAMERA_PRESETS),
        horizontal=True,
    )
    camera_override = CAMERA_PRESETS[selected_preset]
    st.caption("Glass cortex: 20% opacity · highlighted structures: 95% opacity · Hover any colored region to inspect")
with control_protein_view:
    protein_view_mode = st.radio(
        "Protein Fold View Mode:",
        ("Pathogenic Variant", "Wild-Type Reference", "Stacked Comparison"),
    )

with st.spinner("Rendering 3D Neuro-Architectural Model..."):
    viewer_pair = st.container(
        key=f"atlas-viewers-{selected_condition}"
    )
    col_left, col_right = viewer_pair.columns((1.12, 0.88), gap="large")

    with col_left:
        st.markdown(
            "<div class='clinical-heading'>Macroscopic Brain Localization</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='clinical-sub'>Target Structure: {escape(info['short_region'])}</div>",
            unsafe_allow_html=True,
        )

        if selected_condition == "Healthy Control":
            stage_num = 1
            stage_label = healthy_stage_label
            st.markdown(
                "<div class='baseline-chip'>Baseline: Intact Cortical & Subcortical Homeostasis</div>",
                unsafe_allow_html=True,
            )
        else:
            stage_label = st.selectbox(
                "Disease Progression Timeline:",
                (
                    first_disease_stage,
                    "Stage 2: Intermediate Regional Spread",
                    "Stage 3: Advanced Widespread Atrophy",
                ),
                index=0,
                key="disease_progression",
            )
            stage_num = int(stage_label.split(":", 1)[0].split()[1])
        mesh_directory = str(Path(__file__).resolve().parent)
        mesh_path = Path(mesh_directory) / "brain_mesh.obj"
        zip_path = Path(mesh_directory) / "brain_mesh.zip"
        if mesh_path.is_file() or zip_path.is_file():
            vertices, faces = load_mesh(mesh_directory)
            figure = build_brain_figure(
                vertices,
                faces,
                info,
                camera_override=camera_override,
                height=450,
                uirevision=f"{selected_condition}_{stage_num}_{selected_preset}",
                stage=stage_num,
                disorder_key=selected_condition,
                stage_label=stage_label,
            )
            internal_structure_labels = [
                trace.name
                for trace in figure.data
                if trace.name
                not in (
                    "Glass Cortex",
                    "Cortical Pathology",
                )
            ]
            has_cortical_overlay = any(
                trace.name == "Cortical Pathology" for trace in figure.data
            )
            primary_focus = next(
                (focus for focus in info["foci"] if focus.get("primary")), None
            )
            target_label = (
                primary_focus["label"]
                if primary_focus is not None
                else info["short_region"]
            )
            is_als_condition = any(
                token in selected_condition.lower()
                for token in ("amyotrophic", "familial als", "(als)")
            )
            if is_als_condition:
                legend_target_label = (
                    "Motor & Premotor Cortex" if stage_num == 3 else "Motor Cortex"
                )
            else:
                legend_target_label = target_label
            target_label_lower = legend_target_label.lower()
            target_label_covers_surface = any(
                region in target_label_lower
                for region in ("cortex", "lobe", "vessel", "cerebellum", "brainstem")
            )

            st.plotly_chart(figure, use_container_width=True)

            primary_targets = (
                [legend_target_label]
                if has_cortical_overlay and target_label_covers_surface
                else []
            )
            for structure_name in internal_structure_labels:
                structure_lower = structure_name.lower()
                represented_targets = " ".join(primary_targets).lower()
                if (
                    "substantia nigra" in structure_lower
                    and "substantia nigra" in represented_targets
                ):
                    if "brainstem" in structure_lower and "brainstem" not in represented_targets:
                        primary_targets.append("Brainstem")
                    continue
                if (
                    "corticospinal tract" in structure_lower
                    and "brainstem" in represented_targets
                ):
                    primary_targets.append("Corticospinal Tract")
                    continue
                if any(
                    region in structure_lower and region in represented_targets
                    for region in ("striatum", "hippocampus", "thalamus")
                ):
                    continue
                primary_targets.append(structure_name)
            if has_cortical_overlay and not any(
                region in target_label_lower
                for region in (
                    "cortex",
                    "lobe",
                    "vessel",
                    "cerebellum",
                    "brainstem",
                )
            ):
                primary_targets.append("Cerebral Cortex")
            if not primary_targets:
                primary_targets = internal_structure_labels or [info["short_region"]]
            primary_targets = list(dict.fromkeys(primary_targets))

            if selected_condition == "Healthy Control":
                focus_stage = "Healthy Baseline"
                focus_entries = [
                    (
                        "Healthy Human Brain (Normal Baseline)",
                        "Maintains coordinated cognitive, motor, memory, and vascular "
                        "function through intact neural networks and active protein "
                        "clearance.",
                    )
                ]
            else:
                focus_stage = f"Stage {stage_num}"
                focus_entries = [
                    (name, functional_role_for_name(name))
                    for name in primary_targets
                ]
            focus_entries_html = "".join(
                f"""
                <div class="clinical-focus-entry">
                    <div class="clinical-focus-structure">{escape(name)}</div>
                    <div class="clinical-focus-role">{escape(role)}</div>
                </div>
                """
                for name, role in focus_entries
            )
            focus_targets = ", ".join(name for name, _ in focus_entries)
            focus_html = f"""
                <div class="clinical-focus-card">
                    <div class="clinical-focus-header">
                        <div>
                            <div class="clinical-focus-kicker">Clinical Focus</div>
                            <div class="clinical-focus-title">{escape(selected_condition)}</div>
                        </div>
                        <div class="clinical-focus-stage">{escape(focus_stage)}</div>
                    </div>
                    <div class="clinical-focus-active">
                        Active target: {escape(focus_targets)}
                    </div>
                </div>
            """
            with st.container(
                border=True,
                key=f"clinical-focus-{selected_condition}-{stage_num}",
            ):
                st.markdown(clean_html_markup(focus_html), unsafe_allow_html=True)
                anatomy_tab, cellular_tab, pathophysiology_tab = st.tabs(
                    [
                        "Anatomical Summary",
                        "Cellular Vulnerability",
                        "Clinical Pathophysiology",
                    ]
                )
                with anatomy_tab:
                    st.markdown(
                        clean_html_markup(
                            f'<div class="clinical-focus-grid">{focus_entries_html}</div>'
                        ),
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"**Affected region:** {escape(info['target_region'])}"
                    )
                with cellular_tab:
                    st.markdown(info["gene_and_misfolding"])
                with pathophysiology_tab:
                    st.markdown(info["core_impact"])
                    st.caption(
                        f"{focus_stage} profile: {info['stages'][stage_num]}"
                    )

            if selected_condition == "Healthy Control":
                primary_target_text = (
                    "Whole-Brain Status: 100% Intact Neural Networks & "
                    "Active Protein Clearance"
                )
                cortical_status = "Spared / Intact Cortex"
            else:
                primary_target_text = ", ".join(primary_targets)
                is_hindbrain_only = (
                    "ataxia" in selected_condition.lower()
                    or (
                        "prion" in selected_condition.lower()
                        and stage_num == 1
                    )
                )
                if is_hindbrain_only:
                    cortical_status = (
                        f"Spared / Intact Cortex · Stage {stage_num} "
                        "Hindbrain Surface"
                    )
                elif has_cortical_overlay:
                    cortical_status = f"Stage {stage_num} Cortical Involvement"
                else:
                    cortical_status = "Spared / Intact Cortex"

            is_healthy_brain = selected_condition == "Healthy Control"
            target_swatch = "#DCE3EC" if is_healthy_brain else info["hex"]
            profile_heading = (
                "Baseline Profile:"
                if is_healthy_brain
                else f"Stage {stage_num} Progression Profile:"
            )
            raw_html = f"""
                <div class="clinical-legend-card">
                    <div class="clinical-legend-heading">3D Brain Anatomy Key</div>
                    <div class="telemetry-grid">
                        <div class="telemetry-item">
                            <span class="telemetry-label">Primary Target(s)</span>
                            <span class="telemetry-value"><span class="telemetry-swatch" style="background:{target_swatch}"></span>{escape(primary_target_text)}</span>
                        </div>
                        <div class="telemetry-item">
                            <span class="telemetry-label">Cortical Layer</span>
                            <span class="telemetry-value">{escape(cortical_status)}</span>
                        </div>
                        <div class="telemetry-item">
                            <span class="telemetry-label">Reference Shell</span>
                            <span class="telemetry-value"><span class="telemetry-swatch" style="background:#CBD5E1"></span>20% X-Ray Glass Cortex (Drag to rotate · Scroll to zoom)</span>
                        </div>
                    </div>
                    <div class="stage-banner">
                        <span class="clinical-label">{profile_heading}</span> {escape(info['stages'][stage_num])}
                    </div>
                </div>
            """
            st.markdown(clean_html_markup(raw_html), unsafe_allow_html=True)
        else:
            st.error(f"Cannot find `{mesh_path}` or `{zip_path}`.")

    with col_right:
        if selected_condition == "Healthy Control":
            protein_title = info["protein"]
            protein_pdb_id = (
                info["wt_pdb_id"]
                if protein_view_mode == "Wild-Type Reference"
                else info["pdb_id"]
            )
        elif protein_view_mode == "Wild-Type Reference":
            protein_title = info["wt_protein"]
            protein_pdb_id = info["wt_pdb_id"]
        else:
            protein_title = info["protein"]
            protein_pdb_id = info["pdb_id"]
        linked_pdb_html = format_pdb_link(protein_pdb_id)
        raw_html = f"""
            <div class="protein-header">
                <div>
                    <div class="clinical-heading">3D Molecular Structure</div>
                    <div class="clinical-sub"><strong>{escape(protein_title)}</strong></div>
                </div>
                {linked_pdb_html}
            </div>
            """
        st.markdown(clean_html_markup(raw_html), unsafe_allow_html=True)
        mutation_name = st.selectbox(
            "Mutation Locus (3D Residue Highlight):", tuple(info["mutations"])
        )
        active_mutation = info["mutations"][mutation_name]
        if selected_condition == "Healthy Control":
            if protein_view_mode == "Stacked Comparison":
                st.info(
                    "Healthy Control shows an intact native baseline; there is no "
                    "pathogenic fold to compare."
                )
            healthy_view_pdb = (
                info["wt_pdb_id"]
                if protein_view_mode == "Wild-Type Reference"
                else info["pdb_id"]
            )
            render_molecule_viewer(
                healthy_view_pdb,
                "#005EB8",
                446,
                "mol-healthy-reference",
            )
        elif protein_view_mode == "Wild-Type Reference":
            st.markdown(
                f"<div class='clinical-sub'>{escape(info['wt_protein'])}</div>",
                unsafe_allow_html=True,
            )
            render_molecule_viewer(
                info["wt_pdb_id"], "#005EB8", 446, "mol-wt"
            )
        elif (
            protein_view_mode == "Stacked Comparison"
            and selected_condition != "Healthy Control"
        ):
            st.markdown(
                f"<div class='clinical-sub'>{escape(info['wt_protein'])}</div>",
                unsafe_allow_html=True,
            )
            render_molecule_viewer(info["wt_pdb_id"], "#005EB8", 205, "mol-wt-stack")
            st.markdown(
                f"<div class='clinical-sub'>{escape(info['protein'])}</div>",
                unsafe_allow_html=True,
            )
            render_molecule_viewer(
                info["pdb_id"],
                info["hex"],
                205,
                "mol-mutant-stack",
                active_mutation["res"],
            )
        else:
            render_molecule_viewer(
                info["pdb_id"],
                info["hex"],
                446,
                "mol-primary",
                active_mutation["res"],
            )
        is_healthy_control = selected_condition == "Healthy Control"
        if is_healthy_control:
            protein_site_label = "Native Folding State"
            protein_site_text = (
                "100% Functional Conformation (Zero Toxic Aggregation)"
            )
            protein_dna_text = "Standard Human DNA (Normal Baseline)"
            impact_heading = "Healthy Protein Status"
            impact_text = (
                "Intact native protein structure with functional folding and "
                "protein-clearance activity."
            )
        elif protein_view_mode == "Wild-Type Reference":
            protein_site_label = "Highlighted Mutation Site"
            protein_site_text = "Reference Structure · Mutation Markers Hidden"
            protein_dna_text = escape(active_mutation["dna"])
            impact_heading = "Reference Protein Status"
            impact_text = escape(info["wt_protein"])
        else:
            protein_site_label = "Highlighted Mutation Site"
            protein_site_text = (
                f"Mutated Amino Acid: Position {active_mutation['res'] or 'Unspecified'} "
                "(Gold 3D Spheres)"
            )
            protein_dna_text = escape(active_mutation["dna"])
            impact_heading = f"Mutation Impact · {escape(mutation_name)}"
            impact_text = escape(active_mutation["effect"])

        raw_html = f"""
            <div class="clinical-legend-card">
                <div class="clinical-legend-heading">3D Protein Structure Key</div>
                <div class="telemetry-grid">
                    <div class="telemetry-item">
                        <span class="telemetry-label">3D Ribbon Structure</span>
                        <span class="telemetry-value"><span class="telemetry-swatch" style="background:{info['hex']}"></span>{escape(protein_title)} · PDB {escape(protein_pdb_id)}</span>
                    </div>
                    <div class="telemetry-item">
                        <span class="telemetry-label">{protein_site_label}</span>
                        <span class="telemetry-value"><span class="telemetry-swatch" style="background:{'#FFD700' if not is_healthy_control and protein_view_mode != 'Wild-Type Reference' else info['hex']}"></span>{escape(protein_site_text)}</span>
                    </div>
                    {f'<div class="telemetry-item"><span class="telemetry-label">DNA Reference</span><span class="telemetry-value">{escape(protein_dna_text)}</span></div>' if is_healthy_control else ''}
                </div>
                <div class="telemetry-note">
                    <strong>{impact_heading}</strong><br>
                    <strong>Codon / locus:</strong> {escape(active_mutation['dna'])}<br>
                    {impact_text}
                </div>
            </div>
            """
        st.markdown(clean_html_markup(raw_html), unsafe_allow_html=True)

if compare_healthy:
    healthy_info = DISEASE_DATA["Healthy Control"]
    st.markdown(
        "<div class='hatch-divider' style='margin-top:24px'></div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='clinical-heading'>Side-by-Side Baseline Comparison: Healthy Control vs. {escape(selected_condition)}</div>",
        unsafe_allow_html=True,
    )
    compare_left, compare_right = st.columns((1.12, 0.88), gap="large")
    with compare_left:
        st.markdown(
            f"<div class='clinical-sub'><strong>Healthy Control Brain Baseline</strong> ({escape(healthy_info['short_region'])})</div>",
            unsafe_allow_html=True,
        )
        if mesh_path.is_file() or zip_path.is_file():
            healthy_vertices, healthy_faces = load_mesh(mesh_directory)
            healthy_figure = build_brain_figure(
                healthy_vertices,
                healthy_faces,
                healthy_info,
                camera_override=camera_override,
                height=340,
                uirevision=f"healthy_compare_{selected_preset}",
                stage=1,
                disorder_key="Healthy Control",
                stage_label=healthy_stage_label,
            )
            st.plotly_chart(healthy_figure, use_container_width=True)
    with compare_right:
        st.markdown(
            f"<div class='clinical-sub'><strong>Healthy Reference Protein:</strong> {escape(healthy_info['protein'])}</div>",
            unsafe_allow_html=True,
        )
        render_molecule_viewer(
            healthy_info["pdb_id"], healthy_info["hex"], 336, "mol-healthy"
        )

st.markdown("---")
st.markdown(
    f"<div class='hatch-divider' style='margin-top:24px'></div><div class='clinical-heading'>Clinical Overview: {escape(selected_condition)}</div>",
    unsafe_allow_html=True,
)

card_columns = st.columns(3, gap="medium")
if selected_condition == "Healthy Control":
    with card_columns[0]:
        st.markdown(
            """
            <div class="clinical-card">
                <h4>1. Baseline Proteostasis & Quality Control</h4>
                <p><span class="clinical-label">Reference Genome:</span> Standard Human DNA (Normal Baseline)</p>
                <p><span class="clinical-label">Reference Protein:</span> Intact Native Protein Structure (Ubiquitin, 1UBQ) — The cell's master tag for protein recycling</p>
                <p><span class="clinical-label">Homeostatic Mechanism:</span> Healthy neurons fold proteins accurately with the help of molecular chaperones. When a protein gets worn out or damaged, ubiquitin tags it for safe disposal via the proteasome and autophagy pathways—preventing toxic buildup.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with card_columns[1]:
        st.markdown(
            """
            <div class="clinical-card">
                <h4>2. Whole-Brain Structural Integrity</h4>
                <p><span class="clinical-label">Anatomical Status:</span> Intact Whole-Brain Equilibrium (Zero Atrophy)</p>
                <p><span class="clinical-label">Protected Networks:</span> Cerebral cortex, hippocampus, basal ganglia, substantia nigra, cerebellum, brainstem, and cerebral blood vessels operate in synchronized balance without plaque or tangle interference.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with card_columns[2]:
        st.markdown(
            """
            <div class="clinical-card">
                <h4>3. Healthy Physiological Function</h4>
                <p><span class="clinical-label">Functional Baseline:</span> Smooth motor coordination, sharp episodic memory formation, clear executive decision-making, restorative sleep-wake cycles, and resilient vascular perfusion.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    with card_columns[0]:
        st.markdown(
            f"""
            <div class="clinical-card">
                <h4>1. Genetic Trigger & Protein Misfolding</h4>
                <p><span class="clinical-label">Gene(s):</span> {linked_genes_html}</p>
                <p><span class="clinical-label">Protein:</span> {escape(info['protein'])}</p>
                <p><span class="clinical-label">Why it misfolds:</span> {escape(info['gene_and_misfolding'])}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with card_columns[1]:
        st.markdown(
            f"""
            <div class="clinical-card">
                <h4>2. Vulnerable Brain Regions</h4>
                <p><span class="clinical-label">Primary region:</span> {escape(info['short_region'])}</p>
                <p><span class="clinical-label">Why these cells:</span> {escape(info['target_region'])}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with card_columns[2]:
        st.markdown(
            f"""
            <div class="clinical-card">
                <h4>3. Clinical Impact on the Body</h4>
                <p><span class="clinical-label">From circuitry to symptoms:</span> {escape(info['core_impact'])}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )