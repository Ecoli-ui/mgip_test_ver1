import numpy as np
from pymgipsim.InputGeneration.signal import Signal, Events
from pymgipsim.Utilities.Scenario import scenario, controller
from pymgipsim.Controllers import OpenLoop
import pymgipsim.VirtualPatient.Models.Physact.Heartrate2Energyexp as EE
from pymgipsim.ModelSolver.singlescale import SingleScaleSolver

def generate_energy_expenditure(scenario_instance: scenario, args):
    no_subjects = scenario_instance.patient.number_of_subjects
    # magnitude = np.expand_dims(np.asarray(scenario_instance.patient.demographic_info.resting_heart_rate),1)
    # start_time = np.zeros((no_subjects,1))
    sampling_time = 1.0
    time = np.arange(scenario_instance.settings.start_time,scenario_instance.settings.end_time,sampling_time)
    model = EE.Model(sampling_time=sampling_time)

    model.inputs.deltaEE = Signal(time=time, sampling_time=sampling_time,
                                        start_time=np.zeros((no_subjects, 1)), magnitude=np.zeros((no_subjects, 1)))
    model.inputs.METACSM = Signal(time=time, sampling_time=sampling_time,
                                        start_time=scenario_instance.inputs.METACSM.start_time,
                                        magnitude=scenario_instance.inputs.METACSM.magnitude)
    model.inputs.heart_rate = Signal(time=time, sampling_time=sampling_time,
                                        start_time=scenario_instance.inputs.heart_rate.start_time,
                                        magnitude=scenario_instance.inputs.heart_rate.magnitude)
    model.time.as_unix = time

    scenario_controller = scenario_instance.controller
    scenario_instance.controller = controller(OpenLoop.controller.Controller.name,[])
    solver = SingleScaleSolver(scenario_instance, model)
    solver.set_solver("RK4")
    solver.model.preprocessing()
    solver.do_simulation(False)

    energy_expenditure = solver.model.states.as_array[:,0,:]

    scenario_instance.controller = scenario_controller
    return Events(magnitude=energy_expenditure, start_time=time*np.ones((no_subjects,1))).as_dict()