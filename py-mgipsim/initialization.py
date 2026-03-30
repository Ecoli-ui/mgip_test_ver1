import os, subprocess, json, tqdm
from pymgipsim.Utilities.units_conversions_constants import DEFAULT_RANDOM_SEED
from pymgipsim.Utilities.paths import results_path


_ = """
######################################################################
Defining Paths and Default Settings
######################################################################
"""

if not os.path.exists(os.path.join(os.getcwd(), 'SimulationResults')):
    os.mkdir(os.path.join(os.getcwd(), 'SimulationResults'))

subprocess.run(['python', 'scenarios_default.py'])

from pymgipsim.Utilities.paths import default_settings_path, results_path, simulator_path

for path in [default_settings_path, results_path, simulator_path]:
    assert os.path.isdir(path), f"Required path {path} does not exist. Verify files."


_ = """
######################################################################
Verify Folders
######################################################################
"""

with open(os.path.join(default_settings_path, "scenario_default.json"), "r") as f:
    default_settings = json.load(f)
f.close()

for folder in ['InputGeneration', 'ModelSolver', 'ODESolvers', 'Plotting', 'Settings', 'Utilities', 'VirtualPatient']:
    assert os.path.exists(os.path.join(simulator_path, folder)), f"Required folder {folder} does not exist. Verify files."


"""
######################################################################
Delete the undesirable folders and files
######################################################################
"""

subprocess.run(['python', 'clear_pycache.py'])


"""
######################################################################
Setting Random Seed
######################################################################
"""
import numpy as np

np.random.seed(DEFAULT_RANDOM_SEED)
