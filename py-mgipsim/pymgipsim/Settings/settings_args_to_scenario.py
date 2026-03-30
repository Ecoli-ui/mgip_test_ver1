from pymgipsim.Utilities.Scenario import scenario



def settings_args_to_scenario(scenario_instance: scenario, args):
    scenario_instance.mode = args.mode