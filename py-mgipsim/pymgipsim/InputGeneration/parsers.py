import json, argparse
import os
from ..Utilities.paths import default_settings_path
from pymgipsim.Interface.Messages.parser_colors import color_help_text, color_group_header_text

with open(os.path.join(default_settings_path, "scenario_default.json")) as f:
    default_settings = json.load(f)

def generate_carb_settings_parser(parent_parser = [], add_help = True):

    carb_settings_parser = argparse.ArgumentParser(
                                                    prog = 'Carbohydrate Intake Settings',
                                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                                    parents=parent_parser,
                                                    add_help=add_help
                                                    )

    carb_group = carb_settings_parser.add_argument_group(color_group_header_text('Carbohydrate Intake'))
    carb_group.add_argument(
                            '-bcr',
                            '--breakfast-carb-range',\
                            help = color_help_text('Breakfast carbohydrate intake range in grams. This can be either a single, constant value or a min and max for random sampling.' + \
                                                    "Breakfast is given between 06:00-08:00. The duration is between 30-60 minutes long."),\
                            dest = 'breakfast_carb_range',\
                            nargs = "+",
                            type = float,
                            default = default_settings['input_generation']['breakfast_carb_range']
                            )

    carb_group.add_argument(
                            '-amscr',
                            '--am-snack-carb-range',\
                            help = color_help_text('AM snack carbohydrate intake range in grams. This can be either a single, constant value or a min and max for random sampling.' + \
                                                    "This snack is given between 09:00-11:00. The duration is between 5-15 minutes long."),\
                            dest = 'am_snack_carb_range',\
                            nargs = "+",
                            type = float,
                            default = default_settings['input_generation']['am_snack_carb_range']
                            )


    carb_group.add_argument(
                            '-lcr',
                            '--lunch-carb-range',\
                            help = color_help_text('Lunch carbohydrate intake range in grams. This can be either a single, constant value or a min and max for random sampling.' + \
                                                    "Lunch is given between 12:00-14:00. The duration is between 30-60 minutes long."),\
                            dest = 'lunch_carb_range',\
                            nargs = "+",
                            type = float,
                            default = default_settings['input_generation']['lunch_carb_range']
                            )

    carb_group.add_argument(
                            '-pmscr',
                            '--pm-snack-carb-range',\
                            help = color_help_text('PM snack carbohydrate intake range in grams. This can be either a single, constant value or a min and max for random sampling.' + \
                                            "This snack is given between 15:00-17:00. The duration is between 5-15 minutes long."),\
                            dest = 'pm_snack_carb_range',\
                            nargs = "+",
                            type = float,
                            default = default_settings['input_generation']['pm_snack_carb_range']
                            )

    carb_group.add_argument(
                            '-dcr',
                            '--dinner-carb-range',\
                            help = color_help_text('Dinner carbohydrate intake range in grams. This can be either a single, constant value or a min and max for random sampling.' + \
                                                    "Dinner is given between 18:00-20:00. The duration is between 30-60 minutes long."),\
                            dest = 'dinner_carb_range',\
                            nargs = "+",
                            type = float,
                            default = default_settings['input_generation']['dinner_carb_range']
                            )

    return carb_settings_parser

def generate_multiscale_carb_settings_parser(parent_parser = [], add_help = True):

    carb_energy_settings_parser = argparse.ArgumentParser(
                                                    prog = 'Carbohydrate Intake Settings',
                                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                                    parents=parent_parser,
                                                    add_help=add_help
                                                    )

    carb_energy_group = carb_energy_settings_parser.add_argument_group(color_group_header_text('Carbohydrate Intake'))
    carb_energy_group.add_argument(
                                    '-fcho',
                                    '--fraction-cho-intake',\
                                    help = color_help_text("Fraction of energy daily intake composed of carbohydrates. Can be a single value or a range, and should be <= 1."),\
                                    dest = 'fraction_cho_intake',\
                                    nargs = '+',
                                    type = float,
                                    default = default_settings['input_generation']['fraction_cho_intake']
                                    )
    
    carb_energy_group.add_argument(
                                    '-fcas',
                                    '--fraction-cho-as-snack',\
                                    help = color_help_text("Fraction of carbohydrates obtained from snacks. Can be a single value or a a range, and must be <= 1."),\
                                    dest = 'fraction_cho_as_snack',\
                                    nargs = 1,
                                    type = float,
                                    default = default_settings['input_generation']['fraction_cho_as_snack']
                                    )
    
    carb_energy_group.add_argument(
                                    '-ncb',
                                    '--net-calorie-balance',\
                                    help = color_help_text("The net energy balance per day in calories. This can be a single value or a range, and can be positive (more intake than expenditure) or negative (less intake than expenditure)."),\
                                    dest = 'net_calorie_balance',\
                                    nargs = 1,
                                    default = default_settings['input_generation']['net_calorie_balance'],
                                    type = float,
                                    )


    return carb_energy_settings_parser



