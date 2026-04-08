"""
exScan_fluor.py
---------------
Excitation scan fluorescence visualization script.
Normalizes intensity data by laser power (SP8), combines technical and
biological replicates, propagates SEM, log-transforms, and plots.

Usage: Run in Spyder. Follow the prompts.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# ---------------------------------------------------------------------------
# Laser power map (SP8, 10% setting) — embedded so no file load needed
# ---------------------------------------------------------------------------
LASER_POWER_MAP = {
    680: 4.0, 690: 6.5, 700: 6.6, 710: 6.3, 720: 6.3,
    730: 7.0, 740: 8.5, 750: 11.0, 760: 13.2, 770: 13.7,
    780: 13.5, 790: 13.8, 800: 15.4, 810: 17.7, 820: 19.5,
    830: 23.1, 840: 22.4, 850: 22.7, 860: 22.5, 870: 20.0,
    880: 18.5, 890: 17.5, 900: 17.0, 910: 16.3, 920: 16.7,
    930: 16.2, 940: 17.2, 950: 17.1, 960: 16.1, 970: 15.9,
    980: 16.1, 990: 15.4, 1000: 14.1,
}

WAVELENGTH_START = 680   # nm for row 1
WAVELENGTH_STEP  = 10    # nm per row
WAVELENGTH_RANGE = (680, 780)

COMPARTMENT_COLORS = {
    'transfected':   '#8B008B',   # dark magenta
    'untransfected': '#2E8B57',   # sea green
    'cytoplasm':     '#1E90FF',   # dodger blue
}

COMPARTMENT_LABELS = {
    'transfected':   'Transfected Nuclei',
    'untransfected': 'Untransfected Nuclei',
    'cytoplasm':     'Cytoplasm',
}


# ---------------------------------------------------------------------------
# Column detection
# ---------------------------------------------------------------------------

def detect_columns(headers):
    """
    Returns dict: {'transfected': [...], 'untransfected': [...], 'cytoplasm': [...]}
    Priority: cytoplasm first (contains 'cyto'), then transfected vs untransfected
    by checking for 'untransfected' keyword (which also contains 'transfected').
    """
    compartments = {'transfected': [], 'untransfected': [], 'cytoplasm': []}

    for h in headers:
        hl = h.lower()
        if 'cyto' in hl:
            compartments['cytoplasm'].append(h)
        elif 'untransfected' in hl and 'nuc' in hl:
            compartments['untransfected'].append(h)
        elif 'transfected' in hl and 'nuc' in hl:
            compartments['transfected'].append(h)

    return compartments


# ---------------------------------------------------------------------------
# Processing one file (one biological replicate)
# ---------------------------------------------------------------------------

def process_file(filepath):
    """
    Read a results CSV, assign wavelengths, filter to 680-780 nm,
    normalise by laser power, and return per-compartment (mean, sem) per wavelength.

    Returns:
        dict keyed by compartment name ->
            list of dicts: {wavelength, mean, sem}
    """
    df = pd.read_csv(filepath, index_col=0)

    # Assign wavelengths
    wavelengths = [WAVELENGTH_START + i * WAVELENGTH_STEP for i in range(len(df))]
    df['wavelength'] = wavelengths

    # Filter to desired range
    mask = (df['wavelength'] >= WAVELENGTH_RANGE[0]) & (df['wavelength'] <= WAVELENGTH_RANGE[1])
    df = df[mask].copy()

    compartment_cols = detect_columns(df.columns.tolist())

    result = {}
    for compartment, cols in compartment_cols.items():
        if not cols:
            continue
        rows = []
        for _, row in df.iterrows():
            wl = int(row['wavelength'])
            lp = LASER_POWER_MAP.get(wl, np.nan)
            if np.isnan(lp) or lp == 0:
                continue

            values = [row[c] for c in cols if not np.isnan(row[c])]
            if not values:
                continue

            mean_raw = np.mean(values)
            n = len(values)
            sem_raw = (np.std(values, ddof=1) / np.sqrt(n)) if n > 1 else 0.0

            mean_norm = mean_raw / lp
            sem_norm  = sem_raw  / lp

            rows.append({'wavelength': wl, 'mean': mean_norm, 'sem': sem_norm})
        result[compartment] = rows

    return result


# ---------------------------------------------------------------------------
# Combine biological replicates
# ---------------------------------------------------------------------------

def combine_replicates(replicate_results):
    """
    replicate_results: list of dicts returned by process_file()
    For each compartment and wavelength, combine means and propagate SEM.

    SEM propagation:
        combined_mean = mean of bio replicate means
        combined_sem  = sqrt( sum(tech_sem^2) + bio_SEM^2 )
    """
    # Collect all compartments across replicates
    all_compartments = set()
    for r in replicate_results:
        all_compartments.update(r.keys())

    combined = {}
    for compartment in all_compartments:
        # Build wavelength -> list of (mean, sem) across replicates
        wl_data = {}
        for rep in replicate_results:
            if compartment not in rep:
                continue
            for entry in rep[compartment]:
                wl = entry['wavelength']
                wl_data.setdefault(wl, []).append((entry['mean'], entry['sem']))

        rows = []
        for wl in sorted(wl_data.keys()):
            pairs = wl_data[wl]
            valid_means  = [p[0] for p in pairs if not np.isnan(p[0])]
            valid_sems   = [p[1] for p in pairs if not np.isnan(p[1])]

            if not valid_means:
                continue

            combined_mean = np.mean(valid_means)
            n_bio = len(valid_means)

            # Biological SEM
            if n_bio > 1:
                bio_sem = np.std(valid_means, ddof=1) / np.sqrt(n_bio)
            else:
                bio_sem = 0.0

            # Technical error propagation
            tech_sem_sq = sum(s**2 for s in valid_sems)

            combined_sem = np.sqrt(tech_sem_sq + bio_sem**2)

            rows.append({'wavelength': wl, 'mean': combined_mean, 'sem': combined_sem})

        combined[compartment] = rows

    return combined


# ---------------------------------------------------------------------------
# Log transform
# ---------------------------------------------------------------------------

def log_transform(combined):
    """
    Apply log10 to means; propagate SEM via delta method:
        sem_log = sem_linear / (value * ln(10))
    """
    result = {}
    for compartment, rows in combined.items():
        log_rows = []
        for entry in rows:
            m = entry['mean']
            s = entry['sem']
            if m <= 0:
                continue
            log_mean = np.log10(m)
            log_sem  = s / (m * np.log(10))
            log_rows.append({'wavelength': entry['wavelength'],
                              'mean': log_mean, 'sem': log_sem})
        result[compartment] = log_rows
    return result


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_fluorophore(log_data, fluorophore_name, output_path=None, dpi=300):
    """
    Plot log-normalised excitation spectrum with ±SEM error bands.
    """
    fig, ax = plt.subplots(figsize=(8, 5))

    for compartment, rows in log_data.items():
        if not rows:
            continue
        wls   = [r['wavelength'] for r in rows]
        means = [r['mean']       for r in rows]
        sems  = [r['sem']        for r in rows]
        lower = [m - s for m, s in zip(means, sems)]
        upper = [m + s for m, s in zip(means, sems)]

        color = COMPARTMENT_COLORS.get(compartment, 'gray')
        label = COMPARTMENT_LABELS.get(compartment, compartment)

        ax.plot(wls, means, color=color, linewidth=2, label=label)
        ax.fill_between(wls, lower, upper, color=color, alpha=0.2)

    ax.set_xlabel('Excitation Wavelength (nm)', fontsize=12)
    ax.set_ylabel('Log\u2081\u2080 (Normalised Intensity)', fontsize=12)
    ax.set_title(f'Excitation Spectrum — {fluorophore_name}', fontsize=13)
    ax.set_xlim(*WAVELENGTH_RANGE)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(fontsize=10)
    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=dpi, bbox_inches='tight')
        print(f"  Figure saved: {output_path}")

    return fig, ax


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 55)
    print("  Excitation Scan Fluorescence Visualisation Tool")
    print("=" * 55)

    while True:
        print("\nEnter fluorophore name (or 'quit' to exit):")
        name = input("  > ").strip()
        if name.lower() in ('quit', 'q', ''):
            break

        print(f"\nHow many biological replicates for {name}?")
        try:
            n_reps = int(input("  > ").strip())
        except ValueError:
            print("  Invalid number. Skipping.")
            continue

        replicate_results = []
        for i in range(1, n_reps + 1):
            print(f"\n  Path to CSV file for replicate {i}:")
            filepath = input("  > ").strip().strip('"').strip("'")
            if not os.path.exists(filepath):
                print(f"  File not found: {filepath}. Skipping replicate.")
                continue
            try:
                res = process_file(filepath)
                replicate_results.append(res)
                print(f"  Replicate {i} loaded OK.")
            except Exception as e:
                print(f"  Error reading file: {e}")

        if not replicate_results:
            print("  No valid replicates loaded. Skipping fluorophore.")
            continue

        combined  = combine_replicates(replicate_results)
        log_data  = log_transform(combined)

        # Output filename
        default_out = f"{name}_excitation_scan.png"
        print(f"\nSave figure? Enter filename (default: {default_out}), or press Enter:")
        out_name = input("  > ").strip()
        if out_name == '':
            out_name = default_out

        print("DPI? (default 300):")
        dpi_input = input("  > ").strip()
        dpi = int(dpi_input) if dpi_input.isdigit() else 300

        fig, ax = plot_fluorophore(log_data, name, output_path=out_name, dpi=dpi)

        print("Show figure now? (y/n):")
        if input("  > ").strip().lower() == 'y':
            plt.show()
        else:
            plt.close(fig)

        print(f"\n  Done with {name}.")

    print("\nAll done. Goodbye!")


if __name__ == "__main__":
    main()
