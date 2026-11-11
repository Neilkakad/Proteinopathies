import json
from html import escape
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import numpy as np
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components


DISEASE_DATA = {
    "Healthy Control": {
        "genes": "Wild-Type Reference Genome (Unmutated)",
        "protein": "Normal Physiological Homeostasis (Ubiquitin Reference)",
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
        "camera_eye": {"x": 1.45, "y": 1.15, "z": 0.65},
        "rgb": (100, 116, 139),
        "hex": "#64748B",
    },
    "Huntington's Disease": {
        "genes": "HTT",
        "protein": "Huntingtin",
        "pdb_id": "4FE8",
        "short_region": "Striatum (Basal Ganglia) & Cortex",
        "gene_and_misfolding": (
            "A CAG repeat expansion in HTT lengthens huntingtin's polyglutamine "
            "tract. The expanded protein can misfold, form toxic oligomers and "
            "aggregates, and disrupt transcription, axonal transport, and "
            "neuronal maintenance."
        ),
        "target_region": (
            "Striatum (caudate nucleus and putamen of the basal ganglia) and "
            "cerebral cortex; medium spiny neurons are especially vulnerable."
        ),
        "core_impact": (
            "Involuntary movements (chorea), impaired coordination, cognitive "
            "decline, mood changes, and progressive difficulty with daily "
            "activities."
        ),
        "foci": [
            {"dir": [0.35, 0.45, 0.35], "radius": 0.56, "primary": True, "label": "Striatum & Cerebral Cortex"},
            {"dir": [-0.35, 0.45, 0.35], "radius": 0.56, "primary": False, "label": "Contralateral Striatum"},
        ],
        "camera_eye": {"x": 0.85, "y": 1.55, "z": 0.75},
        "rgb": (225, 29, 72),
        "hex": "#E11D48",
    },
    "Familial Alzheimer's Disease": {
        "genes": "APP, PSEN1, PSEN2",
        "protein": "Amyloid-beta (Aβ42) & Hyperphosphorylated Tau",
        "pdb_id": "2M4J",
        "short_region": "Hippocampus & Cerebral Cortex",
        "gene_and_misfolding": (
            "Pathogenic variants in APP, PSEN1, or PSEN2 can alter amyloid "
            "processing and increase aggregation-prone amyloid-beta. Amyloid "
            "deposits and abnormal tau aggregates are associated with synaptic "
            "dysfunction and neuronal injury."
        ),
        "target_region": (
            "Hippocampus, entorhinal cortex, and association cerebral cortex; "
            "memory-related circuits are often affected early."
        ),
        "core_impact": (
            "Severe and progressive memory loss, confusion, disorientation, "
            "language or problem-solving difficulties, and loss of "
            "independence as brain atrophy advances."
        ),
        "foci": [
            {"dir": [0.85, -0.15, -0.10], "radius": 0.62, "primary": True, "label": "Hippocampus & Temporal Cortex"},
            {"dir": [-0.85, -0.15, -0.10], "radius": 0.62, "primary": False, "label": "Contralateral Temporal Cortex"},
        ],
        "camera_eye": {"x": 1.75, "y": -0.35, "z": 0.25},
        "rgb": (234, 88, 12),
        "hex": "#EA580C",
    },
    "Familial Parkinson's Disease": {
        "genes": "SNCA, LRRK2, PRKN",
        "protein": "Alpha-synuclein (Lewy bodies)",
        "pdb_id": "1XQ8",
        "short_region": "Substantia Nigra (Midbrain)",
        "gene_and_misfolding": (
            "SNCA variants or gene multiplications can alter alpha-synuclein "
            "and promote misfolding and aggregation into Lewy bodies. LRRK2 "
            "and PRKN variants can affect pathways involved in neuronal "
            "maintenance and protein clearance."
        ),
        "target_region": (
            "Substantia nigra pars compacta (midbrain) and basal ganglia."
        ),
        "core_impact": (
            "Tremors, muscle stiffness, slowed movement, and gait or balance "
            "difficulties associated with loss of dopamine-producing neurons."
        ),
        "foci": [
            {"dir": [0.0, -0.45, -0.75], "radius": 0.54, "primary": True, "label": "Substantia Nigra (Midbrain)"},
        ],
        "camera_eye": {"x": 0.95, "y": -1.35, "z": -0.85},
        "rgb": (126, 34, 206),
        "hex": "#7E22CE",
    },
    "Familial Amyotrophic Lateral Sclerosis (ALS)": {
        "genes": "SOD1, TARDBP, FUS, C9orf72",
        "protein": "TDP-43, SOD1, or FUS",
        "pdb_id": "2C9V",
        "short_region": "Motor Cortex, Brainstem, & Spinal Cord",
        "gene_and_misfolding": (
            "SOD1 variants can produce misfolded SOD1, while TARDBP and FUS "
            "variants affect RNA-binding proteins that may mislocalize and "
            "aggregate. C9orf72 repeat expansions can also cause toxic RNA- "
            "and protein-related effects. These mechanisms impair motor-neuron "
            "function and are not identical across all genetic forms."
        ),
        "target_region": (
            "Primary motor cortex, brainstem motor nuclei, and spinal cord "
            "motor neurons (upper and lower motor neuron pathways)."
        ),
        "core_impact": (
            "Progressive muscle weakness, loss of motor control, paralysis, "
            "and increasing difficulty speaking, swallowing, or breathing."
        ),
        "foci": [
            {"dir": [0.25, 0.15, 0.90], "radius": 0.54, "primary": True, "label": "Motor Cortex & Brainstem"},
            {"dir": [-0.25, 0.15, 0.90], "radius": 0.54, "primary": False, "label": "Contralateral Motor Cortex"},
            {"dir": [0.0, -0.35, -0.85], "radius": 0.50, "primary": False, "label": "Spinal Motor Pathways"},
        ],
        "camera_eye": {"x": 1.35, "y": 0.55, "z": 1.25},
        "rgb": (2, 132, 199),
        "hex": "#0284C7",
    },
    "Genetic Frontotemporal Dementia (FTD)": {
        "genes": "MAPT, GRN, C9orf72",
        "protein": "Tau or TDP-43",
        "pdb_id": "5O3L",
        "short_region": "Frontal & Temporal Lobes",
        "gene_and_misfolding": (
            "MAPT variants can alter tau splicing or function and promote "
            "abnormal tau accumulation. GRN and C9orf72 variants are often "
            "associated with TDP-43 pathology. The underlying proteinopathy "
            "varies by genetic cause and can injure frontal and temporal "
            "networks."
        ),
        "target_region": (
            "Prefrontal, orbitofrontal, and anterior temporal lobes; the "
            "distribution and asymmetry vary among FTD subtypes."
        ),
        "core_impact": (
            "Personality and behavioral changes, reduced social inhibition or "
            "empathy, executive difficulties, and progressive language "
            "impairment."
        ),
        "foci": [
            {"dir": [0.35, 0.85, 0.20], "radius": 0.60, "primary": True, "label": "Frontal & Temporal Lobes"},
            {"dir": [-0.35, 0.85, 0.20], "radius": 0.60, "primary": False, "label": "Contralateral Frontal Lobe"},
            {"dir": [0.75, 0.25, -0.25], "radius": 0.52, "primary": False, "label": "Temporal Lobe"},
            {"dir": [-0.75, 0.25, -0.25], "radius": 0.52, "primary": False, "label": "Contralateral Temporal Lobe"},
        ],
        "camera_eye": {"x": 1.15, "y": 1.50, "z": 0.45},
        "rgb": (190, 24, 93),
        "hex": "#BE185D",
    },
    "Genetic Prion Diseases (e.g., Familial CJD, FFI)": {
        "genes": "PRNP",
        "protein": "Prion protein (PrPSc)",
        "pdb_id": "1QLX",
        "short_region": "Cerebral Cortex, Thalamus, & Cerebellum",
        "gene_and_misfolding": (
            "Pathogenic PRNP variants can alter cellular prion protein and "
            "promote conversion to misfolded PrPSc. The abnormal form can "
            "template further misfolding and is associated with prion "
            "aggregation and neurodegeneration."
        ),
        "target_region": (
            "Cerebral cortex, thalamus, and cerebellum; involvement varies "
            "with the specific inherited prion syndrome."
        ),
        "core_impact": (
            "Rapidly progressive dementia and loss of coordination; Fatal "
            "Familial Insomnia can also cause profound sleep disruption."
        ),
        "foci": [
            {"dir": [0.0, -0.80, -0.35], "radius": 0.58, "primary": True, "label": "Cerebellum, Thalamus & Cortex"},
            {"dir": [0.40, 0.10, 0.65], "radius": 0.52, "primary": False, "label": "Cerebral Cortex"},
            {"dir": [-0.40, 0.10, 0.65], "radius": 0.52, "primary": False, "label": "Contralateral Cortex"},
        ],
        "camera_eye": {"x": 1.25, "y": -1.35, "z": 0.45},
        "rgb": (22, 163, 74),
        "hex": "#16A34A",
    },
    "Spinocerebellar Ataxias (SCAs)": {
        "genes": "ATXN1, ATXN2, ATXN3, etc.",
        "protein": "Ataxin proteins (Polyglutamine aggregates)",
        "pdb_id": "1YZB",
        "short_region": "Cerebellum & Brainstem",
        "gene_and_misfolding": (
            "CAG repeat expansions in several ATXN genes produce ataxin "
            "proteins with expanded polyglutamine tracts. These proteins can "
            "misfold and aggregate, disrupting vulnerable cerebellar neurons; "
            "the affected gene and clinical course differ among SCA subtypes."
        ),
        "target_region": (
            "Cerebellar cortex, deep cerebellar nuclei, and brainstem."
        ),
        "core_impact": (
            "Progressive loss of balance and coordination, unsteady gait, "
            "slurred speech, and difficulty controlling precise movements."
        ),
        "foci": [
            {"dir": [0.0, -0.85, -0.50], "radius": 0.62, "primary": True, "label": "Cerebellum & Brainstem"},
        ],
        "camera_eye": {"x": 0.85, "y": -1.60, "z": -0.45},
        "rgb": (13, 148, 136),
        "hex": "#0D9488",
    },
    "Familial Cerebral Amyloid Angiopathy (CAA)": {
        "genes": "APP, CST3",
        "protein": "Amyloid-beta (Aβ40/42) or Cystatin C",
        "pdb_id": "1G96",
        "short_region": "Cerebral Blood Vessels",
        "gene_and_misfolding": (
            "Some APP or CST3 variants promote amyloid-beta or cystatin C "
            "aggregation. These proteins can deposit in cerebral vessel walls, "
            "compromising vascular integrity."
        ),
        "target_region": (
            "Cortical and leptomeningeal cerebral blood vessels; the pattern "
            "and distribution depend on the underlying CAA subtype."
        ),
        "core_impact": (
            "Weakened brain-vessel walls that can lead to cerebral "
            "microbleeds, hemorrhagic stroke, and related neurological "
            "deficits."
        ),
        "foci": [
            {"dir": [0.45, 0.35, 0.75], "radius": 0.58, "primary": True, "label": "Cerebral Blood Vessels"},
            {"dir": [-0.45, -0.45, 0.70], "radius": 0.58, "primary": False, "label": "Contralateral Cerebral Vessels"},
        ],
        "camera_eye": {"x": 1.15, "y": 0.95, "z": 1.25},
        "rgb": (217, 119, 6),
        "hex": "#D97706",
    },
}

