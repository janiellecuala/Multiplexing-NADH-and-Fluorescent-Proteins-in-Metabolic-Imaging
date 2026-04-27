# Multiplexing NADH and Fluorescent Proteins in Metabolic Imaging

This repository contains analysis code and processing workflows accompanying:

**Cuala & Alberto et al. – *Mapping Cross-Excitation: Multiplexing NADH and Fluorescent Proteins in Metabolic Imaging***

---

## 🧠 Overview

Fluorescence lifetime imaging microscopy (FLIM) of NAD(P)H enables label-free assessment of cellular metabolic state. This repository provides computational workflows used to evaluate fluorescent protein (FP) cross-excitation and its impact on NADH lifetime measurements under two-photon excitation.

The repository is organized into two analysis modules:

* **Excitation and emission scan analysis**
* **Metabolic trajectory (phasor) analysis**

And contains the following example data: 

* **Really beautiful data. 

These workflows enable quantitative characterization of spectral cross-talk and its influence on metabolic FLIM measurements.

---

## 🔬 Analysis Workflow

```text
Raw microscopy data
    ↓
FIJI/ImageJ preprocessing and ROI selection
    ↓
Export of ROI-level measurements (CSV)
    ↓
Python-based analysis and visualization
    ↓
Final outputs:
    • Excitation scan plots
    • Emission scan preprocessing outputs
    • Phasor-based metabolic trajectory plots
```

---

## 📁 Repository Structure

```text
excitation_emission_scans/
    Fiji_ROI_csv_creation.ijm
    Fiji_Preprocessing.ijm
    py_preprocessing_stackCSV.py
    py_emscan_plot.py
    exScan_fluor.py

metabolic_trajectory/
    figure6_phasor_metabolic_trajectory.py
```

---

## ⚙️ Requirements

Python 3.9+ (tested)

Install dependencies:

```bash
pip install -r requirements.txt
```

Core dependencies:

* numpy
* pandas
* matplotlib
* scipy
* seaborn
* pillow
* tifffile
* openpyxl
* scikit-learn

---

## 📥 Input Data

Each analysis module expects a specific input format:

### Excitation / Emission Scans

* **Excitation input:** CSV files containing ROI intensity values across excitation wavelengths

* **Emission input:** microscopy image data (e.g., TIFF stacks)

* **Generated / processed using:**

```
excitation_emission_scans/Fiji_ROI_csv_creation.ijm
excitation_emission_scans/Fiji_Preprocessing.ijm
```

* CSV data should include:

  * intensity measurements per ROI
  * multiple columns corresponding to compartments
    (e.g., transfected nuclei, untransfected nuclei, cytoplasm)

* Multiple CSV files represent biological replicates

---

### Metabolic Trajectory (Phasor Analysis)

* **Input:** CSV files containing phasor coordinates

**Required columns:**

* `G_coordinate`
* `S_coordinate`

**Optional columns:**

* `Intensity`
* `Lifetime`

**Example:**

```csv
ROI,Intensity,Lifetime,G_coordinate,S_coordinate
Cell_1,1523,1.85,0.42,0.31
Cell_2,1398,2.10,0.38,0.28
Cell_3,1672,1.65,0.47,0.34
```

* Each row corresponds to a single ROI
* Separate files represent distinct experimental conditions
* File paths are defined within scripts (e.g., `DATA_PATHS`)

---

## ▶️ Usage

### Excitation Scan Analysis

```bash
python excitation_emission_scans/py_preprocessing_stackCSV.py
python excitation_emission_scans/py_emscan_plot.py
```

Optional interactive visualization:

```bash
python excitation_emission_scans/exScan_fluor.py
```

This tool:

* normalizes intensity by laser power
* combines biological replicates
* propagates SEM
* applies log transformation and visualization

---

### Emission Scan Preprocessing

Run in FIJI/ImageJ:

```
excitation_emission_scans/Fiji_Preprocessing.ijm
```

---

### Metabolic Trajectory Analysis

```bash
python metabolic_trajectory/figure6_phasor_metabolic_trajectory.py
```

Generates phasor-based representations of metabolic state across conditions.

---

## ⚠️ Notes

* Fluorescent protein cross-excitation can introduce signal into the NADH detection channel under two-photon excitation
* Interpretation of lifetime and intensity measurements should account for spectral overlap
* Upstream preprocessing (e.g., phasor extraction) is assumed to be performed in Leica LAS X or equivalent software

---

## 🧾 Citation

If you use this code or workflow, please cite:

Cuala, J. & Alberto, O. et al. (2026)
*Mapping Cross-Excitation: Multiplexing NADH and Fluorescent Proteins in Metabolic Imaging*

---

## 🤝 Contact

For questions or data requests, please contact the corresponding author listed in the manuscript.
