"""
Example Script for Controller Parameter Optimization
=====================================================

This script demonstrates how to use the T1D simulator for parameter optimization.
It shows the structure for a grid search approach without actually running it.

To perform optimization, you would:
1. Define parameter ranges to explore
2. Loop through parameter combinations
3. Run simulation for each combination
4. Calculate metrics (especially time in range)
5. Select best parameters

Code construction update (Feb 2026):
- Patient-specific physiology can now be provided through `PatientProfile`.
- `insulin_clearance_rate` is now part of `PhysiologicalParams`.
- Backward compatibility is preserved: passing `PhysiologicalParams()` directly
    to `T1DSimulator` still works.

Recommended usage for optimization:
1. Build one `PatientProfile` per virtual patient.
2. Reuse that profile while scanning controller parameter sets.
3. Compare controller settings within-patient and across-patient.

This file now includes:
- `create_example_patients()`: returns a small cohort of virtual patients.
- `optimize_across_patients_example()`: compares controller sets on all patients.
"""

import numpy as np
import pandas as pd
from pathlib import Path
import sys
import argparse
import json
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from glucose_simulator import (
    PhysiologicalParams, PatientProfile,
    SensorParams, PumpParams, ControllerParams,
    T1DSimulator, calculate_time_in_range
)


def create_example_patients() -> list:
    """
    Create a small cohort of virtual patients with diverse physiology.

    Returns:
        List of PatientProfile objects
    """
    return [
        PatientProfile(
            # These are the archetype patients from the original cohort; the params below are means of the distributions of patients in a virtual population, but with body_weight and meal_bioavailability
            patient_id="insulin_sensitive_fast_absorption",
            physiological_params=PhysiologicalParams(
                Gb=95.0,
                Ib=9.0,
                p1=0.030,
                p2=0.027,
                p3=0.000017,
                tau_meal=30.0,
                Vg=1.45,
                insulin_clearance_rate=0.11
            )
        ),
        PatientProfile(
            patient_id="reference_adult",
            physiological_params=PhysiologicalParams(
                Gb=100.0,
                Ib=10.0,
                p1=0.028,
                p2=0.025,
                p3=0.000013,
                tau_meal=40.0,
                Vg=1.50,
                insulin_clearance_rate=0.10
            )
        ),
        PatientProfile(
            patient_id="insulin_resistant_slow_absorption",
            physiological_params=PhysiologicalParams(
                Gb=110.0,
                Ib=13.0,
                p1=0.024,
                p2=0.022,
                p3=0.000009,
                tau_meal=55.0,
                Vg=1.70,
                insulin_clearance_rate=0.08
            )
        ),
    ]


def _sample_truncated_normal(rng: np.random.Generator,
                             mean: float,
                             std: float,
                             lower: float,
                             upper: float,
                             max_attempts: int = 1000) -> float:
    """Sample from a truncated normal via rejection sampling."""
    for _ in range(max_attempts):
        value = rng.normal(mean, std)
        if lower <= value <= upper:
            return value
    return float(np.clip(mean, lower, upper))


def _sample_lognormal_bounded(rng: np.random.Generator,
                              median: float,
                              sigma_log: float,
                              lower: float,
                              upper: float,
                              max_attempts: int = 1000) -> float:
    """Sample from a bounded lognormal with median control."""
    for _ in range(max_attempts):
        value = rng.lognormal(mean=np.log(median), sigma=sigma_log)
        if lower <= value <= upper:
            return value
    return float(np.clip(median, lower, upper))


def sample_virtual_patient(rng: np.random.Generator,
                           patient_index: int,
                           phenotype_probs: tuple = (0.25, 0.50, 0.25)) -> tuple:
    """
    Sample one synthetic patient using mixture archetypes and bounded distributions.

    Returns:
        Tuple of (PatientProfile, metadata_dict)
    """
    archetypes = {
        'insulin_sensitive_fast_absorption': dict(
            Gb=95.0, Ib=9.0, p1=0.030, p2=0.027, p3=0.000017,
            tau_meal=30.0, Vg=1.45, insulin_clearance_rate=0.11
        ),
        'reference_adult': dict(
            Gb=100.0, Ib=10.0, p1=0.028, p2=0.025, p3=0.000013,
            tau_meal=40.0, Vg=1.50, insulin_clearance_rate=0.10
        ),
        'insulin_resistant_slow_absorption': dict(
            Gb=110.0, Ib=13.0, p1=0.024, p2=0.022, p3=0.000009,
            tau_meal=55.0, Vg=1.70, insulin_clearance_rate=0.08
        )
    }
    phenotype_names = list(archetypes.keys())
    phenotype = rng.choice(phenotype_names, p=phenotype_probs)
    base = archetypes[phenotype]

    # Latent factors to induce clinically plausible dependence:
    # - z_resistance: higher means more resistance (higher Ib, lower p3)
    # - z_kinetics: faster/slower kinetics (affects p1, p2, tau_meal)
    z_resistance = rng.normal(0.0, 1.0)
    z_kinetics = rng.normal(0.0, 1.0)

    Gb = _sample_truncated_normal(rng, base['Gb'], 8.0, 75.0, 140.0)

    ib_median = base['Ib'] * np.exp(0.20 * z_resistance)
    Ib = _sample_lognormal_bounded(rng, ib_median, 0.25, 4.0, 25.0)

    p1_median = base['p1'] * np.exp(0.10 * z_kinetics)
    p1 = _sample_lognormal_bounded(rng, p1_median, 0.20, 0.015, 0.045)

    p2_median = base['p2'] * np.exp(0.10 * z_kinetics)
    p2 = _sample_lognormal_bounded(rng, p2_median, 0.20, 0.012, 0.040)

    p3_median = base['p3'] * np.exp(-0.25 * z_resistance)
    p3 = _sample_lognormal_bounded(rng, p3_median, 0.35, 4e-6, 3e-5)

    tau_median = base['tau_meal'] * np.exp(-0.12 * z_kinetics)
    tau_meal = _sample_lognormal_bounded(rng, tau_median, 0.25, 20.0, 90.0)

    vg_mean = base['Vg'] + 0.04 * z_resistance
    Vg = _sample_truncated_normal(rng, vg_mean, 0.15, 1.1, 2.2)

    clearance_median = base['insulin_clearance_rate'] * np.exp(0.15 * (Vg - base['Vg']) / 0.2)
    insulin_clearance_rate = _sample_lognormal_bounded(
        rng, clearance_median, 0.20, 0.05, 0.18
    )

    # Sample body weight (correlated with insulin resistance)
    # Mean 70 kg, std 12 kg, with correlation to z_resistance
    body_weight_mean = 70.0 + 5.0 * z_resistance  # Heavier patients tend to be more resistant
    body_weight = _sample_truncated_normal(rng, body_weight_mean, 12.0, 45.0, 120.0)

    # Meal bioavailability (slight variation from default)
    meal_bioavailability = _sample_truncated_normal(rng, 0.525, 0.05, 0.40, 0.70)

    patient_id = f"synthetic_{patient_index:03d}_{phenotype}"
    profile = PatientProfile(
        patient_id=patient_id,
        physiological_params=PhysiologicalParams(
            Gb=float(Gb),
            Ib=float(Ib),
            p1=float(p1),
            p2=float(p2),
            p3=float(p3),
            tau_meal=float(tau_meal),
            Vg=float(Vg),
            insulin_clearance_rate=float(insulin_clearance_rate),
            body_weight=float(body_weight),
            meal_bioavailability=float(meal_bioavailability)
        )
    )

    metadata = {
        'patient_id': patient_id,
        'phenotype': phenotype,
        'Gb': Gb,
        'Ib': Ib,
        'p1': p1,
        'p2': p2,
        'p3': p3,
        'tau_meal': tau_meal,
        'Vg': Vg,
        'insulin_clearance_rate': insulin_clearance_rate,
        'body_weight': body_weight,
        'meal_bioavailability': meal_bioavailability,
    }
    return profile, metadata


