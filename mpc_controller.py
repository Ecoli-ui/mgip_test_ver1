"""
Model Predictive Control (MPC) for T1D Glucose Regulation
==========================================================

This module implements a Model Predictive Control algorithm for closed-loop
glucose regulation. MPC uses a predictive model to optimize insulin delivery
over a future horizon, providing superior performance compared to PID control.

Key advantages of MPC:
- Anticipates future glucose trends
- Handles constraints explicitly (glucose bounds, insulin limits)
- Can incorporate meal announcements
- Optimizes over multiple time steps
"""

import numpy as np
from scipy.optimize import minimize
from dataclasses import dataclass
from typing import Optional, Tuple
import matplotlib.pyplot as plt
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from glucose_simulator import (
    PhysiologicalModel, PhysiologicalParams,
    GlucoseSensor, SensorParams,
    InsulinPump, PumpParams,
    calculate_time_in_range
)


# ============================================================================
# MPC CONTROLLER
# ============================================================================

@dataclass
class MPCParams:
    """
    MPC Controller Parameters - THESE ARE THE PARAMETERS TO OPTIMIZE.
    
    Key parameters for tuning:
    - Prediction horizon: How far ahead to predict
    - Control horizon: How many control moves to optimize
    - Weight parameters: Balance between objectives
    
    Note on glucose units:
    - All glucose values in this simulator are in mg/dL (USA standard)
    - To convert to mmol/L (international): divide by 18
    - Example: target_glucose=110 mg/dL = 6.1 mmol/L
    - Typical ranges: 70-180 mg/dL (3.9-10.0 mmol/L) or 80-140 mg/dL (4.4-7.8 mmol/L)
    """
    # Horizons
    prediction_horizon: int = 30  # Time steps to predict ahead (e.g., 30 min)
    control_horizon: int = 10  # Time steps to optimize control (e.g., 10 min)
    
    # Target and bounds
    target_glucose: float = 110.0  # Target glucose (mg/dL)
    glucose_lower_bound: float = 70.0  # Hard lower constraint
    glucose_upper_bound: float = 180.0  # Soft upper constraint
    
    # Cost function weights (OPTIMIZATION PARAMETERS)
    weight_tracking: float = 1.0  # Weight for tracking error
    weight_control: float = 0.01  # Weight for insulin usage (control effort)
    weight_rate: float = 0.05  # Weight for rate of insulin change (smoothness)
    weight_terminal: float = 2.0  # Weight for terminal state
    weight_violation: float = 100.0  # Penalty for constraint violations
    
    # Insulin constraints
    min_insulin_rate: float = 0.0  # Minimum insulin rate (U/min)
    max_insulin_rate: float = 0.12  # Maximum insulin rate (U/min)
    max_insulin_change: float = 0.02  # Max change per step (U/min)
    
    # Model parameters (for internal prediction model)
    dt: float = 1.0  # Time step (minutes)


