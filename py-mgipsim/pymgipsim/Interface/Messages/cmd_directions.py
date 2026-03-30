from pymgipsim.Interface.Messages.parser_colors import *

""" 
Make the direction messages
"""

directions_helper_1 = f"\n\nThis is the CMD interface for the mGIPsim Python simulator ({color_pymgipsim_logo()})."

directions_helper_2 = f"\nBasic directions are given below. Use {color_command_text('directions -h')} to see a list of the directions section."

directions_helper_3 = f"\nIf you are unsure where to start, try {color_command_text('directions -v')} or {color_command_text('directions -pa')}\n"


initial_directions = directions_helper_1 + directions_helper_2 + directions_helper_3 + '\n'



"""
Parser Directions
"""

parser_directions_title = color_group_header_text('\n>>>>> Parsing Arguments')

parser_directions_1 = "\n\nParsing arguments refers to interpreting command line inputs as commands and performing the requested functions. For instance, a program could have a command " +\
						"line argument for saving the results of the program or generating plots. The library used for argument parsing in this interface is called argparse, and is a "+ \
						f"part of the standard Python library. Just by accessing these directions by inputting {color_command_text('directions -pa')} or {color_command_text('directions -v')} you have used this feature. " + \
						f"This refered to the command {color_command_text('directions')}, to indicate the directions should be generated, with the input {color_command_text('-pa')} to " +\
						"further select the directions for how to parse arguments."


parser_directions_2 = f"\n\nGenerally, parsers commands generally have the form {color_command_text('X -y')} or {color_command_text('X --y')} where X is some command and y is some "+ \
						f"input argument. The single dash - is used to indicate an abbreviation while the double dash -- is used to indicate the full word (such as {color_command_text('-y')} versus {color_command_text('--yellow')}). " + \
						f"This is largely conventional."


parser_directions_3 = f"\n\nAt any point while using this interface, the inputs that may be entered from the command line can be displayed by entering the command followed by {color_command_text('-h')} or {color_command_text('--help')} " + \
					 f"(such as {color_command_text('directions -h')} or {color_command_text('directions --help')})"



parser_directions = parser_directions_title + parser_directions_1 + parser_directions_2 + parser_directions_3 + '\n'


"""
CMD Interface Workflow
"""

cmd_directions_title = color_group_header_text('\n>>>>> Basic Command Workflow')


cmd_directions_1 = f"\n\nThere are various commands that can be used to generate simulation results. The key commands are {color_command_text('settings')}, {color_command_text('cohort')}, " + \
					f"{color_command_text('inputs')}, and {color_command_text('simulate')}. These constitute the basic functional workflow of this interface and can be used in any order as long as " + \
					f"{color_command_text('simulate')} is entered after the other. This is because {color_command_text('simulate')} will run a simulation with the currently defined settings."

cmd_directions_2 = f"\n\n{color_command_text('settings')} allows the user to set broad settings such as the simulation sampling time and the duration in days."

cmd_directions_3 = f"\n{color_command_text('cohort')} allows the user to set virtual subject characteristics such as the model and type of diabetes or number of subjects."

cmd_directions_4 = f"\n{color_command_text('inputs')} allows the user to set model inputs such as carbohydrate intake, basal or bolus insulin therapy, or SGLT2I treatment."

cmd_directions_5 = f"\n\nThe individual options for each command can be found with the {color_command_text('-h')} flag, such as {color_command_text('settings -h')}."

cmd_directions = cmd_directions_title + cmd_directions_1 + cmd_directions_2 + cmd_directions_3 + cmd_directions_4 + cmd_directions_5 + '\n'




"""
Model and Cohort Directions
"""

model_directions_title = color_group_header_text('\n>>>>> Choosing a Model and a Virtual Subject Cohort')

model_directions_1 = f"\n\nThe mathematical model and virtual cohorts are linked in this simulator. When a model is chosen, the associated virtual subjects that have been generated are chosen as well. " +\
					f"This means that choosing a model selects a type of diabetes, a specific model, and a virtual cohort together."

model_directions_2 = f"\n\nThe model is chosen with the {color_command_text('cohort')} command followed by the option {color_command_text('-mn')} and a valid model name. " +\
					f"The default model is T2DM.Jauslin - a type 2 diabetes model. This can be selected using the command {color_command_text('cohort -mn T2DM.Jauslin')}"


model_directions_3 = f"\n\nSeveral type 1 and type 2 diabetes models are available. {color_command_text('T1DM.IVP')} is a simple, 4-state type 1 diabetes model. {color_command_text('T1DM.Hovorka')} is an extended Hovorka model for type 1 diabetes capturing physical activity. " + \
						f"{color_command_text('T2DM.Jauslin')} is a type 2 diabetes model incorportating endogenous insulin secretion. Please see either {color_command_text('cohort -h')} or the online documentation for more details."


model_directions = model_directions_title + model_directions_1 + model_directions_2 + model_directions_3 + '\n'


"""
Input Directions
"""

input_directions_title = color_group_header_text('\n>>>>> Choosing Inputs')

input_directions_1 = f"\n\nThere are several inputs available for the models. Currently, some of the inputs are common between models while others are model-specific. "

input_directions_2 = f"\n\nThe common inputs are meal and snack carbohydrates, which are given in grams either as a single, constant value or as a range for random sampling. " +\
						"Meals are given between 06:00-08:00 (breakfast), 12:00-14:00 (lunch), and 18:00-20:00 (dinner) between 30-60 minutes. A morning snack can be given between 09:00-11:00 " + \
						"and an afternoon snack can be given between 15:00-17:00. Snacks are between 5-15 minutes long."

input_directions_3 = f"The type 1 diabetes-specific model inputs are basal and bolus insulin, which are simply activated or deactivated and dosed based on meals and subject characteristics. "

input_directions_4 = f"The type 2 diabetes-specific model input is a sodium-glucose cotransporter-2 inhibitor, which is given in milligrams and dosed once-daily between 06:00 and 09:00."

input_directions_5 = f"\n\nThe model inputs are selected using the {color_command_text('inputs')} command. Use {color_command_text('inputs -h')} to learn more."

input_directions = input_directions_title + input_directions_1 + input_directions_2 + input_directions_3 + input_directions_4 + input_directions_5 + '\n'



"""
Simulate Directions
"""

simulate_directions_title = color_group_header_text('\n>>>>> Running Simulation')

simulation_directions_1 = f"\n\nThe {color_command_text('simulate')} command has a single argument for formatting the model results in Microsoft Excel format. " +\
							f"Running {color_command_text('simulate')} will run a simulation with the " + \
							"currently-defined settings. If no other commands have been used, then a default simulation is run. These settings are displayed when the simulation is run."

simulate_directions = simulate_directions_title + simulation_directions_1 + '\n'


"""
Plotting Directions
"""

plot_directions_title = color_group_header_text('\n>>>>> Plotting Results')

plot_directions_1 = f"\n\nThe plotting module generates all available plots by default when {color_command_text('plot')} is run regardless of the options used. " + \
					"These plots are stored along with the simulation results. Commands can be used to select which of the generated plots are displayed. " + \
					"The other options are used to change display settings such as color and figure size."

plot_directions_2 = f"\n\nUse {color_command_text('plot -h')} to learn more."

plot_directions = plot_directions_title + plot_directions_1 + plot_directions_2 + '\n'