def create_synthetic_patient_cohort(n_patients: int = 30,
                                    random_seed: int = 123,
                                    phenotype_probs: tuple = (0.25, 0.50, 0.25)) -> tuple:
    """
    Create a reproducible cohort of synthetic patients.

    Args:
        n_patients: Number of synthetic patients to sample
        random_seed: RNG seed for reproducibility
        phenotype_probs: Mixture probabilities for
            (sensitive, reference, resistant)

    Returns:
        Tuple of (list_of_profiles, metadata_dataframe)
    """
    rng = np.random.default_rng(random_seed)

    profiles = []
    metadata_rows = []
    for i in range(1, n_patients + 1):
        profile, metadata = sample_virtual_patient(
            rng,
            patient_index=i,
            phenotype_probs=phenotype_probs
        )
        profiles.append(profile)
        metadata_rows.append(metadata)

    cohort_df = pd.DataFrame(metadata_rows)
    return profiles, cohort_df


def evaluate_controller_params(controller_params: ControllerParams,
                               patient_profile: PatientProfile = None,
                               meal_scenario: list = None,
                               duration: float = 12*60,
                               dt: float = 1.0,
                               random_seed: int = None) -> dict:
    """
    Evaluate a controller configuration and return metrics.
    
    Args:
        controller_params: Controller parameters to test
        patient_profile: Patient-specific physiology definition
        meal_scenario: List of (time, carbs) tuples
        duration: Simulation duration (minutes)
        dt: Time step (minutes)
        random_seed: Random seed for reproducibility
    
    Returns:
        Dictionary with performance metrics
    """
    if random_seed is not None:
        np.random.seed(random_seed)
    
    # Standard physiological and device parameters
    if patient_profile is None:
        patient_profile = PatientProfile(
            patient_id="reference_adult",
            physiological_params=PhysiologicalParams()
        )

    sensor_params = SensorParams(noise_std=3.0, delay=2)
    pump_params = PumpParams(basal_rate=0.02)
    
    # Default meal scenario
    if meal_scenario is None:
        meal_scenario = [
            (60, 50),   # Breakfast
            (240, 60),  # Lunch
            (480, 55),  # Dinner
        ]
    
    # Create and run simulator
    simulator = T1DSimulator(
        patient_profile.physiological_params,
        sensor_params,
        pump_params,
        controller_params,
        patient_profile=patient_profile
    )
    results = simulator.simulate(duration, dt, meal_scenario)
    
    # Calculate metrics
    metrics = calculate_time_in_range(results['true_glucose'])
    
    # Add controller parameters to metrics for tracking
    metrics['Kp'] = controller_params.Kp
    metrics['Ki'] = controller_params.Ki
    metrics['Kd'] = controller_params.Kd
    metrics['target_glucose'] = controller_params.target_glucose
    metrics['deadband'] = controller_params.deadband
    
    return metrics


