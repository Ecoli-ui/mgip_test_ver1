from pymgipsim.Interface.Messages.parser_colors import *

""" 
Make the direction messages
"""

directions_helper_1 = f"\n\nThis is the command line interface (CLI) for the mGIPsim Python simulator ({color_pymgipsim_logo()})."

directions_helper_2 = f"\nThe CLI can be used in singlescale ({color_command_text('python -m interface_cli singlescale')}) or multiscale modes ({color_command_text('python -m interface_cli multiscale')})."

directions_helper_3 = f"\nThe command inputs for each mode can be accessed by adding -h to each mode ({color_command_text('python -m interface_cli singlescale -h')}) or multiscale modes ({color_command_text('python -m interface_cli multiscale -h')})."

initial_directions = directions_helper_1 + directions_helper_2 + directions_helper_3 + '\n'
