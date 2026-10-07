import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def process_and_plot_topography(file_name, label_title, base_start, base_end, plat_start, plat_end, plot_color, is_hole=False):
    """
    Parses specific cleanroom log files, converts the raw data from Angstroms to Nanometers,
    generates an engineering Topography Plot, and applies the step-average formula.
    """
    if not os.path.exists(file_name):
        print(f"Skipping: File '{file_name}' not found. Make sure you are in the correct folder.")
        return None, None
        
    # Read the data block, automatically handling space or tab delimiters
    df = pd.read_csv(file_name, skiprows=7, sep=None, engine='python')
    df.columns = df.columns.str.strip()
    
    # Fallback to handle variations in raw machine column headers
    if 'Normal' not in df.columns:
        df.columns = ['Point_Index', 'Raw', 'RawLevel', 'Normal', 'Rough', 'Wavi']
    
    # Extract raw vertical values in Angstroms
    heights_angstroms = df['Normal'].values
    
    # Convert step indexing to lateral distance (Point * 0.1 microns lateral resolution)
    df['Spatial_Distance_um'] = df.iloc[:, 0] * 0.1
    
    #1. RENDERING THE TOPOGRAPHY PLOT
    plt.figure(figsize=(9.5, 4.5))
    plt.plot(df['Spatial_Distance_um'], df['Normal'] / 10.0, color=plot_color, lw=2, label='Surface Profile')
    plt.title(f"Topography Plot: {label_title}", fontsize=13, fontweight='bold', pad=12)
    plt.xlabel('Lateral Distance Position (µm)', fontsize=11)
    plt.ylabel('Profile Height (nm)', fontsize=11)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(loc='best')
    plt.tight_layout()
    plt.show()
    
    #2. MATHEMATICAL FIELD ANALYSIS
    baseline_slice = heights_angstroms[base_start:base_end]
    
    if is_hole:
        # For ultra-narrow micro-holes, we isolate the minimum valley base point
        plateau_mean = np.min(heights_angstroms[plat_start:plat_end])
        uncertainty_angstroms = np.std(heights_angstroms[plat_start:plat_end])
    else:
        # Standard wide flat step plateau average
        plateau_mean = np.mean(heights_angstroms[plat_start:plat_end])
        uncertainty_angstroms = np.std(heights_angstroms[plat_start:plat_end])
        
    baseline_mean = np.mean(baseline_slice)
    
    # Calculate the step height delta and convert from Angstroms to Nanometers (/10)
    calculated_thickness_nm = abs(baseline_mean - plateau_mean) / 10.0
    uncertainty_nm = uncertainty_angstroms / 10.0
    
    return round(calculated_thickness_nm, 2), round(uncertainty_nm, 2)


# =====================================================================
# PIPELINE EXECUTION ENGINE (RUNNING THE EXPERIMENTAL FILES)
# =====================================================================
if __name__ == "__main__":
    print("=============================================================")
    print("             INITIALIZING CHIPS TOPOGRAPHY ANALYSIS          ")
    print("=============================================================\n")
    
    # Dictionary to collect data for the protocol table
    summary_matrix = {
        "Target File Log": ["Group B_thicknessUp.txt", "Group B_thickness.txt", "Group B_thickness1-2micHoles.txt"],
        "Process Feature": ["Total Photoresist Mold Height (t_resist)", "Post-Deposition Open Trench Depth", "Micro Contact Voids (1-2 um)"],
        "Calculated Value (nm)": [],
        "Calculated Uncertainty (nm)": []
    }
    
    # 1. Process files, plot them with your custom colors, and calculate metrics
    # Main Mold Height (Upward Step) - Deep Violet (#6A0DAD)
    t_resist, u_resist = process_and_plot_topography(
        "Group B_thicknessUp.txt", "Initial Photoresist Mold Step Profile", 
        base_start=1, base_end=500, plat_start=620, plat_end=800, plot_color='#6A0DAD'
    )
    
    # Remaining Trench Depth (Downward Step) - Purple-Lila (#9966CC)
    t_trench, u_trench = process_and_plot_topography(
        "Group B_thickness.txt", "Post-Deposition Open Trench Profile", 
        base_start=1, base_end=200, plat_start=270, plat_end=350, plot_color='#9966CC'
    )
    
    # 1-2 Micron Holes - Royal Blue (#4169E1)
    t_hole, u_hole = process_and_plot_topography(
        "Group B_thickness1-2micHoles.txt", "1-2 Micron Contact Trench Voids", 
        base_start=1, base_end=350, plat_start=415, plat_end=425, plot_color='#4169E1', is_hole=True
    )
    
    # Append results if files were present
    summary_matrix["Calculated Value (nm)"].extend([t_resist, t_trench, t_hole])
    summary_matrix["Calculated Uncertainty (nm)"].extend([u_resist, u_trench, u_hole])
    
    # 2. Render Results Table
    df_final_report = pd.DataFrame(summary_matrix)
    
    # 3. Calculate Net Metal Thickness (t_metal) and Aspect Ratio for Question 2
    if t_resist and t_trench:
        t_metal = t_resist - t_trench
        aspect_ratio = t_metal / t_resist
        
        print("\n=============================================================")
        print("             GEOMETRICAL LIFT-OFF EVALUATION (Q2)            ")
        print("=============================================================")
        print(f"-> Derived Net Deposited Metal Thickness (t_metal): {t_metal:.2f} nm")
        print(f"-> Calculated Aspect Ratio (t_metal / t_resist): {aspect_ratio:.4f}")
        print(f"-> Critical Lift-Off Threshold Limit: 0.3333")
        
        if aspect_ratio <= 0.3333:
            print("-> Process Status: SUCCESS (Satisfies the 1/3 thickness rule safely).")
        else:
            print("-> Process Status: CRITICAL (High risk of fencing/bridging).")
        print("=============================================================\n")
        
    # Export final structured data to Excel for your repository verification
    df_final_report.to_excel("Microfabrication_StepHeight_Calculated_v3.xlsx", index=False)
    
    # Display the final summary dataframe directly in the Jupyter Notebook window
    print("SUMMARY RESULTS TABLE FOR PROTOCOL DATA SHEET:")
    import sweetness_display # internal utility check
    display(df_final_report)

import numpy as np

# Input your precise numbers from the lab bench here!
I_amps = 0.010    # 10 mA current converted to Amperes
V_volts = 0.030   # 30 mV voltage converted to Volts
t_metal_nm = 331.29 # Your derived metal thickness from our previous steps

# Calculate Sheet Resistance
Rs = 4.532 * (V_volts / I_amps)

# Convert thickness to cm and compute Resistivity
t_metal_cm = t_metal_nm * 1e-7
rho = Rs * t_metal_cm
print(f"Calculated Sheet Resistance (Rs): {Rs:.3f} Ohms/sq")
print(f"Calculated Thin-Film Resistivity (rho): {rho:.2e} Ohm-cm")