def generate_sglt2i_settings_parser(parent_parser = [], add_help = True):

    sglt2i_settings_parser = argparse.ArgumentParser(
                                                prog = 'SGLT2I Settings Parser',
                                                formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                                parents=parent_parser,
                                                add_help=add_help
                                                )
    
    sglt2i_group = sglt2i_settings_parser.add_argument_group(color_group_header_text('SGLT2I Intake'))
    sglt2i_group.add_argument('-sdm',
                                        '--sglt2i_dose_magnitude',
                                        help = color_help_text('SGLT2I dose in mg.'),\
                                        nargs = 1,\
                                        dest = 'sglt2i_dose_magnitude',\
                                        type = int,
                                        default = default_settings["input_generation"]['sglt2i_dose_magnitude']
                                        )

    return sglt2i_settings_parser


def generate_exog_insulin_parser(parent_parser = [], add_help = True):

    insulin_settings_parser = argparse.ArgumentParser(
                                                    prog = 'Exogenous Insulin Settings Parser',
                                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                                    parents=parent_parser,
                                                    add_help=add_help
                                                    )

    exog_insulin_group = insulin_settings_parser.add_argument_group(color_group_header_text('Basal and Bolus Insulin Intake'))

    exog_insulin_group.add_argument('-bo',
                                    '--bolus',
                                    help = color_help_text('Insulin carb fraction multiplier.'),
                                    dest = 'bolus_multiplier',
                                    type=float,
                                    default=1.0
                                    )

    exog_insulin_group.add_argument('-ba',
                                    '--basal',
                                    help = color_help_text('Basal insulin multiplier.'),
                                    dest = 'basal_multiplier',
                                    type=float,
                                    default=1.0
                                    )

    return insulin_settings_parser


def generate_activity_parser(parent_parser=[], add_help=True):
    # net_energy_balance_parser = generate_energy_balance_parser(add_help = False)

    activity_parser = argparse.ArgumentParser(
        prog='Activity Settings',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        add_help=add_help
    )
    physact = activity_parser.add_argument_group(color_group_header_text('Physical activity'))

    physact.add_argument('-rst',
                                    '--running_start-time',
                                    help = color_help_text('Start time of the activity'),
                                    dest = 'running_start_time',
                                    nargs="+",
                                    type=str,
                                    default=["16:00", "18:00"]
                                    )

    physact.add_argument('-rd',
                                    '--running_duration',
                                    help = color_help_text('Duration of the activity'),
                                    dest = 'running_duration',
                                    type=float,
                                    nargs="+",
                                    default=[20.0, 90.0]
                                    )



    physact.add_argument('-rinc',
                                    '--running_incline',
                                    help = color_help_text('Incline.'),
                                    dest = 'running_incline',
                                    type=float,
                                    nargs = "+",
                                    default = [0.0, 6.0]
                                    )

    physact.add_argument('-rsp',
                                    '--running_speed',
                                    help = color_help_text('Incline.'),
                                    dest = 'running_speed',
                                    type=float,
                                    nargs = "+",
                                    default = [1.7, 7.0]
                                    )


    physact.add_argument('-cst',
                                    '--cycling_start_time',
                                    help = color_help_text('Start time of the activity'),
                                    dest = 'cycling_start_time',
                                    nargs="+",
                                    type=str,
                                    default=["16:00", "18:00"]
                                    )

    physact.add_argument('-cd',
                                    '--cycling_duration',
                                    help = color_help_text('Duration of the activity'),
                                    dest = 'cycling_duration',
                                    type=float,
                                    nargs="+",
                                    default=[20.0, 90.0]
                                    )

    physact.add_argument('-cpwr',
                                    '--cycling_power',
                                    help = color_help_text('Average exerted power.'),
                                    dest = 'cycling_power',
                                    type=float,
                                    nargs = "+",
                                    default = [0.0]
                                    )

    return activity_parser



def generate_input_parser(parent_parser = [], add_help = True):

    carb_settings_parser = generate_carb_settings_parser(add_help = False)
    carb_multiscale_settings_parser = generate_multiscale_carb_settings_parser(add_help = False)

    sglt2i_settings_parser = generate_sglt2i_settings_parser(add_help = False)

    insulin_settings_parser = generate_exog_insulin_parser(add_help = False)

    activity_parser = generate_activity_parser(add_help = False)

    if parent_parser:
        parent_parser_combined = [
                                carb_settings_parser,
                                carb_multiscale_settings_parser,
                                sglt2i_settings_parser,
                                insulin_settings_parser,
                                activity_parser,
                                ] + parent_parser
    else:
        parent_parser_combined = [
                                carb_settings_parser,
                                carb_multiscale_settings_parser,
                                sglt2i_settings_parser,
                                insulin_settings_parser,
                                activity_parser
                                ]
    
    input_parser = argparse.ArgumentParser(
                                            prog = 'Input Settings',
                                            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                            parents=parent_parser_combined,
                                            add_help=add_help
                                            )

    return input_parser