class MPCController:
    """Model Predictive Control for glucose regulation."""
    
    def __init__(self, 
                 params: MPCParams,
                 model_params: PhysiologicalParams,
                 basal_rate: float):
        """
        Initialize MPC controller.
        
        Args:
            params: MPC parameters
            model_params: Physiological model parameters for prediction
            basal_rate: Basal insulin rate (U/min)
        """
        self.params = params
        self.model_params = model_params
        self.basal_rate = basal_rate
        
        # Internal prediction model (copy of physiological model)
        self.prediction_model = PhysiologicalModel(model_params)
        
        # State tracking
        self.previous_insulin_rate = basal_rate
        self.announced_meals = []  # List of (time_ahead, carbs) tuples
        
        self.reset()
    
    def reset(self):
        """Reset controller state."""
        self.prediction_model.reset()
        self.previous_insulin_rate = self.basal_rate
        self.announced_meals = []
    
    def update_state(self, measured_glucose: float, measured_insulin: float = None):
        """
        Update internal model state based on measurements.
        
        Args:
            measured_glucose: Current measured glucose (mg/dL)
            measured_insulin: Current measured insulin (optional, mU/L)
        """
        # State estimation: update internal model to match current measurement
        # Simple approach: directly set glucose state
        self.prediction_model.G = measured_glucose
        
        # Could implement more sophisticated state estimation (e.g., Kalman filter)
        # For now, we'll rely on the model's natural dynamics
    
    def announce_meal(self, time_ahead: float, carbs: float):
        """
        Announce upcoming meal for feedforward control.
        
        Args:
            time_ahead: Time until meal (minutes)
            carbs: Meal size (grams)
        """
        self.announced_meals.append((time_ahead, carbs))
    
    def _predict_trajectory(self, 
                           initial_state: Tuple[float, float, float, float],
                           insulin_sequence: np.ndarray) -> np.ndarray:
        """
        Predict glucose trajectory given insulin sequence.
        
        Args:
            initial_state: (G, X, I, meal_remaining)
            insulin_sequence: Array of insulin rates (U/min) for prediction horizon
        
        Returns:
            Array of predicted glucose values
        """
        # Create temporary model for prediction
        temp_model = PhysiologicalModel(self.model_params)
        temp_model.G, temp_model.X, temp_model.I, temp_model.meal_remaining = initial_state
        
        glucose_predictions = np.zeros(self.params.prediction_horizon + 1)
        glucose_predictions[0] = temp_model.G
        
        for i in range(self.params.prediction_horizon):
            # Check for announced meals
            meal_input = 0.0
            for j, (time_ahead, carbs) in enumerate(self.announced_meals):
                if abs(time_ahead - i * self.params.dt) < 0.5 * self.params.dt:
                    # Convert to mg/dL equivalent using body weight scaling
                    total_volume = self.model_params.Vg * self.model_params.body_weight
                    meal_input = carbs * 1000 * self.model_params.meal_bioavailability / total_volume
                    # Remove consumed meal
                    self.announced_meals.pop(j)
                    break
            
            # Step model forward
            insulin_rate = insulin_sequence[i] if i < len(insulin_sequence) else self.basal_rate
            glucose_predictions[i + 1] = temp_model.step(
                self.params.dt, insulin_rate, meal_input
            )
        
        return glucose_predictions
    
    def _cost_function(self, insulin_sequence: np.ndarray, 
                       initial_state: Tuple[float, float, float, float]) -> float:
        """
        MPC cost function to minimize.
        
        Components:
        1. Tracking error: deviation from target glucose
        2. Control effort: total insulin used
        3. Rate of change: smoothness of insulin delivery
        4. Terminal cost: final state deviation
        5. Constraint violations: penalties for bounds
        
        Args:
            insulin_sequence: Proposed insulin rates for control horizon
            initial_state: Current physiological state
        
        Returns:
            Total cost
        """
        params = self.params
        
        # Extend insulin sequence to full prediction horizon (constant after control horizon)
        full_sequence = np.zeros(params.prediction_horizon)
        full_sequence[:len(insulin_sequence)] = insulin_sequence
        full_sequence[len(insulin_sequence):] = insulin_sequence[-1]
        
        # Predict glucose trajectory
        glucose_pred = self._predict_trajectory(initial_state, full_sequence)
        
        # 1. Tracking error cost
        tracking_errors = glucose_pred[1:] - params.target_glucose
        tracking_cost = params.weight_tracking * np.sum(tracking_errors ** 2)
        
        # 2. Control effort cost (minimize insulin usage)
        control_cost = params.weight_control * np.sum((full_sequence - self.basal_rate) ** 2)
        
        # 3. Rate of change cost (smoothness)
        insulin_changes = np.diff(np.concatenate(([self.previous_insulin_rate], full_sequence)))
        rate_cost = params.weight_rate * np.sum(insulin_changes ** 2)
        
        # 4. Terminal cost (emphasize final state)
        terminal_error = glucose_pred[-1] - params.target_glucose
        terminal_cost = params.weight_terminal * (terminal_error ** 2)
        
        # 5. Constraint violation penalties
        violation_cost = 0.0
        
        # Penalize hypoglycemia heavily
        hypo_violations = np.maximum(0, params.glucose_lower_bound - glucose_pred[1:])
        violation_cost += params.weight_violation * np.sum(hypo_violations ** 2)
        
        # Soft penalty for hyperglycemia
        hyper_violations = np.maximum(0, glucose_pred[1:] - params.glucose_upper_bound)
        violation_cost += params.weight_violation * 0.1 * np.sum(hyper_violations ** 2)
        
        total_cost = (tracking_cost + control_cost + rate_cost + 
                     terminal_cost + violation_cost)
        
        return total_cost
    
    def compute_insulin_rate(self, measured_glucose: float) -> float:
        """
        Compute optimal insulin delivery rate using MPC.
        
        Args:
            measured_glucose: Current measured glucose (mg/dL)
        
        Returns:
            Optimal insulin delivery rate (U/min)
        """
        params = self.params
        
        # Update internal model state
        self.update_state(measured_glucose)
        
        # Get current state
        current_state = (
            self.prediction_model.G,
            self.prediction_model.X,
            self.prediction_model.I,
            self.prediction_model.meal_remaining
        )
        
        # Initial guess: maintain previous rate
        initial_guess = np.ones(params.control_horizon) * self.previous_insulin_rate
        
        # Bounds for insulin rates
        bounds = [(params.min_insulin_rate, params.max_insulin_rate) 
                 for _ in range(params.control_horizon)]
        
        # Constraints for rate of change
        constraints = []
        for i in range(params.control_horizon):
            if i == 0:
                # First control move: constrain change from previous rate
                def rate_constraint_first(u, idx=i):
                    return params.max_insulin_change - abs(u[idx] - self.previous_insulin_rate)
                constraints.append({'type': 'ineq', 'fun': rate_constraint_first})
            else:
                # Subsequent moves: constrain change between consecutive controls
                def rate_constraint(u, idx=i):
                    return params.max_insulin_change - abs(u[idx] - u[idx-1])
                constraints.append({'type': 'ineq', 'fun': rate_constraint})
        
        # Optimize
        result = minimize(
            fun=self._cost_function,
            x0=initial_guess,
            args=(current_state,),
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 100, 'ftol': 1e-6}
        )
        
        if not result.success:
            # If optimization fails, use safe fallback
            optimal_rate = self.basal_rate
        else:
            # Use first control move (receding horizon principle)
            optimal_rate = result.x[0]
        
        # Update previous rate
        self.previous_insulin_rate = optimal_rate
        
        return optimal_rate


