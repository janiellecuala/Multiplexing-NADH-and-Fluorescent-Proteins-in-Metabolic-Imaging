# Multiplexing NADH and Fluorescent Proteins in Metabolic Imaging

This repository contains analysis code and processing workflows accompanying:

> **Cuala & Alberto et al.** – *Mapping Cross-Excitation: Multiplexing NADH and Fluorescent Proteins in Metabolic Imaging*

---

## 🧠 Overview

Fluorescence lifetime imaging microscopy (FLIM) of NAD(P)H enables label-free assessment of cellular metabolic state. This repository provides computational workflows used to evaluate fluorescent protein (FP) cross-excitation and its impact on NADH lifetime measurements under two-photon excitation.

The repository is organized into two analysis modules:

- **Excitation and emission scan analysis**
- **Metabolic trajectory (phasor) analysis**

These workflows enable quantitative characterization of spectral cross-talk and its influence on metabolic FLIM measurements.

---

## 🔬 Analysis Workflow

### Excitation and Emission Scan Pipeline

The same pipeline handles both scan types — select excitation or emission when prompted in `scan_fluor.py`.

```
Raw SP8 data (per-wavelength, per-channel .tif files)
    ↓
1. Assemble_ExScan_ch0_Stack.ijm
   — selects intensity channel (ch0)
   — assembles all wavelength steps into one stack
   — LA00 = 680nm, each step = +10nm, variable number of steps
    ↓
2. FijiROI_csvcreation.ijm
   — manual ROI drawing (transfected nuclei, untransfected nuclei, cytoplasm)
   — extracts mean intensity per ROI per wavelength
   — outputs one clean CSV per biological replicate
    ↓
3. scan_fluor.py  (select excitation or emission when prompted)
   — SP8 laser power normalization (see Calibration note below)
   — combines biological replicates with SEM propagation
   — log₁₀ transformation via delta method
   — generates plots with ±SEM shaded error bands
```

### Metabolic Trajectory Pipeline

```
Phasor coordinate CSV files
    ↓
metabolic_trajectory/figure6_phasor_metabolic_trajectory.py
   — phasor-based metabolic state visualization
```

---

## 📁 Repository Structure

```
repo/
├── Fiji_Preprocessing/
│   ├── Assemble_ExScan_ch0_Stack.ijm       # Step 1: assemble ch0 intensity stack from raw files
│   └── FijiROI_csvcreation.ijm             # Step 2: draw ROIs, extract intensities, export CSV
│
├── scan_fluor/
│   └── scan_fluor.py                       # Step 3: normalize, combine replicates, plot
│                                           # handles both excitation and emission scans
│
├── metabolic_trajectory/
│   └── figure6_phasor_metabolic_trajectory.py
│
├── data_example/
│   ├── raw/
│   │   ├── av-post2_LA00_ch0.tif           # Example raw SP8 files (av-post2, LA00–LA44)
│   │   ├── av-post2_LA00_ch1.tif           # ch0 = intensity, ch1–ch7 = other channels
│   │   └── ...                             # 680nm (LA00) to 1120nm (LA44), 8 channels each
│   ├── avGFP1_Results.csv                  # Example processed CSV — biological replicate 1
│   ├── avGFP2_Results.csv                  # Example processed CSV — biological replicate 2
│   └── SP8_Laser_power_measurements.csv    # SP8 laser power calibration (10% power, 2024-08-07)
│
├── requirements.txt
└── README.md
```

> **Note:** `preprocessing_stackCSV.py` and `emscanplot.py` are no longer part of the pipeline. `FijiROI_csvcreation.ijm` now outputs a clean CSV directly compatible with `scan_fluor.py`, which handles both excitation and emission scans.

---

## ⚙️ Requirements

Python 3.9+ (tested)

Install dependencies:

```bash
pip install -r requirements.txt
```

Core dependencies:

- `numpy`
- `pandas`
- `matplotlib`
- `scipy`
- `seaborn`
- `pillow`
- `tifffile`
- `openpyxl`

---

## 📥 Input Data

### Excitation and Emission Scans

Raw input files follow the SP8 naming convention:

```
{sampleName}_LA00_ch0.tif   →  680 nm
{sampleName}_LA01_ch0.tif   →  690 nm
{sampleName}_LA02_ch0.tif   →  700 nm
...
```

