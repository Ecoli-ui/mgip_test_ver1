import colorama
from pymgipsim.Interface.Messages.parser_colors import *

"""
Make Header Logo
"""

header_text = colorama.Style.BRIGHT + colorama.Fore.WHITE + 'Welcome to ' + color_pymgipsim_logo() + colorama.Style.BRIGHT + colorama.Fore.WHITE + ' v1.0.1'  + colorama.Style.RESET_ALL + colorama.Fore.CYAN

header_logo = (
				colorama.Fore.CYAN + "\n###############################################################\n"\
				f"################ {header_text} ################\n"\
				"###############################################################\n"+colorama.Style.RESET_ALL
				)
				


"""
Make Intro Message
"""

intro_message_1 =	""

intro_direction = "\n>>>>> Use the " + color_command_text('directions') + " command to get more in-depth instructions on how to use the command line interface."

intro_help = "\n>>>>> Use the " + color_command_text('help') + " command to learn about the different command line interface options.\n"

intro_singlescale = ">>>>> You booted into" + colorama.Fore.CYAN + " singlescale" + colorama.Style.RESET_ALL + " mode, type " + color_command_text('mode multiscale') + " to switch into multiscale mode.\n"
intro_multiscale = ">>>>> You booted into multiscale mode, type " + color_command_text('mode singlescale') + " to switch into singlescale mode.\n"


"""
Make the prompts
"""

simulator_prompt = colorama.Style.BRIGHT+colorama.Fore.CYAN+'('+color_pymgipsim_logo() + colorama.Style.BRIGHT+colorama.Fore.CYAN + ") > " + colorama.Style.RESET_ALL



"""
Closing Logo
"""

closer_text = colorama.Style.BRIGHT + colorama.Fore.WHITE + 'Closing ' +colorama.Fore.RED+'**'+colorama.Fore.CYAN+'PYmGIPsim' + colorama.Style.BRIGHT + colorama.Fore.WHITE + ' v1.0.1'  + colorama.Style.RESET_ALL + colorama.Fore.CYAN

closing_logo = (
				colorama.Fore.CYAN + "\n###############################################################\n"\
				f"################## {closer_text} #################\n"\
				"###############################################################\n"+colorama.Style.RESET_ALL
				)		