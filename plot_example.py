"""
Quick example script to plot patient scenarios.

Simply run this after optimization to visualize results.
Modify the patient_id and config_idx variables below as needed.
"""

from plot_patient_scenarios import plot_patient_scenarios
from pathlib import Path

# ==============================================================================
# CONFIGURATION - Modify these values
# ==============================================================================

# Directory containing simulation results
base_dir = Path(__file__).resolve().parent / 'simulation_time_series'

# Choose which patient to plot (use tab-completion or check directory names)
# Examples: 'synthetic_001_insulin_sensitive_fast_absorption', 'synthetic_015_reference_adult'
patient_id = None  # Will auto-select first patient if None

# Which controller configuration to plot (1-6 with default settings)
config_idx = 1

# ==============================================================================

if __name__ == "__main__":
    print("="*70)
    print("PATIENT GLUCOSE TIME-SERIES VISUALIZATION")
    print("="*70)
    
    if not base_dir.exists():
        print(f"\nError: Simulation directory not found: {base_dir}")
        print("Please run parameter_optimization_example.py first to generate data.")
        exit(1)
    
    # Get list of patients
    patient_dirs = sorted([d for d in base_dir.iterdir() if d.is_dir()])
    
    if not patient_dirs:
        print(f"\nError: No patient directories found in {base_dir}")
        exit(1)
    
    print(f"\nFound {len(patient_dirs)} patients in {base_dir.name}/")
    
    # Select patient
    if patient_id is None:
        selected_patient_dir = patient_dirs[0]
        print(f"\nAuto-selected first patient: {selected_patient_dir.name}")
    else:
        matching = [d for d in patient_dirs if d.name == patient_id]
        if matching:
            selected_patient_dir = matching[0]
        else:
            print(f"\nError: Patient '{patient_id}' not found")
            print("\nAvailable patients:")
            for i, d in enumerate(patient_dirs[:10], 1):
                print(f"  {i}. {d.name}")
            if len(patient_dirs) > 10:
                print(f"  ... and {len(patient_dirs) - 10} more")
            exit(1)
    
    print(f"Configuration: {config_idx}")
    print(f"\nGenerating plot...")
    
    # Create plot
    plot_patient_scenarios(selected_patient_dir, config_idx=config_idx, save_fig=True)
    
    print("\n" + "="*70)
    print("To plot a different patient, edit this script and set:")
    print(f"  patient_id = '{selected_patient_dir.name}'")
    print(f"  config_idx = {config_idx}")
    print("="*70)
