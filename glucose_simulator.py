"""
T1D Blood Glucose Simulator with Closed-Loop Controller
========================================================

This simulator consists of three main components:
1. Physiological Model: Simplified compartment model for glucose-insulin dynamics
2. Glucose Sensor: Sensor with noise and delay
3. Insulin Pump: Insulin delivery device

The controller parameters are separated to enable optimization via grid search.
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from typing import Tuple, List, Optional, Sequence
from pathlib import Path


# ============================================================================
# COMPONENT 1: PHYSIOLOGICAL MODEL
# ============================================================================

@dataclass
class PhysiologicalParams:
    """Parameters for the physiological model (Bergman minimal model variant).
    
    Note on glucose units:
    - This simulator uses mg/dL (milligrams per deciliter) - common in the USA
    - Many countries use mmol/L (millimoles per liter)
    - Conversion: mg/dL ÷ 18 = mmol/L  (or mmol/L × 18 = mg/dL)
    - Example: 100 mg/dL = 5.6 mmol/L, 180 mg/dL = 10.0 mmol/L
    """
    # Glucose dynamics
    Gb: float = 100.0  # Basal glucose (mg/dL)
    p1: float = 0.028  # Glucose effectiveness (1/min)
    
    # Insulin dynamics
    Ib: float = 10.0   # Basal insulin (mU/L)
    p2: float = 0.025  # Rate of insulin action (1/min)
    p3: float = 0.000013  # Insulin sensitivity (1/min per mU/L)
    insulin_clearance_rate: float = 0.1  # Insulin clearance rate (1/min)
    
    # Meal absorption
    tau_meal: float = 40.0  # Meal absorption time constant (min)
    meal_bioavailability: float = 0.525  # Fraction of ingested carbs affecting blood glucose
    
    # Body parameters
    body_weight: float = 70.0  # Body weight (kg)
    Vg: float = 1.5  # Glucose distribution volume (dL/kg)


@dataclass
class PatientProfile:
    """Patient-specific configuration for physiological simulation."""
    patient_id: str = "default_patient"
    physiological_params: PhysiologicalParams = field(default_factory=PhysiologicalParams)


class PhysiologicalModel:
    """Compartment model for glucose-insulin dynamics."""
    
    def __init__(self, params: PhysiologicalParams):
        self.params = params
        self.reset()
    
    def reset(self):
        """Reset to basal state."""
        self.G = self.params.Gb  # Glucose concentration (mg/dL)
        self.X = 0.0  # Insulin action (1/min)
        self.I = self.params.Ib  # Plasma insulin (mU/L)
        self.meal_remaining = 0.0  # Meal glucose to be absorbed (mg/dL)
    
    def step(self, dt: float, insulin_infusion: float, meal_input: float = 0.0) -> float:
        """
        Simulate one time step.
        
        Args:
            dt: Time step (minutes)
            insulin_infusion: Insulin delivery rate (U/min)
            meal_input: Meal carbohydrate input (mg/dL equivalent)
        
        Returns:
            Current glucose level (mg/dL)
        """
        params = self.params
        
        # Add new meal input
        self.meal_remaining += meal_input
        
        # Meal absorption (first-order kinetics)
        meal_absorption = (self.meal_remaining / params.tau_meal) * dt
        self.meal_remaining -= meal_absorption
        
        # Glucose dynamics
        # dG/dt = -p1*(G - Gb) - X*G + meal_absorption
        dG = (-params.p1 * (self.G - params.Gb) - self.X * self.G + meal_absorption) * dt
        self.G += dG
        
        # Insulin action dynamics
        # dX/dt = -p2*X + p3*I
        dX = (-params.p2 * self.X + params.p3 * self.I) * dt
        self.X += dX
        
        # Insulin dynamics (simplified: direct relation to infusion)
        # Convert U/min to mU/L (simplified pharmacokinetics)
        # Total glucose distribution volume = Vg (dL/kg) * body_weight (kg)
        total_volume = params.Vg * params.body_weight  # Total volume in dL
        insulin_to_plasma = insulin_infusion * 1000 / total_volume  # U/min -> mU/L/min
        dI = (insulin_to_plasma - params.insulin_clearance_rate * (self.I - params.Ib)) * dt
        self.I += dI
        
        # Keep glucose non-negative
        self.G = max(self.G, 20.0)
        
        return self.G


# ============================================================================
# COMPONENT 2: GLUCOSE SENSOR
# ============================================================================

@dataclass
class SensorParams:
    """Parameters for the glucose sensor."""
    noise_std: float = 2.0  # Measurement noise std dev (mg/dL)
    delay: int = 2  # Sensor delay (time steps)
    calibration_error: float = 1.0  # Multiplicative calibration error (1.0 = perfect)


class GlucoseSensor:
    """Glucose sensor with noise and delay."""
    
    def __init__(self, params: SensorParams):
        self.params = params
        self.measurement_buffer = []
    
    def reset(self):
        """Reset sensor state."""
        self.measurement_buffer = []
    
    def measure(self, true_glucose: float) -> float:
        """
        Measure glucose with sensor characteristics.
        
        Args:
            true_glucose: True glucose value (mg/dL)
        
        Returns:
            Measured glucose value (mg/dL)
        """
        # Add calibration error and noise
        noisy_measurement = (true_glucose * self.params.calibration_error + 
                           np.random.normal(0, self.params.noise_std))
        
        # Add to buffer for delay
        self.measurement_buffer.append(noisy_measurement)
        
        # Return delayed measurement
        if len(self.measurement_buffer) > self.params.delay:
            return self.measurement_buffer.pop(0)
        else:
            # If buffer not full, return current (no delay initially)
            return noisy_measurement


# ============================================================================
# COMPONENT 3: INSULIN PUMP
# ============================================================================

@dataclass
class PumpParams:
    """Parameters for the insulin pump."""
    basal_rate: float = 0.02  # Basal insulin rate (U/min)
    max_bolus_rate: float = 0.1  # Maximum bolus rate (U/min)
    min_rate: float = 0.0  # Minimum delivery rate (U/min)


class InsulinPump:
    """Insulin delivery device."""
    
    def __init__(self, params: PumpParams):
        self.params = params
    
    def deliver(self, requested_rate: float) -> float:
        """
        Deliver insulin at requested rate with pump constraints.
        
        Args:
            requested_rate: Requested insulin delivery rate (U/min)
        
        Returns:
            Actual delivered rate (U/min)
        """
        # Apply pump constraints
        actual_rate = np.clip(requested_rate, 
                             self.params.min_rate, 
                             self.params.basal_rate + self.params.max_bolus_rate)
        return actual_rate


# ============================================================================
# CONTROLLER
# ============================================================================

@dataclass
class ControllerParams:
    """
    Controller parameters - THESE ARE THE PARAMETERS TO OPTIMIZE.
    
    This is a simple PID-like controller with:
    - Proportional gain (Kp): Response to current error
    - Integral gain (Ki): Response to accumulated error
    - Derivative gain (Kd): Response to rate of change
    - Target glucose level and deadband
    
    Note on glucose units:
    - All glucose values in this simulator are in mg/dL (USA standard)
    - To convert to mmol/L (international): divide by 18
    - Example: target_glucose=110 mg/dL = 6.1 mmol/L
    - Typical target ranges: 70-180 mg/dL (3.9-10.0 mmol/L) or 80-140 mg/dL (4.4-7.8 mmol/L)
    """
    Kp: float = 0.0005  # Proportional gain (U/min per mg/dL)
    Ki: float = 0.00001  # Integral gain (U/min per (mg/dL)*min)
    Kd: float = 0.0001  # Derivative gain (U/min per (mg/dL)/min)
    
    target_glucose: float = 100.0  # Target glucose (mg/dL)
    deadband: float = 10.0  # No action if within target ± deadband (mg/dL)
    
    integral_limit: float = 5000.0  # Anti-windup: max integral term (mg/dL*min)


class ClosedLoopController:
    """PID-style controller for glucose regulation."""
    
    def __init__(self, params: ControllerParams, basal_rate: float):
        self.params = params
        self.basal_rate = basal_rate
        self.reset()
    
    def reset(self):
        """Reset controller state."""
        self.integral_error = 0.0
        self.previous_error = 0.0
        self.previous_glucose = None
    
    def compute_insulin_rate(self, measured_glucose: float, dt: float) -> float:
        """
        Compute insulin delivery rate based on measured glucose.
        
        Args:
            measured_glucose: Measured glucose from sensor (mg/dL)
            dt: Time step (minutes)
        
        Returns:
            Insulin delivery rate (U/min)
        """
        params = self.params
        
        # Compute error
        error = measured_glucose - params.target_glucose
        
        # Apply deadband (don't correct if within acceptable range)
        if abs(error) < params.deadband:
            error = 0.0
        
        # Proportional term
        proportional = params.Kp * error
        
        # Integral term (with anti-windup)
        self.integral_error += error * dt
        self.integral_error = np.clip(self.integral_error, 
                                     -params.integral_limit, 
                                     params.integral_limit)
        integral = params.Ki * self.integral_error
        
        # Derivative term
        if self.previous_glucose is not None:
            derivative = params.Kd * (measured_glucose - self.previous_glucose) / dt
        else:
            derivative = 0.0
        
        self.previous_glucose = measured_glucose
        
        # Total insulin rate = basal + correction
        total_rate = self.basal_rate + proportional + integral + derivative
        
        return total_rate


# ============================================================================
# SIMULATOR
# ============================================================================

class T1DSimulator:
    """Main simulator combining all components."""
    
    def __init__(self, 
                 phys_params: Optional[PhysiologicalParams],
                 sensor_params: SensorParams,
                 pump_params: PumpParams,
                 controller_params: ControllerParams,
                 patient_profile: Optional[PatientProfile] = None):

        if patient_profile is not None:
            self.patient_profile = patient_profile
            resolved_phys_params = patient_profile.physiological_params
        else:
            resolved_phys_params = phys_params if phys_params is not None else PhysiologicalParams()
            self.patient_profile = PatientProfile(physiological_params=resolved_phys_params)

        self.physiology = PhysiologicalModel(resolved_phys_params)
        self.sensor = GlucoseSensor(sensor_params)
        self.pump = InsulinPump(pump_params)
        self.controller = ClosedLoopController(controller_params, pump_params.basal_rate)
    
    def reset(self):
        """Reset all components to initial state."""
        self.physiology.reset()
        self.sensor.reset()
        self.controller.reset()
    
    def simulate(self, 
                 duration: float, 
                 dt: float, 
                 meals: Optional[Sequence[Tuple[float, float]]] = None) -> dict:
        """
        Run a simulation.
        
        Args:
            duration: Simulation duration (minutes)
            dt: Time step (minutes)
            meals: List of (time, carbs) tuples. Time in minutes, carbs in grams.
        
        Returns:
            Dictionary with simulation results
        """
        if meals is None:
            meals = []
        
        # Prepare meal schedule
        meal_schedule = {int(time / dt): carbs for time, carbs in meals}
        
        # Storage for results
        n_steps = int(duration / dt)
        times = np.arange(0, duration, dt)
        true_glucose = np.zeros(n_steps)
        measured_glucose = np.zeros(n_steps)
        insulin_rates = np.zeros(n_steps)
        
        # Reset system
        self.reset()
        
        # Simulation loop
        for i in range(n_steps):
            # Check for meal
            carbs = meal_schedule.get(i, 0.0)
            # Convert grams to mg/dL equivalent
            # 1g carb = 1000mg glucose / (Vg * body_weight) dL * bioavailability
            total_volume = self.physiology.params.Vg * self.physiology.params.body_weight
            meal_input = carbs * 1000 * self.physiology.params.meal_bioavailability / total_volume if carbs > 0 else 0.0
            
            # Get sensor measurement
            measured_glucose[i] = self.sensor.measure(self.physiology.G)
            
            # Controller computes insulin rate
            insulin_request = self.controller.compute_insulin_rate(measured_glucose[i], dt)
            
            # Pump delivers insulin
            insulin_rates[i] = self.pump.deliver(insulin_request)
            
            # Physiological model steps forward
            true_glucose[i] = self.physiology.step(dt, insulin_rates[i], meal_input)
        
        return {
            'time': times,
            'true_glucose': true_glucose,
            'measured_glucose': measured_glucose,
            'insulin_rate': insulin_rates
        }


# ============================================================================
# METRICS
# ============================================================================

def calculate_time_in_range(glucose_values: np.ndarray, 
                            lower: float = 70.0, 
                            upper: float = 180.0) -> dict:
    """
    Calculate time in range and related metrics.
    
    Note on glucose units:
    - Default range: 70-180 mg/dL (USA standard)
    - In mmol/L (international): 3.9-10.0 mmol/L
    - Conversion factor: mg/dL ÷ 18 = mmol/L
    - Common international target: 4-9 mmol/L (72-162 mg/dL)
    
    Args:
        glucose_values: Array of glucose values (mg/dL)
        lower: Lower bound of target range (mg/dL)
        upper: Upper bound of target range (mg/dL)
    
    Returns:
        Dictionary with metrics
    """
    total_points = len(glucose_values)
    
    in_range = np.sum((glucose_values >= lower) & (glucose_values <= upper))
    below_range = np.sum(glucose_values < lower)
    above_range = np.sum(glucose_values > upper)
    
    metrics = {
        'time_in_range_pct': (in_range / total_points) * 100,
        'time_below_range_pct': (below_range / total_points) * 100,
        'time_above_range_pct': (above_range / total_points) * 100,
        'mean_glucose': np.mean(glucose_values),
        'std_glucose': np.std(glucose_values),
        'cv_glucose': (np.std(glucose_values) / np.mean(glucose_values)) * 100,
        'min_glucose': np.min(glucose_values),
        'max_glucose': np.max(glucose_values)
    }
    
    return metrics


# ============================================================================
# DEMONSTRATION
# ============================================================================

def run_demonstration():
    """Run a demonstration simulation with example parameters."""
    
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Define component parameters
    patient_profile = PatientProfile(
        patient_id="demo_adult",
        physiological_params=PhysiologicalParams()
    )
    sensor_params = SensorParams(noise_std=3.0, delay=2)
    pump_params = PumpParams(basal_rate=0.02)
    
    # Define controller parameters (THESE CAN BE OPTIMIZED)
    controller_params = ControllerParams(
        Kp=0.0005,
        Ki=0.00001,
        Kd=0.0001,
        target_glucose=110.0,
        deadband=15.0
    )
    
    # Create simulator
    simulator = T1DSimulator(
        patient_profile.physiological_params,
        sensor_params,
        pump_params,
        controller_params,
        patient_profile=patient_profile
    )
    
    # Define meal schedule: (time_minutes, carbs_grams)
    meals = [
        (60, 50),   # Breakfast at 1 hour: 50g carbs
        (240, 60),  # Lunch at 4 hours: 60g carbs
        (480, 55),  # Dinner at 8 hours: 55g carbs
    ]
    
    # Run simulation
    duration = 12 * 60  # 12 hours in minutes
    dt = 1.0  # 1 minute time step
    
    print("Running T1D simulation...")
    results = simulator.simulate(duration, dt, meals)
    
    # Calculate metrics
    metrics = calculate_time_in_range(results['true_glucose'])
    
    # Print metrics
    print("\n" + "="*60)
    print("SIMULATION METRICS")
    print("="*60)
    print(f"Time in Range (70-180 mg/dL): {metrics['time_in_range_pct']:.1f}%")
    print(f"Time Below Range (<70 mg/dL):  {metrics['time_below_range_pct']:.1f}%")
    print(f"Time Above Range (>180 mg/dL): {metrics['time_above_range_pct']:.1f}%")
    print(f"Mean Glucose:                   {metrics['mean_glucose']:.1f} mg/dL")
    print(f"Glucose CV:                     {metrics['cv_glucose']:.1f}%")
    print(f"Min/Max Glucose:                {metrics['min_glucose']:.1f} / {metrics['max_glucose']:.1f} mg/dL")
    print("="*60)
    
    # Plot results
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    
    # Plot glucose
    axes[0].plot(results['time'] / 60, results['true_glucose'], 
                label='True Glucose', linewidth=2, alpha=0.8)
    axes[0].plot(results['time'] / 60, results['measured_glucose'], 
                label='Measured Glucose', linewidth=1, alpha=0.6, linestyle='--')
    axes[0].axhline(70, color='red', linestyle='--', alpha=0.5, label='Range: 70-180 mg/dL')
    axes[0].axhline(180, color='red', linestyle='--', alpha=0.5)
    axes[0].fill_between([0, duration/60], 70, 180, color='green', alpha=0.1)
    
    # Mark meals
    for meal_time, meal_carbs in meals:
        axes[0].axvline(meal_time / 60, color='orange', linestyle=':', alpha=0.7)
        axes[0].text(meal_time / 60, axes[0].get_ylim()[1] * 0.95, 
                    f'{meal_carbs}g', ha='center', fontsize=8)
    
    axes[0].set_ylabel('Glucose (mg/dL)', fontsize=12)
    axes[0].set_title('T1D Closed-Loop Simulation', fontsize=14, fontweight='bold')
    axes[0].legend(loc='upper right')
    axes[0].grid(True, alpha=0.3)
    
    # Plot insulin
    axes[1].plot(results['time'] / 60, results['insulin_rate'] * 60, 
                linewidth=2, color='purple', label='Insulin Rate')
    axes[1].axhline(pump_params.basal_rate * 60, color='gray', 
                   linestyle='--', alpha=0.5, label='Basal Rate')
    axes[1].set_xlabel('Time (hours)', fontsize=12)
    axes[1].set_ylabel('Insulin Rate (U/hr)', fontsize=12)
    axes[1].legend(loc='upper right')
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = Path(__file__).resolve().parent / 'simulation_results.png'
    plt.savefig(output_path, dpi=150)
    print(f"\nPlot saved to: {output_path}")
    plt.show()
    
    return results, metrics


if __name__ == "__main__":
    run_demonstration()
