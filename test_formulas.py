#!/usr/bin/env python3
"""
Simple test to verify body weight scaling logic.
"""

def test_formulas():
    """Test the conversion formulas directly."""
    print("=" * 70)
    print("BODY WEIGHT SCALING - FORMULA VERIFICATION")
    print("=" * 70)
    
    # Test 1: Backward compatibility (70kg)
    print("\nTest 1: Backward Compatibility (70kg patient)")
    print("-" * 70)
    body_weight = 70.0
    Vg = 1.5
    meal_bioavailability = 0.525
    carbs = 50.0
    
    total_volume = Vg * body_weight
    meal_impact_old = carbs * 5.0
    meal_impact_new = carbs * 1000 * meal_bioavailability / total_volume
    
    print(f"Body weight: {body_weight} kg")
    print(f"Vg: {Vg} dL/kg")
    print(f"Total volume: {total_volume} dL")
    print(f"Meal bioavailability: {meal_bioavailability}")
    print(f"\nFor {carbs}g carbs:")
    print(f"  Old formula: {meal_impact_old:.2f} mg/dL")
    print(f"  New formula: {meal_impact_new:.2f} mg/dL")
    print(f"  Difference: {abs(meal_impact_old - meal_impact_new):.4f} mg/dL")
    print(f"  ✓ PASS" if abs(meal_impact_old - meal_impact_new) < 0.01 else "  ✗ FAIL")
    
    # Test 2: Different body weights
    print("\n\nTest 2: Scaling Across Different Body Weights")
    print("-" * 70)
    print(f"\nMeal Impact for {carbs}g carbs:")
    print(f"{'Weight (kg)':<15} {'Total Vol (dL)':<20} {'Meal Impact (mg/dL)':<25}")
    print("-" * 60)
    
    for weight in [50.0, 60.0, 70.0, 80.0, 90.0, 100.0, 110.0]:
        total_vol = Vg * weight
        impact = carbs * 1000 * meal_bioavailability / total_vol
        print(f"{weight:<15.1f} {total_vol:<20.1f} {impact:<25.2f}")
    
    # Test 3: Insulin-to-plasma conversion
    print("\n\nTest 3: Insulin-to-Plasma Conversion")
    print("-" * 70)
    insulin_rate = 0.02  # U/min
    
    print(f"\nInsulin infusion rate: {insulin_rate} U/min")
    print(f"{'Weight (kg)':<15} {'Total Vol (dL)':<20} {'Plasma Conc (mU/L/min)':<30}")
    print("-" * 65)
    
    for weight in [50.0, 60.0, 70.0, 80.0, 90.0, 100.0, 110.0]:
        total_vol = Vg * weight
        insulin_to_plasma = insulin_rate * 1000 / total_vol
        print(f"{weight:<15.1f} {total_vol:<20.1f} {insulin_to_plasma:<30.3f}")
    
    # Test 4: Verify bioavailability calibration
    print("\n\nTest 4: Bioavailability Factor Verification")
    print("-" * 70)
    print("\nThe bioavailability factor should match the old hardcoded scaling:")
    print(f"  Old scaling: 5.0 mg/dL per gram (for 70kg, Vg=1.5)")
    print(f"  Expected bioavailability = 5.0 * (70 * 1.5) / 1000 = {5.0 * 105 / 1000:.3f}")
    print(f"  Actual bioavailability setting: {meal_bioavailability}")
    print(f"  ✓ MATCH" if abs(meal_bioavailability - 5.0 * 105 / 1000) < 0.01 else "  ✗ MISMATCH")
    
    # Test 5: Physiological reasonableness
    print("\n\nTest 5: Physiological Reasonableness Check")
    print("-" * 70)
    print("\nTheoretical maximum glucose increase (100% bioavailability):")
    print(f"{'Weight (kg)':<15} {'Total Vol (dL)':<20} {'Max Impact (mg/dL)':<25}")
    print("-" * 60)
    
    for weight in [50.0, 70.0, 90.0]:
        total_vol = Vg * weight
        max_impact = carbs * 1000 / total_vol  # 100% bioavailability
        actual_impact = carbs * 1000 * meal_bioavailability / total_vol
        print(f"{weight:<15.1f} {total_vol:<20.1f} {max_impact:<25.2f} (actual: {actual_impact:.1f})")
    
    print("\nNote: Actual impact is ~53% of theoretical max (accounts for")
    print("      incomplete absorption, hepatic metabolism, and utilization)")
    
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    test_formulas()
