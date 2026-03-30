#!/usr/bin/env python3
"""
Regenerate synthetic patient cohort with body_weight and meal_bioavailability.
"""
import sys
import csv
from pathlib import Path
import numpy as np

# Script directory
SCRIPT_DIR = Path(__file__).parent.absolute()


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
    """Sample one synthetic patient."""
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
    body_weight_mean = 70.0 + 5.0 * z_resistance
    body_weight = _sample_truncated_normal(rng, body_weight_mean, 12.0, 45.0, 120.0)
    
    # Meal bioavailability (slight variation from default)
    meal_bioavailability = _sample_truncated_normal(rng, 0.525, 0.05, 0.40, 0.70)
    
    patient_id = f"synthetic_{patient_index:03d}_{phenotype}"
    
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
    return metadata


def main():
    """Generate synthetic patient cohort."""
    print("=" * 70)
    print("REGENERATING SYNTHETIC PATIENT COHORT")
    print("=" * 70)
    
    n_patients = 30
    random_seed = 123
    
    print(f"\nNumber of patients: {n_patients}")
    print(f"Random seed: {random_seed}")
    
    rng = np.random.default_rng(random_seed)
    
    # Generate patients
    patients = []
    for i in range(1, n_patients + 1):
        metadata = sample_virtual_patient(rng, i)
        patients.append(metadata)
    
    # Write to CSV
    output_file = SCRIPT_DIR / 'synthetic_patient_cohort.csv'
    
    fieldnames = ['patient_id', 'phenotype', 'Gb', 'Ib', 'p1', 'p2', 'p3', 
                  'tau_meal', 'Vg', 'insulin_clearance_rate', 'body_weight', 
                  'meal_bioavailability']
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(patients)
    
    print(f"\n✓ Saved to: {output_file}")
    print(f"✓ Columns: {', '.join(fieldnames)}")
    
    # Print summary statistics
    print("\n" + "=" * 70)
    print("COHORT STATISTICS")
    print("=" * 70)
    
    phenotypes = [p['phenotype'] for p in patients]
    body_weights = [p['body_weight'] for p in patients]
    meal_bioavailabilities = [p['meal_bioavailability'] for p in patients]
    
    from collections import Counter
    phenotype_counts = Counter(phenotypes)
    
    print("\nPhenotype distribution:")
    for phenotype, count in phenotype_counts.items():
        print(f"  {phenotype}: {count} ({100*count/n_patients:.1f}%)")
    
    print(f"\nBody weight:")
    print(f"  Range: [{min(body_weights):.1f}, {max(body_weights):.1f}] kg")
    print(f"  Mean: {np.mean(body_weights):.1f} kg")
    print(f"  Std: {np.std(body_weights, ddof=1):.1f} kg")
    
    print(f"\nMeal bioavailability:")
    print(f"  Range: [{min(meal_bioavailabilities):.3f}, {max(meal_bioavailabilities):.3f}]")
    print(f"  Mean: {np.mean(meal_bioavailabilities):.3f}")
    print(f"  Std: {np.std(meal_bioavailabilities, ddof=1):.3f}")
    
    print("\n" + "=" * 70)
    print("DONE!")
    print("=" * 70)


if __name__ == "__main__":
    main()
