# MPC Implementation Summary

A complete Model Predictive Control (MPC) implementation is provided as a separate module ([mpc_controller.py](mpc_controller.py)), providing an alternative to the PID controller.


### 1. mpc_controller.py 
Complete MPC implementation with:
- **MPCParams class**: Dataclass containing all MPC parameters for optimization
- **MPCController class**: Full MPC algorithm with:
  - Prediction model for glucose trajectory forecasting
  - Cost function with multiple objectives (tracking, control effort, rate, terminal, violations)
  - Constrained optimization using scipy.optimize
  - Meal announcement capability for feedforward control
  - Receding horizon control implementation
- **MPCSimulator class**: Integration with existing components (physiology, sensor, pump)
- **Demonstration functions**:
  - `compare_mpc_vs_pid()`: Side-by-side comparison of both controllers
  - `optimize_mpc_parameters_example()`: Example of MPC parameter optimization
- **Visualization**: Comparison plots showing glucose, insulin, and differences

### 2. mpc_tuning_guide.md (300+ lines)
Comprehensive guide for MPC parameter optimization:
- Detailed explanation of each parameter (7+ parameters vs 5 for PID)
- Parameter ranges and effects
- Tuning strategy (step-by-step)
- Parameter interactions and trade-offs
- Grid search recommendations (coarse and fine)
- Common issues and solutions
- Comparison with PID
- Multi-objective optimization strategies
- Computational considerations
- Expected performance metrics

### 3. Updated README.md
Added sections for:
- MPC controller overview
- Quick start for MPC
- Custom usage examples for MPC
- MPC optimization workflow
- Dependencies (scipy added)
- Updated project structure

## Key MPC Features

### 1. Predictive Capability
Unlike PID (reactive), MPC:
- Predicts glucose trajectory over horizon (e.g., 30 minutes ahead)
- Anticipates insulin effects before they occur
- Plans control moves considering future consequences

### 2. Explicit Constraint Handling
- Hard constraint: Glucose > 70 mg/dL (safety)
- Soft constraint: Glucose < 180 mg/dL (target range)
- Insulin rate bounds: 0 - 0.12 U/min
- Rate of change limits: Max 0.02 U/min per step

### 3. Multi-Objective Optimization
Balances five competing objectives:
1. **Tracking**: Minimize deviation from target glucose
2. **Control effort**: Minimize insulin usage
3. **Smoothness**: Minimize rate of insulin changes
4. **Terminal state**: Ensure good final state at horizon end
5. **Constraint violations**: Penalize safety violations

### 4. Meal Announcement
- Can announce meals 10-20 minutes before consumption
- Enables feedforward control (preemptive insulin delivery)
- Reduces post-meal glucose spikes
- Improves overall time in range

## MPC Parameters (7+ vs PID's 5)

### Horizon Parameters
1. `prediction_horizon` (20-40 min typical)
2. `control_horizon` (8-15 min typical)

### Weight Parameters (Key for Optimization)
3. `weight_tracking` (0.5-2.0) - How aggressively to track target
4. `weight_control` (0.001-0.1) - Penalty for insulin usage
5. `weight_rate` (0.01-0.2) - Penalty for rate changes
6. `weight_terminal` (1.0-5.0) - Importance of final state
7. `weight_violation` (50-200) - Penalty for constraint violations

### Target and Constraints
8. `target_glucose` (100-120 mg/dL)
9. `glucose_lower_bound` (70 mg/dL)
10. `glucose_upper_bound` (180 mg/dL)

## Optimization Approach

### Grid Search Structure
Similar to PID but with more parameters:

```python
# Coarse grid example
prediction_horizon_range = [20, 30, 40]
control_horizon_range = [8, 10, 12]
weight_tracking_range = [0.8, 1.2, 1.6, 2.0]
weight_control_range = [0.005, 0.01, 0.02, 0.03]
weight_rate_range = [0.03, 0.05, 0.08, 0.1]

# Total: 3×3×4×4×4 = 576 combinations
```

### Optimization Priority
1. **Safety first**: Tune `weight_violation` high (100-200)
2. **Set horizons**: Start with 30/10, adjust based on performance
3. **Balance weights**: Tune tracking vs control vs rate
4. **Fine-tune**: Refine around best coarse parameters
5. **Validate**: Test across multiple meal scenarios

## Performance Comparison

### Initial Demo Results (with example parameters)
- **PID**: 96.5% TIR, 3.5% below range
- **MPC** (initial): 78.8% TIR, 21.2% below range

The initial MPC parameters were too aggressive. This demonstrates the importance of tuning!

### After Parameter Tuning (Config 3 in example)
- **MPC** (tuned): 100% TIR, 0% below range

This shows MPC's potential when properly configured.