# ============================================================================
# MPC SIMULATOR
# ============================================================================

class MPCSimulator:
    """Simulator with MPC controller."""
    
    def __init__(self,
                 phys_params: PhysiologicalParams,
                 sensor_params: SensorParams,
                 pump_params: PumpParams,
                 mpc_params: MPCParams):
        """
        Initialize MPC simulator.
        
        Args:
            phys_params: Physiological model parameters
            sensor_params: Sensor parameters
            pump_params: Pump parameters
            mpc_params: MPC controller parameters
        """
        self.physiology = PhysiologicalModel(phys_params)
        self.sensor = GlucoseSensor(sensor_params)
        self.pump = InsulinPump(pump_params)
        self.controller = MPCController(mpc_params, phys_params, pump_params.basal_rate)
    
    def reset(self):
        """Reset all components."""
        self.physiology.reset()
        self.sensor.reset()
        self.controller.reset()
    
    def simulate(self,
                 duration: float,
                 dt: float,
                 meals: list = None,
                 meal_announcement_time: float = 15.0) -> dict:
        """
        Run MPC simulation.
        
        Args:
            duration: Simulation duration (minutes)
            dt: Time step (minutes)
            meals: List of (time, carbs) tuples
            meal_announcement_time: How many minutes before meal to announce (for MPC)
        
        Returns:
            Dictionary with simulation results
        """
        if meals is None:
            meals = []
        
        # Prepare meal schedule
        meal_schedule = {int(time / dt): carbs for time, carbs in meals}
        
        # Storage
        n_steps = int(duration / dt)
        times = np.arange(0, duration, dt)
        true_glucose = np.zeros(n_steps)
        measured_glucose = np.zeros(n_steps)
        insulin_rates = np.zeros(n_steps)
        
        # Reset
        self.reset()
        
        # Simulation loop
        for i in range(n_steps):
            current_time = i * dt
            
            # Check for meal announcement (before actual meal)
            for meal_time, meal_carbs in meals:
                if abs(current_time - (meal_time - meal_announcement_time)) < 0.5 * dt:
                    # Announce meal to MPC
                    self.controller.announce_meal(meal_announcement_time, meal_carbs)
            
            # Check for actual meal
            carbs = meal_schedule.get(i, 0.0)
            # Convert to mg/dL equivalent using body weight scaling
            total_volume = self.physiology.params.Vg * self.physiology.params.body_weight
            meal_input = carbs * 1000 * self.physiology.params.meal_bioavailability / total_volume if carbs > 0 else 0.0
            
            # Sensor measurement
            measured_glucose[i] = self.sensor.measure(self.physiology.G)
            
            # MPC computes insulin rate
            insulin_request = self.controller.compute_insulin_rate(measured_glucose[i])
            
            # Pump delivers
            insulin_rates[i] = self.pump.deliver(insulin_request)
            
            # Physiology steps forward
            true_glucose[i] = self.physiology.step(dt, insulin_rates[i], meal_input)
        
        return {
            'time': times,
            'true_glucose': true_glucose,
            'measured_glucose': measured_glucose,
            'insulin_rate': insulin_rates
        }


