# Model Predictive Control (MPC) Parameter Optimization Guide

## Overview

Model Predictive Control (MPC) is an advanced control strategy that optimizes insulin delivery by predicting future glucose trajectories over a horizon. Unlike PID, MPC can:
- Anticipate future trends
- Handle constraints explicitly
- Incorporate meal announcements
- Balance multiple objectives simultaneously

## MPC Parameters to Optimize

### 1. Prediction Horizon (`prediction_horizon`)
**What it does**: How many time steps ahead the controller predicts glucose

- **Range**: 10-60 minutes (typical: 20-40 min)
- **Trade-offs**:
  - **Longer**: Better anticipation, can prepare for future events, more robust
  - **Shorter**: Faster computation, more reactive, less forward-looking
- **Typical**: 30 minutes (30 time steps at dt=1 min)

### 2. Control Horizon (`control_horizon`)
**What it does**: How many future insulin rates to optimize

- **Range**: 5-20 minutes (typical: 8-15 min)
- **Trade-offs**:
  - **Longer**: More flexibility, better optimization, slower computation
  - **Shorter**: Faster computation, less complex optimization
  - Must be ≤ prediction_horizon
- **Typical**: 10 minutes (10 time steps)
- **Rule of thumb**: control_horizon ≈ 1/3 to 1/2 of prediction_horizon

### 3. Tracking Weight (`weight_tracking`)
**What it does**: Importance of minimizing glucose deviation from target

- **Range**: 0.5-5.0 (typical: 1.0-2.0)
- **Effect**:
  - **Higher**: More aggressive tracking, tighter control, more insulin
  - **Lower**: Looser control, allows more deviation
- **Typical**: 1.0-1.5

### 4. Control Effort Weight (`weight_control`)
**What it does**: Penalty for insulin usage (regularization)

- **Range**: 0.001-0.1 (typical: 0.01-0.05)
- **Effect**:
  - **Higher**: Conservative insulin delivery, less aggressive
  - **Lower**: More aggressive insulin use, risk of stacking
- **Typical**: 0.01-0.02
- **Purpose**: Prevents excessive insulin delivery

### 5. Rate of Change Weight (`weight_rate`)
**What it does**: Penalty for rapid changes in insulin delivery (smoothness)

- **Range**: 0.01-0.2 (typical: 0.03-0.08)
- **Effect**:
  - **Higher**: Smoother insulin delivery, less reactive
  - **Lower**: Can make rapid adjustments, more reactive
- **Typical**: 0.05
- **Purpose**: Prevents erratic control actions

### 6. Terminal Weight (`weight_terminal`)
**What it does**: Extra emphasis on final predicted state

- **Range**: 1.0-10.0 (typical: 2.0-5.0)
- **Effect**:
  - **Higher**: Ensures good final state, more stable long-term
  - **Lower**: More emphasis on immediate trajectory
- **Typical**: 2.0-3.0
- **Purpose**: Stabilizes predictions at horizon end

### 7. Violation Weight (`weight_violation`)
**What it does**: Penalty for constraint violations (especially hypoglycemia)

- **Range**: 50-500 (typical: 100-200)
- **Effect**:
  - **Higher**: Stronger avoidance of bounds, very conservative
  - **Lower**: May allow constraint violations
- **Typical**: 100-150
- **Critical**: Should be high enough to prevent hypoglycemia

### 8. Target Glucose (`target_glucose`)
**What it does**: Target glucose setpoint

- **Range**: 100-120 mg/dL (typical: 105-115)
- **Effect**: Similar to PID target
- **Typical**: 110 mg/dL

### 9. Glucose Bounds (`glucose_lower_bound`, `glucose_upper_bound`)
**What they do**: Hard/soft constraints on glucose levels

- **Lower bound**: 70 mg/dL (safety constraint)
- **Upper bound**: 180 mg/dL (soft constraint)
- **Purpose**: Ensure safe glucose ranges

### 10. Insulin Constraints
- `max_insulin_change`: Maximum rate change per step (0.01-0.03 U/min)
- `min_insulin_rate`: Minimum delivery (usually 0.0)
- `max_insulin_rate`: Maximum delivery (0.1-0.15 U/min)

## MPC Tuning Strategy

### Step 1: Set Horizons
Start with reasonable horizons:
```python
prediction_horizon = 30  # 30 minutes
control_horizon = 10     # 10 minutes
```

