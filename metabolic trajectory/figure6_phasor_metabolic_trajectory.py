"""
Figure 6: Maximum Metabolic Phasor Plot
Cuala et al. - Mapping Cross-Excitation: Multiplexing NADH and Fluorescent Proteins

Generates a phasor plot showing:
  - Gray encompassing envelope (50th percentile convex hull, smoothed)
  - Individual condition ellipses (25th percentile, smoothed)
  - Two subpopulations for High Glucose + Drug (via GMM)
  - Universal semicircle reference
  - Metabolic trajectory (free NADH endpoint)

Dependencies: numpy, pandas, matplotlib, scipy, sklearn
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Arc, Polygon, Circle
from scipy.spatial import ConvexHull
from scipy.interpolate import splprep, splev
from sklearn.mixture import GaussianMixture
import warnings
warnings.filterwarnings('ignore')

# ── Data paths ─────────────────────────────────────────────────────────────────
DATA_PATHS = {
    'Baseline':            '/mnt/project/Baseline_coordinates.csv',
    'Low Glucose':         '/mnt/project/Low_Glucose_coordinates.csv',
    'High Glucose':        '/mnt/project/High_Glucose_coordinates.csv',
    'High Glucose + Drug': '/mnt/project/High_Glucose__Drug_coordinates.csv',
}

# ── Appearance ──────────────────────────────────────────────────────────────────
COLORS = {
    'Baseline':               '#5DADE2',   # blue
    'Low Glucose':            '#F39C12',   # orange
    'High Glucose':           '#52BE80',   # green
    'High Glucose + Drug Pop 1': '#E74C3C',  # red
    'High Glucose + Drug Pop 2': '#C0392B',  # dark red
}

ENVELOPE_PERCENTILE    = 50   # gray encompassing envelope
INDIVIDUAL_PERCENTILE  = 25   # per-condition ellipses
ENVELOPE_SMOOTHING     = 5.0  # spline smoothing factor for gray envelope
ELLIPSE_SMOOTHING      = 0.001  # spline smoothing factor for individual ellipses
N_SPLINE_POINTS        = 300  # output points after smoothing


# ── Helper functions ────────────────────────────────────────────────────────────

def mahalanobis_envelope(g, s, percentile):
    """
    Return (hull_g, hull_s) points that form the boundary of the
    Mahalanobis-distance percentile envelope for a 2-D dataset.
    """
    data = np.column_stack([g, s])
    mean = data.mean(axis=0)
    cov  = np.cov(data.T)
    inv_cov = np.linalg.inv(cov)

    # Mahalanobis distance for every point
    diff      = data - mean
    distances = np.sqrt(np.einsum('ij,jk,ik->i', diff, inv_cov, diff))
    threshold = np.percentile(distances, percentile)

    # Eigendecomposition → axis-aligned ellipse points
    eigenvalues, eigenvectors = np.linalg.eig(cov)
    angle  = np.degrees(np.arctan2(eigenvectors[1, 0], eigenvectors[0, 0]))
    width  = 2 * threshold * np.sqrt(eigenvalues[0])
    height = 2 * threshold * np.sqrt(eigenvalues[1])

    t         = np.linspace(0, 2 * np.pi, 200, endpoint=False)
    cos_a, sin_a = np.cos(np.radians(angle)), np.sin(np.radians(angle))
    x = (width  / 2) * np.cos(t)
    y = (height / 2) * np.sin(t)
    hull_g = cos_a * x - sin_a * y + mean[0]
    hull_s = sin_a * x + cos_a * y + mean[1]
    return hull_g, hull_s


def smooth_polygon(pts, smoothing_factor, n_out=N_SPLINE_POINTS):
    """
    Smooth a closed polygon (N x 2 array) using periodic spline interpolation.
    pts must NOT include a closing duplicate point (per=True handles closure).
    smoothing_factor: absolute spline smoothing value (larger = smoother).
    Returns an (n_out x 2) array.
    """
    try:
        tck, _ = splprep([pts[:, 0], pts[:, 1]],
                         s=smoothing_factor, per=True, k=3)
    except Exception:
        # Fallback with more smoothing
        tck, _ = splprep([pts[:, 0], pts[:, 1]],
                         s=smoothing_factor * 10, per=True, k=3)
    u_new = np.linspace(0, 1, n_out)
    sx, sy = splev(u_new, tck)
    return np.column_stack([sx, sy])


# ── Load data ───────────────────────────────────────────────────────────────────
print("Loading data …")
all_data = {name: pd.read_csv(path) for name, path in DATA_PATHS.items()}

# ── GMM split for High Glucose + Drug ──────────────────────────────────────────
X_drug  = all_data['High Glucose + Drug'][['G_coordinate', 'S_coordinate']].values
gmm     = GaussianMixture(n_components=2, random_state=42, covariance_type='full')
labels  = gmm.fit_predict(X_drug)

# Assign population labels so that Pop 1 has the larger G (more glycolytic)
mean0 = X_drug[labels == 0, 0].mean()
mean1 = X_drug[labels == 1, 0].mean()
if mean0 < mean1:          # flip so Pop 1 = higher G
    labels = 1 - labels

drug_pop1 = all_data['High Glucose + Drug'][labels == 0]
drug_pop2 = all_data['High Glucose + Drug'][labels == 1]
print(f"  HG+Drug Pop 1  n={len(drug_pop1):>5}  "
      f"G={drug_pop1['G_coordinate'].mean():.3f}  "
      f"S={drug_pop1['S_coordinate'].mean():.3f}")
print(f"  HG+Drug Pop 2  n={len(drug_pop2):>5}  "
      f"G={drug_pop2['G_coordinate'].mean():.3f}  "
      f"S={drug_pop2['S_coordinate'].mean():.3f}")

# ── Build per-condition dataset list ───────────────────────────────────────────
datasets = {
    'Baseline':               all_data['Baseline'],
    'Low Glucose':            all_data['Low Glucose'],
    'High Glucose':           all_data['High Glucose'],
    'High Glucose + Drug Pop 1': drug_pop1,
    'High Glucose + Drug Pop 2': drug_pop2,
}

# ── Compute gray encompassing envelope ─────────────────────────────────────────
print(f"Building {ENVELOPE_PERCENTILE}th-percentile encompassing envelope …")
all_envelope_pts = []

for name, df in datasets.items():
    g, s = df['G_coordinate'].values, df['S_coordinate'].values
    eg, es = mahalanobis_envelope(g, s, ENVELOPE_PERCENTILE)
    all_envelope_pts.append(np.column_stack([eg, es]))

all_envelope_pts = np.vstack(all_envelope_pts)
gray_hull_idx    = ConvexHull(all_envelope_pts).vertices
gray_hull_pts    = all_envelope_pts[gray_hull_idx]
gray_smooth      = smooth_polygon(gray_hull_pts, ENVELOPE_SMOOTHING)

# ── Compute individual-condition ellipses ───────────────────────────────────────
print(f"Building {INDIVIDUAL_PERCENTILE}th-percentile individual ellipses …")
individual_ellipses = {}
for name, df in datasets.items():
    g, s = df['G_coordinate'].values, df['S_coordinate'].values
    eg, es = mahalanobis_envelope(g, s, INDIVIDUAL_PERCENTILE)
    raw = np.column_stack([eg, es])
    individual_ellipses[name] = smooth_polygon(raw, ELLIPSE_SMOOTHING)

# ── Compute condition mean points ───────────────────────────────────────────────
means = {name: (df['G_coordinate'].mean(), df['S_coordinate'].mean())
         for name, df in datasets.items()}

# ── Plot ────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 8), facecolor='white')
ax.set_facecolor('white')

# Universal semicircle
semicircle = Arc(xy=(0.5, 0), width=1.0, height=1.0,
                 angle=0, theta1=0, theta2=180,
                 color='black', linewidth=2.5)
ax.add_patch(semicircle)

# Free-NADH endpoint on circle  (τ = 0.4 ns → ω·τ at 80 MHz)
omega = 2 * np.pi * 80e6          # rad/s  (80 MHz laser rep rate)
tau_free = 0.4e-9                  # 0.4 ns
g_free = 1 / (1 + (omega * tau_free)**2)
s_free = (omega * tau_free) / (1 + (omega * tau_free)**2)
ax.plot(g_free, s_free, 'o', color='black', markersize=7,
        zorder=6, label=f'Free NADH (0.4 ns)')

# Gray encompassing envelope
gray_poly = Polygon(gray_smooth, closed=True,
                    facecolor='lightgray', edgecolor='darkgray',
                    alpha=0.35, linewidth=2, zorder=2,
                    label=f'Metabolic space ({ENVELOPE_PERCENTILE}th %ile)')
ax.add_patch(gray_poly)

# Individual condition ellipses + mean markers
legend_handles = []
for name, smooth_pts in individual_ellipses.items():
    color = COLORS[name]
    ellipse_poly = Polygon(smooth_pts, closed=True,
                           facecolor='none', edgecolor=color,
                           linewidth=2.5, alpha=0.9, zorder=4)
    ax.add_patch(ellipse_poly)

    gm, sm = means[name]
    ax.plot(gm, sm, 'o', color=color, markersize=9,
            markeredgecolor='white', markeredgewidth=0.8, zorder=5)

    patch = mpatches.Patch(facecolor='none', edgecolor=color,
                           linewidth=2.5, label=name)
    legend_handles.append(patch)

# Axes formatting
ax.set_xlim(0.0, 1.0)
ax.set_ylim(0.0, 0.52)
ax.set_aspect('equal')
ax.set_xlabel('G', fontsize=14, fontweight='bold')
ax.set_ylabel('S', fontsize=14, fontweight='bold')
ax.tick_params(labelsize=12)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(False)

# Legend
gray_handle = mpatches.Patch(facecolor='lightgray', edgecolor='darkgray',
                              linewidth=1.5, alpha=0.6,
                              label=f'Metabolic space ({ENVELOPE_PERCENTILE}th %ile)')
legend_handles = [gray_handle] + legend_handles
ax.legend(handles=legend_handles, loc='upper left',
          fontsize=9, frameon=True, edgecolor='gray', framealpha=0.9)

plt.tight_layout()

# ── Save ────────────────────────────────────────────────────────────────────────
out_base = 'figure6_phasor_metabolic_trajectory'
for ext in ('png', 'svg', 'pdf'):
    path = f'/mnt/user-data/outputs/{out_base}.{ext}'
    dpi  = 300 if ext == 'png' else None
    plt.savefig(path, dpi=dpi, bbox_inches='tight')
    print(f"  Saved → {path}")

print("Done.")
