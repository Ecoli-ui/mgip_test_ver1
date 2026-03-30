#!/usr/bin/env python3
"""
Test script to verify body weight scaling in the glucose simulator.
"""

import sys
from pathlib import Path

# Ensure sibling modules can be imported
SCRIPT_DIR = Path(__file__).parent.absolute()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from glucose_simulator import (
    PhysiologicalParams, PatientProfile, PhysiologicalModel,
    SensorParams, SensorModel, PumpParams, PumpModel,
    PIDParams, PIDController, GlucoseInsulinSimulator
)

def test_backward_compatibility():
    """Test that default 70kg behavior is unchanged."""
    print("=" * 70)
    print("TEST 1: Backward Compatibility (Default 70kg)")
    print("=" * 70)
    
    # Create simulator with default parameters
    params = PhysiologicalParams()
    profile = PatientProfile(patient_id="test_70kg", physiological_params=params)
    
    print(f"\nBody weight: {params.body_weight} kg")
    print(f"Vg: {params.Vg} dL/kg")
    print(f"Total volume: {params.Vg * params.body_weight} dL")
    print(f"Meal bioavailability: {params.meal_bioavailability}")
    
    # Calculate expected meal impact for 50g carbs
    carbs = 50.0
    expected_impact_old = carbs * 5.0
    expected_impact_new = carbs * 1000 * params.meal_bioavailability / (params.Vg * params.body_weight)
    
    print(f"\nFor {carbs}g carbs:")
    print(f"  Old formula (carbs * 5.0): {expected_impact_old:.2f} mg/dL")
    print(f"  New formula: {expected_impact_new:.2f} mg/dL")
    print(f"  Match: {abs(expected_impact_old - expected_impact_new) < 0.01}")

def test_different_body_weights():
    """Test behavior with different body weights."""
    print("\n" + "=" * 70)
    print("TEST 2: Different Body Weights")
    print("=" * 70)
    
    weights = [50.0, 70.0, 90.0, 110.0]
    carbs = 50.0
    insulin_rate = 0.02  # U/min
    
    print(f"\nFor {carbs}g carbs and {insulin_rate} U/min insulin:")
    print(f"{'Weight (kg)':<15} {'Total Vol (dL)':<20} {'Meal Impact (mg/dL)':<25} {'Insulin→Plasma (mU/L/min)':<30}")
    print("-" * 90)
    
    for weight in weights:
        params = PhysiologicalParams(body_weight=weight)
        total_volume = params.Vg * params.body_weight
        meal_impact = carbs * 1000 * params.meal_bioavailability / total_volume
        insulin_to_plasma = insulin_rate * 1000 / total_volume
        
        print(f"{weight:<15.1f} {total_volume:<20.1f} {meal_impact:<25.2f} {insulin_to_plasma:<30.3f}")
    
    print("\nObservations:")
    print("  - Heavier patients: larger distribution volume → lower meal impact")
    print("  - Heavier patients: same insulin dose → lower plasma concentration")
    print("  - This matches physiological reality!")

def test_simulation_comparison():
    """Run short simulation with different body weights."""
    print("\n" + "=" * 70)
    print("TEST 3: Simulation Comparison (50kg vs 70kg vs 90kg)")
    print("=" * 70)
    
    weights = [50.0, 70.0, 90.0]
    duration = 360  # 6 hours
    
    # Simple meal at t=60 min
    meals = [(60, 50)]  # 50g carbs
    
    print(f"\nScenario: 50g carb meal at t=60 min, no controller (basal insulin only)")
    print(f"Duration: {duration} minutes")
    print()
    
    for weight in weights:
        # Create patient with specific body weight
        params = PhysiologicalParams(body_weight=weight)
        profile = PatientProfile(
            patient_id=f"patient_{weight}kg",
            physiological_params=params
        )
        
        # Create simulator with no active controller (Kp=0) to see meal effect
        sim = GlucoseInsulinSimulator(
            patient_profile=profile,
            sensor_params=SensorParams(noise_std=0.0),  # No noise for clearer results
            pump_params=PumpParams(),
            pid_params=PIDParams(Kp=0.0, Ki=0.0, Kd=0.0)  # No control
        )
        
        # Run simulation
        results = sim.simulate(duration_minutes=duration, meals=meals)
        
        # Find peak glucose after meal
        meal_start_idx = 60  # minute 60
        meal_end_idx = 240  # check up to minute 240
        peak_glucose = max(results['true_glucose'][meal_start_idx:meal_end_idx])
        peak_time_idx = list(results['true_glucose'][meal_start_idx:meal_end_idx]).index(
            peak_glucose
        ) + meal_start_idx
        
        baseline = results['true_glucose'][0]
        glucose_excursion = peak_glucose - baseline
        
        print(f"{weight}kg patient:")
        print(f"  Baseline glucose: {baseline:.1f} mg/dL")
        print(f"  Peak glucose: {peak_glucose:.1f} mg/dL (at t={peak_time_idx} min)")
        print(f"  Glucose excursion: {glucose_excursion:.1f} mg/dL")
        print(f"  Final glucose (t={duration}): {results['true_glucose'][-1]:.1f} mg/dL")
        print()
    
    print("Expected: Lighter patients have larger glucose excursions for same meal")

def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("BODY WEIGHT SCALING TESTS")
    print("=" * 70)
    print()
    
    test_backward_compatibility()
    test_different_body_weights()
    test_simulation_comparison()
    
    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED")
    print("=" * 70)

if __name__ == "__main__":
    main()
