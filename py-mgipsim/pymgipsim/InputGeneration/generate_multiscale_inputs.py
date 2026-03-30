from pymgipsim.Utilities.units_conversions_constants import UnitConversion
from pymgipsim.Utilities.Scenario import scenario
from .signal import Events
import numpy as np

def generate_multiscale_inputs(scenario_instance: scenario):

    number_of_days = int(UnitConversion.time.convert_minutes_to_days(scenario_instance.settings.end_time - scenario_instance.settings.start_time))

    time = np.arange(0, number_of_days, scenario_instance.settings.sampling_time)

    start_time = time
    duration = scenario_instance.settings.sampling_time

    for index, (baseline_name, attribute_name) in enumerate(zip(
                                                            ['baseline_daily_energy_intake', 'baseline_daily_energy_expenditure', 'baseline_daily_urinary_glucose_excretion'],
                                                            ['daily_energy_intake', 'daily_energy_expenditure', 'daily_urinary_glucose_excretion']
                                                            )):
                    
        match attribute_name:
            case 'daily_energy_intake':
                if hasattr(scenario_instance.input_generation, attribute_name):
                    magnitude = getattr(scenario_instance.input_generation, attribute_name)
        
            case 'daily_energy_expenditure':
                if hasattr(scenario_instance.patient.demographic_info, baseline_name):
                    magnitude = getattr(scenario_instance.patient.demographic_info, baseline_name)

            case 'daily_urinary_glucose_excretion':
                if hasattr(scenario_instance.patient.demographic_info, baseline_name):
                    magnitude = getattr(scenario_instance.patient.demographic_info, baseline_name)

        magnitude = np.asarray(magnitude).reshape(-1,1)

        magnitude = np.tile(magnitude, (1, number_of_days))

        events = Events(start_time=np.full_like(magnitude, start_time), duration=np.full_like(magnitude, duration), magnitude=magnitude).as_dict()
    
        setattr(scenario_instance.inputs, attribute_name, events)

def generate_bodyweight_events(scenario_instance: scenario):

    time = np.arange(0, int(scenario_instance.settings.end_time - scenario_instance.settings.start_time), scenario_instance.settings.sampling_time)

    
    start_time = np.tile(time, (scenario_instance.patient.number_of_subjects, 1))

    magnitude=np.tile(np.ones_like(time), (scenario_instance.patient.number_of_subjects, 1))

    scenario_instance.inputs.bodyweighteffect = Events(start_time=start_time,
                                                                    magnitude=magnitude
                                                                    ).as_dict()