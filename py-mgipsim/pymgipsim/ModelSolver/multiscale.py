from tqdm import tqdm
from abc import ABC, abstractmethod
from ..ODESolvers.ode_solvers import euler_single_step, rk4_single_step
import numpy as np
from pymgipsim.Utilities.Scenario import scenario
from pymgipsim.VirtualPatient.Models.Model import BaseModel
from pymgipsim.Utilities.units_conversions_constants import UnitConversion


class MultiscaleSolverBase(ABC):


    def __init__(self, scenario_instance: scenario, model: BaseModel):

        # Directory where the results should be stored
        self.scenario_instance = scenario_instance

        self.model = model

        # ODE solver function
        self.set_solver(self.scenario_instance.settings.solver_name)

    def set_solver(self, solver_name):
        match solver_name:
            case "RK4":
                self.ode_solver = rk4_single_step
            case 'Euler':
                self.ode_solver = euler_single_step

    @abstractmethod
    def do_simulation(self):
        pass

class MultiScaleSolver(MultiscaleSolverBase):
    name = 'MultiScaleSolver'

    def __init__(self, scenario_instance: scenario, singlescale_model: BaseModel, multiscale_model):
        super().__init__(scenario_instance, singlescale_model)
        
        self.singlescale_model = singlescale_model
        self.multiscale_model = multiscale_model

    def do_simulation(self, no_progress_bar):

        """ Initialize multiscale model """
        multiscale_state_results = self.multiscale_model.states.as_array
        multiscale_inputs = self.multiscale_model.inputs.as_array
        multiscale_parameters = self.multiscale_model.parameters.as_array
        multiscale_state_results[:, :, 0] = self.multiscale_model.initial_conditions.as_array

        """ Initialize singlescale model """
        singlescale_state_results = self.singlescale_model.states.as_array
        singlescale_inputs = self.singlescale_model.inputs.as_array
        singlescale_parameters = self.singlescale_model.parameters.as_array
        singlescale_state_results[:, :, 0] = self.singlescale_model.initial_conditions.as_array

        """ Loop """
        skip_multiscale = False
        multiscale_range = range(1, multiscale_inputs.shape[2])

        if not len(multiscale_range):
            multiscale_range = [1]
            skip_multiscale = True

        for multiscale_sample in tqdm(multiscale_range, disable = no_progress_bar):

            if skip_multiscale:
                x = np.arange(UnitConversion.time.convert_days_to_minutes(multiscale_sample-1) + 1,
                            UnitConversion.time.convert_days_to_minutes(multiscale_sample)
                            ).astype(int)
                        
            else:
                """ Calculate singlescale ranges """
                x = np.arange(UnitConversion.time.convert_days_to_minutes(multiscale_sample-1) + 1,
                            UnitConversion.time.convert_days_to_minutes(multiscale_sample) + 1
                            ).astype(int)
                        
            for singlescale_sample in tqdm(x, disable = True):

                singlescale_state_results[:, :, singlescale_sample] = self.ode_solver(
                                                                        f=self.singlescale_model.model,
                                                                        time=float(singlescale_sample),
                                                                        h=float(self.singlescale_model.sampling_time),
                                                                        initial=singlescale_state_results[:, :, singlescale_sample - 1].copy(),
                                                                        parameters=singlescale_parameters,
                                                                        inputs=singlescale_inputs[:, :, singlescale_sample - 1]
                                                                    )
                
            """ Update urinary glucose excretion """
            uge = UnitConversion.glucose.mmol_glcuose_to_g(self.singlescale_model.rate_equations(singlescale_state_results[:, :, x], x, singlescale_parameters, singlescale_inputs[:, :, x])[-1][0])
            multiscale_inputs[:, -1, multiscale_sample-1] = np.trapz(y = uge, x = x, axis = -1)

            
            if not skip_multiscale:

                multiscale_state_results[:, :, multiscale_sample] = self.ode_solver(
                                                                        f=self.multiscale_model.model,
                                                                        time=float(multiscale_sample),
                                                                        h=float(self.multiscale_model.sampling_time),
                                                                        initial=multiscale_state_results[:, :, multiscale_sample - 1].copy(),
                                                                        parameters=multiscale_parameters,
                                                                        inputs=multiscale_inputs[:, :, multiscale_sample - 1]
                                                                    )

                singlescale_inputs[:, -1, singlescale_sample] = multiscale_state_results[:, :, multiscale_sample].flatten() / self.scenario_instance.patient.demographic_info.body_weight

        if not skip_multiscale:

            """ Calculate singlescale ranges """
            x = np.arange(UnitConversion.time.convert_days_to_minutes(multiscale_sample),
                            UnitConversion.time.convert_days_to_minutes(multiscale_sample + 1)
                            ).astype(int)
                    
            for singlescale_sample in tqdm(x, disable = True):

                singlescale_state_results[:, :, singlescale_sample] = self.ode_solver(
                                                                        f=self.singlescale_model.model,
                                                                        time=float(singlescale_sample),
                                                                        h=float(self.singlescale_model.sampling_time),
                                                                        initial=singlescale_state_results[:, :, singlescale_sample - 1].copy(),
                                                                        parameters=singlescale_parameters,
                                                                        inputs=singlescale_inputs[:, :, singlescale_sample - 1]
                                                                    )
                
        """ Set states and inputs """
        self.singlescale_model.states.as_array = singlescale_state_results
        self.singlescale_model.inputs.as_array = singlescale_inputs

        self.multiscale_model.states.as_array = multiscale_state_results
        self.multiscale_model.inputs.as_array = multiscale_inputs

        return singlescale_state_results
