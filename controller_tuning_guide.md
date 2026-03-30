# Controller Parameter Tuning Guide

## Controller Parameters Overview

The closed-loop controller uses a PID-like algorithm with five tunable parameters:

### 1. **Kp** (Proportional Gain)
- **Range**: 0.0001 - 0.001 (typical)
- **Effect**: Controls response to current glucose error
- **Too High**: Aggressive corrections, potential oscillations, hypoglycemia
- **Too Low**: Slow response, prolonged hyperglycemia
- **Typical**: 0.0003 - 0.0007

### 2. **Ki** (Integral Gain)
- **Range**: 0.000005 - 0.00002 (typical)
- **Effect**: Eliminates steady-state error over time
- **Too High**: Overshooting, insulin stacking, delayed hypoglycemia
- **Too Low**: Persistent offset from target
- **Typical**: 0.000008 - 0.000015

### 3. **Kd** (Derivative Gain)
- **Range**: 0.00005 - 0.0002 (typical)
- **Effect**: Dampens rapid glucose changes (anticipatory action)
- **Too High**: Excessive sensitivity to noise, erratic behavior
- **Too Low**: Poor anticipation of trends
- **Typical**: 0.00008 - 0.00015

### 4. **target_glucose** (Target Glucose)
- **Range**: 100 - 120 mg/dL (typical)
- **Effect**: Setpoint for controller
- **Lower**: More aggressive control, higher risk of hypoglycemia
- **Higher**: More conservative, higher average glucose
- **Typical**: 105 - 115 mg/dL

### 5. **deadband** (Deadband)
- **Range**: 10 - 20 mg/dL (typical)
- **Effect**: No correction within target ± deadband
- **Lower**: More frequent corrections, tighter control
- **Higher**: Less frequent corrections, allows more variation
- **Typical**: 10 - 15 mg/dL

## Tuning Strategy
This describes how things are done in the way of the "manual human engineer", which 
is basically early stage, software enabled design iteration. Same principles might be
applied to other control problems (unless one has a linear system description, $s$-domain, say, 
for the patients, which is usually not the case).

### Step 1: Start with Conservative Values
```python
Kp = 0.0003
Ki = 0.00001
Kd = 0.0001
target_glucose = 110
deadband = 15
```

### Step 2: Tune Proportional Gain (Kp)
- Fix Ki and Kd
- Increase Kp until you see good response to meals
- Watch for hypoglycemia 2-3 hours post-meal
- If oscillations appear, reduce Kp

### Step 3: Tune Integral Gain (Ki)
- Fix Kp from Step 2
- Increase Ki to eliminate steady-state offset
- Watch for insulin stacking (cumulative effect)
- If delayed hypoglycemia occurs, reduce Ki

### Step 4: Tune Derivative Gain (Kd)
- Adjust Kd to smooth glucose response
- Higher Kd dampens rapid rises from meals
- Too high causes noise sensitivity

### Step 5: Fine-tune Target and Deadband
- Adjust target based on desired average glucose
- Adjust deadband for desired control tightness

## Parameter Interactions

### Kp vs Ki
- Higher Kp → Can use lower Ki
- Lower Kp → May need higher Ki for same performance
- Balance between immediate and long-term correction

### Kp vs Kd
- Kd dampens aggressive Kp
- High Kp + High Kd can work, but sensitive to noise
- Low Kp + Low Kd may be too sluggish

### Target vs Deadband
- Lower target + wider deadband = similar to higher target + tighter deadband
- Tight deadband needs careful Kp tuning to avoid oscillations

## Common Issues and Solutions

### Issue: Hypoglycemia 2-3 hours after meals
**Cause**: Kp too high, insulin stacking
**Solution**: Reduce Kp by 20-30%, or increase deadband

### Issue: Persistent high glucose after meals
**Cause**: Kp too low, or target too high
**Solution**: Increase Kp by 20%, or lower target

### Issue: Glucose oscillations
**Cause**: Kp too high, Ki too high, or deadband too small
**Solution**: Reduce Kp and Ki, or increase deadband

