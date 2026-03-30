import numpy as np
from pymgipsim.Utilities.units_conversions_constants import UnitConversion
from pymgipsim.Utilities.Scenario import scenario
from pymgipsim.InputGeneration.signal import Signal
from pymgipsim.VirtualPatient.Models import T1DM


class Controller:
    name = "SAPT"

    def __init__(self, scenario_instance: scenario, target_glucose, state_units):
        self.demographic_info = scenario_instance.patient.demographic_info
        self.model_name = scenario_instance.patient.model.name
        self.target_glucose = target_glucose
        self.sampling_time = scenario_instance.settings.sampling_time
        self.previous_boluses = np.zeros((len(self.demographic_info.carb_insulin_ratio),1))
        self.previous_rescue_carbs = np.zeros((len(self.demographic_info.carb_insulin_ratio),1))
        time = np.arange(scenario_instance.settings.start_time,scenario_instance.settings.end_time,scenario_instance.settings.sampling_time)
        events = scenario_instance.inputs.meal_carb
        self.meal_announcement = Signal(time=time, sampling_time=scenario_instance.settings.sampling_time, duration=np.ones_like(events.duration),
                                        start_time=events.start_time, magnitude=scenario_instance.settings.sampling_time*np.asarray(events.magnitude))
        self.state_units = state_units
        self.bolus_uncertainty = None#1.0/1.5

        match self.model_name:
            case T1DM.ExtHovorka.Model.name:
                self.hyper_threshold = UnitConversion.glucose.concentration_mgdl_to_mmolL(200.0)
                self.hypo_threshold = UnitConversion.glucose.concentration_mgdl_to_mmolL(70.0)
                basal = np.expand_dims(np.asarray(scenario_instance.patient.demographic_info.basal), 1)
                start_time = np.ones_like(basal) * scenario_instance.settings.start_time
                converted = UnitConversion.insulin.Uhr_to_mUmin(basal)
                self.basal = Signal(time=time, sampling_time=scenario_instance.settings.sampling_time,start_time=start_time, magnitude=converted)
            case T1DM.IVP.Model.name:
                self.hyper_threshold = 200.0
                self.hypo_threshold = 70.0
                basal = np.expand_dims(np.asarray(scenario_instance.patient.demographic_info.basal), 1)
                start_time = np.ones_like(basal) * scenario_instance.settings.start_time
                converted = UnitConversion.insulin.Uhr_to_uUmin(basal)
                self.basal = Signal(time=time, sampling_time=scenario_instance.settings.sampling_time, start_time=start_time,magnitude=converted)
            case _:
                raise Exception(f"Unknown model name {self.model_name}")


    def run(self, measurements, inputs, states, sample):

        chos = self.meal_announcement.sampled_signal[:,sample]
        meal_ongoing_binmap = chos > np.finfo(float).eps
        rng = np.random.default_rng()
        if self.bolus_uncertainty is not None:
            ratio = (1.0+rng.standard_normal((len(self.demographic_info.carb_insulin_ratio),))*self.bolus_uncertainty)
        else:
            ratio = 1.0
        bolus_meal_contribution = ratio*chos/np.asarray(self.demographic_info.carb_insulin_ratio)
        correction_contribution = ratio*(measurements-self.target_glucose)/np.asarray(self.demographic_info.correction_bolus)

        bolus_in_2hours = np.any(self.previous_boluses > np.finfo(float).eps, axis=1)
        correction_contribution[np.logical_or(bolus_in_2hours, np.logical_and(~meal_ongoing_binmap, measurements<self.hyper_threshold))] = 0.0

        bolus = bolus_meal_contribution + correction_contribution
        bolus[bolus < 0.0] = 0.0

        rescue_carbs = np.zeros_like(self.demographic_info.carb_insulin_ratio)
        allowed_rescue_carb = np.logical_and(measurements < self.hypo_threshold, np.all(self.previous_rescue_carbs < np.finfo(float).eps, axis=1))
        rescue_carbs[allowed_rescue_carb] = 15.0

        self.previous_boluses = np.concatenate((self.previous_boluses, bolus[:,None]),axis=1)
        if self.previous_boluses.shape[1] > 120.0/self.sampling_time:
            self.previous_boluses = self.previous_boluses[:,1:]

        self.previous_rescue_carbs = np.concatenate((self.previous_rescue_carbs, rescue_carbs[:,None]),axis=1)
        if self.previous_rescue_carbs.shape[1] > 5.0/self.sampling_time:
            self.previous_rescue_carbs = self.previous_rescue_carbs[:,1:]

        match self.model_name:
            case T1DM.ExtHovorka.Model.name:
                bolus = UnitConversion.insulin.U_to_mU(bolus)/self.sampling_time
                rescue_carbs = UnitConversion.glucose.g_glucose_to_mmol(rescue_carbs)/self.sampling_time
                inputs[:, 3, sample] = self.basal.sampled_signal[:, sample] + bolus
                inputs[:, 0, sample] = rescue_carbs
            case T1DM.IVP.Model.name:
                bolus = UnitConversion.insulin.U_to_uU(bolus) / self.sampling_time
                inputs[:, 1, sample] = self.basal.sampled_signal[:, sample] + bolus
            case _:
                raise Exception(f"Unknown model name {self.model_name}")

        # infusion_rate = self.basal.sampled_signal[:,self.iteration] + bolus
        # if UnitConversion.insulin.mUmin_to_Uhr(infusion_rate)>300.0:


        return