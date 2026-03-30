import traceback, json
from tabulate import tabulate
import copy
import os

import matplotlib.pyplot as plt
from pymgipsim.Utilities.Scenario import scenario

from pymgipsim.Settings.parser import generate_settings_parser
from pymgipsim.Utilities import simulation_folder

from pymgipsim.VirtualPatient.parser import generate_virtual_subjects_parser, generate_results_parser
from pymgipsim.InputGeneration.activity_settings import activity_args_to_scenario

from pymgipsim.Utilities.paths import default_settings_path, results_path
from pymgipsim.Utilities.parser import generate_load_parser
from pymgipsim.Utilities.simulation_folder import load_settings_file

from pymgipsim.Interface.BaseClassesCMD import SimulatorCMD
from pymgipsim.InputGeneration.carb_energy_settings import make_carb_settings
from pymgipsim.InputGeneration.parsers import generate_activity_parser, generate_sglt2i_settings_parser, generate_exog_insulin_parser, generate_carb_settings_parser, generate_multiscale_carb_settings_parser
from pymgipsim.Controllers.parser import generate_controller_settings_parser
from pymgipsim.Interface.parser import directions_parser
from pymgipsim.Interface.Messages.cmd_directions import *


from pymgipsim.Plotting.parser import generate_plot_parser

from pymgipsim.generate_settings import generate_simulation_settings_main
from pymgipsim.generate_subjects import generate_virtual_subjects_main
from pymgipsim.generate_inputs import generate_inputs_main
from pymgipsim.generate_plots import generate_plots_main
from pymgipsim.generate_results import generate_results_main
from pymgipsim.Utilities.units_conversions_constants import UnitConversion
from pymgipsim.VirtualPatient.Models import T1DM


def add_hints(table, hints):
    table = [[row[0] + " (" + hint + ")", row[1]] for row, hint in zip(table, hints)]
    return table

