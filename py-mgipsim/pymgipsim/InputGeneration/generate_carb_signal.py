import numpy as np
from pymgipsim.Probability.pdfs_samplers import sample_generator
from pymgipsim.Utilities.units_conversions_constants import UnitConversion
from pymgipsim.InputGeneration.signal import Events
from pymgipsim.Utilities.Scenario import scenario
from itertools import repeat

def generate_carb_ranges_multiscale(scenario_instance):

    fraction_of_cho_meals = 1 - np.array(scenario_instance.input_generation.fraction_cho_as_snack)

    total_meal_cho = []
    total_snack_cho = []
    for i in range(len(scenario_instance.input_generation.total_carb_range)):

        total_meal_cho.append(list(fraction_of_cho_meals * np.array(scenario_instance.input_generation.total_carb_range[i])))
        total_snack_cho.append(list(np.array(scenario_instance.input_generation.fraction_cho_as_snack) * np.array(scenario_instance.input_generation.total_carb_range[i])))

    return list(total_meal_cho), list(total_snack_cho)

def generate_carb_magnitudes_singlescale(scenario_instance, number_of_days):

    """ Meal Magnitude """
    value_limits = [scenario_instance.input_generation.breakfast_carb_range,
                    scenario_instance.input_generation.lunch_carb_range,
                    scenario_instance.input_generation.dinner_carb_range
                    ]

    distribution = ['uniform'] * 3
    samples_size = [(scenario_instance.patient.number_of_subjects, number_of_days)] * len(value_limits)

    rng_generator = np.random.default_rng(scenario_instance.settings.random_seed)
    rng_generator.bit_generator.state = scenario_instance.settings.random_state
    breakfast, lunch, dinner = map(sample_generator, value_limits, distribution, samples_size, repeat(rng_generator))
    scenario_instance.settings.random_state = rng_generator.bit_generator.state


    breakfast_magnitude_samples, lunch_magnitude_samples, dinner_magnitude_samples = breakfast[-1], lunch[-1], dinner[-1]
    combined_meal_magnitudes = np.concatenate((breakfast_magnitude_samples, lunch_magnitude_samples, dinner_magnitude_samples), axis = -1)

    """ Snack Magnitude """
    value_limits = [scenario_instance.input_generation.am_snack_carb_range,
                    scenario_instance.input_generation.pm_snack_carb_range,
                    ]

    distribution = ['uniform'] * 3
    samples_size = [(scenario_instance.patient.number_of_subjects, number_of_days)] * len(value_limits)

    rng_generator = np.random.default_rng(scenario_instance.settings.random_seed)
    rng_generator.bit_generator.state = scenario_instance.settings.random_state
    am_snack_magnitude, pm_snack_magnitude = map(sample_generator, value_limits, distribution, samples_size, repeat(rng_generator))
    scenario_instance.settings.random_state = rng_generator.bit_generator.state


    am_snack_magnitude_samples = am_snack_magnitude[-1]
    pm_snack_magnitude_sample = pm_snack_magnitude[-1]

    combined_snack_magnitudes = np.concatenate((am_snack_magnitude_samples, pm_snack_magnitude_sample), axis = -1)

    return combined_meal_magnitudes, combined_snack_magnitudes

def generate_carb_magnitudes_multiscale(scenario_instance, number_of_days, combined_meal_times, combined_snack_times):

    for i in range(scenario_instance.patient.number_of_subjects):

        """ Meal Magnitude """
        value_limits = [scenario_instance.input_generation.breakfast_carb_range[i],
                        scenario_instance.input_generation.lunch_carb_range[i],
                        scenario_instance.input_generation.dinner_carb_range[i]
                        ]

        distribution = ['uniform'] * 3
        samples_size = [(1, number_of_days)] * len(value_limits)

        rng_generator = np.random.default_rng(scenario_instance.settings.random_seed)
        rng_generator.bit_generator.state = scenario_instance.settings.random_state
        breakfast, lunch, dinner = map(sample_generator, value_limits, distribution, samples_size, repeat(rng_generator))
        scenario_instance.settings.random_state = rng_generator.bit_generator.state
        breakfast_magnitude_samples, lunch_magnitude_samples, dinner_magnitude_samples = breakfast[-1], lunch[-1], dinner[-1]

        if i == 0:
            combined_meal_magnitudes = np.concatenate((breakfast_magnitude_samples, lunch_magnitude_samples, dinner_magnitude_samples), axis = -1)

        else:
            combined_meal_magnitudes = np.vstack((combined_meal_magnitudes, np.concatenate((breakfast_magnitude_samples, lunch_magnitude_samples, dinner_magnitude_samples), axis = -1)))


        """ Snack Magnitude """
        value_limits = [scenario_instance.input_generation.am_snack_carb_range[i],
                        scenario_instance.input_generation.pm_snack_carb_range[i]
                        ]

        distribution = ['uniform'] * len(value_limits)
        samples_size = [(1, number_of_days)] * len(value_limits)

        rng_generator = np.random.default_rng(scenario_instance.settings.random_seed)
        rng_generator.bit_generator.state = scenario_instance.settings.random_state
        am_snack, pm_snack = map(sample_generator, value_limits, distribution, samples_size, repeat(rng_generator))
        scenario_instance.settings.random_state = rng_generator.bit_generator.state
        am_snack_magnitude_samples, pm_snack_magnitude_samples = am_snack[-1], pm_snack[-1]

        if i == 0:
            combined_snack_magnitudes = np.concatenate((am_snack_magnitude_samples, pm_snack_magnitude_samples), axis = -1)

        else:
            combined_snack_magnitudes = np.vstack((combined_snack_magnitudes, np.concatenate((am_snack_magnitude_samples, pm_snack_magnitude_samples), axis = -1)))

    return combined_meal_magnitudes, combined_snack_magnitudes

