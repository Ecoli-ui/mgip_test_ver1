import cmd, subprocess, json
import os
from pprint import pprint
from pymgipsim.Settings.parser import generate_settings_parser
from pymgipsim.Utilities import simulation_folder
from pymgipsim.Utilities.paths import default_settings_path, results_path
from pymgipsim.Utilities.Scenario import scenario
from pymgipsim.VirtualPatient.parser import generate_virtual_subjects_parser, generate_results_parser
from pymgipsim.InputGeneration.parsers import generate_activity_parser, generate_sglt2i_settings_parser, generate_exog_insulin_parser, generate_carb_settings_parser, generate_multiscale_carb_settings_parser
from pymgipsim.Controllers.parser import generate_controller_settings_parser
from pymgipsim.Interface.Messages.messages_headers import *


class SimulatorCMD(cmd.Cmd):

	print(f">>>>> Initializing CMD Interface")

	intro  = header_logo + intro_message_1 + intro_direction + intro_help 
	
	prompt = simulator_prompt
	file   = None
	""" Define Results Path """

	""" Initialization """
	subprocess.run(['python', 'initialization.py'])

	results_directory = simulation_folder.create_simulation_results_folder(results_path)[-1]

	""" Initialize Attributes """
	settings_args = generate_settings_parser(add_help = True).parse_args('')
	cohort_args = None
	input_args = None
	activity_args = None
	model_output = None
	simulation_args = None
	results_args = None
	plotting_args = None
	activity_table = [["",""]]

	results_list = []

	inputs_parser = generate_carb_settings_parser(add_help=True,
												  parent_parser=[generate_controller_settings_parser(add_help=False),
																 generate_exog_insulin_parser(add_help=False),
																 generate_sglt2i_settings_parser(add_help=False)])
	# inputs_parser = generate_sglt2i_settings_parser(add_help = True, parent_parser = [ generate_exog_insulin_parser(add_help = False), generate_carb_settings_parser(add_help = False)])

	settings_args_prev = vars(generate_settings_parser(add_help = True).parse_args(''))
	cohort_args_prev = vars(generate_virtual_subjects_parser(add_help = True).parse_args(''))
	input_args_prev = vars(inputs_parser.parse_args(''))
	activity_args_prev = vars(generate_activity_parser(add_help = True).parse_args(''))
	results_args_prev = vars(generate_results_parser(add_help = True).parse_args(''))

	with open(os.path.join(default_settings_path, "scenario_default.json"), "r") as f:
		simulation_scenario = scenario(**json.load(f))
	f.close()

	def __init__(self):
		cmd.Cmd.__init__(self)

	def close(self):
		if self.file:
			self.file.close()
			self.file = None


	def do_help(self, *args):
		"""
		Get help for a specific command
		"""
		cmd.Cmd.do_help(self, *args)

		if (len(args) == 1 or len(args) == 2) and args[0] != "" and args[0] != '-' and args[0] != '-h':
			help_topic = args[0]

		else:
			help_topic = 'topic'

		print("Use " + color_command_text(f'{help_topic} -h') + " to get the list of options for the " + color_command_text(f'{help_topic}') + " command")


	def do_quit(self, arg = None):

		"""
		This closes the simulator and runs the finalization program.
		"""

		if self.results_list:
			pprint(f"\n>>>>> The simulation results can be found in the directory {self.results_list}.", indent = 2)
		else:
			print(f"\n>>>>> No simulation results were saved.")


		print(closing_logo)

		""" Tear down simulation and save results """			

		self.close()
		# return True
		quit()


	""" Abstract Methods """

	# @abstractmethod
	# def do_directions(self, line):
	#
	# 	"""
	# 	Directions for using the simulator.
	# 	"""
	#
	# 	pass
	#
	# @abstractmethod
	# def do_settings(self, line):
	# 	pass
	#
	# @abstractmethod
	# def do_cohort(self, line):
	# 	pass
	#
	# @abstractmethod
	# def do_inputs(self, line):
	# 	pass
	#
	# @abstractmethod
	# def do_activity(self, line):
	# 	pass
	#
	# @abstractmethod
	# def do_simulate(self, line):
	# 	pass
	#
	# @abstractmethod
	# def do_reset(self, line):
	# 	pass
	#
	# @abstractmethod
	# def do_load(self, line):
	# 	pass