# ============================================================================
# DEMONSTRATION
# ============================================================================

def compare_mpc_vs_pid():
    """Compare MPC controller against PID controller."""
    from glucose_simulator import T1DSimulator, ControllerParams
    
    np.random.seed(42)
    
    # Standard parameters
    phys_params = PhysiologicalParams()
    sensor_params = SensorParams(noise_std=3.0, delay=2)
    pump_params = PumpParams(basal_rate=0.02)
    
    # Meal scenario
    meals = [
        (60, 50),   # Breakfast
        (240, 60),  # Lunch
        (480, 55),  # Dinner
    ]
    
    duration = 12 * 60
    dt = 1.0
    
    # --- PID Controller ---
    pid_params = ControllerParams(
        Kp=0.0005,
        Ki=0.00001,
        Kd=0.0001,
        target_glucose=110.0,
        deadband=15.0
    )
    
    print("Running PID simulation...")
    pid_sim = T1DSimulator(phys_params, sensor_params, pump_params, pid_params)
    pid_results = pid_sim.simulate(duration, dt, meals)
    pid_metrics = calculate_time_in_range(pid_results['true_glucose'])
    
    # --- MPC Controller ---
    mpc_params = MPCParams(
        prediction_horizon=30,
        control_horizon=10,
        target_glucose=110.0,
        weight_tracking=1.0,
        weight_control=0.01,
        weight_rate=0.05,
        weight_terminal=2.0,
        weight_violation=100.0
    )
    
    print("Running MPC simulation...")
    mpc_sim = MPCSimulator(phys_params, sensor_params, pump_params, mpc_params)
    mpc_results = mpc_sim.simulate(duration, dt, meals, meal_announcement_time=15.0)
    mpc_metrics = calculate_time_in_range(mpc_results['true_glucose'])
    
    # --- Print Comparison ---
    print("\n" + "="*70)
    print("PERFORMANCE COMPARISON: PID vs MPC")
    print("="*70)
    print(f"{'Metric':<30} {'PID':>15} {'MPC':>15} {'Improvement':>10}")
    print("-"*70)
    
    metrics_to_compare = [
        ('Time in Range (%)', 'time_in_range_pct'),
        ('Time Below Range (%)', 'time_below_range_pct'),
        ('Time Above Range (%)', 'time_above_range_pct'),
        ('Mean Glucose (mg/dL)', 'mean_glucose'),
        ('Glucose CV (%)', 'cv_glucose'),
        ('Min Glucose (mg/dL)', 'min_glucose'),
        ('Max Glucose (mg/dL)', 'max_glucose'),
    ]
    
    for label, key in metrics_to_compare:
        pid_val = pid_metrics[key]
        mpc_val = mpc_metrics[key]
        
        if key == 'time_in_range_pct':
            improvement = f"+{mpc_val - pid_val:+.1f}%"
        elif key in ['time_below_range_pct', 'time_above_range_pct', 'cv_glucose']:
            improvement = f"{mpc_val - pid_val:+.1f}%"
        else:
            improvement = f"{mpc_val - pid_val:+.1f}"
        
        print(f"{label:<30} {pid_val:>15.1f} {mpc_val:>15.1f} {improvement:>10}")
    
    print("="*70)
    
    # --- Plot Comparison ---
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    
    # Glucose comparison
    axes[0].plot(pid_results['time'] / 60, pid_results['true_glucose'],
                label='PID Controller', linewidth=2, alpha=0.8, color='blue')
    axes[0].plot(mpc_results['time'] / 60, mpc_results['true_glucose'],
                label='MPC Controller', linewidth=2, alpha=0.8, color='red')
    axes[0].axhline(70, color='gray', linestyle='--', alpha=0.5)
    axes[0].axhline(180, color='gray', linestyle='--', alpha=0.5)
    axes[0].fill_between([0, duration/60], 70, 180, color='green', alpha=0.1)
    
    # Mark meals
    for meal_time, meal_carbs in meals:
        axes[0].axvline(meal_time / 60, color='orange', linestyle=':', alpha=0.7)
        axes[0].text(meal_time / 60, axes[0].get_ylim()[1] * 0.95,
                    f'{meal_carbs}g', ha='center', fontsize=8)
    
    axes[0].set_ylabel('Glucose (mg/dL)', fontsize=12)
    axes[0].set_title('PID vs MPC Controller Comparison', fontsize=14, fontweight='bold')
    axes[0].legend(loc='upper right')
    axes[0].grid(True, alpha=0.3)
    
    # Insulin comparison
    axes[1].plot(pid_results['time'] / 60, pid_results['insulin_rate'] * 60,
                label='PID Insulin', linewidth=2, alpha=0.8, color='blue')
    axes[1].plot(mpc_results['time'] / 60, mpc_results['insulin_rate'] * 60,
                label='MPC Insulin', linewidth=2, alpha=0.8, color='red')
    axes[1].axhline(pump_params.basal_rate * 60, color='gray',
                   linestyle='--', alpha=0.5, label='Basal Rate')
    axes[1].set_ylabel('Insulin Rate (U/hr)', fontsize=12)
    axes[1].legend(loc='upper right')
    axes[1].grid(True, alpha=0.3)
    
    # Glucose difference
    glucose_diff = mpc_results['true_glucose'] - pid_results['true_glucose']
    axes[2].plot(pid_results['time'] / 60, glucose_diff,
                linewidth=2, color='purple', label='MPC - PID')
    axes[2].axhline(0, color='gray', linestyle='-', alpha=0.5)
    axes[2].fill_between(pid_results['time'] / 60, 0, glucose_diff,
                        where=(glucose_diff >= 0), alpha=0.3, color='green',
                        label='MPC Higher')
    axes[2].fill_between(pid_results['time'] / 60, 0, glucose_diff,
                        where=(glucose_diff < 0), alpha=0.3, color='red',
                        label='MPC Lower')
    axes[2].set_xlabel('Time (hours)', fontsize=12)
    axes[2].set_ylabel('Glucose Difference (mg/dL)', fontsize=12)
    axes[2].legend(loc='upper right')
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = Path(__file__).resolve().parent / 'mpc_comparison.png'
    plt.savefig(output_path, dpi=150)
    print(f"\nComparison plot saved to: {output_path}")
    plt.show()
    
    return pid_results, mpc_results, pid_metrics, mpc_metrics