All files for one sample should be in a single folder. `LA00` always corresponds to 680 nm; the number of wavelength steps varies per experiment (e.g. avGFP1/avGFP2 example data = 11 steps / 680–780 nm; av-post2 raw example = 45 steps / 680–1120 nm). The pipeline handles any number of steps automatically.

The same folder structure and Fiji macros are used for both excitation and emission scans. Scan type is specified at the Python step.

After Fiji preprocessing, each biological replicate produces one CSV with the following structure:

```
Wavelength_nm, Mean(trans_nuc1), Mean(trans_nuc2), Mean(untrans_nuc1), Mean(cyto1), ...
680,            245.3,            231.1,             102.1,              88.4
690,            312.7,            298.4,             110.3,              91.2
...
```

ROI naming convention used during manual segmentation:

| Compartment | Naming pattern |
|---|---|
| Transfected nuclei | `trans_nuc1`, `trans_nuc2`, ... |
| Untransfected nuclei | `untrans_nuc1`, `untrans_nuc2`, ... |
| Cytoplasm | `cyto1`, `cyto2`, ... |

Multiple CSV files (one per biological replicate) are passed to `scan_fluor.py` for combined analysis.

### Metabolic Trajectory (Phasor Analysis)

Input: CSV files containing phasor coordinates per ROI.

Required columns:

- `G_coordinate`
- `S_coordinate`

Optional columns:

- `Intensity`
- `Lifetime`

Example:

```
ROI,Intensity,Lifetime,G_coordinate,S_coordinate
Cell_1,1523,1.85,0.42,0.31
Cell_2,1398,2.10,0.38,0.28
Cell_3,1672,1.65,0.47,0.34
```

Each row corresponds to a single ROI. Separate files represent distinct experimental conditions. File paths are defined within the script (`DATA_PATHS`).

> Upstream phasor extraction is assumed to be performed in Leica LAS X or equivalent software.

---

## ▶️ Usage

### Step 1 — Assemble intensity stack (Fiji)

Open Fiji, drag in `Assemble_ExScan_ch0_Stack.ijm` and run. When prompted:
- Select the folder containing raw `.tif` files
- Enter the sample name exactly as it appears in the filenames (e.g. `av-post2`)

This produces a single stack with slices labeled by wavelength, ready for ROI drawing.

### Step 2 — Draw ROIs and export CSV (Fiji)

With the assembled stack open, run `FijiROI_csvcreation.ijm`. When prompted:
- Draw ROIs for each compartment using any selection tool
- Name each ROI following the convention above (`trans_nuc1`, `untrans_nuc1`, `cyto1`, etc.)
- Click OK when all ROIs are added

Outputs one CSV file per biological replicate.

### Step 3 — Scan analysis (Python)

```bash
python scan_fluor/scan_fluor.py
```

The script will interactively prompt for:
- Scan type (excitation or emission)
- Fluorophore name
- Number of biological replicates
- File path to each replicate CSV
- Output filename and DPI

This script:
- Normalizes intensity by SP8 laser power (calibration values embedded — see Calibration note)
- Combines biological replicates and propagates SEM
- Applies log₁₀ transformation via the delta method
- Generates and saves plots with ±SEM shaded error bands

### Metabolic Trajectory Analysis (Python)

```bash
python metabolic_trajectory/figure6_phasor_metabolic_trajectory.py
```

Generates phasor-based representations of metabolic state across conditions.

---

## ⚠️ Notes

- Fluorescent protein cross-excitation can introduce signal into the NADH detection channel under two-photon excitation
- Interpretation of lifetime and intensity measurements should account for spectral overlap
- **Calibration:** Laser power normalization values in `scan_fluor.py` are specific to the SP8 system used in this study (10% laser power, measured 2024-08-07). If using a different instrument or acquisition date, replace the `LASER_POWERS` dictionary in `scan_fluor.py` with your own calibration measurements

---

## 🧾 Citation

If you use this code or workflow, please cite:

> Cuala, J. & Alberto, O. et al. (2026). *Mapping Cross-Excitation: Multiplexing NADH and Fluorescent Proteins in Metabolic Imaging.*

---

## 🤝 Contact

For questions or data requests, please contact the corresponding author listed in the manuscript.
