import argparse
import numpy as np

from pymgipsim.Utilities.units_conversions_constants import DEFAULT_RANDOM_SEED
from pymgipsim.Utilities.Scenario import scenario

np.random.seed(DEFAULT_RANDOM_SEED)


def make_sglt2i_settings(scenario_instance: scenario, args: argparse.Namespace):

    scenario_instance.input_generation.sglt2i_dose_magnitude = args.sglt2i_dose_magnitude

    return scenario_instance