def calculate_meal_time_samples(scenario_instance, number_of_days):

    value_limits = [
                    scenario_instance.input_generation.breakfast_time_range,
                    scenario_instance.input_generation.lunch_time_range,
                    scenario_instance.input_generation.dinner_time_range
                    ]

    distribution = ['uniform'] * 3
    samples_size = [(scenario_instance.patient.number_of_subjects, number_of_days)] * 3



    rng_generator = np.random.default_rng(scenario_instance.settings.random_seed)
    rng_generator.bit_generator.state = scenario_instance.settings.random_state
    breakfast, lunch, dinner = map(sample_generator, value_limits, distribution, samples_size, repeat(rng_generator))
    scenario_instance.settings.random_state = rng_generator.bit_generator.state

    breakfast_start_samples, lunch_start_samples, dinner_start_samples = breakfast[-1].astype(float), lunch[-1].astype(float), dinner[-1].astype(float)

    breakfast_start_samples += UnitConversion.time.calculate_time_adjustment_array(
                                                                                breakfast_start_samples.shape,
                                                                                )
    
    lunch_start_samples += UnitConversion.time.calculate_time_adjustment_array(
                                                                            lunch_start_samples.shape,
                                                                            )

    dinner_start_samples += UnitConversion.time.calculate_time_adjustment_array(
                                                                            dinner_start_samples.shape,
                                                                            )

    return np.concatenate((breakfast_start_samples, lunch_start_samples, dinner_start_samples), axis = -1)

def calculate_snack_time_samples(scenario_instance, number_of_days):

    value_limits = [scenario_instance.input_generation.am_snack_time_range,
                    scenario_instance.input_generation.pm_snack_time_range
                    ]

    distribution = ['uniform'] * 2
    samples_size = [(scenario_instance.patient.number_of_subjects, number_of_days)] * 2

    rng_generator = np.random.default_rng(scenario_instance.settings.random_seed)
    rng_generator.bit_generator.state = scenario_instance.settings.random_state
    am_snack_start_time, pm_snack_start_time = map(sample_generator, value_limits, distribution, samples_size, repeat(rng_generator))
    scenario_instance.settings.random_state = rng_generator.bit_generator.state


    am_snack_start_time_samples = am_snack_start_time[-1].astype(float)
    pm_snack_start_time_samples = pm_snack_start_time[-1].astype(float)


    am_snack_start_time_samples += UnitConversion.time.calculate_time_adjustment_array(
                                                                                        am_snack_start_time_samples.shape,
                                                                                        )

    pm_snack_start_time_samples += UnitConversion.time.calculate_time_adjustment_array(
                                                                                        pm_snack_start_time_samples.shape,
                                                                                        )

    return np.concatenate((am_snack_start_time_samples, pm_snack_start_time_samples), axis = -1)


def generate_carb_events(scenario_instance: scenario, args):

    number_of_days = int(UnitConversion.time.convert_minutes_to_days(scenario_instance.settings.end_time - scenario_instance.settings.start_time))

    ####################################################### Meal and Snack Start Times
    """ Meal Start Time """
    combined_meal_times = calculate_meal_time_samples(scenario_instance, number_of_days)

    """ Snack Start Time """
    combined_snack_times = calculate_snack_time_samples(scenario_instance, number_of_days)

    ####################################################### Meal and Snack Duration
    value_limits = [scenario_instance.input_generation.meal_duration,
                    scenario_instance.input_generation.snack_duration,
                    ]

    distribution = ['uniform'] * 2
    samples_size = [combined_meal_times.shape, combined_snack_times.shape]

    rng_generator = np.random.default_rng(scenario_instance.settings.random_seed)
    rng_generator.bit_generator.state = scenario_instance.settings.random_state
    meal_duration, snack_duration = map(sample_generator, value_limits, distribution, samples_size, repeat(rng_generator))
    scenario_instance.settings.random_state = rng_generator.bit_generator.state

    meal_duration_samples, snack_duration_samples = meal_duration[-1], snack_duration[-1]


    ####################################################### Magnitudes

    if scenario_instance.settings.simulator_name == "MultiScaleSolver":
        combined_meal_magnitudes, combined_snack_magnitudes = generate_carb_magnitudes_multiscale(scenario_instance, number_of_days, combined_meal_times,combined_snack_times)
    else:
        combined_meal_magnitudes, combined_snack_magnitudes = generate_carb_magnitudes_singlescale(scenario_instance, number_of_days)


    ####################################################### Events

    # Sort Meal times and magnitudes
    meal_ascending_order_index_by_subject = np.argsort(combined_meal_times, axis = -1)
    snack_ascending_order_index_by_subject = np.argsort(combined_snack_times, axis = -1)

    meal_events = Events()
    snack_events = Events()

    for name, meal_arr, snack_arr in zip(['magnitude', 'start_time', 'duration'],
                                        [combined_meal_magnitudes, combined_meal_times, meal_duration_samples],
                                        [combined_snack_magnitudes, combined_snack_times, snack_duration_samples]
                                        ):

        setattr(meal_events, name, np.take_along_axis(meal_arr,
                                                    meal_ascending_order_index_by_subject,
                                                    axis = -1)
                )

        setattr(snack_events, name, np.take_along_axis(snack_arr,
                                                    snack_ascending_order_index_by_subject,
                                                    axis = -1)
                )

    return meal_events.as_dict(), snack_events.as_dict()