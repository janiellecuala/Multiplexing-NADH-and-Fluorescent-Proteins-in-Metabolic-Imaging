"""
scan_fluor.py
-------------
Unified fluorescence scan visualization script for excitation and emission scans.

Handles:
  - SP8 laser power normalization (instrument-specific — see CALIBRATION NOTE below)
  - Combining technical replicates within a biological replicate (mean ± SEM)
  - Combining biological replicates with SEM propagation
  - Log₁₀ transformation via the delta method
  - Plotting with shaded ±SEM error bands per cellular compartment

Compartments detected automatically from column names:
  - Transfected nuclei   : columns containing 'trans' but not 'untrans'
  - Untransfected nuclei : columns containing 'untrans' and 'nuc'
  - Cytoplasm            : columns containing 'cyto'

Input CSV format (output of FijiROI_csvcreation.ijm):
  Wavelength_nm, Mean(trans_nuc1), Mean(trans_nuc2), Mean(untrans_nuc1), Mean(cyto1), ...
  680,            245.3,            231.1,             102.1,              88.4
  690,            ...

Usage:
  Run in terminal or Spyder: python scan_fluor.py
  Follow the interactive prompts.

CALIBRATION NOTE:
  Laser power values below are specific to the SP8 system used in this study
  (measurements taken 2024-08-07 at 10% laser power).
  If using a different instrument or date, replace the LASER_POWERS dictionary
  with your own calibration measurements.

@faldalf
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats


# ── Instrument calibration ────────────────────────────────────────────────────
# SP8 laser power measurements at 10% — replace with your own if using
# a different instrument or acquisition date.
LASER_POWERS = {
    680: 4.0,    690: 6.5,    700: 6.6,    710: 6.3,    720: 6.3,
    730: 7.0,    740: 8.5,    750: 11.0,   760: 13.2,   770: 13.7,
    780: 13.5,   790: 13.8,   800: 15.4,   810: 17.7,   820: 19.5,
    830: 23.1,   840: 22.4,   850: 22.7,   860: 22.5,   870: 20.0,
    880: 18.5,   890: 17.5,   900: 17.0,   910: 16.3,   920: 16.7,
    930: 16.2,   940: 17.2,   950: 17.1,   960: 16.1,   970: 15.9,
    980: 16.1,   990: 15.4,   1000: 14.1,  1010: 13.2,  1020: 10.9,
    1030: 8.76,  1040: 7.48,  1050: 5.57,  1060: 4.85,  1070: 3.97,
    1080: 3.51,  1090: 1.53,  1100: 1.41,  1110: 1.15,  1120: 0.735,
    1130: 0.629, 1140: 0.455, 1150: 0.403
}

# ── Compartment colors ────────────────────────────────────────────────────────
COMPARTMENT_COLORS = {
    'transfected_nuc':   '#2196F3',   # blue
    'untransfected_nuc': '#F44336',   # red
    'cytoplasm':         '#4CAF50',   # green
}

COMPARTMENT_LABELS = {
    'transfected_nuc':   'Transfected Nuclei',
    'untransfected_nuc': 'Untransfected Nuclei',
    'cytoplasm':         'Cytoplasm',
}


# ── Laser power helpers ───────────────────────────────────────────────────────
def get_laser_power(wavelength):
    """Return laser power for the closest calibrated wavelength."""
    closest = min(LASER_POWERS.keys(), key=lambda w: abs(w - wavelength))
    return LASER_POWERS[closest]


# ── Column detection ──────────────────────────────────────────────────────────
def detect_compartment_columns(df):
    """
    Auto-detect which columns belong to each compartment.
    Returns dict: {'transfected_nuc': [...], 'untransfected_nuc': [...], 'cytoplasm': [...]}
    """
    compartments = {
        'transfected_nuc':   [],
        'untransfected_nuc': [],
        'cytoplasm':         [],
    }

    for col in df.columns:
        col_lower = col.lower()
        if 'wavelength' in col_lower:
            continue
        if 'untrans' in col_lower and 'nuc' in col_lower:
            compartments['untransfected_nuc'].append(col)
        elif 'cyto' in col_lower:
            compartments['cytoplasm'].append(col)
        elif 'trans' in col_lower and 'nuc' in col_lower:
            compartments['transfected_nuc'].append(col)

    return compartments


# ── Wavelength extraction ─────────────────────────────────────────────────────
def get_wavelengths(df):
    """
    Extract wavelength values from the dataframe.
    Looks for a 'Wavelength' column first; if absent, infers from row index
    starting at 680nm in 10nm steps.
    """
    for col in df.columns:
        if 'wavelength' in col.lower():
            return df[col].values.astype(float)
    # Fallback: infer from row index
    print("  Warning: No Wavelength column found — inferring 680nm + 10nm * row index.")
    return np.array([680 + i * 10 for i in range(len(df))], dtype=float)


# ── Single replicate processing ───────────────────────────────────────────────
def process_replicate(filepath):
    """
    Load one biological replicate CSV and return:
      wavelengths (array),
      compartment_data dict: {compartment: {'mean': array, 'sem': array}}
    """
    df = pd.read_csv(filepath, index_col=0)

    wavelengths = get_wavelengths(df)
    compartments = detect_compartment_columns(df)

    # Validate detection
    found = {k: v for k, v in compartments.items() if v}
    if not found:
        raise ValueError(
            f"No compartment columns detected in {filepath}.\n"
            "Expected column names containing: trans+nuc, untrans+nuc, or cyto."
        )

    print(f"  Detected compartments:")
    for comp, cols in found.items():
        print(f"    {COMPARTMENT_LABELS[comp]}: {cols}")

    compartment_data = {}

    for comp, cols in compartments.items():
        if not cols:
            continue

        values_matrix = df[cols].values.astype(float)  # shape: (n_wavelengths, n_tech_reps)

        # Normalize each column by laser power per wavelength
        normalized = np.zeros_like(values_matrix)
        for i, wl in enumerate(wavelengths):
            power = get_laser_power(wl)
            normalized[i, :] = values_matrix[i, :] / power

        # Combine technical replicates: mean and SEM per wavelength
        means = np.mean(normalized, axis=1)
        sems  = stats.sem(normalized, axis=1) if normalized.shape[1] > 1 else np.zeros(len(wavelengths))

        compartment_data[comp] = {'mean': means, 'sem': sems}

    return wavelengths, compartment_data


# ── Biological replicate combination ─────────────────────────────────────────
def combine_replicates(all_replicate_data):
    """
    Combine across biological replicates with SEM propagation.
    Input: list of (wavelengths, compartment_data) tuples from process_replicate()
    Returns: {compartment: {'mean': array, 'sem': array}}, wavelengths
    """
    wavelengths = all_replicate_data[0][0]
    compartments = list(all_replicate_data[0][1].keys())

    combined = {}

    for comp in compartments:
        rep_means = np.array([rep[1][comp]['mean'] for rep in all_replicate_data
                              if comp in rep[1]])
        rep_sems  = np.array([rep[1][comp]['sem']  for rep in all_replicate_data
                              if comp in rep[1]])

        n_bio = rep_means.shape[0]

        # Combined mean across biological replicates
        bio_mean = np.mean(rep_means, axis=0)

        # Propagate SEM: combine technical SEM (squared sum) + biological SEM
        tech_sem_sq   = np.sum(rep_sems ** 2, axis=0)
        bio_sem       = stats.sem(rep_means, axis=0) if n_bio > 1 else np.zeros(len(wavelengths))
        combined_sem  = np.sqrt(tech_sem_sq + bio_sem ** 2)

        combined[comp] = {'mean': bio_mean, 'sem': combined_sem}

    return wavelengths, combined


# ── Log₁₀ transform via delta method ─────────────────────────────────────────
def log_transform(wavelengths, combined_data):
    """
    Apply log₁₀ transformation with delta-method SEM propagation.
    SEM_log = SEM / (mean * ln(10))
    Values <= 0 are masked (set to NaN).
    """
    log_data = {}

    for comp, data in combined_data.items():
        mean = data['mean'].copy()
        sem  = data['sem'].copy()

        # Mask non-positive values
        valid = mean > 0
        log_mean = np.where(valid, np.log10(mean), np.nan)
        log_sem  = np.where(valid, sem / (mean * np.log(10)), np.nan)

        log_data[comp] = {'mean': log_mean, 'sem': log_sem}

    return wavelengths, log_data


# ── Plotting ──────────────────────────────────────────────────────────────────
def plot_scan(wavelengths, log_data, fluorophore_name, scan_type, output_path, dpi):
    """
    Plot log₁₀ normalized intensity vs wavelength with ±SEM shaded bands.
    scan_type: 'excitation' or 'emission'
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    for comp, data in log_data.items():
        mean = data['mean']
        sem  = data['sem']
        color = COMPARTMENT_COLORS[comp]
        label = COMPARTMENT_LABELS[comp]

        ax.plot(wavelengths, mean, color=color, linewidth=2, label=label)
        ax.fill_between(
            wavelengths,
            mean - sem,
            mean + sem,
            color=color,
            alpha=0.2
        )

    # Axis labels depend on scan type
    if scan_type == 'excitation':
        xlabel = 'Excitation Wavelength (nm)'
        title  = f'{fluorophore_name} — Excitation Scan'
    else:
        xlabel = 'Emission Wavelength (nm)'
        title  = f'{fluorophore_name} — Emission Scan'

    ax.set_xlabel(xlabel, fontsize=13, fontweight='bold')
    ax.set_ylabel('Log₁₀ Normalized Intensity', fontsize=13, fontweight='bold')
    ax.set_title(title, fontsize=15, fontweight='bold', pad=15)
    ax.legend(fontsize=11, framealpha=0.9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    fig.savefig(output_path, dpi=dpi, bbox_inches='tight')
    print(f"  Figure saved: {output_path}")

    return fig, ax


# ── Interactive main ──────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  scan_fluor.py — Fluorescence Scan Visualization")
    print("=" * 55)
    print()

    # Scan type
    print("Scan type:")
    print("  1. Excitation scan")
    print("  2. Emission scan")
    while True:
        choice = input("  Enter 1 or 2: ").strip()
        if choice == '1':
            scan_type = 'excitation'
            break
        elif choice == '2':
            scan_type = 'emission'
            break
        else:
            print("  Please enter 1 or 2.")

    print()

    # Fluorophore name
    fluorophore = input("Fluorophore name (e.g. avGFP, mCherry): ").strip()
    if not fluorophore:
        fluorophore = 'fluorophore'

    print()

    # Number of biological replicates
    while True:
        try:
            n_reps = int(input("Number of biological replicates: ").strip())
            if n_reps >= 1:
                break
            else:
                print("  Must be at least 1.")
        except ValueError:
            print("  Please enter a whole number.")

    print()

    # File paths
    replicate_data = []
    for i in range(n_reps):
        while True:
            path = input(f"  Path to replicate {i+1} CSV: ").strip()
            if os.path.exists(path):
                try:
                    print(f"  Loading replicate {i+1}...")
                    wl, comp_data = process_replicate(path)
                    replicate_data.append((wl, comp_data))
                    print(f"  Loaded: {len(wl)} wavelength points ({int(wl[0])}–{int(wl[-1])} nm)")
                    break
                except Exception as e:
                    print(f"  Error loading file: {e}")
                    print("  Please try again.")
            else:
                print(f"  File not found: {path}")

    print()
    print("Combining replicates and applying log₁₀ transform...")

    # Combine replicates
    wavelengths, combined = combine_replicates(replicate_data)

    # Log transform
    wavelengths, log_data = log_transform(wavelengths, combined)

    print("Done.")
    print()

    # Output filename
    default_out = f"{fluorophore}_{scan_type}_scan.png"
    out_input = input(f"Output filename (default: {default_out}): ").strip()
    output_path = out_input if out_input else default_out

    # DPI
    dpi_input = input("DPI (default: 300): ").strip()
    dpi = int(dpi_input) if dpi_input.isdigit() else 300

    print()
    print("Plotting...")

    fig, ax = plot_scan(wavelengths, log_data, fluorophore, scan_type, output_path, dpi)

    print()
    print("=" * 55)
    print("  Done!")
    print(f"  Wavelength range : {int(wavelengths[0])}–{int(wavelengths[-1])} nm")
    print(f"  Biological reps  : {n_reps}")
    print(f"  Output           : {output_path}")
    print("=" * 55)

    plt.show()


if __name__ == "__main__":
    main()