**Guidelines**:
- For meal responses: longer horizons help (30-40 min)
- For disturbance rejection: medium horizons (20-30 min)
- Control horizon = 30-50% of prediction horizon

### Step 2: Set Constraints
Define safety bounds:
```python
glucose_lower_bound = 70   # Hard constraint
glucose_upper_bound = 180  # Soft constraint
weight_violation = 150     # High penalty for violations
```

### Step 3: Tune Weight Balance
Start conservative and adjust:

```python
# Conservative starting point
weight_tracking = 1.0    # Track target
weight_control = 0.02    # Moderate insulin penalty
weight_rate = 0.05       # Smooth delivery
weight_terminal = 2.0    # Stable horizon end
weight_violation = 150   # Strong safety
```

**Tuning sequence**:
1. Increase `weight_tracking` if response too slow
2. Decrease `weight_control` if too conservative
3. Adjust `weight_rate` for smoothness vs reactivity
4. Tune `weight_violation` to ensure safety

### Step 4: Validate
Test across scenarios:
- Standard meals
- Large meals (high carb)
- Small meals (low carb)
- Meal timing variations

## Parameter Interactions

### Horizon Trade-offs
- **Long horizons + High tracking weight** = Anticipatory but aggressive
- **Short horizons + Low control weight** = Very reactive
- **Long control horizon** = More optimization flexibility but slower

### Weight Trade-offs
- **High tracking + Low control** = Aggressive insulin delivery
- **High tracking + High rate** = Aggressive but smooth
- **High violation + High tracking** = May conflict (balance needed)
- **High control + High rate** = Very conservative

### Optimal Combinations
1. **Aggressive control** (for tight TIR):
   ```python
   prediction_horizon = 35
   control_horizon = 12
   weight_tracking = 2.0
   weight_control = 0.01
   weight_rate = 0.03
   ```

2. **Balanced control** (good all-around):
   ```python
   prediction_horizon = 30
   control_horizon = 10
   weight_tracking = 1.5
   weight_control = 0.015
   weight_rate = 0.05
   ```

3. **Conservative control** (safety first):
   ```python
   prediction_horizon = 25
   control_horizon = 8
   weight_tracking = 1.0
   weight_control = 0.03
   weight_rate = 0.08
   ```

## Grid Search for MPC

### Coarse Grid
```python
# Horizons
prediction_horizon_range = [20, 30, 40]
control_horizon_range = [8, 10, 12]

# Weights
weight_tracking_range = [0.8, 1.2, 1.6, 2.0]
weight_control_range = [0.005, 0.01, 0.02, 0.03]
weight_rate_range = [0.03, 0.05, 0.08, 0.1]
weight_terminal_range = [1.5, 2.0, 3.0]

# Total: 3×3×4×4×4×3 = 1,728 combinations
```

### Fine Grid
After coarse search, refine around best parameters:
```python
# Example: best from coarse was [30, 10, 1.6, 0.01, 0.05, 2.0]

prediction_horizon_range = [28, 30, 32]
control_horizon_range = [9, 10, 11]
weight_tracking_range = np.linspace(1.4, 1.8, 5)
weight_control_range = np.linspace(0.008, 0.012, 5)
weight_rate_range = np.linspace(0.04, 0.06, 5)

# Total: 3×3×5×5×5 = 1,125 combinations
```

## Advanced MPC Features

### 1. Meal Announcement
MPC can use announced meals for feedforward control:
```python
# Announce meal 15 minutes before
controller.announce_meal(time_ahead=15.0, carbs=60)
```

**Benefits**:
- Preemptive insulin delivery
- Reduces post-meal hyperglycemia
- Improves time in range

**Optimization**: Tune announcement time (10-20 min typical)

### 2. Adaptive Weights
Dynamically adjust weights based on glucose level:
```python
if measured_glucose < 90:
    weight_violation *= 2  # More conservative when low
elif measured_glucose > 150:
    weight_tracking *= 1.5  # More aggressive when high
```

### 3. Model Mismatch Handling
If internal model differs from true physiology:
- Increase `weight_control` for robustness
- Shorter horizons may perform better
- Use state estimation (e.g., Kalman filter)

## Common Issues and Solutions

### Issue: Time Below Range too high
**Causes**: 
- `weight_violation` too low
- `weight_tracking` too high
- Horizons too short to anticipate insulin effect

