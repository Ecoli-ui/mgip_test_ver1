"""
Plot comparison of multiple patients for the same configuration and scenario.

This shows how different patients respond to the same controller and meal scenario.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import argparse


def load_simulation_data(json_path):
    """Load simulation data from JSON file."""
    with open(json_path, 'r') as f:
        return json.load(f)


def plot_patient_comparison(simulation_dir, config_idx=1, scenario='standard', 
                           max_patients=6, save_fig=True):
    """
    Plot glucose time-series for multiple patients with the same config/scenario.
    
    Args:
        simulation_dir: Base directory containing patient subdirectories
        config_idx: Configuration index to plot
        scenario: Meal scenario to plot ('standard', 'low_carb', 'high_carb', 'irregular')
        max_patients: Maximum number of patients to show
        save_fig: Whether to save the figure
    """
    simulation_dir = Path(simulation_dir)
    
    # Get all patient directories
    patient_dirs = sorted([d for d in simulation_dir.iterdir() if d.is_dir()])
    
    if not patient_dirs:
        print(f"No patient directories found in {simulation_dir}")
        return
    
    # Limit number of patients
    patient_dirs = patient_dirs[:max_patients]
    
    # Create figure
    fig, axes = plt.subplots(len(patient_dirs), 1, figsize=(14, 3*len(patient_dirs)))
    if len(patient_dirs) == 1:
        axes = [axes]
    
    scenario_titles = {
        'standard': 'Standard Meals',
        'low_carb': 'Low Carb',
        'high_carb': 'High Carb',
        'irregular': 'Irregular Timing'
    }
    
    # Load and plot each patient
    for idx, patient_dir in enumerate(patient_dirs):
        ax = axes[idx]
        patient_id = patient_dir.name
        
        json_file = patient_dir / f"config_{config_idx:03d}_{scenario}.json"
        
        if not json_file.exists():
            ax.text(0.5, 0.5, f"No data for {patient_id}", 
                   ha='center', va='center', transform=ax.transAxes)
            continue
        
        sim_data = load_simulation_data(json_file)
        
        # Extract time series
        time = np.array(sim_data['time_series']['time_minutes'])
        true_glucose = np.array(sim_data['time_series']['true_glucose_mgdL'])
        measured_glucose = np.array(sim_data['time_series']['measured_glucose_mgdL'])
        insulin_rate = np.array(sim_data['time_series']['insulin_rate_U_per_min'])
        
        # Plot glucose levels on primary axis
        ax.plot(time / 60, true_glucose, 'b-', linewidth=2, label='True Glucose', alpha=0.8)
        ax.plot(time / 60, measured_glucose, 'r--', linewidth=1, label='Measured', alpha=0.5)
        
        # Add target range shading
        ax.axhspan(70, 180, alpha=0.1, color='green', label='Target Range' if idx == 0 else '')
        ax.axhline(70, color='orange', linestyle=':', linewidth=1, alpha=0.5)
        ax.axhline(180, color='orange', linestyle=':', linewidth=1, alpha=0.5)
        
        # Add controller target
        ctrl = sim_data['controller_parameters']
        ax.axhline(ctrl['target_glucose'], color='purple', linestyle='--', 
                  linewidth=1.5, alpha=0.7, label=f"Target" if idx == 0 else '')
        
        # Create secondary y-axis for insulin rate
        ax2 = ax.twinx()
        ax2.plot(time / 60, insulin_rate, 'g-', linewidth=1.5, 
                label='Insulin' if idx == 0 else '', alpha=0.6, color='darkviolet')
        ax2.set_ylabel('Insulin (U/min)', fontsize=9, color='darkviolet')
        ax2.tick_params(axis='y', labelcolor='darkviolet', labelsize=8)
        ax2.set_ylim(0, max(insulin_rate.max() * 1.2, 0.05))
        
        # Plot carb intakes
        meals = sim_data['meal_scenario']
        y_max = min(300, true_glucose.max() * 1.1)
        
        for meal in meals:
            meal_time = meal['time_minutes'] / 60
            meal_carbs = meal['carbs_grams']
            ax.axvline(meal_time, color='darkgreen', linestyle='-', linewidth=2, alpha=0.5)
            ax.annotate(f"{meal_carbs:.0f}g", xy=(meal_time, y_max * 0.95),
                       ha='center', fontsize=9, color='darkgreen',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.6))
        
        # Get metrics and patient phenotype
        metrics = sim_data['metrics']
        phenotype = patient_id.split('_')[-1] if '_' in patient_id else 'unknown'
        
        # Set labels and title
        ax.set_ylabel('Glucose (mg/dL)', fontsize=10)
        ax.set_title(
            f"{patient_id} ({phenotype})\n"
            f"TIR: {metrics['time_in_range_pct']:.1f}%, "
            f"Mean: {metrics['mean_glucose']:.0f} mg/dL, "
            f"CV: {metrics['cv_glucose']:.1f}%",
            fontsize=10, fontweight='bold', loc='left'
        )
        
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, time[-1] / 60)
        ax.set_ylim(50, min(300, max(true_glucose.max(), 200)))
        
        if idx == 0:
            # Combine legends from both axes
            lines1, labels1 = ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=9, ncol=5)
    
    # Overall title
    ctrl = sim_data['controller_parameters']
    fig.suptitle(
        f"Patient Comparison: {scenario_titles[scenario]} - Config {config_idx}\n"
        f"Controller: Kp={ctrl['Kp']:.4f}, Ki={ctrl['Ki']:.5f}, Kd={ctrl['Kd']:.5f}, "
        f"Target={ctrl['target_glucose']:.0f}, Deadband={ctrl['deadband']:.0f}",
        fontsize=12, fontweight='bold', y=0.995
    )
    
    # Common x-label
    axes[-1].set_xlabel('Time (hours)', fontsize=11)
    
    plt.tight_layout()
    
    # Save figure
    if save_fig:
        output_dir = simulation_dir.parent / 'plots'
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"patient_comparison_config_{config_idx:03d}_{scenario}.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Plot saved to: {output_file}")
    
    plt.show()
    
    return fig


def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(
        description='Compare multiple patients for the same controller configuration'
    )
    parser.add_argument(
        '--sim-dir',
        type=str,
        default='simulation_time_series',
        help='Base directory containing patient subdirectories (default: simulation_time_series)'
    )
    parser.add_argument(
        '--config',
        type=int,
        default=1,
        help='Configuration index to plot (default: 1)'
    )
    parser.add_argument(
        '--scenario',
        type=str,
        default='standard',
        choices=['standard', 'low_carb', 'high_carb', 'irregular'],
        help='Meal scenario to plot (default: standard)'
    )
    parser.add_argument(
        '--max-patients',
        type=int,
        default=6,
        help='Maximum number of patients to show (default: 6)'
    )
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save the figure to file'
    )
    
    args = parser.parse_args()
    
    sim_dir = Path(args.sim_dir)
    if not sim_dir.exists():
        print(f"Error: Directory not found: {sim_dir}")
        return
    
    plot_patient_comparison(
        sim_dir,
        config_idx=args.config,
        scenario=args.scenario,
        max_patients=args.max_patients,
        save_fig=not args.no_save
    )


if __name__ == "__main__":
    main()
