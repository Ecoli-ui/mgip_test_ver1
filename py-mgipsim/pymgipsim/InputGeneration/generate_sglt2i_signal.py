import numpy as np
from pymgipsim.Probability.pdfs_samplers import sample_generator
from pymgipsim.Utilities.units_conversions_constants import UnitConversion
from .sglt2i_settings import make_sglt2i_settings
from pymgipsim.Utilities.Scenario import scenario
from .signal import Events
from itertools import repeat

def generate_sglt2i_events(scenario_instance: scenario, args):

	scenario_instance = make_sglt2i_settings(scenario_instance = scenario_instance, args = args)

	number_of_days = int(UnitConversion.time.convert_minutes_to_days(scenario_instance.settings.end_time - scenario_instance.settings.start_time))

	value_limits = [scenario_instance.input_generation.sglt2i_dose_time_range,
	                scenario_instance.input_generation.sglt2i_dose_magnitude,
	                ]

	distribution = ['uniform'] * 2
	samples_size = [(scenario_instance.patient.number_of_subjects, number_of_days)] * 2

	rng_generator = np.random.default_rng(scenario_instance.settings.random_seed)
	rng_generator.bit_generator.state = scenario_instance.settings.random_state
	dose_start_time, dose_magnitude = map(sample_generator, value_limits, distribution, samples_size, repeat(rng_generator))
	scenario_instance.settings.random_state = rng_generator.bit_generator.state

	dose_start_time_samples, dose_magnitude_samples = dose_start_time[-1].astype(float), dose_magnitude[-1].astype(float)

	dose_start_time_samples += UnitConversion.time.calculate_time_adjustment_array(
																				dose_start_time_samples.shape,
																				)

	return Events(start_time=dose_start_time_samples,
	                       duration=np.full_like(dose_magnitude_samples, scenario_instance.settings.sampling_time),
	                        magnitude=dose_magnitude_samples
	                        ).as_dict()