**Solutions**:
- Increase `weight_violation` to 200+
- Reduce `weight_tracking` by 20-30%
- Increase prediction horizon to 35-40
- Increase `weight_control` to be more conservative

### Issue: Slow response to meals
**Causes**:
- `weight_control` too high
- `weight_rate` too high
- Control horizon too short

**Solutions**:
- Reduce `weight_control` by 30-50%
- Reduce `weight_rate` to allow faster changes
- Increase control horizon to 12-15

### Issue: Erratic insulin delivery
**Causes**:
- `weight_rate` too low
- Sensor noise too high
- Control horizon too long

**Solutions**:
- Increase `weight_rate` to 0.08-0.1
- Reduce sensor noise or add filtering
- Reduce control horizon

### Issue: Optimization fails frequently
**Causes**:
- Constraints too tight
- Horizons too long
- Initial guess poor

**Solutions**:
- Relax insulin rate change constraint
- Reduce horizons by 20%
- Improve initial guess (warm start)

### Issue: High computational cost
**Causes**:
- Long horizons
- Many constraints

**Solutions**:
- Reduce control horizon (biggest impact)
- Reduce prediction horizon
- Increase optimization tolerance
- Use faster solver

## Comparison: MPC vs PID Parameters

| Aspect | PID | MPC |
|--------|-----|-----|
| **Parameters** | 5 (Kp, Ki, Kd, target, deadband) | 7-10 (horizons + weights) |
| **Tuning complexity** | Moderate | Higher |
| **Computation** | Very fast | Moderate (optimization) |
| **Anticipation** | None (reactive) | Yes (predictive) |
| **Constraints** | Implicit | Explicit |
| **Meal handling** | Reactive only | Can announce |
| **Typical TIR** | 85-95% | 90-98% (when tuned) |

## Optimization Objective Functions

### Primary Objective: Maximize Time in Range
```python
def evaluate_mpc(mpc_params):
    results = mpc_sim.simulate(duration, dt, meals)
    metrics = calculate_time_in_range(results['true_glucose'])
    return metrics['time_in_range_pct']
```

### With Safety Constraint
```python
def evaluate_mpc_safe(mpc_params):
    results = mpc_sim.simulate(duration, dt, meals)
    metrics = calculate_time_in_range(results['true_glucose'])
    
    if metrics['time_below_range_pct'] > 4.0:
        return 0  # Penalty for unsafe
    
    return metrics['time_in_range_pct']
```

### Multi-Objective
```python
def evaluate_mpc_multi(mpc_params):
    results = mpc_sim.simulate(duration, dt, meals)
    metrics = calculate_time_in_range(results['true_glucose'])
    
    # Weighted combination
    score = (0.6 * metrics['time_in_range_pct'] +
             0.3 * (100 - metrics['time_below_range_pct']) +
             0.1 * (100 - metrics['cv_glucose']))
    
    return score
```

## Practical Workflow

1. **Start with default parameters** from conservative example
2. **Run single scenario** to verify it works
3. **Coarse grid search** over key parameters
4. **Select top 10** configurations
5. **Fine grid refinement** around best
6. **Multi-scenario validation** with various meals
7. **Robustness testing** with different sensor noise
8. **Final selection** based on average performance

## Computational Considerations

- Each MPC optimization takes ~0.1-0.5 seconds
- Full simulation (720 time steps) takes ~1-5 minutes
- Grid search of 1000 combinations: 15-80 hours
- Use parallel processing for multiple evaluations
- Consider Bayesian optimization for efficiency

## Expected Performance

With well-tuned parameters:
- **Time in Range**: 92-98%
- **Time Below Range**: 1-3%
- **Time Above Range**: 1-5%
- **CV**: 25-35%
- **Computational time**: 1-3 minutes per simulation

MPC typically outperforms PID by 5-10% in time in range, especially with:
- Meal announcements
- Large meal disturbances
- Variable meal timing
- Need for tight glucose control

## Summary

MPC requires more tuning effort than PID but offers:
✓ Better anticipation of future events
✓ Explicit constraint handling
✓ Multi-objective optimization
✓ Meal announcement capability
✓ Typically 5-10% better time in range

Key tuning priorities:
1. Set safe violation weights first (safety)
2. Balance tracking vs control weights (performance)
3. Tune horizons for your scenario (anticipation)
4. Adjust rate weights for smoothness (stability)