class SimulatorCLI(SimulatorCMD):

	""" """
	def __init__(self):
		SimulatorCMD.__init__(self)
		self.do_settings('', print_info=True)
		self.do_activity('', print_info=False)

	def do_settings(self, line, print_info = True):
		"""
		This method generates the simulation settings.
		"""

		# Print a message indicating that simulation settings are being updated
		try:
			if self.model_output:
				results_directory = simulation_folder.create_simulation_results_folder(results_path)[-1]
				self.model_output = None

			# Parse command-line arguments using the created parser
			flags = [self.settings_args.multi_scale, self.settings_args.profile, self.settings_args.no_print, self.settings_args.no_progress_bar]
			self.settings_args = generate_settings_parser(add_help=True, flags = flags).parse_known_args(line.split(), self.settings_args)[0]
			hints = [k.option_strings[0] for k in generate_settings_parser(add_help=False)._actions]

			# Define the simulation settings
			self.simulation_scenario = generate_simulation_settings_main(self.simulation_scenario, self.settings_args, self.results_directory)

			self.settings_table = [[k, v] if v == self.settings_args_prev[k] else [color_modified_text(k), v] for k, v in vars(self.settings_args).items()]
			self.settings_table = add_hints(self.settings_table, hints)

			self.do_cohort(line='', print_info = False)

			if print_info:
				print(self.generate_table())

		except Exception as error:
			# Print any exceptions with traceback in case of an error
			print(traceback.format_exc())

		except:
			# Handle other exceptions if any
			pass

	def do_cohort(self, line, print_info = True):
		"""
		This method generates the virtual subject cohort, which includes the specific mathematical model and type of diabetes.
		"""
		try:

			if self.model_output:
				self.results_directory = simulation_folder.create_simulation_results_folder(results_path)[-1]
				self.model_output = None

			# Check if simulation settings parser is not available, and if so, run the settings command to generate them
			self.cohort_args = generate_virtual_subjects_parser(add_help = True).parse_known_args(line.split(), self.cohort_args)[0]
			hints = [k.option_strings[0] for k in generate_virtual_subjects_parser(add_help=False)._actions]
			self.cohort_args.no_progress_bar = self.settings_args.no_progress_bar
			self.cohort_args.no_print = self.settings_args.no_print

			# Generate cohort
			self.simulation_scenario = generate_virtual_subjects_main(self.simulation_scenario, self.cohort_args, self.results_directory)

			cohort_plot = copy.deepcopy(vars(self.cohort_args))
			del cohort_plot["no_progress_bar"]
			del cohort_plot["no_print"]

			self.cohort_table = [[k, v] if (v == self.cohort_args_prev[k]) else [color_modified_text(k), v] for k, v in cohort_plot.items()]
			self.cohort_table = add_hints(self.cohort_table, hints)

			self.do_inputs(line='', print_info=False)
			self.do_activity(line='', print_info=False)

			if print_info:
				print(self.generate_table())

		except Exception as error:
			# Print any exceptions with traceback in case of an error
			print(traceback.format_exc())


		except:
			# Handle other exceptions if any
			pass

	def do_inputs(self, line, print_info = True):
		"""
		This method generates the carbohydrate and drug intake settings.
		"""
		try:

			if self.model_output:
				self.results_directory = simulation_folder.create_simulation_results_folder(results_path)[-1]
				self.model_output = None

			# Check if cohort parser is not available, and if so, run the settings command to generate them
			parent_parser = [generate_controller_settings_parser(add_help=False),
							 generate_exog_insulin_parser(add_help=False),
							 generate_sglt2i_settings_parser(add_help=False)]
			self.inputs_parser = generate_carb_settings_parser(add_help=True, parent_parser=parent_parser)
			if self.settings_args.multi_scale:
				self.inputs_parser = generate_multiscale_carb_settings_parser(add_help=False, parent_parser=[self.inputs_parser])
			self.input_args = self.inputs_parser.parse_known_args(line.split(), self.input_args)[0]
			make_carb_settings(self.simulation_scenario, self.input_args)
			self.input_args.no_progress_bar = self.settings_args.no_progress_bar
			hint_actions = self.inputs_parser._actions[1:]

			input_plot = copy.deepcopy(vars(self.input_args))
			if "T2DM" not in self.simulation_scenario.patient.model.name:
				del input_plot["sglt2i_dose_magnitude"]
				hint_actions = [action for action in hint_actions if (action.dest != 'sglt2i_dose_magnitude')]
			if "T1DM" not in self.simulation_scenario.patient.model.name or self.simulation_scenario.controller.name != "OpenLoop":
				del input_plot["bolus_multiplier"]
				del input_plot["basal_multiplier"]
				hint_actions = [action for action in hint_actions if
								(action.dest != 'bolus_multiplier' and action.dest != 'basal_multiplier')]
			del input_plot["no_progress_bar"]

			hints = [k.option_strings[0] for k in hint_actions]

			self.input_table = [[k, v] if (k in self.input_args_prev and v == self.input_args_prev[k]) else [color_modified_text(k), v] for k, v in input_plot.items()]
			self.input_table = add_hints(self.input_table, hints)

			if print_info:
				print(self.generate_table())

		except Exception as error:
			# Print any exceptions with traceback in case of an error
			print(traceback.format_exc())

		except:
			# Handle other exceptions if any
			pass

	def do_activity(self, line, print_info = True):
		"""
		This method generates the carbohydrate and drug intake settings.
		"""
		try:

			if self.model_output:
				self.results_directory = simulation_folder.create_simulation_results_folder(results_path)[-1]
				self.model_output = None

			self.activity_args = generate_activity_parser(add_help = True).parse_known_args(line.split(), self.activity_args)[0]
			hints = [k.option_strings[0] for k in generate_activity_parser(add_help=False)._actions]
			activity_args_to_scenario(self.simulation_scenario, self.activity_args)
			self.activity_args.no_progress_bar = self.settings_args.no_progress_bar

			activity_plot = copy.deepcopy(vars(self.activity_args))
			del activity_plot["no_progress_bar"]

			self.activity_table = [[k, v] if (v == self.activity_args_prev[k]) else [color_modified_text(k), v] for k, v in activity_plot.items()]
			self.activity_table = add_hints(self.activity_table, hints)

			if print_info:
				print(self.generate_table())

		except Exception as error:
			# Print any exceptions with traceback in case of an error
			print(traceback.format_exc())

		except:
			# Handle other exceptions if any
			pass

	def do_simulate(self, line, print_info = True):
		"""
		This method runs the defined simulation. 
		"""

		try:

			self.results_args = generate_results_parser(add_help = True).parse_known_args(line.split(), self.results_args)[0]

			if self.model_output:
				self.results_directory = simulation_folder.create_simulation_results_folder(results_path)[-1]
				self.model_output = None

			# self.do_inputs(line='', print_info = False)
			self.input_args.no_print = self.settings_args.no_print
			self.simulation_scenario = generate_inputs_main(self.simulation_scenario, self.input_args, self.results_directory)
			del self.input_args.no_print

			self.combined_args = vars(self.settings_args).copy()
			self.combined_args.update(vars(self.cohort_args))
			self.combined_args.update(vars(self.input_args))
			self.combined_args.update(vars(self.activity_args))
			self.combined_args.update(vars(self.results_args))

			if print_info:
				print(tabulate([[k, v] for k, v in self.combined_args.items()], headers = ['Setting', 'Value'], tablefmt = 'outline', floatfmt=".4f", colalign = ['center', 'center']))

			self.model_output,_ = generate_results_main(scenario_instance = self.simulation_scenario, args = self.combined_args, results_folder_path = self.results_directory)

			self.results_list.append(self.results_directory)

			# with open(self.results_directory + "\\model.pkl", 'wb') as f:
			# 	pickle.dump(self.model_output, f)

		except Exception as error:
			# Print any exceptions with traceback in case of an error
			print(traceback.format_exc())

		except:
			# Handle other exceptions if any
			pass

	def do_load(self, line):
		"""
		Can be used to load already saved scenarios from the ./Scenarios folder.
		"""

		try:

			load_parser = generate_load_parser()
			args = load_parser.parse_args(line.split())

			self.simulation_scenario = load_settings_file(args, self.results_directory)
			self.settings_args.sampling_time = self.simulation_scenario.settings.sampling_time
			self.settings_args.number_of_days = UnitConversion.convert_minutes_to_days((self.simulation_scenario.settings.end_time - self.simulation_scenario.settings.start_time))
			self.cohort_args.number_of_subjects = self.simulation_scenario.patient.number_of_subjects
			self.cohort_args.model_name = self.simulation_scenario.patient.model.name
			self.cohort_args.patient_names = self.simulation_scenario.patient.files

		except Exception as error:
			args.scenario_name = None
			print(traceback.format_exc())
		except:
			args.scenario_name = None
		
		self.do_inputs('')

	def do_directions(self, line):

		"""
		Directions for using the simulator.
		"""

		try:
			args = directions_parser.parse_args(line.split())

			if not any(d == True for d in vars(args).values()):
				print(initial_directions)

			if args.directions_verbose or args.directions_parser:
				print(parser_directions)

			if args.directions_verbose or args.directions_cmd:
				print(cmd_directions)

			if args.directions_verbose or args.directions_model:
				print(model_directions)

			if args.directions_verbose or args.directions_inputs:
				print(input_directions)

			if args.directions_verbose or args.directions_simulate:
				print(simulate_directions)

			if args.directions_verbose or args.directions_plot:
				print(plot_directions)

		except Exception as error:
			# Print any exceptions with traceback in case of an error
			print(traceback.format_exc())

		except:
			# Handle other exceptions if any
			pass

	def do_plot(self, line):
		"""
		This method generates the plots. Running <plot> with no arguments will save the plots without displaying them.
		Otherwise, choosing a plot (or plots) with an argument will save them and produce dynamic matplotlib plots.
		Enter <plot -h> to see a list of arguments and input values.
		"""

		try:
			plotting_parser = generate_plot_parser()
			args = plotting_parser.parse_args(line.split())
			args.no_progress_bar = self.settings_args.no_progress_bar
			args.no_print = self.settings_args.no_print
			args.multi_scale = self.settings_args.multi_scale


			if not self.model_output:
				print(f"Run the {color_command_text('simulate')} command before producing and plots")

			else:
				generate_plots_main(self.results_directory, args)
	
				plt.show()

		except Exception as error:
			# Print any exceptions with traceback in case of an error
			print(traceback.format_exc())

		except:
			# Handle other exceptions if any
			pass

	def generate_table(self):
		# print("\n")
		tables = []
		tables.append(
			str((tabulate(self.settings_table, headers=['Option', 'Value'], tablefmt='outline', floatfmt=".1f",
						  colalign=['center', 'center'], disable_numparse=True))).splitlines())
		tables.append(str((tabulate(self.cohort_table, headers=['Option', 'Value'], tablefmt='outline', floatfmt=".4f",
									colalign=['center', 'center']))).splitlines())
		tables.append(str(tabulate(self.input_table, headers=['Option', 'Value'], tablefmt='outline', floatfmt=".4f",
								   colalign=['center', 'center'])).splitlines())
		if self.simulation_scenario.patient.model.name == T1DM.ExtHovorka.Model.name:
			tables.append(
				str(tabulate(self.activity_table, headers=['Option', 'Value'], tablefmt='outline', floatfmt=".4f",
							 colalign=['center', 'center'])).splitlines())
		max_len = max((lambda x: [len(i) for i in x])(tables))

		# Adds empty rows to match the longest table
		[table.extend([table[-1] for i in range(max_len - len(table))]) for table in tables]
		master_headers = [color_group_header_text('> Settings'), color_group_header_text('> Cohort'),
						  color_group_header_text('> Inputs')]
		if self.simulation_scenario.patient.model.name == T1DM.ExtHovorka.Model.name:
			master_headers.append(color_group_header_text('> Activities'))
		master_table = tabulate([list(item) for item in zip(*tables)],
								master_headers, tablefmt="simple")

		return master_table

	def do_reset(self, arg = None):
		""" Resets the scenario to the default one. """
		self.settings_args = generate_settings_parser(add_help=True).parse_args('')
		self.cohort_args = None
		self.input_args = None
		self.model_output = None
		self.simulation_args = None
		self.results_args = None
		self.plotting_args = None
		self.activity_table = [["",""]]
		self.simulation_scenario.input_generation = None
		self.simulation_scenario.inputs = None

		self.results_list = []

		with open(os.path.join(default_settings_path, "scenario_default.json"), "r") as f:  #
			self.simulation_scenario = scenario(**json.load(f))
		f.close()

		self.do_settings('')



if __name__ == '__main__':
	SimulatorCLI().cmdloop()
