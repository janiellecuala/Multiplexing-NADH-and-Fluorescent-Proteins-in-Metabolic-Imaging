import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import glob
from pathlib import Path
import seaborn as sns
from scipy import stats
import argparse
from tifffile import imread  # Better for handling TIFF stacks
import json

class ZAxisProcessor:
    def __init__(self):
        # SP8 Laser power measurements from your Excel sheet
        self.laser_powers = {
            680: 4.0, 690: 6.5, 700: 6.0, 710: 3.0, 720: 3.0, 730: 7.0, 740: 8.5,
            750: 11.0, 760: 13.2, 770: 8.0, 780: 9.0, 790: 8.0, 800: 15.4, 810: 17.0,
            820: 19.0, 830: 23.1, 840: 22.0, 850: 5.0, 860: 7.0, 870: 20.0, 880: 8.0,
            890: 7.0, 900: 6.0, 910: 16.0, 920: 2.0, 930: 16.0, 940: 7.0, 950: 6.0,
            960: 5.9, 970: 5.0, 980: 4.0, 990: 3.9, 1000: 3.5, 1010: 3.4, 1020: 1.7,
            1030: 0.73, 1040: 7.4, 1050: 5.5, 1060: 4.8, 1070: 3.9, 1080: 3.5,
            1090: 3.4, 1100: 1.7, 1110: 0.73, 1120: 0.73
        }
        
        # Set up matplotlib styling
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
    def get_laser_power(self, wavelength):
        """Get laser power for a given wavelength, using closest available value"""
        wavelengths = list(self.laser_powers.keys())
        closest_wavelength = min(wavelengths, key=lambda x: abs(x - wavelength))
        return self.laser_powers[closest_wavelength]
    
    def wavelength_from_index(self, index):
        """Convert image index to wavelength (0->400nm, 1->410nm, etc.)"""
        return 400 + (index * 10)
    
    def extract_z_profile_from_stack(self, stack_path):
        """Extract z-profile from a TIFF stack where each slice is a different wavelength"""
        try:
            # Read the entire TIFF stack
            stack = imread(stack_path)
            
            # Handle different stack dimensions
            if stack.ndim == 2:
                # Single image
                print(f"Warning: {stack_path} appears to be a single image, not a stack")
                return [np.mean(stack)]
            elif stack.ndim == 3:
                # Stack of images (depth, height, width)
                z_profile = []
                for i in range(stack.shape[0]):
                    # Calculate mean intensity for each slice
                    slice_mean = np.mean(stack[i])
                    z_profile.append(slice_mean)
                return z_profile
            else:
                print(f"Warning: Unexpected stack dimensions in {stack_path}: {stack.shape}")
                return None
                
        except Exception as e:
            print(f"Error processing stack {stack_path}: {e}")
            return None
    
    def process_replicate(self, replicate_folder, channel_type):
        """Process a single replicate folder"""
        stacks_folder = os.path.join(replicate_folder, 'Stacks')
        
        if not os.path.exists(stacks_folder):
            print(f"Warning: Stacks folder not found in {replicate_folder}")
            return None
        
        # Determine channel pattern based on type
        if channel_type.lower() == 'intensity':
            pattern = '*ch0*.tif'
        elif channel_type.lower() == 'lifetime':
            pattern = '*ch1*.tif'
        else:
            raise ValueError("Channel type must be 'intensity' or 'lifetime'")
        
        # Find all matching files
        file_pattern = os.path.join(stacks_folder, pattern)
        stack_files = glob.glob(file_pattern)
        
        if not stack_files:
            print(f"Warning: No {channel_type} files found in {stacks_folder}")
            return None
        
        # Usually there should be only one stack file per channel
        if len(stack_files) > 1:
            print(f"Warning: Multiple {channel_type} files found in {stacks_folder}. Using first one: {stack_files[0]}")
        
        stack_file = stack_files[0]
        print(f"Processing stack: {stack_file}")
        
        # Extract z-profile from the stack
        z_profile = self.extract_z_profile_from_stack(stack_file)
        
        if z_profile is None:
            return None
        
        # Create wavelength array
        wavelengths = [self.wavelength_from_index(i) for i in range(len(z_profile))]
        
        print(f"Extracted {len(z_profile)} wavelength points from {stack_file}")
        print(f"Wavelength range: {wavelengths[0]}-{wavelengths[-1]} nm")
        
        return pd.DataFrame({
            'wavelength': wavelengths,
            'value': z_profile,
            'replicate': os.path.basename(replicate_folder)
        })
    
    def normalize_intensity_individual(self, df, excitation_wavelength):
        """Normalize intensity values based on the excitation wavelength's laser power"""
        excitation_power = self.get_laser_power(excitation_wavelength)
        
        normalized_values = []
        for _, row in df.iterrows():
            current_power = self.get_laser_power(row['wavelength'])
            # Normalize to the excitation wavelength power
            normalized_value = (row['value'] / current_power) * excitation_power
            normalized_values.append(normalized_value)
        
        df['normalized_value'] = normalized_values
        df['excitation_power'] = excitation_power
        return df
    
    def calculate_statistics(self, grouped_data):
        """Calculate mean and SEM for grouped data"""
        stats_data = []
        
        for wavelength, group in grouped_data.groupby('wavelength'):
            values = group['plot_value'].values
            n = len(values)
            mean_val = np.mean(values)
            sem_val = stats.sem(values) if n > 1 else 0
            std_val = np.std(values, ddof=1) if n > 1 else 0
            
            stats_data.append({
                'wavelength': wavelength,
                'mean': mean_val,
                'sem': sem_val,
                'std': std_val,
                'n': n
            })
        
        return pd.DataFrame(stats_data)
    
    def process_condition(self, condition_folder, fluorophore_name, excitation_wavelength, 
                         channel_type):
        """Process a single condition (fluorophore + excitation wavelength)"""
        
        print(f"\n--- Processing Condition: {fluorophore_name} @ {excitation_wavelength}nm ---")
        print(f"Folder: {condition_folder}")
        
        if channel_type == 'intensity':
            excitation_power = self.get_laser_power(excitation_wavelength)
            print(f"Excitation power: {excitation_power}mW (will normalize to this)")
        
        # Find all replicate folders in this condition
        replicate_folders = [f for f in os.listdir(condition_folder) 
                           if os.path.isdir(os.path.join(condition_folder, f))]
        
        if not replicate_folders:
            print(f"Warning: No replicate folders found in {condition_folder}")
            return None
        
        print(f"Found {len(replicate_folders)} replicates: {replicate_folders}")
        
        # Process each replicate
        condition_data = []
        
        for folder in replicate_folders:
            folder_path = os.path.join(condition_folder, folder)
            print(f"  Processing replicate: {folder}")
            
            replicate_data = self.process_replicate(folder_path, channel_type)
            if replicate_data is not None:
                # Add condition metadata
                replicate_data['fluorophore'] = fluorophore_name
                replicate_data['excitation_wavelength'] = excitation_wavelength
                replicate_data['condition'] = f"{fluorophore_name}_{excitation_wavelength}nm"
                replicate_data['replicate_name'] = folder
                condition_data.append(replicate_data)
        
        if not condition_data:
            print(f"Warning: No valid data found for condition {fluorophore_name}_{excitation_wavelength}nm")
            return None
        
        # Combine all replicates for this condition
        combined_data = pd.concat(condition_data, ignore_index=True)
        
        # Normalize intensity data using individual excitation wavelength
        if channel_type.lower() == 'intensity':
            combined_data = self.normalize_intensity_individual(combined_data, excitation_wavelength)
            combined_data['plot_value'] = combined_data['normalized_value']
        else:
            combined_data['plot_value'] = combined_data['value']
        
        print(f"  Successfully processed {len(condition_data)} replicates")
        return combined_data
    
    def process_multiple_conditions(self, conditions_config, channel_type,
                                   show_individual=True, show_statistics=True, output_dir=None):
        """Process multiple conditions and create comparison plots"""
        
        print("=== MULTI-CONDITION PROCESSING ===")
        print(f"Processing {len(conditions_config)} conditions")
        if channel_type == 'intensity':
            print("Using individual normalization (each condition normalized to its own excitation wavelength)")
        
        all_condition_data = []
        
        # Process each condition
        for condition in conditions_config:
            fluorophore = condition['fluorophore']
            excitation = condition['excitation_wavelength'] 
            folder = condition['folder']
            
            condition_data = self.process_condition(
                folder, fluorophore, excitation, channel_type
            )
            
            if condition_data is not None:
                all_condition_data.append(condition_data)
        
        if not all_condition_data:
            print("No valid data found for any condition!")
            return None
        
        # Combine all conditions
        combined_data = pd.concat(all_condition_data, ignore_index=True)
        
        # Save data
        self.save_data(combined_data, channel_type, output_dir)
        
        # Create comparison plots
        fig, ax = self.plot_multi_condition_results(
            combined_data, channel_type,
            show_individual, show_statistics, output_dir
        )
        
        return combined_data, fig, ax
    
    def plot_multi_condition_results(self, all_data, channel_type,
                                    show_individual=True, show_statistics=True, output_dir=None):
        """Create comprehensive plots comparing multiple conditions"""
        
        # Set up the plot
        fig, ax = plt.subplots(1, 1, figsize=(14, 10))
        
        # Get unique conditions
        conditions = all_data['condition'].unique()
        
        # Create color palette - different colors for fluorophores, different shades for excitation wavelengths
        fluorophores = all_data['fluorophore'].unique()
        base_colors = sns.color_palette("husl", len(fluorophores))
        fluorophore_colors = dict(zip(fluorophores, base_colors))
        
        # Create condition-specific colors
        condition_colors = {}
        for condition in conditions:
            fluorophore = condition.split('_')[0]
            excitation = condition.split('_')[1]
            
            base_color = fluorophore_colors[fluorophore]
            
            # Create variations for different excitation wavelengths
            if '740' in excitation:
                condition_colors[condition] = base_color
            elif '940' in excitation or '1040' in excitation or '1050' in excitation:
                # Darker shade for higher wavelengths
                condition_colors[condition] = tuple(0.7 * c for c in base_color)
            else:
                condition_colors[condition] = base_color
        
        # Plot individual replicates
        if show_individual:
            for condition in conditions:
                condition_data = all_data[all_data['condition'] == condition]
                for replicate in condition_data['replicate_name'].unique():
                    rep_data = condition_data[condition_data['replicate_name'] == replicate]
                    ax.plot(rep_data['wavelength'], rep_data['plot_value'], 
                           color=condition_colors[condition], alpha=0.3, linewidth=1,
                           linestyle='--')
        
        # Plot statistics (mean ± SEM)
        if show_statistics:
            for condition in conditions:
                condition_data = all_data[all_data['condition'] == condition]
                unique_replicates = len(condition_data['replicate_name'].unique())
                
                # Get excitation power for legend
                excitation_wavelength = condition_data['excitation_wavelength'].iloc[0]
                excitation_power = self.get_laser_power(excitation_wavelength)
                
                if unique_replicates > 1:  # Only if multiple replicates
                    stats_df = self.calculate_statistics(condition_data)
                    
                    # Plot mean line
                    ax.plot(stats_df['wavelength'], stats_df['mean'], 
                           color=condition_colors[condition], linewidth=3, 
                           marker='o', markersize=6, 
                           label=f'{condition} (n={unique_replicates}, {excitation_power}mW)')
                    
                    # Add error bars
                    ax.errorbar(stats_df['wavelength'], stats_df['mean'], 
                               yerr=stats_df['sem'], 
                               color=condition_colors[condition], 
                               capsize=4, capthick=2, alpha=0.7)
                else:
                    # Single replicate - just plot the line
                    ax.plot(condition_data['wavelength'], condition_data['plot_value'], 
                           color=condition_colors[condition], linewidth=3, 
                           marker='o', markersize=6, 
                           label=f'{condition} (n=1, {excitation_power}mW)')
        
        # Customize plot
        ax.set_xlabel('Wavelength (nm)', fontsize=14, fontweight='bold')
        
        if channel_type.lower() == 'intensity':
            ax.set_ylabel('Normalized Intensity (to respective excitation power)', 
                         fontsize=14, fontweight='bold')
            title = 'Multi-Condition Z-Axis Intensity Profiles (Individual Normalization)'
        else:
            ax.set_ylabel('Lifetime (picoseconds)', fontsize=14, fontweight='bold')
            title = 'Multi-Condition Z-Axis Lifetime Profiles'
        
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Adjust layout to prevent legend cutoff
        plt.tight_layout()
        
        # Save plot if output directory specified
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            filename = f'multi_condition_z_axis_{channel_type}_profile.png'
            filepath = os.path.join(output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"Plot saved to: {filepath}")
        
        plt.show()
        
        return fig, ax
    
    def save_data(self, all_data, channel_type, output_dir):
        """Save processed data to CSV"""
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            filename = f'z_axis_{channel_type}_data.csv'
            filepath = os.path.join(output_dir, filename)
            all_data.to_csv(filepath, index=False)
            print(f"Data saved to: {filepath}")

    def create_conditions_config(self):
        """Interactive function to create conditions configuration"""
        print("\n=== CONDITION SETUP ===")
        print("You'll now set up your experimental conditions.")
        print("Each condition = Fluorophore + Excitation Wavelength + Folder Path")
        print("\nExample conditions:")
        print("- mCherry @ 740nm")
        print("- mCherry @ 1040nm") 
        print("- EGFP @ 740nm")
        print("- EGFP @ 940nm")
        print()
        
        conditions = []
        condition_num = 1
        
        while True:
            print(f"--- Condition {condition_num} ---")
            
            # Get fluorophore name
            fluorophore = input(f"Enter fluorophore name (e.g., mCherry, EGFP): ").strip()
            if not fluorophore:
                break
            
            # Get excitation wavelength
            while True:
                try:
                    excitation = int(input(f"Enter excitation wavelength (e.g., 740, 940, 1040): ").strip())
                    break
                except ValueError:
                    print("Please enter a valid number")
            
            # Get folder path
            while True:
                folder = input(f"Enter folder path for {fluorophore} @ {excitation}nm: ").strip()
                if os.path.exists(folder):
                    break
                else:
                    print("Folder does not exist! Please enter a valid path.")
            
            # Add condition
            conditions.append({
                'fluorophore': fluorophore,
                'excitation_wavelength': excitation,
                'folder': folder
            })
            
            print(f"✓ Added: {fluorophore} @ {excitation}nm")
            
            # Ask if user wants to add more conditions
            add_more = input(f"\nAdd another condition? (y/n): ").strip().lower()
            if add_more != 'y':
                break
            
            condition_num += 1
        
        return conditions

    def save_conditions_config(self, conditions, output_dir):
        """Save conditions configuration to JSON file"""
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            config_file = os.path.join(output_dir, 'conditions_config.json')
            with open(config_file, 'w') as f:
                json.dump(conditions, f, indent=2)
            print(f"Conditions configuration saved to: {config_file}")

    def load_conditions_config(self, config_file):
        """Load conditions configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Configuration file {config_file} not found!")
            return None
        except json.JSONDecodeError:
            print(f"Error reading configuration file {config_file}")
            return None

    def process_single_condition(self, base_folder, channel_type, reference_wavelength=None, 
                              show_individual=True, show_statistics=True, output_dir=None):
        """Process all replicates in a single folder (legacy single-condition mode)"""
        
        print(f"Processing single condition folder: {base_folder}")
        print(f"Channel type: {channel_type}")
        if reference_wavelength:
            print(f"Reference wavelength: {reference_wavelength}nm")
        
        # Find all replicate folders
        replicate_folders = [f for f in os.listdir(base_folder) 
                           if os.path.isdir(os.path.join(base_folder, f))]
        
        if not replicate_folders:
            print("No replicate folders found!")
            return None
        
        print(f"Found {len(replicate_folders)} replicate folders: {replicate_folders}")
        
        # Process each replicate
        all_data = []
        
        for folder in replicate_folders:
            folder_path = os.path.join(base_folder, folder)
            print(f"Processing replicate: {folder}")
            
            replicate_data = self.process_replicate(folder_path, channel_type)
            if replicate_data is not None:
                all_data.append(replicate_data)
        
        if not all_data:
            print("No valid data found!")
            return None
        
        # Combine all data
        combined_data = pd.concat(all_data, ignore_index=True)
        
        # Add fluorophore grouping (assuming naming like EGFP1, EGFP2, etc.)
        combined_data['fluorophore'] = combined_data['replicate'].str.replace(r'\d+$', '', regex=True)
        
        # Normalize intensity data if requested (single condition mode only)
        if channel_type.lower() == 'intensity' and reference_wavelength:
            combined_data = self.normalize_intensity(combined_data, reference_wavelength)
            combined_data['plot_value'] = combined_data['normalized_value']
        else:
            combined_data['plot_value'] = combined_data['value']
        
        # Save data
        self.save_data(combined_data, channel_type, output_dir)
        
        # Create plots (use single condition plotting)
        fig, ax = self.plot_single_condition_results(combined_data, channel_type, reference_wavelength,
                                                   show_individual, show_statistics, output_dir)
        
        return combined_data, fig, ax

    def plot_single_condition_results(self, all_data, channel_type, reference_wavelength=None,
                                    show_individual=True, show_statistics=True, output_dir=None):
        """Create plots for single condition (legacy mode)"""
        
        # Set up the plot
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        # Get unique fluorophore groups
        fluorophores = all_data['fluorophore'].unique()
        colors = sns.color_palette("husl", len(fluorophores))
        color_map = dict(zip(fluorophores, colors))
        
        # Plot individual replicates
        if show_individual:
            for fluorophore in fluorophores:
                fluor_data = all_data[all_data['fluorophore'] == fluorophore]
                for replicate in fluor_data['replicate'].unique():
                    rep_data = fluor_data[fluor_data['replicate'] == replicate]
                    ax.plot(rep_data['wavelength'], rep_data['plot_value'], 
                           color=color_map[fluorophore], alpha=0.4, linewidth=1,
                           linestyle='--')
        
        # Plot statistics (mean ± SEM)
        if show_statistics:
            for fluorophore in fluorophores:
                fluor_data = all_data[all_data['fluorophore'] == fluorophore]
                if len(fluor_data['replicate'].unique()) > 1:  # Only if multiple replicates
                    stats_df = self.calculate_statistics(fluor_data)
                    
                    # Plot mean line
                    ax.plot(stats_df['wavelength'], stats_df['mean'], 
                           color=color_map[fluorophore], linewidth=3, 
                           marker='o', markersize=8, 
                           label=f'{fluorophore} (n={stats_df["n"].iloc[0]})')
                    
                    # Add error bars
                    ax.errorbar(stats_df['wavelength'], stats_df['mean'], 
                               yerr=stats_df['sem'], 
                               color=color_map[fluorophore], 
                               capsize=5, capthick=2, alpha=0.7)
        
        # Customize plot
        ax.set_xlabel('Wavelength (nm)', fontsize=14, fontweight='bold')
        
        if channel_type.lower() == 'intensity':
            if reference_wavelength:
                ref_power = self.get_laser_power(reference_wavelength)
                ax.set_ylabel(f'Normalized Intensity (to {reference_wavelength}nm, {ref_power}mW)', 
                             fontsize=14, fontweight='bold')
                title = f'Z-Axis Intensity Profiles (Normalized to {reference_wavelength}nm)'
            else:
                ax.set_ylabel('Raw Intensity (arbitrary units)', fontsize=14, fontweight='bold')
                title = 'Z-Axis Intensity Profiles (Raw)'
        else:
            ax.set_ylabel('Lifetime (picoseconds)', fontsize=14, fontweight='bold')
            title = 'Z-Axis Lifetime Profiles'
        
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Adjust layout to prevent legend cutoff
        plt.tight_layout()
        
        # Save plot if output directory specified
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            filename = f'z_axis_{channel_type}_profile.png'
            filepath = os.path.join(output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"Plot saved to: {filepath}")
        
        plt.show()
        
        return fig, ax


def main():
    """Main function with options for single or multi-condition processing"""
    processor = ZAxisProcessor()
    
    print("=== Z-Axis Profile Batch Processor ===")
    print("This script processes TIFF stacks where each slice represents a different wavelength")
    print("Image 1 = 400nm, Image 2 = 410nm, Image 3 = 420nm, etc.")
    print()
    
    # Choose processing mode
    print("Processing modes:")
    print("1. Single condition (one fluorophore, one excitation wavelength)")
    print("2. Multi-condition comparison (multiple fluorophores/excitation wavelengths)")
    print("3. Load from configuration file")
    
    while True:
        mode_choice = input("\nEnter your choice (1, 2, or 3): ").strip()
        if mode_choice in ['1', '2', '3']:
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")
    
    # Get channel type
    print("\nChannel options:")
    print("1. intensity - Process ch0 (intensity) stacks")
    print("2. lifetime - Process ch1 (lifetime) stacks")
    
    while True:
        channel_choice = input("\nEnter your choice (1 or 2): ").strip()
        if channel_choice == '1':
            channel_type = 'intensity'
            print("Note: Intensity will be normalized individually for each condition")
            print("(Each condition normalized to its own excitation wavelength power)")
            break
        elif channel_choice == '2':
            channel_type = 'lifetime'
            print("Note: Lifetime values will not be normalized")
            break
        else:
            print("Invalid choice. Please enter 1 or 2.")
    
    # Get reference wavelength for intensity normalization (only for single condition mode)
    reference_wavelength = None
    if mode_choice == '1' and channel_type == 'intensity':
        while True:
            ref_input = input("\nEnter reference wavelength for normalization (e.g., 740) or press Enter to skip: ").strip()
            if ref_input == '':
                print("No normalization will be applied - using raw intensity values.")
                break
            try:
                reference_wavelength = int(ref_input)
                if 400 <= reference_wavelength <= 1200:
                    print(f"All data will be normalized to {reference_wavelength}nm")
                    break
                else:
                    print("Wavelength should be between 400-1200 nm")
            except ValueError:
                print("Please enter a valid number")
    
    # Get plotting options
    print("\nPlotting options:")
    show_individual = input("Show individual replicates? (y/n, default=y): ").strip().lower() != 'n'
    show_statistics = input("Show statistics (mean ± SEM)? (y/n, default=y): ").strip().lower() != 'n'
    
    # Get output directory
    output_dir = input("\nEnter output directory (press Enter for current directory): ").strip()
    if output_dir == '':
        output_dir = os.getcwd()
    
    print("\n" + "="*50)
    print("PROCESSING STARTED")
    print("="*50)
    
    try:
        if mode_choice == '1':
            # Single condition mode
            base_folder = input("\nEnter the path to your replicates folder: ").strip()
            if not os.path.exists(base_folder):
                print("Error: Folder does not exist!")
                return
            
            # Process as single condition
            data, fig, ax = processor.process_single_condition(
                base_folder=base_folder,
                channel_type=channel_type,
                reference_wavelength=reference_wavelength,
                show_individual=show_individual,
                show_statistics=show_statistics,
                output_dir=output_dir
            )
            
        elif mode_choice == '2':
            # Multi-condition mode
            conditions = processor.create_conditions_config()
            if not conditions:
                print("No conditions specified!")
                return
            
            # Save configuration
            processor.save_conditions_config(conditions, output_dir)
            
            # Process multiple conditions
            data, fig, ax = processor.process_multiple_conditions(
                conditions_config=conditions,
                channel_type=channel_type,
                show_individual=show_individual,
                show_statistics=show_statistics,
                output_dir=output_dir
            )
            
        elif mode_choice == '3':
            # Load from configuration file
            config_file = input("\nEnter path to configuration file: ").strip()
            conditions = processor.load_conditions_config(config_file)
            if not conditions:
                return
            
            # Process multiple conditions
            data, fig, ax = processor.process_multiple_conditions(
                conditions_config=conditions,
                channel_type=channel_type,
                show_individual=show_individual,
                show_statistics=show_statistics,
                output_dir=output_dir
            )
        
        print("\n" + "="*50)
        print("PROCESSING COMPLETE")
        print("="*50)
        print(f"Total data points: {len(data)}")
        
        if 'condition' in data.columns:
            print(f"Conditions processed: {len(data['condition'].unique())}")
            for condition in data['condition'].unique():
                condition_data = data[data['condition'] == condition]
                n_replicates = len(condition_data['replicate_name'].unique())
                print(f"  {condition}: {n_replicates} replicates")
        else:
            print(f"Replicates processed: {len(data['replicate'].unique())}")
        
        print(f"Wavelength range: {data['wavelength'].min()}-{data['wavelength'].max()} nm")
        
    except Exception as e:
        print(f"Error during processing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Check if tifffile is available
    try:
        import tifffile
    except ImportError:
        print("Error: tifffile library not found!")
        print("Please install it with: pip install tifffile")
        exit(1)
    
    main()