DISEASE_FEATURES = {
    "Healthy Control": {
        "wt_pdb_id": "1UBQ",
        "wt_protein": "Native Folded Ubiquitin",
        "stages": {
            1: "Baseline homeostasis: normal protein folding and synaptic function.",
            2: "Stable neural networks with ongoing protein quality control.",
            3: "Healthy reference anatomy; no disease progression is represented.",
        },
        "mutations": {
            "Wild-Type Reference (No Mutation)": {
                "res": None,
                "dna": "Normal reference sequence",
                "effect": "Reference protein conformation; no pathogenic residue is highlighted.",
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
    if "Wild-Type" in gene_text:
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
        f"<a class='clinical-link' href='https://www.rcsb.org/structure/"
        f"{quote(pdb_id)}' target='_blank' rel='noopener noreferrer'>"
        f"{escape(pdb_id)} ↗</a>"
    )


@st.cache_data(show_spinner=False)
def load_obj(file_path: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load, triangulate, and normalize an OBJ mesh, including face centroids."""
    vertices = []
    triangles = []

    with open(file_path, encoding="utf-8") as obj_file:
        for line_number, line in enumerate(obj_file, start=1):
            fields = line.split()
            if not fields or fields[0].startswith("#"):
                continue
            if fields[0] == "v":
                if len(fields) < 4:
                    raise ValueError(f"Invalid vertex at line {line_number} in {file_path}")
                vertices.append([float(value) for value in fields[1:4]])
            elif fields[0] == "f":
                if len(fields) < 4:
                    raise ValueError(f"Invalid face at line {line_number} in {file_path}")
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

    if not vertices or not triangles:
        raise ValueError(f"No usable vertices or faces found in {file_path}")

    vertex_array = np.asarray(vertices, dtype=np.float32)
    triangle_array = np.asarray(triangles, dtype=np.int32)
    if not np.isfinite(vertex_array).all():
        raise ValueError(f"Non-finite vertex coordinate in {file_path}")
    if triangle_array.min() < 0 or triangle_array.max() >= len(vertex_array):
        raise ValueError(f"Face index outside the vertex range in {file_path}")
    bounds_min = vertex_array.min(axis=0)
    bounds_max = vertex_array.max(axis=0)
    center = (bounds_min + bounds_max) / 2
    scale = np.max(bounds_max - bounds_min) / 2
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError(f"Cannot normalize degenerate OBJ mesh in {file_path}")
    normalized_vertices = (vertex_array - center) / scale
    face_centroids = normalized_vertices[triangle_array].mean(axis=1)
    return normalized_vertices, triangle_array, face_centroids


def render_molecule_viewer(
    pdb_id, color_hex, height=450, viewer_id="mol-main", highlight_res=None
):
    residue_selector = ""
    if highlight_res is not None:
        residue_parts = highlight_res.split("-", 1)
        if not all(part.isdigit() for part in residue_parts):
            raise ValueError(f"Invalid residue selector: {highlight_res}")
        start = int(residue_parts[0])
        end = int(residue_parts[-1])
        if start < 1 or end < start or end - start > 1000:
            raise ValueError(f"Invalid residue range: {highlight_res}")
        residues = json.dumps(list(range(start, end + 1)))
        residue_selector = f"""
            viewer.addStyle({{resi: {residues}}}, {{
                sphere: {{color: "#FFD700", radius: 1.45}},
                stick: {{color: "#FF003C", radius: 0.35}}
            }});
        """
    html_code = f"""
    <div id="{viewer_id}" style="height: {height}px; width: 99%; box-sizing: border-box; position: relative; border-radius: 8px; border: 1px solid #E2E8F0; background-color: #F8FAFC;"></div>
    <script src="https://3Dmol.org/build/3Dmol-min.js"></script>
    <script>
        let element = document.getElementById('{viewer_id}');
        let viewer = $3Dmol.createViewer(element, {{ backgroundColor: '#F8FAFC' }});
        $3Dmol.download("pdb:{pdb_id}", viewer, {{}}, function() {{
            viewer.setStyle({{}}, {{cartoon: {{color: '{color_hex}'}}}});
            {residue_selector}
            viewer.zoomTo();
            viewer.render();
            viewer.spin("y", 0.6);
        }});
    </script>
    """
    components.html(html_code, height=height + 15)


def build_brain_figure(
    vertices: np.ndarray,
    faces: np.ndarray,
    face_centroids: np.ndarray,
    condition_info: dict,
    camera_override: Optional[dict] = None,
    height: int = 450,
    uirevision: str = "brain",
    stage: int = 2,
    cortical_opacity: float = 1.0,
) -> go.Figure:
    x, y, z = vertices.T
    highlighted = np.zeros(len(faces), dtype=bool)
    annotations = []
    camera_eye = camera_override or condition_info["camera_eye"]

    stage_scale = {1: 0.78, 2: 1.0, 3: 1.24}.get(stage)
    if stage_scale is None:
        raise ValueError(f"Invalid disease stage: {stage}")
    if not 0.15 <= cortical_opacity <= 1.0:
        raise ValueError(f"Invalid cortical opacity: {cortical_opacity}")

    for focus_index, focus in enumerate(condition_info["foci"]):
        minimum_stage = focus.get("min_stage", min(3, 1 + focus_index // 2))
        if stage < minimum_stage:
            continue
        direction = np.asarray(focus["dir"], dtype=np.float32)
        direction_length = float(np.linalg.norm(direction))
        if not np.isfinite(direction_length) or direction_length == 0:
            raise ValueError(f"Invalid focus direction for {condition_info['short_region']}")
        direction /= direction_length
        projection = x * direction[0] + y * direction[1] + z * direction[2]
        surface = vertices[int(np.argmax(projection))]
        face_distance = np.linalg.norm(face_centroids - surface, axis=1)
        highlighted |= face_distance <= focus["radius"] * stage_scale

        if focus.get("primary"):
            offset_y = 32 if surface[2] > 0.25 else -30
            y_anchor = "top" if surface[2] > 0.25 else "bottom"
            annotations.append(
                {
                    "x": float(surface[0]),
                    "y": float(surface[1]),
                    "z": float(surface[2]),
                    "text": f"<b>{escape(focus['label'])} (Stage {stage})</b>",
                    "showarrow": True,
                    "arrowhead": 2,
                    "arrowsize": 1.1,
                    "arrowwidth": 2,
                    "arrowcolor": "#0F172A",
                    "ax": 0,
                    "ay": offset_y,
                    "xanchor": "center",
                    "yanchor": y_anchor,
                    "bgcolor": "rgba(15,23,42,0.88)",
                    "bordercolor": "rgba(15,23,42,0.88)",
                    "borderpad": 7,
                    "font": {
                        "color": "#FFFFFF",
                        "size": 12,
                        "family": "Arial",
                    },
                }
            )

    if not annotations:
        camera_vector = np.asarray(
            [camera_eye["x"], camera_eye["y"], camera_eye["z"]], dtype=np.float32
        )
        camera_vector /= np.linalg.norm(camera_vector)
        projection = x * camera_vector[0] + y * camera_vector[1] + z * camera_vector[2]
        surface = vertices[int(np.argmax(projection))]
        annotations.append(
            {
                "x": float(surface[0]),
                "y": float(surface[1]),
                "z": float(surface[2]),
                "text": f"<b>Healthy Control (Stage {stage})</b>",
                "showarrow": True,
                "arrowhead": 2,
                "ax": 0,
                "ay": -40,
                "xanchor": "center",
                "yanchor": "bottom",
                "bgcolor": "rgba(15,23,42,0.88)",
                "bordercolor": "rgba(15,23,42,0.88)",
                "borderpad": 7,
                "font": {"color": "#FFFFFF", "size": 12, "family": "Arial"},
            }
        )
    if len(annotations) != 1:
        raise ValueError("A brain view must have exactly one primary callout.")

    lighting = {
        "ambient": 0.36,
        "diffuse": 0.88,
        "specular": 0.35,
        "roughness": 0.4,
        "fresnel": 0.25,
    }
    light_position = {"x": 120, "y": 180, "z": 160}
    traces = []
    healthy_faces = faces[~highlighted]
    target_faces = faces[highlighted]
    if len(healthy_faces):
        traces.append(
            go.Mesh3d(
                x=x, y=y, z=z,
                i=healthy_faces[:, 0], j=healthy_faces[:, 1], k=healthy_faces[:, 2],
                color="#DCE3EC", opacity=cortical_opacity, flatshading=False,
                lighting=lighting, lightposition=light_position,
                hoverinfo="skip", name="Unaffected tissue",
            )
        )
    if len(target_faces):
        traces.append(
            go.Mesh3d(
                x=x, y=y, z=z,
                i=target_faces[:, 0], j=target_faces[:, 1], k=target_faces[:, 2],
                color=condition_info["hex"], opacity=1, flatshading=False,
                lighting=lighting, lightposition=light_position,
                hoverinfo="skip", name="Affected region",
            )
        )

    figure = go.Figure(data=traces)
    zoom_factor = 0.86
    zoomed_camera_eye = {
        axis: camera_eye[axis] * zoom_factor for axis in ("x", "y", "z")
    }
    figure.update_layout(
        uirevision=uirevision,
        scene={
            "xaxis": {"visible": False},
            "yaxis": {"visible": False},
            "zaxis": {"visible": False},
            "aspectmode": "data",
            "bgcolor": "#F8FAFC",
            "camera": {
                "eye": zoomed_camera_eye,
                "center": {"x": 0, "y": 0, "z": 0},
                "up": {"x": 0, "y": 0, "z": 1},
            },
            "annotations": annotations,
        },
        paper_bgcolor="#F8FAFC",
        plot_bgcolor="#F8FAFC",
        margin={"l": 0, "r": 0, "b": 0, "t": 0},
        height=height,
        showlegend=False,
    )
    return figure


st.set_page_config(
    page_title="Proteinopathies | Neurological Disorders",
    layout="wide",
    page_icon="🧬",
)
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
            color: #212529;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
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
            border-radius: 8px;
            padding: 4px;
            overflow: hidden;
        }
        .top-brand-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 24px;
            background: #002D72;
            color: #FFFFFF;
        }
        .top-brand-title {
            font: 700 1.15rem Georgia, "Times New Roman", serif;
            letter-spacing: 0.5px;
            color: #FFFFFF !important;
        }
        .top-brand-sub {
            color: #CBD5E1;
            font-size: 0.85rem;
        }
        .hatch-divider {
            height: 10px;
            margin-bottom: 22px;
            border-bottom: 1px solid #E2E8F0;
            background: repeating-linear-gradient(-45deg, #EDE9FE, #EDE9FE 3px, #FFFFFF 3px, #FFFFFF 7px);
        }
        .main-serif-title {
            margin: 4px 0 8px;
            color: #002D72 !important;
            font: 400 2.6rem/1.15 Georgia, "Times New Roman", serif;
        }
        .category-tag {
            margin-bottom: 18px;
            padding: 8px 0;
            border-top: 1px solid #E2E8F0;
            border-bottom: 1px solid #E2E8F0;
            color: #005EB8 !important;
            font-size: 0.95rem;
        }
        .lead-explanation {
            margin-bottom: 26px;
            color: #212529 !important;
            font-size: 1rem;
            line-height: 1.7;
        }
        .clinical-heading {
            margin-bottom: 12px;
            overflow: visible;
            color: #002D72 !important;
            font: 400 1.48rem/1.2 Georgia, "Times New Roman", serif;
            min-height: 36px;
            display: flex;
            align-items: flex-end;
        }
        .clinical-sub {
            margin-bottom: 12px;
            overflow: visible;
            color: #212529 !important;
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
            background: #F4F6F9;
            border: 1px solid #E2E8F0;
            border-top: 3px solid #002D72;
            color: #212529;
            min-height: 370px;
            box-sizing: border-box;
        }
        .clinical-card h4 {
            margin: 0 0 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #CBD5E1;
            color: #002D72 !important;
            font: 400 1.15rem Georgia, "Times New Roman", serif;
        }
        .clinical-card p {
            margin-bottom: 10px;
            color: #212529 !important;
            font-size: 0.94rem;
            line-height: 1.6;
        }
        .clinical-label {
            color: #002D72 !important;
            font-weight: 700;
        }
        [data-testid="stSidebar"] {
            background: #F4F6F9 !important;
            border-right: 1px solid #E2E8F0;
        }
        .sidebar-heading {
            margin-bottom: 12px;
            color: #002D72 !important;
            font: 400 1.35rem Georgia, "Times New Roman", serif;
        }
        .sidebar-box {
            margin-bottom: 12px;
            padding: 12px 14px;
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-left: 3px solid #005EB8;
        }
        .sidebar-box-title {
            color: #005EB8 !important;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.4px;
            text-transform: uppercase;
        }
        .sidebar-box-value {
            color: #212529 !important;
            font-size: 0.92rem;
            line-height: 1.45;
        }
        .legend-strip {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 14px;
            margin-top: 8px;
            padding: 9px 14px;
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 6px;
            color: #212529;
            font-size: 0.84rem;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 7px;
        }
        .legend-dot {
            display: inline-block;
            width: 12px;
            height: 12px;
            border: 1px solid rgba(0,0,0,0.15);
            border-radius: 50%;
        }
        .stage-banner, .mutation-pill {
            margin-top: 10px;
            padding: 12px 14px;
            background: #F4F6F9;
            border-left: 3px solid #005EB8;
            border-radius: 4px;
            color: #212529;
            font-size: 0.9rem;
            line-height: 1.5;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="top-brand-bar">
        <div class="top-brand-title">NEURO-GENETIC MEDICINE</div>
        <div class="top-brand-sub">Clinical Atlas of Molecular Neuropathology</div>
    </div>
    <div class="hatch-divider"></div>
    <div class="main-serif-title">Proteinopathies</div>
    <div class="category-tag">Brain, Nerves, Spine &amp; Molecular Genetics</div>
    <div class="lead-explanation">
        <strong>Proteinopathies</strong> are progressive neurological diseases
        associated with abnormal protein folding, aggregation, or clearance.
        Genetic changes can alter a protein's structure or processing, and
        resulting deposits may disrupt vulnerable neural or vascular tissues.
        This educational atlas summarizes representative molecular mechanisms,
        affected regions, and clinical impacts; it is not a diagnostic tool.
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    "<div class='sidebar-heading'>Directory Filter</div>",
    unsafe_allow_html=True,
)
selected_condition = st.sidebar.selectbox(
    "Select Disorder:", tuple(DISEASE_DATA)
)
info = DISEASE_DATA[selected_condition]
compare_healthy = False
if selected_condition != "Healthy Control":
    compare_healthy = st.sidebar.checkbox("Compare with Healthy Control")

linked_genes_html = format_gene_links(info["genes"])
linked_pdb_html = format_pdb_link(info["pdb_id"])

st.sidebar.markdown("---")
st.sidebar.markdown(
    f"""
    <div class="sidebar-box">
        <div class="sidebar-box-title">Key Gene(s)</div>
        <div class="sidebar-box-value">{linked_genes_html}</div>
    </div>
    <div class="sidebar-box">
        <div class="sidebar-box-title">Misfolded Protein</div>
        <div class="sidebar-box-value">{escape(info['protein'])}<br>PDB ID: {linked_pdb_html}</div>
    </div>
    <div class="sidebar-box">
        <div class="sidebar-box-title">Primary Brain Region</div>
        <div class="sidebar-box-value">{escape(info['short_region'])}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

control_camera, control_opacity, control_protein_view = st.columns(
    (0.48, 0.26, 0.26), gap="medium"
)
with control_camera:
    selected_preset = st.radio(
        "3D Brain Camera Angle:",
        tuple(CAMERA_PRESETS),
        horizontal=True,
    )
    camera_override = CAMERA_PRESETS[selected_preset]
with control_opacity:
    cortical_opacity = st.slider(
        "Cortical Opacity (Glass Brain X-Ray):",
        min_value=0.15,
        max_value=1.0,
        value=1.0,
        step=0.05,
        help="Lower opacity makes unaffected mesh tissue translucent; highlighted disease tissue remains opaque.",
    )
with control_protein_view:
    protein_view_mode = st.radio(
        "Protein Fold View Mode:",
        ("Pathogenic Variant", "Wild-Type Reference", "Stacked Comparison"),
    )

col_left, col_right = st.columns((1.12, 0.88), gap="large")

with col_left:
    st.markdown(
        "<div class='clinical-heading'>Macroscopic Brain Localization</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='clinical-sub'>Target Structure: {escape(info['short_region'])}</div>",
        unsafe_allow_html=True,
    )

    stage_label = st.selectbox(
        "Disease Progression Timeline:",
        (
            "Stage 1: Early / Focal Onset",
            "Stage 2: Intermediate Regional Spread",
            "Stage 3: Advanced Widespread Atrophy",
        ),
        index=1,
    )
    stage_num = int(stage_label.split(":", 1)[0].split()[1])
    mesh_path = Path(__file__).resolve().parent / "brain_mesh.obj"
    if mesh_path.is_file():
        with st.spinner("Rendering 3D Brain Mesh..."):
            vertices, faces, face_centroids = load_obj(str(mesh_path))
            figure = build_brain_figure(
                vertices,
                faces,
                face_centroids,
                info,
                camera_override=camera_override,
                height=450,
                uirevision=f"{selected_condition}_{selected_preset}",
                stage=stage_num,
                cortical_opacity=cortical_opacity,
            )
            st.plotly_chart(figure, use_container_width=True)
            st.markdown(
                f"""
                <div class="legend-strip">
                    <div class="legend-item"><span class="legend-dot" style="background:{info['hex']}"></span>
                    <span>Affected region (Stage {stage_num})</span></div>
                    <div class="legend-item"><span class="legend-dot" style="background:#DCE3EC"></span>
                    <span>Unaffected tissue ({int(cortical_opacity * 100)}% opacity)</span></div>
                    <div class="legend-item" style="margin-left:auto;color:#005EB8">Drag to rotate · Scroll to zoom</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                f"""
                <div class="stage-banner">
                    <span class="clinical-label">Stage {stage_num} progression profile:</span>
                    {escape(info['stages'][stage_num])}
                    <br><small>Illustrative visualization stage; not a patient-specific clinical score.</small>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.error(f"Cannot find `{mesh_path}`.")

with col_right:
    st.markdown(
        "<div class='clinical-heading'>3D Molecular Structure</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='clinical-sub'><strong>{escape(info['protein'])}</strong> &nbsp;|&nbsp; PDB ID: {linked_pdb_html}</div>",
        unsafe_allow_html=True,
    )
    mutation_name = st.selectbox(
        "Mutation Locus (3D Residue Highlight):", tuple(info["mutations"])
    )
    active_mutation = info["mutations"][mutation_name]
    if selected_condition == "Healthy Control":
        if protein_view_mode == "Stacked Comparison":
            st.info(
                "Healthy Control is the wild-type reference; there is no "
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
            f"<div class='clinical-sub'>{escape(info['wt_protein'])} ({escape(info['wt_pdb_id'])})</div>",
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
            f"<div class='clinical-sub'>{escape(info['wt_protein'])} ({escape(info['wt_pdb_id'])})</div>",
            unsafe_allow_html=True,
        )
        render_molecule_viewer(info["wt_pdb_id"], "#005EB8", 205, "mol-wt-stack")
        st.markdown(
            f"<div class='clinical-sub'>{escape(info['protein'])} ({escape(info['pdb_id'])})</div>",
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
    st.markdown(
        f"""
        <div class="legend-strip">
            <div class="legend-item"><span class="legend-dot" style="background:{info['hex']}"></span>
            <span>{'Healthy reference' if selected_condition == 'Healthy Control' else 'Wild-type reference' if protein_view_mode == 'Wild-Type Reference' else 'Pathogenic protein reference'}</span></div>
            <div class="legend-item"><span class="legend-dot" style="background:#FFD700"></span>
            <span>Selected residue: {escape(active_mutation['res'] or 'N/A') if selected_condition != 'Healthy Control' and protein_view_mode != 'Wild-Type Reference' else 'Not highlighted'}</span></div>
            <div class="legend-item" style="margin-left:auto">PDB: {linked_pdb_html}</div>
        </div>
        <div class="mutation-pill">
            <span class="clinical-label">Mutation impact ({escape(mutation_name)}):</span><br>
            <strong>Codon / locus:</strong> {escape(active_mutation['dna'])}<br>
            {escape(active_mutation['effect'])}
            <br><small>Residue markers are illustrative and depend on residue numbering in the displayed reference structure; the PDB model is not a custom patient-specific mutant.</small>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
        if mesh_path.is_file():
            healthy_vertices, healthy_faces, healthy_centroids = load_obj(str(mesh_path))
            healthy_figure = build_brain_figure(
                healthy_vertices,
                healthy_faces,
                healthy_centroids,
                healthy_info,
                camera_override=camera_override or info["camera_eye"],
                height=340,
                uirevision=f"healthy_compare_{selected_preset}",
                stage=1,
                cortical_opacity=cortical_opacity,
            )
            st.plotly_chart(healthy_figure, use_container_width=True)
    with compare_right:
        healthy_pdb = format_pdb_link(healthy_info["pdb_id"])
        st.markdown(
            f"<div class='clinical-sub'><strong>Healthy Reference Protein:</strong> {escape(healthy_info['protein'])} (PDB: {healthy_pdb})</div>",
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
with card_columns[0]:
    st.markdown(
        f"""
        <div class="clinical-card">
            <h4>1. Genetic Mutation &amp; Protein Misfolding</h4>
            <p><span class="clinical-label">Key gene(s):</span> {linked_genes_html}</p>
            <p><span class="clinical-label">Misfolded protein:</span> {escape(info['protein'])} (PDB: {linked_pdb_html})</p>
            <p><span class="clinical-label">Pathological mechanism:</span> {escape(info['gene_and_misfolding'])}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with card_columns[1]:
    st.markdown(
        f"""
        <div class="clinical-card">
            <h4>2. Primary Brain Region Affected</h4>
            <p><span class="clinical-label">Anatomical localization:</span> {escape(info['short_region'])}</p>
            <p><span class="clinical-label">Structural vulnerability:</span> {escape(info['target_region'])}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with card_columns[2]:
    st.markdown(
        f"""
        <div class="clinical-card">
            <h4>3. Impact on the Human Body</h4>
            <p><span class="clinical-label">Clinical manifestations:</span></p>
            <p>{escape(info['core_impact'])}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
