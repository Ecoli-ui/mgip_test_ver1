import colorama


def color_help_text(prompt):
	return colorama.Fore.CYAN + prompt + colorama.Fore.WHITE + colorama.Style.RESET_ALL

def color_command_text(prompt):
	return colorama.Style.BRIGHT + colorama.Fore.RED + prompt + colorama.Fore.WHITE + colorama.Style.RESET_ALL
	
def color_group_header_text(prompt):
	return colorama.Style.BRIGHT + colorama.Fore.CYAN + prompt + colorama.Fore.WHITE + colorama.Style.RESET_ALL

def color_error_warning_text(prompt):
	return colorama.Style.BRIGHT + colorama.Fore.RED + prompt + colorama.Fore.WHITE + colorama.Style.RESET_ALL

def color_modified_text(prompt):
	return colorama.Style.BRIGHT + colorama.Fore.CYAN + prompt + colorama.Style.RESET_ALL

def color_pymgipsim_logo():
	return colorama.Style.BRIGHT + colorama.Fore.RED+'**'+ colorama.Fore.CYAN + 'PYmGIPsim' + colorama.Style.RESET_ALL


