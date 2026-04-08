# Multiplexing NADH and Fluorescent Proteins in Metabolic Imaging

This repository contains analysis code, example datasets, and processing workflows accompanying:

**Cuala & Alberto et al. – *Mapping Cross-Excitation: Multiplexing NADH and Fluorescent Proteins in Metabolic Imaging***

---

## 🧠 Overview

Fluorescence lifetime imaging microscopy (FLIM) of NAD(P)H enables label-free assessment of cellular metabolism. This project investigates how fluorescent proteins (FPs) interfere with NADH lifetime measurements under two-photon excitation and provides a computational pipeline for analyzing these effects.

Specifically, this repository supports:

* Quantification of excitation and emission spectra
* Analysis of fluorescence lifetime (FLIM) data using phasor-based approaches
* Extraction of ROI-based measurements from microscopy images
* Reproduction of key plots (e.g., excitation scans, intensity comparisons)

---

## 🔬 Analysis Workflow

The general analysis pipeline used in this study is:

```
Raw microscopy images
    ↓
FIJI/ImageJ ROI selection (macros provided)
    ↓
Exported CSV data (intensity, lifetime, G/S coordinates)
    ↓
Python-based processing and plotting
    ↓
Final figures (e.g., excitation scans, comparisons across FPs)
```

---

## 📁 Repository Structure

```
data_example/
    Example datasets for testing the pipeline

scripts/
    Python scripts for data processing, normalization, and plotting

fiji_macros/
    ImageJ/FIJI macros for ROI selection and batch processing

results_reproduction/
    Organized scripts and workflows for reproducing specific figures

docs/
    Additional documentation and workflow explanations (if applicable)
```

---

## ⚙️ Requirements

Python 3.x

Install dependencies using:

```
pip install -r requirements.txt
```

Typical dependencies include:

* numpy
* pandas
* matplotlib
* scipy

---

## ▶️ Getting Started

### 1. Extract ROIs from images

Use FIJI/ImageJ and run:

```
fiji_macros/ROI_extraction.ijm
```

This will generate CSV files containing:

* fluorescence intensity
* lifetime values
* phasor coordinates (G and S)

---

### 2. Run analysis scripts

Example: excitation scan analysis

```
python scripts/excitation_scan_analysis.py
```

This script:

* reads CSV data
* normalizes intensity values
* averages replicates
* generates plots comparable to those shown in the manuscript

Each folder contains:

* input data (or example data)
* analysis scripts
* expected outputs

---

## 📊 Notes on Data

* `data_example/` contains representative datasets for demonstration
* Full raw datasets are not included due to size but are available upon reasonable request
* Data processing steps follow those described in the Methods section of the manuscript

---

## ⚠️ Important Considerations

* Fluorescent protein cross-talk can introduce signal into the NADH channel under two-photon excitation
* Careful interpretation of lifetime and intensity data is required, especially when multiplexing
* This pipeline assumes preprocessing (e.g., phasor extraction) has been performed in Leica LAS X or equivalent software

---

## 🧾 Citation

If you use this code or workflow, please cite:

Cuala, J. & Alberto, O. et al. (2025)
*Mapping Cross-Excitation: Multiplexing NADH and Fluorescent Proteins in Metabolic Imaging*

---

## 🤝 Contact

For questions, data requests, or collaboration inquiries, please contact the corresponding author listed in the manuscript.