def evaluate_and_save_simulation(controller_params: ControllerParams,
                                 patient_profile: PatientProfile,
                                 meal_scenario: list,
                                 scenario_name: str,
                                 output_dir: Path,
                                 config_idx: int,
                                 duration: float = 12*60,
                                 dt: float = 1.0,
                                 random_seed: int = None) -> dict:
    """
    Evaluate a controller configuration, return metrics, and save full time-series data.
    
    Args:
        controller_params: Controller parameters to test
        patient_profile: Patient-specific physiology definition
        meal_scenario: List of (time, carbs) tuples
        scenario_name: Name of the meal scenario
        output_dir: Directory to save JSON files
        config_idx: Configuration index number
        duration: Simulation duration (minutes)
        dt: Time step (minutes)
        random_seed: Random seed for reproducibility
    
    Returns:
        Dictionary with performance metrics
    """
    if random_seed is not None:
        np.random.seed(random_seed)
    
    sensor_params = SensorParams(noise_std=3.0, delay=2)
    pump_params = PumpParams(basal_rate=0.02)
    
    # Create and run simulator
    simulator = T1DSimulator(
        patient_profile.physiological_params,
        sensor_params,
        pump_params,
        controller_params,
        patient_profile=patient_profile
    )
    results = simulator.simulate(duration, dt, meal_scenario)
    
    # Calculate metrics
    metrics = calculate_time_in_range(results['true_glucose'])
    
    # Add controller parameters to metrics for tracking
    metrics['Kp'] = controller_params.Kp
    metrics['Ki'] = controller_params.Ki
    metrics['Kd'] = controller_params.Kd
    metrics['target_glucose'] = controller_params.target_glucose
    metrics['deadband'] = controller_params.deadband
    
    # Save full simulation data to JSON
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create filename: config_scenario.json
    filename = f"config_{config_idx:03d}_{scenario_name}.json"
    filepath = output_dir / filename
    
    # Prepare data for JSON serialization
    simulation_data = {
        'metadata': {
            'patient_id': patient_profile.patient_id,
            'scenario': scenario_name,
            'config_idx': config_idx,
            'simulation_date': datetime.now().isoformat(),
            'duration_minutes': duration,
            'time_step_minutes': dt,
        },
        'controller_parameters': {
            'Kp': float(controller_params.Kp),
            'Ki': float(controller_params.Ki),
            'Kd': float(controller_params.Kd),
            'target_glucose': float(controller_params.target_glucose),
            'deadband': float(controller_params.deadband),
        },
        'patient_parameters': {
            'Gb': float(patient_profile.physiological_params.Gb),
            'Ib': float(patient_profile.physiological_params.Ib),
            'p1': float(patient_profile.physiological_params.p1),
            'p2': float(patient_profile.physiological_params.p2),
            'p3': float(patient_profile.physiological_params.p3),
            'tau_meal': float(patient_profile.physiological_params.tau_meal),
            'Vg': float(patient_profile.physiological_params.Vg),
            'insulin_clearance_rate': float(patient_profile.physiological_params.insulin_clearance_rate),
            'body_weight': float(patient_profile.physiological_params.body_weight),
            'meal_bioavailability': float(patient_profile.physiological_params.meal_bioavailability),
        },
        'meal_scenario': [
            {'time_minutes': float(t), 'carbs_grams': float(c)} 
            for t, c in meal_scenario
        ],
        'device_parameters': {
            'sensor_noise_std': float(sensor_params.noise_std),
            'sensor_delay': int(sensor_params.delay),
            'pump_basal_rate': float(pump_params.basal_rate),
        },
        'time_series': {
            'time_minutes': results['time'].tolist(),
            'true_glucose_mgdL': results['true_glucose'].tolist(),
            'measured_glucose_mgdL': results['measured_glucose'].tolist(),
            'insulin_rate_U_per_min': results['insulin_rate'].tolist(),
        },
        'metrics': {
            'time_in_range_pct': float(metrics['time_in_range_pct']),
            'time_below_range_pct': float(metrics['time_below_range_pct']),
            'time_above_range_pct': float(metrics['time_above_range_pct']),
            'mean_glucose': float(metrics['mean_glucose']),
            'std_glucose': float(metrics['std_glucose']),
            'cv_glucose': float(metrics['cv_glucose']),
            'min_glucose': float(metrics['min_glucose']),
            'max_glucose': float(metrics['max_glucose']),
        }
    }
    
    # Save to JSON
    with open(filepath, 'w') as f:
        json.dump(simulation_data, f, indent=2)
    
    return metrics


def grid_search_example():
    """
    Comprehensive grid search over controller parameters using synthetic patient cohort.
    
    This performs a full grid search across Kp, Ki, Kd, target_glucose, and deadband,
    evaluating each configuration on a diverse cohort of 30 synthetic patients.
    """
    
    print("="*70)
    print("GRID SEARCH PARAMETER OPTIMIZATION")
    print("="*70)
    print("\nGenerating 30 synthetic patients (10 per archetype)...")
    
    # Generate synthetic patient cohort
    patients, _ = create_synthetic_patient_cohort(
        n_patients=30,
        random_seed=42,
        phenotype_probs=(1/3, 1/3, 1/3)  # Equal probability for each archetype
    )
    print(f"Generated {len(patients)} patients\n")
    
    # Define parameter ranges to explore

