import argparse
import os
from ..Utilities.paths import default_settings_path
from ..Utilities.Scenario import load_scenario
from pymgipsim.Interface.Messages.parser_colors import color_help_text, color_group_header_text
from pymgipsim.Utilities.units_conversions_constants import UnitConversion, DEFAULT_RANDOM_SEED

# with open(default_settings_path + "\\scenario_default.json","r") as f:
#     default_settings = scenario(**json.load(f))
# f.close()

default_settings = load_scenario(os.path.join(default_settings_path, "scenario_default.json"))

default_days = UnitConversion.time.convert_minutes_to_days(default_settings.settings.end_time - default_settings.settings.start_time)

def generate_settings_parser(parent_parser = [], add_help = True, flags = [False, False, False, False]):

    parser = argparse.ArgumentParser(
                                    prog = 'Simulation Settings',
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                    parents = parent_parser,
                                    add_help = add_help,
                                    exit_on_error = False
                                    )

    settings_group = parser.add_argument_group(title = color_group_header_text('Simulation Settings'))

    settings_group.add_argument(
                        '-d',
                        '--days',\
                        help = color_help_text('Set the number of days for simulation. This must be >= 1'),\
                        dest = 'number_of_days',\
                        default = default_days,\
                        type = int
                        )



    ######################################################################################

    settings_group.add_argument(
                        '-st',
                        '--sampling-time',\
                        help = color_help_text('Sampling time for the simulation. The sampling time must be > 0.'),\
                        dest = 'sampling_time',\
                        default = default_settings.settings.sampling_time,\
                        type = float
                        )

    settings_group.add_argument(
                        '-pr',
                        '--profiler',\
                        help = color_help_text('Run the profiler with interface_cli.'),\
                        dest = 'profile',
                        action='store_const', default=flags[1], const=not flags[1]
                        )

    settings_group.add_argument(
                        '-rs',
                        '--random_seed',\
                        help = color_help_text('Random seed for the sampling of the pdfs.'),\
                        dest = 'random_seed',
                        type = int,
                        default=DEFAULT_RANDOM_SEED
                        )

    settings_group.add_argument(
                        '-ms',
                        '--multi_scale',
                        help = color_help_text('Run simulation in multiscale mode.'),
                        dest = 'multi_scale',
                        action='store_const', default=flags[0], const=not flags[0]
                        )

    settings_group.add_argument('-npb',action='store_const', default=flags[3], const=not flags[3], dest = 'no_progress_bar', help = 'Turn off progress bars')

    settings_group.add_argument('-np', '--no-print', action='store_const', default=flags[2], const=not flags[2], dest = 'no_print', help = 'Turn off printing')

    return parser
