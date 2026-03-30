import subprocess, pprint
from pymgipsim.Utilities.paths import default_settings_path, results_path
from pymgipsim.Utilities.Scenario import load_scenario
from pymgipsim.Utilities import simulation_folder

from pymgipsim.InputGeneration.activity_settings import activity_args_to_scenario

from pymgipsim.generate_settings import generate_simulation_settings_main
from pymgipsim.generate_inputs import generate_inputs_main
from pymgipsim.generate_subjects import generate_virtual_subjects_main
from pymgipsim.generate_plots import generate_plots_main
from pymgipsim.generate_results import generate_results_main

import cProfile, pstats
import os

"""
#######################
Main Functions for CLI
#######################
"""

def run_simulator_cli(args):

    if args.profile:
        profiler = cProfile.Profile()
        profiler.enable()

    """ Initialization """
    
    if not args.no_print:
        print(f">>>>> Initializing Simulator")

    subprocess.run(['python', 'initialization.py'])

    """ Loading Default Scenario """

    default_scenario = load_scenario(os.path.join(default_settings_path, "scenario_default.json"))

    """ Define Results Path """
    _, _, _, results_folder_path = simulation_folder.create_simulation_results_folder(results_path)

    """ Load Scenario """
    settings_file = simulation_folder.load_settings_file(args, results_folder_path)

    """ Print Settings """
    if not args.no_print:
        print("Simulation Settings")
        pprint.pprint(vars(args), indent = 2)

    if not args.scenario_name:

        settings_file = generate_simulation_settings_main(scenario_instance=settings_file, args=args, results_folder_path=results_folder_path)

        settings_file = generate_virtual_subjects_main(scenario_instance=settings_file, args=args, results_folder_path=results_folder_path)

        activity_args_to_scenario(settings_file, args)
        settings_file = generate_inputs_main(scenario_instance = settings_file, args = args, results_folder_path=results_folder_path)

        
    model,_ = generate_results_main(scenario_instance = settings_file, args = vars(args), results_folder_path = results_folder_path)

    figures = generate_plots_main(results_folder_path, args)


    if args.profile:
        profiler.disable()
        profiler_stats = pstats.Stats(profiler).sort_stats('tottime')
        profiler_stats.print_stats(30)

    return settings_file, model, figures