#    Kp_range = [0.0002, 0.0004, 0.0006, 0.0008]  # 4 values
    Kp_range = [0.0004]  # 1 value
    
    #   Ki_range = [8e-6, 1.2e-5, 1.6e-5, 2e-5]  # 4 values

    Ki_range = [1.2e-5]  # 1 value

    # Kd_range = [8e-5, 1.2e-4, 1.6e-4, 2e-4]  # 4 values

    Kd_range = [1.2e-4]  # 1 value

    target_range = [100, 110, 120]  # 3 values
    deadband_range = [10, 15]  # 2 values
    
    print(f"Parameter Grid Size:")
    print(f"  Kp: {len(Kp_range)} values: {[f'{v:.6f}' for v in Kp_range]}")
    print(f"  Ki: {len(Ki_range)} values: {[f'{v:.6f}' for v in Ki_range]}")
    print(f"  Kd: {len(Kd_range)} values: {[f'{v:.6f}' for v in Kd_range]}")
    print(f"  Target glucose: {target_range} mg/dL")
    print(f"  Deadband: {deadband_range} mg/dL")
    
    total_combinations = (len(Kp_range) * len(Ki_range) * len(Kd_range) * 
                         len(target_range) * len(deadband_range))
    total_simulations = total_combinations * len(patients)
    print(f"\nTotal controller configurations: {total_combinations}")
    print(f"Total simulations: {total_simulations}")
    print(f"Estimated time (at ~1s per simulation): {total_simulations / 60:.1f} minutes\n")
    
    meal_scenario = [(60, 50), (240, 60), (480, 55)]
    
    # Perform grid search
    rows = []
    sim_count = 0
    config_count = 0
    
    for Kp in Kp_range:
        for Ki in Ki_range:
            for Kd in Kd_range:
                for target in target_range:
                    for deadband in deadband_range:
                        config_count += 1
                        
                        if config_count == 1 or config_count % 20 == 0 or config_count == total_combinations:
                            print(f"\nConfiguration {config_count}/{total_combinations}: "
                                  f"Kp={Kp:.6f}, Ki={Ki:.6f}, Kd={Kd:.6f}, "
                                  f"target={target}, deadband={deadband}")
                        
                        controller_params = ControllerParams(
                            Kp=Kp, Ki=Ki, Kd=Kd,
                            target_glucose=target, deadband=deadband
                        )
                        
                        for patient in patients:
                            sim_count += 1
                            if sim_count % 500 == 0:
                                print(f"  Progress: {sim_count}/{total_simulations} simulations "
                                      f"({100*sim_count/total_simulations:.1f}%)")
                            
                            metrics = evaluate_controller_params(
                                controller_params,
                                patient_profile=patient,
                                meal_scenario=meal_scenario,
                                random_seed=42
                            )
                            
                            rows.append({
                                'patient_id': patient.patient_id,
                                'config_idx': config_count,
                                'Kp': Kp,
                                'Ki': Ki,
                                'Kd': Kd,
                                'target_glucose': target,
                                'deadband': deadband,
                                'time_in_range_pct': metrics['time_in_range_pct'],
                                'time_below_range_pct': metrics['time_below_range_pct'],
                                'time_above_range_pct': metrics['time_above_range_pct'],
                                'mean_glucose': metrics['mean_glucose'],
                                'cv_glucose': metrics['cv_glucose'],
                            })
    
    print(f"\nCompleted all {total_simulations} simulations!")
    
    # Convert to DataFrame for analysis
    results_df = pd.DataFrame(rows)
    
    # Aggregate across patients for each configuration
    summary_df = (
        results_df
        .groupby(['config_idx', 'Kp', 'Ki', 'Kd', 'target_glucose', 'deadband'], as_index=False)
        .agg(
            mean_tir_pct=('time_in_range_pct', 'mean'),
            std_tir_pct=('time_in_range_pct', 'std'),
            worst_tir_pct=('time_in_range_pct', 'min'),
            best_tir_pct=('time_in_range_pct', 'max'),
            mean_time_below_pct=('time_below_range_pct', 'mean'),
            mean_time_above_pct=('time_above_range_pct', 'mean'),
            mean_glucose=('mean_glucose', 'mean'),
            mean_cv_glucose=('cv_glucose', 'mean')
        )
        .sort_values(['mean_tir_pct', 'worst_tir_pct'], ascending=False)
    )
    
    # Find best configuration
    best_config = summary_df.iloc[0]
    
    print("\n" + "="*70)
    print("BEST CONFIGURATION (across 30-patient cohort):")
    print("="*70)
    print(f"Kp: {best_config['Kp']:.6f}")
    print(f"Ki: {best_config['Ki']:.6f}")
    print(f"Kd: {best_config['Kd']:.6f}")
    print(f"Target Glucose: {best_config['target_glucose']:.1f} mg/dL")
    print(f"Deadband: {best_config['deadband']:.1f} mg/dL")
    print(f"\nPerformance across cohort:")
    print(f"  Mean TIR: {best_config['mean_tir_pct']:.1f}% (±{best_config['std_tir_pct']:.1f}%)")
    print(f"  Best patient TIR: {best_config['best_tir_pct']:.1f}%")
    print(f"  Worst patient TIR: {best_config['worst_tir_pct']:.1f}%")
    print(f"  Mean Time Below: {best_config['mean_time_below_pct']:.1f}%")
    print(f"  Mean Time Above: {best_config['mean_time_above_pct']:.1f}%")
    print(f"  Mean Glucose: {best_config['mean_glucose']:.1f} mg/dL")
    print(f"  Mean CV: {best_config['mean_cv_glucose']:.1f}%")
    
    # Show top 10 configurations
    print("\n" + "-"*70)
    print("TOP 10 CONFIGURATIONS:")
    print("-"*70)
    for idx, row in summary_df.head(10).iterrows():
        print(f"{int(row['config_idx']):3d}. Kp={row['Kp']:.4f} Ki={row['Ki']:.5f} Kd={row['Kd']:.5f} "
              f"tgt={row['target_glucose']:.0f} db={row['deadband']:.0f} "
              f"→ TIR: {row['mean_tir_pct']:.1f}%±{row['std_tir_pct']:.1f}% "
              f"(worst: {row['worst_tir_pct']:.1f}%)")
    print("="*70)
    
    # Save results
    detailed_csv = Path(__file__).resolve().parent / 'grid_search_detailed_results.csv'
    summary_csv = Path(__file__).resolve().parent / 'grid_search_summary_results.csv'
    
    results_df.to_csv(detailed_csv, index=False)
    summary_df.to_csv(summary_csv, index=False)
    
    print(f"\nDetailed results saved to: {detailed_csv}")
    print(f"Summary results saved to: {summary_csv}")
    
    return results_df, summary_df


