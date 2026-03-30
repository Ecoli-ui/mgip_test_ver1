from pymgipsim.InputGeneration.signal import Events
from pymgipsim.Utilities.Scenario import scenario
from pymgipsim.Probability.pdfs_samplers import sample_generator
from pymgipsim.Utilities.units_conversions_constants import UnitConversion
import numpy as np



def activity_args_to_scenario(scenario_instance: scenario, args):
    scenario_instance.input_generation.running_start_time = args.running_start_time
    scenario_instance.input_generation.running_duration = args.running_duration
    scenario_instance.input_generation.running_incline = args.running_incline
    scenario_instance.input_generation.running_speed = args.running_speed
    scenario_instance.input_generation.cycling_start_time = args.cycling_start_time
    scenario_instance.input_generation.cycling_duration = args.cycling_duration
    scenario_instance.input_generation.cycling_power = args.cycling_power

def time_str_to_float(times):
    transformed = times
    if type(times[0]) is str:
        transformed = [[float(x) for x in val.split(':')] for val in times]
        transformed = [val[0] * 60 + val[1] for val in transformed]
    return transformed

def generate_activities(scenario_instance: scenario, args):
    number_of_days = int(UnitConversion.time.convert_minutes_to_days(scenario_instance.settings.end_time - scenario_instance.settings.start_time))
    no_subjects = scenario_instance.patient.number_of_subjects

    running_start_time = scenario_instance.input_generation.running_start_time
    running_duration = scenario_instance.input_generation.running_duration
    running_incline = scenario_instance.input_generation.running_incline
    running_speed = scenario_instance.input_generation.running_speed
    cycling_start_time = scenario_instance.input_generation.cycling_start_time
    cycling_duration = scenario_instance.input_generation.cycling_duration
    cycling_power = scenario_instance.input_generation.cycling_power


    rng_generator = np.random.default_rng(scenario_instance.settings.random_seed)
    rng_generator.bit_generator.state = scenario_instance.settings.random_state
    running_start_time = sample_generator(time_str_to_float(running_start_time), "uniform", (no_subjects, number_of_days), rng_generator)[-1]
    running_start_time += UnitConversion.time.calculate_time_adjustment_array(running_start_time.shape)
    cycling_start_time = sample_generator(time_str_to_float(cycling_start_time), "uniform", (no_subjects, number_of_days), rng_generator)[-1]
    cycling_start_time += UnitConversion.time.calculate_time_adjustment_array(cycling_start_time.shape)

    running_duration = sample_generator(running_duration, "uniform", (no_subjects, number_of_days), rng_generator)[-1]
    cycling_duration = sample_generator(cycling_duration, "uniform", (no_subjects, number_of_days), rng_generator)[-1]

    cycling_power = sample_generator(cycling_power, "uniform", (no_subjects, number_of_days), rng_generator)[-1]
    cycling_power = Events(start_time=cycling_start_time, duration=cycling_duration, magnitude=cycling_power).as_dict()

    running_speed = sample_generator(running_speed, "uniform", (no_subjects, number_of_days), rng_generator)[-1]
    running_incline = sample_generator(running_incline, "uniform", (no_subjects, number_of_days), rng_generator)[-1]
    running_speed = Events(start_time=running_start_time, duration=running_duration, magnitude=running_speed).as_dict()
    running_incline = Events(start_time=running_start_time, duration=running_duration, magnitude=running_incline).as_dict()

    scenario_instance.settings.random_state = rng_generator.bit_generator.state


    return running_speed, running_incline, cycling_power