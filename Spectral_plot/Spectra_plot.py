# -*- coding: utf-8 -*-
"""
Plot fluorescence emission spectra from Excel files.

The script allows selection of one or more .xlsx files, plots the raw
emission spectra, and generates a second plot with smoothed and normalized
emission spectra.

Expected Excel columns:
    Wavelength
    Ex.
    Em.

Author: Falk Schneider (@faldalf)
Date: 2024-08-30

"""

#%% Imports

import tkinter as tk
import tkinter.filedialog as fd
import os

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


#%% Functions

def make_filelist():
    """Open a file-selection dialog and return the selected Excel files."""

    root = tk.Tk()
    root.withdraw()

    files = fd.askopenfilenames(
        parent=root,
        title='Choose one or more files',
        multiple=True
    )

    files = list(files)

    # Adjust file paths depending on the operating system.
    for i in range(0, len(files)):
        if os.name == 'nt':
            files[i] = files[i].replace("/", "\\\\")
            print('Windows machine, file name modified!')

        elif os.name == 'posix':
            print('Not a Windows machine, file name not modified!')

    # Remove all selected files that are not Excel files.
    xlsx_files = [
        file for file in files
        if file.lower().endswith('.xlsx')
    ]

    return xlsx_files


def moving_average(data, window_size):
    """Smooth data using a simple moving average."""

    return np.convolve(
        data,
        np.ones(window_size) / window_size,
        mode='same'
    )


def moving_average_and_renorm(data, window_size):
    """Smooth data using a moving average and normalize to a maximum of 1."""

    sdata = np.convolve(
        data,
        np.ones(window_size) / window_size,
        mode='same'
    )

    sndata = sdata / np.nanmax(sdata)

    return sndata


#%% Select files

file_list = make_filelist()

# Dictionary containing one dataframe for each selected spectrum.
spectra_dict = {}


#%% Read and plot raw data

for i in range(0, len(file_list)):
    spectra_dict[i] = pd.read_excel(file_list[i])


font_size = 18

fig, ax0 = plt.subplots(
    nrows=1,
    ncols=1,
    figsize=(6, 6)
)

for key in spectra_dict:
    ax0.plot(
        spectra_dict[key]['Wavelength'],
        spectra_dict[key]['Em.'],
        linewidth=2,
        label=os.path.split(file_list[key])[1]
    )


ax0.set_xlabel('Wavelength (nm)', fontsize=font_size)
ax0.set_ylabel('Intensity (a.u.)', fontsize=font_size)
ax0.set_title('Raw Data', fontsize=font_size)

# Indicate the 490 nm cutoff wavelength.
ax0.vlines(
    490,
    0,
    1,
    colors='grey',
    linestyle='--',
    linewidth=2,
    label='490 nm cutoff'
)

# ax0.set_ylim([0, 40])

ax0.tick_params(axis='x', labelsize=font_size)
ax0.tick_params(axis='y', labelsize=font_size)

for axis in ['top', 'bottom', 'left', 'right']:
    ax0.spines[axis].set_linewidth(2)

ax0.xaxis.set_tick_params(width=2)
ax0.yaxis.set_tick_params(width=2)

plt.legend()
plt.tight_layout()


#%% Smooth and normalize data

# Smoothing with a moving-average window size of 5.
window_size = 5

for key in spectra_dict:
    spectra_dict[key]['sEm.'] = moving_average_and_renorm(
        spectra_dict[key]['Em.'],
        window_size=window_size
    )

    # Use this instead if smoothing without normalization is desired:
    # spectra_dict[key]['sEm.'] = moving_average(
    #     spectra_dict[key]['Em.'],
    #     window_size=window_size
    # )


#%% Plot smoothed data

font_size = 18

fig, ax0 = plt.subplots(
    nrows=1,
    ncols=1,
    figsize=(6, 6)
)

for key in spectra_dict:
    ax0.plot(
        spectra_dict[key]['Wavelength'],
        spectra_dict[key]['sEm.'],
        linewidth=2,
        label=os.path.split(file_list[key])[1]
    )


ax0.set_xlabel('Wavelength (nm)', fontsize=font_size)
ax0.set_ylabel('Intensity (a.u.)', fontsize=font_size)
ax0.set_title('Smoothed Data', fontsize=font_size)

# Indicate the 490 nm cutoff wavelength.
ax0.vlines(
    490,
    0,
    1,
    colors='grey',
    linestyle='--',
    linewidth=2,
    label='490 nm cutoff'
)

# ax0.set_ylim([0, 40])

ax0.tick_params(axis='x', labelsize=font_size)
ax0.tick_params(axis='y', labelsize=font_size)

for axis in ['top', 'bottom', 'left', 'right']:
    ax0.spines[axis].set_linewidth(2)

ax0.xaxis.set_tick_params(width=2)
ax0.yaxis.set_tick_params(width=2)

plt.legend()
plt.tight_layout()