def full_grid_search_template():
    """
    Template for running a full grid search.
    Uncomment and modify as needed for actual optimization.
    """
    
    print("\nFULL GRID SEARCH TEMPLATE")
    print("Uncomment the code below to run a comprehensive parameter search:\n")
    
    template_code = '''
    # Define parameter ranges
    Kp_range = np.linspace(0.0001, 0.001, 10)
    Ki_range = np.linspace(0.000005, 0.00002, 10)
    Kd_range = np.linspace(0.00005, 0.0002, 10)
    target_range = [100, 110, 120]
    deadband_range = [10, 15, 20]
    
    results_list = []
    total = len(Kp_range) * len(Ki_range) * len(Kd_range) * len(target_range) * len(deadband_range)
    count = 0
    
    for Kp in Kp_range:
        for Ki in Ki_range:
            for Kd in Kd_range:
                for target in target_range:
                    for deadband in deadband_range:
                        count += 1
                        if count % 100 == 0:
                            print(f"Progress: {count}/{total} ({100*count/total:.1f}%)")
                        
                        controller_params = ControllerParams(
                            Kp=Kp, Ki=Ki, Kd=Kd,
                            target_glucose=target, deadband=deadband
                        )
                        
                        metrics = evaluate_controller_params(controller_params, random_seed=42)
                        results_list.append(metrics)
    
    # Analyze results
    results_df = pd.DataFrame(results_list)
    results_df = results_df.sort_values('time_in_range_pct', ascending=False)
    
    # Save top results
    results_df.to_csv('optimization_results_full.csv', index=False)
    print(f"\\nTop 10 configurations by Time in Range:")
    print(results_df.head(10)[['Kp', 'Ki', 'Kd', 'target_glucose', 'deadband', 
                                 'time_in_range_pct', 'mean_glucose', 'cv_glucose']])
    '''
    
    print(template_code)


def compare_multiple_scenarios():
    """
    Test controller parameters across multiple meal scenarios.
    This is important for robust parameter selection.
    """
    print("\n" + "="*70)
    print("MULTI-SCENARIO EVALUATION")
    print("="*70)
    print("\nTesting controller across different meal scenarios...\n")
    
    # Define different meal scenarios
    scenarios = {
        'Standard': [(60, 50), (240, 60), (480, 55)],
        'High Carb': [(60, 80), (240, 90), (480, 85)],
        'Low Carb': [(60, 30), (240, 35), (480, 30)],
        'Irregular': [(45, 40), (180, 30), (360, 70), (540, 45)],
    }
    
    # Test one controller configuration
    controller_params = ControllerParams(
        Kp=0.0005,
        Ki=0.00001,
        Kd=0.0001,
        target_glucose=110.0,
        deadband=15.0
    )

    patient_profile = PatientProfile(
        patient_id="scenario_test_patient",
        physiological_params=PhysiologicalParams()
    )
    
    results_by_scenario = {}
    
    for scenario_name, meals in scenarios.items():
        print(f"Scenario: {scenario_name}")
        print(f"  Meals: {meals}")
        
        metrics = evaluate_controller_params(
            controller_params, 
            patient_profile=patient_profile,
            meal_scenario=meals, 
            random_seed=42
        )
        
        results_by_scenario[scenario_name] = metrics
        
        print(f"  → Time in Range: {metrics['time_in_range_pct']:.1f}%")
        print(f"  → Mean Glucose: {metrics['mean_glucose']:.1f} mg/dL\n")
    
    # Calculate average performance
    avg_tir = np.mean([m['time_in_range_pct'] for m in results_by_scenario.values()])
    print(f"Average Time in Range across scenarios: {avg_tir:.1f}%")
    print("="*70)
    
    return results_by_scenario


def optimize_across_patients_example():
    """
    Evaluate candidate controller settings across multiple example patients.

    This demonstrates cohort-level scoring, which is usually more robust than
    tuning on a single patient profile.
    
    Generates 30 synthetic patients (10 per archetype) and tests across
    a wider parameter sweep of Kp, Ki, and Kd values.
    """
    print("\n" + "="*70)
    print("MULTI-PATIENT CONTROLLER EVALUATION")
    print("="*70)
    print("\nGenerating 30 synthetic patients (10 per archetype)...")

    # Generate 30 patients with equal probability for each archetype
    # This gives approximately 10 patients per archetype
    patients, _ = create_synthetic_patient_cohort(
        n_patients=30,
        random_seed=42,
        phenotype_probs=(1/3, 1/3, 1/3)  # Equal probability for each archetype
    )
    
    print(f"Generated {len(patients)} patients")
    meal_scenario = [(60, 50), (240, 60), (480, 55)]

    # Wider parameter sweeps
    Kp_values = [0.0001, 0.0003, 0.0005, 0.0007, 0.001]
    Ki_values = [5e-6, 1e-5, 2e-5, 3e-5]
    Kd_values = [5e-5, 1e-4, 2e-4, 3e-4]
    
    candidate_controllers = []
    for Kp in Kp_values:
        for Ki in Ki_values:
            for Kd in Kd_values:
                candidate_controllers.append(
                    ControllerParams(Kp=Kp, Ki=Ki, Kd=Kd, target_glucose=110.0, deadband=15.0)
                )
    
    print(f"Testing {len(candidate_controllers)} controller configurations...")
    print(f"Total simulations: {len(candidate_controllers)} controllers × {len(patients)} patients = {len(candidate_controllers) * len(patients)}")
    print(f"Estimated time (at ~1s per simulation): {len(candidate_controllers) * len(patients) / 60:.1f} minutes\n")

    rows = []
    total_sims = len(candidate_controllers) * len(patients)
    sim_count = 0

    for i, controller_params in enumerate(candidate_controllers, 1):
        if i == 1 or i % 10 == 0 or i == len(candidate_controllers):
            print(f"\nController {i}/{len(candidate_controllers)}: Kp={controller_params.Kp:.6f}, Ki={controller_params.Ki:.6f}, "
                  f"Kd={controller_params.Kd:.6f}")

        for patient in patients:
            sim_count += 1
            if sim_count % 100 == 0:
                print(f"  Progress: {sim_count}/{total_sims} simulations ({100*sim_count/total_sims:.1f}%)")
            
            metrics = evaluate_controller_params(
                controller_params,
                patient_profile=patient,
                meal_scenario=meal_scenario,
                random_seed=42
            )

            rows.append({
                'patient_id': patient.patient_id,
                'controller_idx': i,
                'Kp': controller_params.Kp,
                'Ki': controller_params.Ki,
                'Kd': controller_params.Kd,
                'target_glucose': controller_params.target_glucose,
                'deadband': controller_params.deadband,
                'time_in_range_pct': metrics['time_in_range_pct'],
                'time_below_range_pct': metrics['time_below_range_pct'],
                'time_above_range_pct': metrics['time_above_range_pct'],
                'mean_glucose': metrics['mean_glucose'],
                'cv_glucose': metrics['cv_glucose'],
            })


    print(f"\nCompleted all {total_sims} simulations!")
    
    results_df = pd.DataFrame(rows)
    summary_df = (
        results_df
        .groupby(['controller_idx', 'Kp', 'Ki', 'Kd', 'target_glucose', 'deadband'], as_index=False)
        .agg(
            mean_tir_pct=('time_in_range_pct', 'mean'),
            std_tir_pct=('time_in_range_pct', 'std'),
            worst_tir_pct=('time_in_range_pct', 'min'),
            best_tir_pct=('time_in_range_pct', 'max'),
            mean_time_below_pct=('time_below_range_pct', 'mean'),
            mean_time_above_pct=('time_above_range_pct', 'mean'),
            mean_glucose=('mean_glucose', 'mean')
        )
        .sort_values(['mean_tir_pct', 'worst_tir_pct'], ascending=False)
    )

    best_row = summary_df.iloc[0]

    print("\n" + "-"*70)
    print("BEST COHORT CONTROLLER")
    print("-"*70)
    print(f"Controller index: {int(best_row['controller_idx'])}")
    print(f"Kp={best_row['Kp']:.6f}, Ki={best_row['Ki']:.6f}, Kd={best_row['Kd']:.6f}")
    print(f"Target={best_row['target_glucose']:.0f}, Deadband={best_row['deadband']:.0f}")
    print(f"\nPerformance across 30-patient cohort:")
    print(f"  Mean TIR: {best_row['mean_tir_pct']:.1f}% (±{best_row['std_tir_pct']:.1f}%)")
    print(f"  Best patient TIR: {best_row['best_tir_pct']:.1f}%")
    print(f"  Worst patient TIR: {best_row['worst_tir_pct']:.1f}%")
    print(f"  Mean Time Below Range: {best_row['mean_time_below_pct']:.1f}%")
    print(f"  Mean Time Above Range: {best_row['mean_time_above_pct']:.1f}%")
    
    # Show top 5 controllers
    print("\n" + "-"*70)
    print("TOP 5 CONTROLLERS:")
    print("-"*70)
    for idx, row in summary_df.head(5).iterrows():
        print(f"{int(row['controller_idx']):3d}. Kp={row['Kp']:.6f}, Ki={row['Ki']:.6f}, Kd={row['Kd']:.6f} "
              f"→ Mean TIR: {row['mean_tir_pct']:.1f}% (worst: {row['worst_tir_pct']:.1f}%)")
    print("="*70)

    detailed_csv = SCRIPT_DIR / 'multi_patient_results.csv'
    summary_csv = SCRIPT_DIR / 'multi_patient_summary.csv'
    results_df.to_csv(detailed_csv, index=False)
    summary_df.to_csv(summary_csv, index=False)

    print(f"Detailed multi-patient results saved to: {detailed_csv}")
    print(f"Summary multi-patient results saved to: {summary_csv}")

    return results_df, summary_df


