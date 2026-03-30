from pymgipsim.Utilities.Scenario import scenario
from pymgipsim.VirtualPatient import Models
import numpy as np
from pymgipsim.Utilities.units_conversions_constants import UnitConversion
from pymgipsim.InputGeneration.signal import Signal

class Controller:
    name = "StochasticOpenLoop"
    def __init__(self, scenario_instance: scenario):
        time = np.arange(scenario_instance.settings.start_time,scenario_instance.settings.end_time,scenario_instance.settings.sampling_time)
        self.basal_uncertainty = 1.0/20.0
        self.bolus_uncertainty = 1.0/1.5

        match scenario_instance.patient.model.name:
            case Models.T1DM.ExtHovorka.Model.name:
                rng = np.random.default_rng()
                basal = (1.0+rng.standard_normal((scenario_instance.patient.number_of_subjects,1))*self.basal_uncertainty)*np.asarray(scenario_instance.patient.demographic_info.basal)[:,None]
                scenario_instance.inputs.basal_insulin.magnitude = basal.tolist()
                converted = UnitConversion.insulin.Uhr_to_mUmin(basal)
                basal = Signal(time=time, sampling_time=scenario_instance.settings.sampling_time, start_time=scenario_instance.inputs.basal_insulin.start_time, magnitude=converted)


                meal_times = np.asarray(scenario_instance.inputs.meal_carb.start_time)
                meal_durations = np.asarray(scenario_instance.inputs.meal_carb.duration)
                meal_magnitudes = np.asarray(scenario_instance.inputs.meal_carb.magnitude)
                carb_insulin_ratio = np.expand_dims(np.asarray(scenario_instance.patient.demographic_info.carb_insulin_ratio), 1)

                bolus_magnitudes = (1.0 + rng.standard_normal(meal_magnitudes.shape)*self.bolus_uncertainty)*np.divide(meal_magnitudes, carb_insulin_ratio)
                bolus_magnitudes[bolus_magnitudes < 0.0] = 0.0
                scenario_instance.inputs.bolus_insulin.magnitude = bolus_magnitudes.tolist()

                converted = UnitConversion.insulin.U_to_mU(bolus_magnitudes)
                bolus = Signal(time=time, start_time=meal_times, duration=np.ones_like(meal_durations), magnitude=converted)

                self.insulin = Signal()
                self.insulin.sampled_signal = basal.sampled_signal + bolus.sampled_signal

                pass

    def run(self, measurements, inputs, states, sample):
        inputs[:, 3, sample] = self.insulin.sampled_signal[:, sample]
        return