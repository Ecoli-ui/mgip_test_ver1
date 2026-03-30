import argparse
from pymgipsim.Interface.Messages.parser_colors import color_help_text, color_group_header_text


def generate_plot_parser(parent_parser = [], add_help = True):

	parser = argparse.ArgumentParser(
	                                prog = 'Plots',
	                                formatter_class=argparse.ArgumentDefaultsHelpFormatter,
	                                parents=parent_parser,
	                                add_help=add_help
	                                )

	plot_group = parser.add_argument_group(title = color_group_header_text('Specific Plots'))
	plot_group.add_argument('-pbg',
							'--blood-glucose',
							dest = 'plot_blood_glucose',
							help = color_help_text('Display population blood glucose concentration.'),
							action = 'store_true'
							)

	plot_group.add_argument('-pas',
							'--all-states',
							dest = 'plot_all_states',
							help = color_help_text('Display all models states.'),
							action = 'store_true'
							)
	
	plot_group.add_argument('-pis',
							'--input_signals',
							dest = 'plot_input_signals',
							help = color_help_text('Display all models input signals.'),
							action = 'store_true'
							)


	plot_group.add_argument('-pat',
							'--patient',
							dest = 'plot_patient',
							type=int,
							help = color_help_text('Display blood glucose and inputs for a single subject.')
							)

	plot_group.add_argument('-pa',
							'--all',
							dest = 'plot_all',
							action = 'store_true',
							help = color_help_text('Display all plots.')

							)

	plot_group.add_argument('-pbw',
							'--body-weight',
							dest = 'plot_body_weight',
							help = color_help_text('Display body weight.'),
							action = 'store_true'
							)

	
	plot_options_group = parser.add_argument_group(title = color_group_header_text('Plot Design Options'))
	plot_options_group.add_argument('-fis', '--fig-size', dest='figsize', nargs = 2, default = [12, 6], type = int, help = color_help_text('Set figure size (width, height'))
	plot_options_group.add_argument('-c', '--color', dest='color', choices = ['blue', 'orange', 'red', 'green', 'black'], default = 'blue', type = str, help = color_help_text('Set line color'))


	return parser


def generate_plot_parser_multiscale(parent_parser = [], add_help = True):

	parser = argparse.ArgumentParser(
	                                prog = 'Plots',
	                                formatter_class=argparse.ArgumentDefaultsHelpFormatter,
	                                parents=parent_parser,
	                                add_help=add_help
	                                )

	plot_group = parser.add_argument_group(title = color_group_header_text('Specific Plots'))

	plot_group.add_argument('-pbw',
							'--body-weight',
							dest = 'plot_body_weight',
							help = color_help_text('Display body weight.'),
							action = 'store_true'
							)
	
	return parser
