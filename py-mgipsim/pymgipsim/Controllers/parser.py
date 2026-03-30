import json, argparse, glob, os
from ..Utilities.paths import default_settings_path, controller_path
from pymgipsim.Interface.Messages.parser_colors import color_help_text, color_group_header_text
from pymgipsim import Controllers
from pymgipsim.Utilities.Scenario import scenario
from pymgipsim.Interface.Messages.parser_colors import color_error_warning_text

def controller_args_to_scenario(scenario_instance: scenario, args):
    if args.controller_name!=Controllers.OpenLoop.controller.Controller.name\
            and "T2DM" in scenario_instance.patient.model.name:
        print(color_error_warning_text(scenario_instance.patient.model.name + " does not support " + args.controller_name))
        args.controller_name = scenario_instance.controller.name
        args.controller_parameters = scenario_instance.controller.parameters
    else:
        scenario_instance.controller.name = args.controller_name
        scenario_instance.controller.parameters = args.controller_parameters

def get_controller_names():
    paths = glob.glob(os.path.join(controller_path, "*", ""))
    controllers = [folder for folder in paths if '__' not in folder]
    controllers = [folder.split(os.sep)[-2:] for folder in controllers]
    controllers = [folder[0] for folder in controllers]
    return controllers

def generate_controller_settings_parser(parent_parser = [], add_help = True):

    controller_settings_parser = argparse.ArgumentParser(
                                                    prog = 'Controller Settings',
                                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                                    parents=parent_parser,
                                                    add_help=add_help
                                                    )

    controller_group = controller_settings_parser.add_argument_group(color_group_header_text('Controller'))
    controller_group.add_argument(
                            '-ctrl',
                            '--controller-name',
                            help = color_help_text("Name of the closed-loop controller algorithm."),
                            dest = 'controller_name',
                            choices=get_controller_names(),
                            type = str,
                            default = Controllers.OpenLoop.controller.Controller.name
                            )

    controller_group.add_argument(
                            '-ctrlparams',
                            '--controller-parameters',
                            help = color_help_text("Parameters of the controller."),
                            dest = 'controller_parameters',
                            type = list,
                            default = []
                            )

    return controller_settings_parser
