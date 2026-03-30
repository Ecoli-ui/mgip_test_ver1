import numpy as np
from pymgipsim.Controllers.HCL0.DataContainer import *
import qpsolvers
from pymgipsim.Utilities.units_conversions_constants import UnitConversion
from pymgipsim.Utilities.Scenario import scenario
from pymgipsim.InputGeneration.signal import Signal
from pymgipsim.VirtualPatient.Models import T1DM
from pymgipsim.Controllers.HCL0.VanillaMPC import VanillaMPC

class Controller:
    name = "HCL0"

    def __init__(self, scenario_instance: scenario):
        self.control_sampling = int(5/scenario_instance.settings.sampling_time)
        self.controllers = []
        for patient_idx in range(scenario_instance.patient.number_of_subjects):
            self.controllers.append(VanillaMPC(scenario_instance, patient_idx))

    def run(self, measurements, inputs, states, sample):
        if sample % self.control_sampling == 0:
            for patient_idx in range(inputs.shape[0]):
                self.controllers[patient_idx].run(measurements, inputs, states, sample, patient_idx)
        return