# Multiplexing NADH and Fluorescent Proteins in Metabolic Imaging

This repository contains analysis code and processing workflows accompanying:

**Cuala & Alberto et al. – *Mapping Cross-Excitation: Multiplexing NADH and Fluorescent Proteins in Metabolic Imaging***

---

## 🧠 Overview

Fluorescence lifetime imaging microscopy (FLIM) of NAD(P)H enables label-free assessment of cellular metabolic state. This repository provides the computational workflows used to evaluate fluorescent protein (FP) cross-excitation and its impact on NADH lifetime measurements under two-photon excitation.

The repository is organized into three analysis modules:

* **Excitation scan analysis**
* **Emission scan preprocessing**
* **Metabolic trajectory (phasor) analysis**

Together, these workflows support quantitative characterization of spectral cross-talk and its effects on metabolic FLIM measurements.

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
excitation_scan/
    Fiji_ROI_csv_creation.ijm
    py_preprocessing_stackCSV.py
    py_emscan_plot.py

emission_scan/
    Fiji_Preprocessing.ijm

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

### Excitation Scan

* **Input:** CSV files generated from ROI-based measurements
* **Source:** FIJI/ImageJ (`Fiji_ROI_csv_creation.ijm`)
* **Content:** intensity values across excitation wavelengths

---

### Emission Scan

* **Input:** microscopy image data (e.g., TIFF stacks)
* **Processing:** performed in FIJI/ImageJ (`Fiji_Preprocessing.ijm`)
* **Note:** this repository includes preprocessing macros; downstream analysis depends on acquisition-specific workflows

---

### Metabolic Trajectory (Phasor Analysis)

* **Input:** CSV files containing phasor coordinates

**Required columns:**

* `G_coordinate`
* `S_coordinate`

* Each row corresponds to a single ROI
* Separate files represent distinct experimental conditions
* File paths should be specified within analysis scripts (e.g., `DATA_PATHS`)

---

## ▶️ Usage

### Excitation Scan Analysis

```bash
python excitation_scan/py_preprocessing_stackCSV.py
python excitation_scan/py_exscan_plot.py
```

---

### Emission Scan Preprocessing

Run in FIJI/ImageJ:

```
emission_scan/Fiji_Preprocessing.ijm
python excitation_scan/py_emscan_plot.py
```

---

### Metabolic Trajectory Analysis

```bash
python metabolic_trajectory/figure6_phasor_metabolic_trajectory.py
```

This workflow generates phasor-based representations of metabolic state across experimental conditions.

---

## ⚠️ Notes

* Fluorescent protein cross-excitation can introduce signal into the NADH detection channel under two-photon excitation
* Interpretation of lifetime and intensity measurements should account for potential spectral overlap
* Upstream preprocessing (e.g., phasor extraction) is assumed to be performed in Leica LAS X or equivalent software

---

## 🧾 Citation

If you use this code or workflow, please cite:

Cuala, J. & Alberto, O. et al. (2026)
*Mapping Cross-Excitation: Multiplexing NADH and Fluorescent Proteins in Metabolic Imaging*

---

## 🤝 Contact

For questions or data requests, please contact the corresponding author listed in the manuscript.
