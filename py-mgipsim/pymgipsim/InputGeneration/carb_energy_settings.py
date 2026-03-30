import argparse
import numpy as np
from pymgipsim.InputGeneration.signal import Events

from pymgipsim.Utilities.units_conversions_constants import DEFAULT_RANDOM_SEED
from pymgipsim.InputGeneration.generate_carb_signal import generate_carb_ranges_multiscale
from pymgipsim.Utilities.Scenario import scenario

np.random.seed(DEFAULT_RANDOM_SEED)

def make_carb_settings(scenario_instance: scenario, args: argparse.Namespace):

    match scenario_instance.settings.simulator_name:
        case 'SingleScaleSolver':
            scenario_instance.input_generation.breakfast_carb_range = args.breakfast_carb_range
            scenario_instance.input_generation.lunch_carb_range = args.lunch_carb_range
            scenario_instance.input_generation.dinner_carb_range = args.dinner_carb_range

            scenario_instance.input_generation.am_snack_carb_range = args.am_snack_carb_range
            scenario_instance.input_generation.pm_snack_carb_range = args.pm_snack_carb_range


        case 'MultiScaleSolver':
            meal_cho, snack_cho = generate_carb_ranges_multiscale(scenario_instance)

            scenario_instance.input_generation.breakfast_carb_range = (np.array(meal_cho) / 3 ).tolist()
            scenario_instance.input_generation.lunch_carb_range = (np.array(meal_cho) / 3 ).tolist()
            scenario_instance.input_generation.dinner_carb_range = (np.array(meal_cho) / 3 ).tolist()

            scenario_instance.input_generation.am_snack_carb_range = (np.array(snack_cho) / 2 ).tolist()
            scenario_instance.input_generation.pm_snack_carb_range = (np.array(snack_cho) / 2 ).tolist()

def generate_carb_absorption(scenario_instance: scenario, args):
    meal_times = np.asarray(scenario_instance.inputs.meal_carb.start_time)
    meal_durations = np.asarray(scenario_instance.inputs.meal_carb.duration)
    meal_magnitudes = 40*meal_durations
    carb_absorption_time = Events(start_time= meal_times, duration=meal_durations,
                           magnitude=meal_magnitudes).as_dict()
    return carb_absorption_time