def synthetic_cohort_sampling_example(n_patients: int = 30,
                                      random_seed: int = 123):
    """Generate and save a synthetic patient cohort using defined distributions."""
    print("\n" + "="*70)
    print("SYNTHETIC PATIENT COHORT SAMPLING")
    print("="*70)
    print(f"Sampling {n_patients} synthetic patients with seed={random_seed}")
    print("Mixture probabilities: sensitive=0.25, reference=0.50, resistant=0.25")

    profiles, cohort_df = create_synthetic_patient_cohort(
        n_patients=n_patients,
        random_seed=random_seed,
        phenotype_probs=(0.25, 0.50, 0.25)
    )

    print("\nParameter distribution definitions used:")
    print("  Gb: truncated normal (sigma=8.0, bounds [75, 140])")
    print("  Ib: bounded lognormal (sigma_log=0.25, bounds [4, 25])")
    print("  p1: bounded lognormal (sigma_log=0.20, bounds [0.015, 0.045])")
    print("  p2: bounded lognormal (sigma_log=0.20, bounds [0.012, 0.040])")
    print("  p3: bounded lognormal (sigma_log=0.35, bounds [4e-6, 3e-5])")
    print("  tau_meal: bounded lognormal (sigma_log=0.25, bounds [20, 90])")
    print("  Vg: truncated normal (sigma=0.15, bounds [1.1, 2.2])")
    print("  insulin_clearance_rate: bounded lognormal (sigma_log=0.20, bounds [0.05, 0.18])")
    print("  Correlation mechanism: latent resistance/kinetics factors")

    print("\nPhenotype counts:")
    print(cohort_df['phenotype'].value_counts().to_string())

    print("\nSample of first 5 patients:")
    display_cols = [
        'patient_id', 'phenotype', 'Gb', 'Ib', 'p1', 'p2', 'p3',
        'tau_meal', 'Vg', 'insulin_clearance_rate'
    ]
    print(cohort_df[display_cols].head(5).to_string(index=False))

    output_csv = SCRIPT_DIR / 'synthetic_patient_cohort.csv'
    cohort_df.to_csv(output_csv, index=False)
    print(f"\nSynthetic cohort saved to: {output_csv}")
    print("="*70)

    return profiles, cohort_df