### Expected Performance (Well-Tuned)
With optimal parameters:
- **PID**: 85-95% TIR typical
- **MPC**: 90-98% TIR typical (5-10% improvement)
- **MPC advantages are largest for**:
  - Large meals (high carb loads)
  - Variable meal timing
  - When meal announcements are available
  - When tight glucose control is needed

## Computational Considerations

### Speed
- **PID**: <0.001 seconds per time step (instant)
- **MPC**: 0.1-0.5 seconds per time step (optimization overhead)
- Full simulation (720 steps): PID ~2 sec, MPC ~1-5 min

### Optimization Search
- Grid search of 576 combinations: 10-50 hours (MPC) vs 15 min (PID)
- Recommendation: Use parallel processing or Bayesian optimization for MPC
- Consider starting with coarse PID tuning, then switch to MPC for refinement


## Some examples of use

```python
# Same physiological model, sensor, and pump for both controllers
phys_params = PhysiologicalParams()
sensor_params = SensorParams()
pump_params = PumpParams()

# Option 1: PID Controller
# Use T1DSimulator with PID controller parameters
pid_params = ControllerParams(Kp=0.0005, Ki=0.00001, Kd=0.0001)
pid_sim = T1DSimulator(phys_params, sensor_params, pump_params, pid_params)

# Option 2: MPC Controller
# Use MPCSimulator with MPC controller parameters
mpc_params = MPCParams(prediction_horizon=30, control_horizon=10, weight_tracking=1.5)
mpc_sim = MPCSimulator(phys_params, sensor_params, pump_params, mpc_params)

# Both simulators share the same interface for running simulations
results_pid = pid_sim.simulate(duration, dt, meals)
results_mpc = mpc_sim.simulate(duration, dt, meals)


# Comparing PID with MPC Controller
from mpc_controller import compare_mpc_vs_pid

# Run the comparison
pid_results, mpc_results, pid_metrics, mpc_metrics = compare_mpc_vs_pid()

# The function returns four values:
# - pid_results: dictionary with 'time', 'true_glucose', 'measured_glucose', 'insulin_rate'

# - mpc_results: same structure for MPC

# - pid_metrics: dictionary with time_in_range_pct, mean_glucose, etc.

# - mpc_metrics: same metrics for MPC

# Note that "measured glucose" is a "presumed" measurement, which we get out to the _simulation_ , which is
# of course might be quite confusing. But the idea is that in a
# real patient, this would be replaced with the reach signal from
# the CGM sensor. We will talk about the limitations of this 
# during one of our meetings.

```

## When to Use MPC vs PID

### Use PID when:
- ✓ Fast computation is critical
- ✓ Simple implementation is preferred
- ✓ Easy tuning is important
- ✓ Good enough performance (85-95% TIR)
- ✓ No meal announcements available
- ✓ Limited computational resources

### Use MPC when:
- ✓ Maximum performance is needed (>95% TIR)
- ✓ Meal announcements are available
- ✓ Complex constraints must be satisfied
- ✓ Willing to invest in parameter tuning
- ✓ Computational resources are sufficient
- ✓ Predictive capability is valuable
- ✓ Multi-objective optimization is needed

## Advanced MPC Features (Future Extensions)

The current implementation provides a foundation for:

1. **Adaptive MPC**: Adjust weights based on glucose level or time of day
2. **Robust MPC**: Account for model uncertainty and disturbances
3. **Stochastic MPC**: Incorporate probabilistic constraints
4. **Learning-based MPC**: Use machine learning to improve internal model
5. **Multi-step meal announcement**: Handle multiple future meals
6. **Exercise integration**: Adjust predictions for physical activity
7. **State estimation**: Kalman filter for better state tracking


## How to Get Started with MPC

1. **Run the demo**: `python mpc_controller.py`
2. **Review the comparison**: See PID vs MPC performance
3. **Read the tuning guide**: [mpc_tuning_guide.md](mpc_tuning_guide.md)
4. **Try different parameters**: Use the optimization example as template
5. **Start conservative**: High violation weight, moderate tracking
6. **Iterate**: Gradually tune weights for better performance
7. **Validate**: Test across multiple meal scenarios

## Summary

The MPC implementation provides a more sophisticated alternative to PID control; the perception that we find from discussing this with different people is that patient preference and medical advice is always key; blanket statements are hard to make about which is better for a given individual. 

What we can do is a "textbook" comparison between the two, but all of this has to have the caveat that these are _theoretical_ considerations, and theoretical "betterness" might not hold in practice either for an individual patient, or for a particular subgroup:

| Aspect | PID | MPC |
|--------|-----|-----|
| **Complexity** | Low | High |
| **Parameters** | 5 | 7-10 |
| **Computation** | Instant | Moderate |
| **Tuning effort** | Moderate | High |
| **Performance** | Good (85-95% TIR) | Excellent (90-98% TIR) |
| **Predictive** | No | Yes |
| **Constraints** | Implicit | Explicit |
| **Meal handling** | Reactive | Feedforward capable |

