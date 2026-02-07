"""
SGC Comparison Report Generator
Compares 'Corrected' (X3/Y3) data from 0dB, 10dB, and 20dB start runs.
"""

import matplotlib.pyplot as plt
import numpy as np
import os
import glob

# ================= CONFIGURATION =================
# These match the directory names you just created
dirs = {
    "0dB Start":  "0to31data",
    "10dB Start": "10to31data",
    "20dB Start": "20to31data"
}

output_dir = "Comparison_Images"
# =================================================

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Get list of BPMs from the 0dB folder (assuming it has the complete list)
# We use the key for "0dB Start" to find the master list
master_folder = dirs["0dB Start"]
bpm_files = glob.glob(os.path.join(master_folder, "*_Data.txt"))

print(f"Found {len(bpm_files)} BPM files. Generating plots...")

for file_path in bpm_files:
    # Extract just the filename (e.g., "SR:C01-BI{BPM:1}_Data.txt")
    filename = os.path.basename(file_path)
    bpm_name = filename.replace("_Data.txt", "")
    
    # Initialize plot
    f, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))
    
    # Loop through the 3 datasets
    for label, folder in dirs.items():
        full_path = os.path.join(folder, filename)
        
        if not os.path.exists(full_path):
            # It's possible some BPMs were masked in one run but not another
            print(f"  > Missing data in {label} for {bpm_name}")
            continue
            
        try:
            # Load Data
            # Format: X1, X2, X3, X4, Y1, Y2, Y3, Y4
            # We want X3 (index 2) and Y3 (index 6) -> "Beam with Correction"
            data = np.loadtxt(full_path, delimiter=',')
            
            # Handle edge case if file only has 1 line (rare)
            if data.ndim == 1:
                data = data.reshape(1, -1)

            # Determine X-axis (Attenuation dB) based on row count
            # 32 rows = 0-31 dB
            # 22 rows = 10-31 dB
            # 12 rows = 20-31 dB
            n_rows = data.shape[0]
            start_db = 32 - n_rows 
            
            # Create the dB range for plotting (e.g., 0,1,2...31 or 10,11...31)
            db_range = range(start_db, 32)
            
            # Extract Corrected Beam Position
            X3 = data[:, 2]
            Y3 = data[:, 6]
            
            # Plot X
            ax1.plot(db_range, X3, "-o", markersize=4, alpha=0.8, 
                     label=f"{label} (Mean: {np.mean(X3):.2f})")
            
            # Plot Y
            ax2.plot(db_range, Y3, "-o", markersize=4, alpha=0.8,
                     label=f"{label} (Mean: {np.mean(Y3):.2f})")
            
        except Exception as e:
            print(f"  Error reading {bpm_name} in {label}: {e}")

    # Formatting Plot 1 (X)
    ax1.set_title(f"{bpm_name} - X Corrected Comparison")
    ax1.set_xlabel("Attenuation (dB)")
    ax1.set_ylabel("X Position (um)")
    ax1.grid(True, which='both', linestyle='--', alpha=0.7)
    ax1.legend()
    
    # Formatting Plot 2 (Y)
    ax2.set_title(f"{bpm_name} - Y Corrected Comparison")
    ax2.set_xlabel("Attenuation (dB)")
    ax2.set_ylabel("Y Position (um)")
    ax2.grid(True, which='both', linestyle='--', alpha=0.7)
    ax2.legend()
    
    plt.tight_layout()
    save_path = os.path.join(output_dir, f"{bpm_name}_Compare.png")
    plt.savefig(save_path)
    plt.close(f)

print(f"Done! Check the '{output_dir}' folder.")