### Issue: Slow return to baseline
**Cause**: Ki too low
**Solution**: Increase Ki by 20-30%

### Issue: Erratic insulin delivery
**Cause**: Kd too high, sensor noise
**Solution**: Reduce Kd, increase sensor filtering

## Optimization Objectives (examples)

### Maximize Time in Range (70-180 mg/dL)
- Primary objective
- Target: > 70%
- Balance avoiding hypo and hyper

### Minimize Time Below Range (< 70 mg/dL)
- Safety constraint
- Target: < 4%
- Consider as hard constraint in optimization

### Minimize Coefficient of Variation (CV)
- Glucose variability
- Target: < 36%
- Indicates stable control

### Optimize Mean Glucose
- Target: 100-120 mg/dL
- Too low increases hypo risk
- Too high increases complications

## Grid Search Recommendations

### Coarse Grid (Initial Search)
```python
Kp_range = [0.0002, 0.0004, 0.0006, 0.0008]
Ki_range = [0.000005, 0.00001, 0.000015, 0.00002]
Kd_range = [0.00005, 0.0001, 0.00015, 0.0002]
target_range = [105, 110, 115]
deadband_range = [10, 15, 20]
```
Total: 4 × 4 × 4 × 3 × 3 = 576 combinations

### Fine Grid (Refinement)
After finding best coarse parameters, search ±20% around them:
```python
best_Kp = 0.0005  # Example from coarse search

Kp_range = np.linspace(best_Kp * 0.8, best_Kp * 1.2, 10)
Ki_range = np.linspace(best_Ki * 0.8, best_Ki * 1.2, 10)
Kd_range = np.linspace(best_Kd * 0.8, best_Kd * 1.2, 10)
```

## Multi-Scenario Validation

Always test optimized parameters across multiple scenarios:

1. **Standard meals**: Normal meal sizes and timing
2. **High-carb meals**: Test aggressive situations
3. **Low-carb meals**: Test conservative situations
4. **Irregular timing**: Test robustness to timing changes
5. **Missed meals**: Test basal-only periods
6. **Double meals**: Test cumulative insulin effects

Calculate average TIR across scenarios:
```python
avg_TIR = (TIR_standard + TIR_high_carb + TIR_low_carb + ...) / n_scenarios
```

## More Advanced Considerations

### Constraint-Based Optimization
Instead of just maximizing TIR:
- Maximize TIR subject to: Time_below < 4%
- Use penalty functions for constraint violations

### Combining Objectives
```python
score = w1 * TIR + w2 * (1 - Time_below) + w3 * (1 - CV/100)
```
Where w1, w2, w3 are weights (e.g., 0.5, 0.3, 0.2)

### Optimization across patients, sensor noise and stochastic behaviour
- Add sensor noise variations
- Test with different patient parameters (p1, p2, p3)
- Multiple random seeds for stochastic robustness

### Pareto Optimization
Find Pareto-optimal solutions:
- TIR vs Time_below tradeoff
- TIR vs CV tradeoff
- Multiple objectives simultaneously

## Example Workflow

```python
# 1. Coarse grid search
coarse_results = []
for params in coarse_grid:
    metrics = evaluate_controller_params(params)
    coarse_results.append(metrics)

# 2. Find top 10 configurations
top_10 = sorted(coarse_results, key=lambda x: x['time_in_range_pct'])[-10:]

# 3. Fine search around best
best = top_10[0]
fine_results = []
for params in fine_grid_around(best):
    metrics = evaluate_controller_params(params)
    fine_results.append(metrics)

# 4. Multi-scenario validation
best_refined = max(fine_results, key=lambda x: x['time_in_range_pct'])
avg_tir = validate_across_scenarios(best_refined)

# 5. Select final if avg_tir > threshold
if avg_tir > 70:
    final_params = best_refined
    print("Optimization successful!")
```

## References

- Target TIR > 70%: International Consensus on CGM metrics
- Target CV < 36%: Indicates stable glucose control
- Target Time Below < 4%: Safety guideline
- PID tuning: Ziegler-Nichols method (adapted for glucose control)
