"""
Plot glucose time-series for one patient across different meal scenarios.

This script reads simulation JSON files and creates visualization of glucose
levels and carb intakes for all meal scenarios.
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


def plot_patient_scenarios(patient_dir, config_idx=1, save_fig=True):
    """
    Plot glucose time-series for all scenarios for a given patient and config.
    
    Args:
        patient_dir: Path to patient directory containing JSON files
        config_idx: Configuration index to plot
        save_fig: Whether to save the figure
    """
    patient_dir = Path(patient_dir)
    patient_id = patient_dir.name
    
    # Scenario order for plotting
    scenario_names = ['standard', 'low_carb', 'high_carb', 'irregular']
    scenario_titles = {
        'standard': 'Standard Meals',
        'low_carb': 'Low Carb',
        'high_carb': 'High Carb',
        'irregular': 'Irregular Timing'
    }
    
    # Load data for each scenario
    data = {}
    for scenario in scenario_names:
        json_file = patient_dir / f"config_{config_idx:03d}_{scenario}.json"
        if json_file.exists():
            data[scenario] = load_simulation_data(json_file)
        else:
            print(f"Warning: {json_file} not found")
    
    if not data:
        print(f"No data found for patient {patient_id}, config {config_idx}")
        return
    
    # Create figure with 4 subplots (2x2)
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    axes = axes.flatten()
    
    # Get controller parameters from first scenario
    first_data = list(data.values())[0]
    ctrl = first_data['controller_parameters']
    
    fig.suptitle(
        f"Patient: {patient_id}\n"
        f"Controller: Kp={ctrl['Kp']:.4f}, Ki={ctrl['Ki']:.5f}, Kd={ctrl['Kd']:.5f}, "
        f"Target={ctrl['target_glucose']:.0f} mg/dL, Deadband={ctrl['deadband']:.0f} mg/dL",
        fontsize=12, fontweight='bold'
    )
    
    # Plot each scenario
    for idx, scenario in enumerate(scenario_names):
        if scenario not in data:
            continue
            
        ax = axes[idx]
        sim_data = data[scenario]
        
        # Extract time series
        time = np.array(sim_data['time_series']['time_minutes'])
        true_glucose = np.array(sim_data['time_series']['true_glucose_mgdL'])
        measured_glucose = np.array(sim_data['time_series']['measured_glucose_mgdL'])
        insulin_rate = np.array(sim_data['time_series']['insulin_rate_U_per_min'])
        
        # Plot glucose levels on primary axis
        ax.plot(time / 60, true_glucose, 'b-', linewidth=2, label='True Glucose', alpha=0.8)
        ax.plot(time / 60, measured_glucose, 'r--', linewidth=1, label='Measured (with noise)', alpha=0.6)
        
        # Add target range shading (70-180 mg/dL)
        ax.axhspan(70, 180, alpha=0.1, color='green', label='Target Range (70-180)')
        ax.axhline(70, color='orange', linestyle=':', linewidth=1, alpha=0.5)
        ax.axhline(180, color='orange', linestyle=':', linewidth=1, alpha=0.5)
        
        # Add target glucose line
        ax.axhline(ctrl['target_glucose'], color='purple', linestyle='--', 
                  linewidth=1.5, alpha=0.7, label=f"Target ({ctrl['target_glucose']:.0f})")
        
        # Create secondary y-axis for insulin rate
        ax2 = ax.twinx()
        ax2.plot(time / 60, insulin_rate, 'g-', linewidth=1.5, label='Insulin Rate', alpha=0.7, color='darkviolet')
        ax2.set_ylabel('Insulin Rate (U/min)', fontsize=10, color='darkviolet')
        ax2.tick_params(axis='y', labelcolor='darkviolet')
        ax2.set_ylim(0, max(insulin_rate.max() * 1.2, 0.05))
        
        # Plot carb intakes as vertical lines with annotations
        meals = sim_data['meal_scenario']
        y_max = ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 300
        
        for meal in meals:
            meal_time = meal['time_minutes'] / 60  # Convert to hours
            meal_carbs = meal['carbs_grams']
            
            # Vertical line for meal
            ax.axvline(meal_time, color='darkgreen', linestyle='-', linewidth=2, alpha=0.7)
            
            # Annotate with carb amount
            ax.annotate(
                f"{meal_carbs:.0f}g",
                xy=(meal_time, y_max * 0.95),
                xytext=(0, -5),
                textcoords='offset points',
                ha='center',
                fontsize=10,
                fontweight='bold',
                color='darkgreen',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.7)
            )
        
        # Get metrics
        metrics = sim_data['metrics']
        
        # Set labels and title
        ax.set_xlabel('Time (hours)', fontsize=11)
        ax.set_ylabel('Glucose (mg/dL)', fontsize=11)
        ax.set_title(
            f"{scenario_titles[scenario]}\n"
            f"TIR: {metrics['time_in_range_pct']:.1f}%, "
            f"Mean: {metrics['mean_glucose']:.0f} mg/dL, "
            f"CV: {metrics['cv_glucose']:.1f}%",
            fontsize=11, fontweight='bold'
        )
        
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, time[-1] / 60)
        ax.set_ylim(50, min(300, max(true_glucose.max(), 250)))
        
        if idx == 0:  # Only show legend on first subplot
            # Combine legends from both axes
            lines1, labels1 = ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=9)
    
    plt.tight_layout()
    
    # Save figure
    if save_fig:
        output_dir = patient_dir.parent.parent / 'plots'
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"{patient_id}_config_{config_idx:03d}_scenarios.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Plot saved to: {output_file}")
    
    plt.show()
    
    return fig


def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(
        description='Plot glucose time-series for a patient across meal scenarios'
    )
    parser.add_argument(
        'patient_dir',
        type=str,
        help='Path to patient directory (e.g., simulation_time_series/synthetic_001_...)'
    )
    parser.add_argument(
        '--config',
        type=int,
        default=1,
        help='Configuration index to plot (default: 1)'
    )
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save the figure to file'
    )
    
    args = parser.parse_args()
    
    patient_dir = Path(args.patient_dir)
    if not patient_dir.exists():
        print(f"Error: Directory not found: {patient_dir}")
        return
    
    plot_patient_scenarios(patient_dir, config_idx=args.config, save_fig=not args.no_save)


if __name__ == "__main__":
    main()
