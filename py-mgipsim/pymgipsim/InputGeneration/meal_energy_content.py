from pymgipsim.Utilities.units_conversions_constants import GLUCOSE_KCAL_PER_GRAM
import numpy as np
from pymgipsim.Utilities.Scenario import scenario

def estimate_g_cho_from_energy_intake(scenario_instance:scenario, args, cho_energy_density=GLUCOSE_KCAL_PER_GRAM):
    """
    """

    energy_intake = np.array(scenario_instance.input_generation.daily_energy_intake)
    f_cho = np.array(scenario_instance.input_generation.fraction_cho_intake)

    total_carb_range = []
    for i in range(len(energy_intake)):
        total_carb_range.append((energy_intake[i] * f_cho / cho_energy_density).tolist())
    
    scenario_instance.input_generation.total_carb_range = total_carb_range

def estimate_energy_intake_from_g_cho(g_cho, f_cho, cho_energy_density=GLUCOSE_KCAL_PER_GRAM):
    """
    Estimates the total energy intake from given grams of carbohydrates, carbohydrate fraction, and carbohydrate energy density.

    Parameters:
    - g_cho: float
        Grams of carbohydrates.
    - f_cho: float
        Fraction of energy intake from carbohydrates.
    - cho_energy_density: float, optional
        Energy density of carbohydrates in kilocalories per gram. Default is set to glucose_energy_density_kcal_per_g.

    Returns:
    - float
        Estimated total energy intake in kilocalories.
    """

    """ Check Inputs """
    assert cho_energy_density != 0
    assert f_cho != 0

    return g_cho * cho_energy_density / f_cho

def calculate_daily_energy_intake(scenario_instance: scenario, args):

    """ Calculate daily energy intake based on the baseline values and args.ncb"""
    baseline = scenario_instance.patient.demographic_info.baseline_daily_energy_intake
    balance = args.net_calorie_balance

    max_dimension = max(len(baseline), len(balance))

    if len(baseline) < max_dimension:
        baseline *= max_dimension

    if len(balance) < max_dimension:
        balance *= max_dimension

    total = np.array(baseline) + np.array(balance)

    scenario_instance.input_generation.daily_energy_intake = total.tolist()