def parse_cli_args():
    """Parse command line arguments for optimization demonstrations."""
    parser = argparse.ArgumentParser(
        description="PID optimization and synthetic cohort generation examples"
    )
    parser.add_argument(
        '--cohort-size',
        type=int,
        default=30,
        help='Number of synthetic patients to sample (default: 30)'
    )
    parser.add_argument(
        '--cohort-seed',
        type=int,
        default=123,
        help='Random seed for synthetic cohort sampling (default: 123)'
    )
    parser.add_argument(
        '--cohort-only',
        action='store_true',
        help='Run only synthetic cohort sampling and skip other demos'
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_cli_args()

    if args.cohort_only:
        synthetic_profiles, synthetic_cohort_df = synthetic_cohort_sampling_example(
            n_patients=args.cohort_size,
            random_seed=args.cohort_seed
        )
        print("\nCohort-only mode complete.")
        sys.exit(0)
    
    # =========================================================================
    # COMPREHENSIVE OPTIMIZATION WITH PROPER NESTING
    # =========================================================================
    # 1. Generate patient cohort ONCE
    # 2. Define meal scenarios ONCE  
    # 3. Grid search: For each controller config -> each patient -> each scenario
    # =========================================================================
    
    print("\n" + "="*70)
    print("COMPREHENSIVE CONTROLLER OPTIMIZATION")
    print("="*70)
    print("\nStep 1: Generating synthetic patient cohort...")
    
    # Generate ONE cohort of 30 patients to be used throughout
    patients, cohort_df = create_synthetic_patient_cohort(
        n_patients=30,
        random_seed=42,
        phenotype_probs=(1/3, 1/3, 1/3)
    )
    print(f"Generated {len(patients)} patients")
    print(f"  Phenotype distribution: {cohort_df['phenotype'].value_counts().to_dict()}")
    
    # Save cohort for reference
    cohort_csv = SCRIPT_DIR / 'synthetic_patient_cohort.csv'
    cohort_df.to_csv(cohort_csv, index=False)
    print(f"  Cohort saved to: {cohort_csv}")
    
    print("\nStep 2: Defining meal scenarios...")
    meal_scenarios = {
        'standard': [(60, 50), (240, 60), (480, 55)],
        'high_carb': [(60, 80), (240, 90), (480, 85)],
        'low_carb': [(60, 30), (240, 35), (480, 30)],
        'irregular': [(45, 40), (180, 30), (360, 70), (540, 45)],
    }
    print(f"  Defined {len(meal_scenarios)} meal scenarios: {list(meal_scenarios.keys())}")
    
    print("\nStep 3: Grid search over controller parameters...")
    
    # Define parameter grid
    # Kp_range = [0.0002, 0.0004, 0.0006, 0.0008]  # 4 values
    Kp_range = [0.0004]  # 1 value
    
    # Ki_range = [8e-6, 1.2e-5, 1.6e-5, 2e-5]  # 4 values
    Ki_range = [1.2e-5]  # 1 value
    
    # Kd_range = [8e-5, 1.2e-4, 1.6e-4, 2e-4]  # 4 values
    Kd_range = [1.2e-4]  # 1 value
    
    target_range = [100, 110, 120]  # 3 values
    deadband_range = [10, 15]  # 2 values
    
    print(f"\nParameter grid:")
    print(f"  Kp: {len(Kp_range)} values")
    print(f"  Ki: {len(Ki_range)} values")
    print(f"  Kd: {len(Kd_range)} values")
    print(f"  Target glucose: {len(target_range)} values")
    print(f"  Deadband: {len(deadband_range)} values")
    
    total_configs = len(Kp_range) * len(Ki_range) * len(Kd_range) * len(target_range) * len(deadband_range)
    total_sims = total_configs * len(patients) * len(meal_scenarios)
    
    print(f"\nTotal controller configurations: {total_configs}")
    print(f"Total simulations: {total_configs} configs × {len(patients)} patients × {len(meal_scenarios)} scenarios = {total_sims}")
    print(f"Estimated time (at ~1s per simulation): {total_sims / 60:.1f} minutes")
    
    # Create output directory for time-series data
    simulations_base_dir = SCRIPT_DIR / 'simulation_time_series'
    simulations_base_dir.mkdir(exist_ok=True)
    print(f"\nTime-series data will be saved to: {simulations_base_dir}")
    print(f"  Creating patient subdirectories...")
    
    # Create subdirectories for each patient
    patient_dirs = {}
    for patient in patients:
        patient_dir = simulations_base_dir / patient.patient_id
        patient_dir.mkdir(exist_ok=True)
        patient_dirs[patient.patient_id] = patient_dir
    
    print(f"  Created {len(patient_dirs)} patient directories")
    print(f"\nStarting nested evaluation...\n")
    
    # Nested loop structure: config -> patient -> scenario
    rows = []
    sim_count = 0
    config_count = 0
    
    for Kp in Kp_range:
        for Ki in Ki_range:
            for Kd in Kd_range:
                for target in target_range:
                    for deadband in deadband_range:
                        config_count += 1
                        
                        if config_count == 1 or config_count % 20 == 0 or config_count == total_configs:
                            print(f"\nConfig {config_count}/{total_configs}: "
                                  f"Kp={Kp:.6f}, Ki={Ki:.6f}, Kd={Kd:.6f}, "
                                  f"target={target}, deadband={deadband}")
                        
                        controller_params = ControllerParams(
                            Kp=Kp, Ki=Ki, Kd=Kd,
                            target_glucose=target, deadband=deadband
                        )
                        
                        # Test this controller on all patients
                        for patient in patients:
                            # Get patient output directory
                            patient_output_dir = patient_dirs[patient.patient_id]
                            
                            # Test on all meal scenarios
                            for scenario_name, meals in meal_scenarios.items():
                                sim_count += 1
                                
                                if sim_count % 1000 == 0:
                                    print(f"  Progress: {sim_count}/{total_sims} sims "
                                          f"({100*sim_count/total_sims:.1f}%)")
                                
                                # Run simulation and save time-series data
                                metrics = evaluate_and_save_simulation(
                                    controller_params,
                                    patient_profile=patient,
                                    meal_scenario=meals,
                                    scenario_name=scenario_name,
                                    output_dir=patient_output_dir,
                                    config_idx=config_count,
                                    random_seed=42
                                )
                                
                                rows.append({
                                    'config_idx': config_count,
                                    'patient_id': patient.patient_id,
                                    'scenario': scenario_name,
                                    'Kp': Kp,
                                    'Ki': Ki,
                                    'Kd': Kd,
                                    'target_glucose': target,
                                    'deadband': deadband,
                                    'time_in_range_pct': metrics['time_in_range_pct'],
                                    'time_below_range_pct': metrics['time_below_range_pct'],
                                    'time_above_range_pct': metrics['time_above_range_pct'],
                                    'mean_glucose': metrics['mean_glucose'],
                                    'cv_glucose': metrics['cv_glucose'],
                                })
    
    print(f"\n✓ Completed all {total_sims} simulations!")
    
    # Convert to DataFrame
    results_df = pd.DataFrame(rows)
    
    # Create comprehensive summary aggregating across patients and scenarios
    print("\nGenerating summary statistics...")
    summary_df = (
        results_df
        .groupby(['config_idx', 'Kp', 'Ki', 'Kd', 'target_glucose', 'deadband'], as_index=False)
        .agg(
            mean_tir_pct=('time_in_range_pct', 'mean'),
            std_tir_pct=('time_in_range_pct', 'std'),
            worst_tir_pct=('time_in_range_pct', 'min'),
            best_tir_pct=('time_in_range_pct', 'max'),
            mean_time_below_pct=('time_below_range_pct', 'mean'),
            mean_time_above_pct=('time_above_range_pct', 'mean'),
            mean_glucose=('mean_glucose', 'mean'),
            mean_cv_glucose=('cv_glucose', 'mean')
        )
        .sort_values(['mean_tir_pct', 'worst_tir_pct'], ascending=False)
    )
    
    # Also create per-scenario summary
    scenario_summary_df = (
        results_df
        .groupby(['config_idx', 'Kp', 'Ki', 'Kd', 'target_glucose', 'deadband', 'scenario'], as_index=False)
        .agg(
            mean_tir_pct=('time_in_range_pct', 'mean'),
            std_tir_pct=('time_in_range_pct', 'std'),
            worst_tir_pct=('time_in_range_pct', 'min'),
            best_tir_pct=('time_in_range_pct', 'max'),
        )
    )
    
    # Find best configuration
    best_config = summary_df.iloc[0]
    
    print("\n" + "="*70)
    print("BEST CONTROLLER CONFIGURATION")
    print("="*70)
    print(f"Kp: {best_config['Kp']:.6f}")
    print(f"Ki: {best_config['Ki']:.6f}")
    print(f"Kd: {best_config['Kd']:.6f}")
    print(f"Target Glucose: {best_config['target_glucose']:.1f} mg/dL")
    print(f"Deadband: {best_config['deadband']:.1f} mg/dL")
    print(f"\nPerformance (across {len(patients)} patients and {len(meal_scenarios)} scenarios):")
    print(f"  Mean TIR: {best_config['mean_tir_pct']:.1f}% (±{best_config['std_tir_pct']:.1f}%)")
    print(f"  Best case TIR: {best_config['best_tir_pct']:.1f}%")
    print(f"  Worst case TIR: {best_config['worst_tir_pct']:.1f}%")
    print(f"  Mean Time Below: {best_config['mean_time_below_pct']:.1f}%")
    print(f"  Mean Time Above: {best_config['mean_time_above_pct']:.1f}%")
    print(f"  Mean Glucose: {best_config['mean_glucose']:.1f} mg/dL")
    print(f"  Mean CV: {best_config['mean_cv_glucose']:.1f}%")
    
    # Show top 10 configurations
    print("\n" + "-"*70)
    print("TOP 10 CONTROLLER CONFIGURATIONS:")
    print("-"*70)
    for idx, row in summary_df.head(10).iterrows():
        print(f"{int(row['config_idx']):3d}. Kp={row['Kp']:.4f} Ki={row['Ki']:.5f} Kd={row['Kd']:.5f} "
              f"tgt={row['target_glucose']:.0f} db={row['deadband']:.0f} "
              f"→ TIR: {row['mean_tir_pct']:.1f}%±{row['std_tir_pct']:.1f}% "
              f"(worst: {row['worst_tir_pct']:.1f}%)")
    
    # Show best config performance by scenario
    best_config_idx = int(best_config['config_idx'])
    best_by_scenario = scenario_summary_df[scenario_summary_df['config_idx'] == best_config_idx]
    print("\n" + "-"*70)
    print("BEST CONTROLLER PERFORMANCE BY MEAL SCENARIO:")
    print("-"*70)
    for _, row in best_by_scenario.iterrows():
        print(f"  {row['scenario']:15s}: {row['mean_tir_pct']:5.1f}% ± {row['std_tir_pct']:4.1f}% "
              f"(worst: {row['worst_tir_pct']:5.1f}%)")
    
    print("="*70)
    
    # Save all results
    detailed_csv = SCRIPT_DIR / 'comprehensive_optimization_results.csv'
    summary_csv = SCRIPT_DIR / 'comprehensive_optimization_summary.csv'
    scenario_summary_csv = SCRIPT_DIR / 'comprehensive_optimization_by_scenario.csv'
    
    results_df.to_csv(detailed_csv, index=False)
    summary_df.to_csv(summary_csv, index=False)
    scenario_summary_df.to_csv(scenario_summary_csv, index=False)
    
    print("\n" + "="*70)
    print("OPTIMIZATION COMPLETE")
    print("="*70)
    print(f"\nOutput files:")
    print(f"  1. {detailed_csv.name}")
    print(f"     → All {total_sims} individual simulation results")
    print(f"  2. {summary_csv.name}")
    print(f"     → Aggregated metrics across all patients and scenarios")
    print(f"  3. {scenario_summary_csv.name}")
    print(f"     → Performance breakdown by meal scenario")
    print(f"  4. {cohort_csv.name}")
    print(f"     → Patient cohort characteristics")
    print(f"  5. {simulations_base_dir.name}/")
    print(f"     → {total_sims} JSON files with full time-series data")
    print(f"     → Organized in {len(patients)} patient subdirectories")
    print(f"     → Each file contains: glucose/insulin time series, parameters, metrics")
    print("="*70)