def optimize_mpc_parameters_example():
    """Example of how to optimize MPC parameters."""
    from parameter_optimization_example import evaluate_controller_params
    
    print("\n" + "="*70)
    print("MPC PARAMETER OPTIMIZATION EXAMPLE")
    print("="*70)
    print("\nMPC parameters to optimize:")
    print("  - prediction_horizon: How far ahead to predict (10-60 min)")
    print("  - control_horizon: How many control moves (5-20 min)")
    print("  - weight_tracking: Importance of tracking target (0.5-2.0)")
    print("  - weight_control: Penalty for insulin usage (0.001-0.1)")
    print("  - weight_rate: Penalty for rate changes (0.01-0.2)")
    print("  - weight_terminal: Importance of final state (1.0-5.0)")
    print("  - weight_violation: Penalty for constraints (50-200)")
    
    print("\nExample: Testing 3 MPC configurations...\n")
    
    # Standard setup
    phys_params = PhysiologicalParams()
    sensor_params = SensorParams(noise_std=3.0, delay=2)
    pump_params = PumpParams(basal_rate=0.02)
    meals = [(60, 50), (240, 60), (480, 55)]
    
    test_configs = [
        {'pred_h': 20, 'ctrl_h': 8, 'w_track': 1.0, 'w_ctrl': 0.01, 'w_rate': 0.05},
        {'pred_h': 30, 'ctrl_h': 10, 'w_track': 1.5, 'w_ctrl': 0.02, 'w_rate': 0.08},
        {'pred_h': 40, 'ctrl_h': 12, 'w_track': 2.0, 'w_ctrl': 0.005, 'w_rate': 0.03},
    ]
    
    results = []
    for i, config in enumerate(test_configs, 1):
        print(f"Config {i}: pred_h={config['pred_h']}, ctrl_h={config['ctrl_h']}, "
              f"w_track={config['w_track']}, w_ctrl={config['w_ctrl']}")
        
        mpc_params = MPCParams(
            prediction_horizon=config['pred_h'],
            control_horizon=config['ctrl_h'],
            weight_tracking=config['w_track'],
            weight_control=config['w_ctrl'],
            weight_rate=config['w_rate']
        )
        
        mpc_sim = MPCSimulator(phys_params, sensor_params, pump_params, mpc_params)
        sim_results = mpc_sim.simulate(duration=720, dt=1.0, meals=meals)
        metrics = calculate_time_in_range(sim_results['true_glucose'])
        
        print(f"  → TIR: {metrics['time_in_range_pct']:.1f}%, "
              f"Mean: {metrics['mean_glucose']:.1f} mg/dL\n")
        
        results.append({**config, **metrics})
    
    print("="*70)
    print("\nMPC parameters can be optimized similarly to PID parameters")
    print("using grid search or advanced methods like Bayesian optimization.")
    print("="*70)
    
    return results


if __name__ == "__main__":
    # Run comparison
    print("="*70)
    print("MODEL PREDICTIVE CONTROL (MPC) DEMONSTRATION")
    print("="*70)
    
    pid_res, mpc_res, pid_met, mpc_met = compare_mpc_vs_pid()
    
    # Show optimization example
    mpc_opt_results = optimize_mpc_parameters_example()
    
    print("\n" + "="*70)
    print("MPC IMPLEMENTATION COMPLETE")
    print("="*70)
    print("\nMPC offers several advantages:")
    print("✓ Predictive capability - anticipates future glucose trends")
    print("✓ Constraint handling - explicitly enforces glucose and insulin bounds")
    print("✓ Meal announcement - can prepare for announced meals")
    print("✓ Optimal control - minimizes multi-objective cost function")
    print("✓ Customizable horizons - tune prediction and control windows")
    print("="*70)
