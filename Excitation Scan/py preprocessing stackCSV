#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 22 01:41:14 2024

@author: janiellecuala
"""

import os
import pandas as pd

# Function to prompt the user for input
def get_user_input():
    channel_indices = input("Enter the channel indices to be processed, separated by commas (e.g., 0,1,2,3,4,5,6,7): ").split(',')
    channel_indices = [int(ch.strip()) for ch in channel_indices]
    folder_path = input("Enter the folder path containing the CSV files: ")
    rois = input("Enter the ROI names to be taken into consideration, separated by commas (e.g., ROI_UntransfectedNuc_,ROI_Mito_): ").split(',')
    return channel_indices, folder_path, rois

# Function to determine the channel type based on the channel index
def get_channel_type(channel_index):
    channel_types = {
        0: "_NADHintensity",
        1: "_NADHlifetime",
        2: "_NADH_G",
        3: "_NADH_S",
        4: "_FPintensity",
        5: "_FPlifetime",
        6: "_FP_G",
        7: "_FP_S"
    }
    return channel_types.get(channel_index, "")

# Function to load and process CSV files
def load_and_process_csv_files(channel_indices, folder_path, rois):
    final_sheets = {}

    for channel_index in channel_indices:
        channel_name = f"ch{channel_index}"
        file_path = os.path.join(folder_path, f"Stack_{channel_name}.tif_ExcScacn_all_ROIs.csv")
        
        if not os.path.isfile(file_path):
            print(f"File not found: {file_path}")
            continue
        
        df = pd.read_csv(file_path)
        df = keep_and_rename_average_columns(df)
        channel_type = get_channel_type(channel_index)
        
        sheets = separate_average_sheets(df, channel_name, channel_type, rois)
        final_sheets.update(sheets)

    return final_sheets

# Function to keep only Average columns and rename correctly
def keep_and_rename_average_columns(df):
    new_df = pd.DataFrame()
    for col in df.columns:
        if col.startswith('AverageValue_'):
            new_name = col.replace('AverageValue_', '')
            new_df[new_name] = df[col]
    return new_df

# Function to separate into sheets based on the name and adjust wavelengths
def separate_average_sheets(df, channel_name, channel_type, rois):
    sheets = {}
    wavelength = [680 + 10 * i for i in range(len(df))]
    for col in df.columns:
        for roi in rois:
            if roi in col:
                sheet_name = f"{channel_name}{channel_type}_{roi.rstrip('_')}"
                # Ensure sheet name length is within Excel's limit of 31 characters
                if len(sheet_name) > 31:
                    sheet_name = sheet_name[:31]
                if sheet_name not in sheets:
                    sheets[sheet_name] = pd.DataFrame({'Wavelength': wavelength})
                    sheets[sheet_name][col] = df[col].values
                else:
                    sheets[sheet_name][col] = df[col].values
                break
    return sheets

# Main function to execute the script
def main():
    channel_indices, folder_path, rois = get_user_input()
    final_sheets = load_and_process_csv_files(channel_indices, folder_path, rois)
    
    output_file_path = os.path.join(folder_path, 'Processed_Data_Average_Columns.xlsx')
    with pd.ExcelWriter(output_file_path, engine='openpyxl') as writer:
        for sheet_name, df in final_sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"Excel file with separate sheets has been created successfully at {output_file_path}.")

if __name__ == "__main__":
    main()
