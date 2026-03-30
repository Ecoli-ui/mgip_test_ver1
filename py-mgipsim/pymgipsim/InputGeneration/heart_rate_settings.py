import numpy as np
from pymgipsim.InputGeneration.signal import Signal, Events
from pymgipsim.Utilities.Scenario import scenario, controller
from pymgipsim.Controllers import OpenLoop
import pymgipsim.VirtualPatient.Models.Physact.Activity2Heartrate as Heartrate
from pymgipsim.ModelSolver.singlescale import SingleScaleSolver

def generate_heart_rate(scenario_instance: scenario, args):
    no_subjects = scenario_instance.patient.number_of_subjects
    # magnitude = np.expand_dims(np.asarray(scenario_instance.patient.demographic_info.resting_heart_rate),1)
    # start_time = np.zeros((no_subjects,1))
    sampling_time = 1.0
    time = np.arange(scenario_instance.settings.start_time,scenario_instance.settings.end_time,sampling_time)
    model = Heartrate.Model(sampling_time=sampling_time)

    model.inputs.running_speed = Signal(time=time, sampling_time=sampling_time,
                                        start_time=np.zeros((no_subjects, 1)), magnitude=np.zeros((no_subjects, 1)))
    model.inputs.running_incline = Signal(time=time, sampling_time=sampling_time,
                                        start_time=np.zeros((no_subjects, 1)), magnitude=np.zeros((no_subjects, 1)))
    model.inputs.cycling_power = Signal(time=time, sampling_time=sampling_time,
                                        start_time=np.zeros((no_subjects, 1)), magnitude=np.zeros((no_subjects, 1)))
    model.inputs.standard_power = Signal(time=time, sampling_time=sampling_time,
                                        start_time=np.zeros((no_subjects, 1)), magnitude=np.zeros((no_subjects, 1)))
    model.inputs.METACSM = Signal(time=time, sampling_time=sampling_time,
                                        start_time=np.zeros((no_subjects, 1)), magnitude=np.zeros((no_subjects, 1)))


    if scenario_instance.inputs.cycling_power:
        model.inputs.cycling_power = Signal(time=time, sampling_time=sampling_time,
                                            duration=np.asarray(scenario_instance.inputs.cycling_power.duration),
                                            start_time=scenario_instance.inputs.cycling_power.start_time,
                                            magnitude=np.asarray(scenario_instance.inputs.cycling_power.magnitude)*np.asarray(scenario_instance.inputs.cycling_power.duration))
    if scenario_instance.inputs.running_speed and scenario_instance.inputs.running_incline:
        model.inputs.running_speed = Signal(time=time, sampling_time=sampling_time,
                                            duration=np.asarray(scenario_instance.inputs.running_speed.duration),
                                            start_time=scenario_instance.inputs.running_speed.start_time,
                                            magnitude=np.asarray(scenario_instance.inputs.running_speed.magnitude)*np.asarray(scenario_instance.inputs.running_speed.duration))
        model.inputs.running_incline = Signal(time=time, sampling_time=sampling_time,
                                              start_time=scenario_instance.inputs.running_incline.start_time,
                                              duration=np.asarray(scenario_instance.inputs.running_incline.duration),
                                              magnitude=np.asarray(scenario_instance.inputs.running_incline.magnitude)*np.asarray(scenario_instance.inputs.running_speed.duration))

    model.parameters = Heartrate.Parameters(np.asarray(Heartrate.Parameters.generate(scenario_instance)))
    model.time.as_unix = time

    scenario_controller = scenario_instance.controller
    scenario_instance.controller = controller(OpenLoop.controller.Controller.name,[])
    solver = SingleScaleSolver(scenario_instance, model)
    solver.set_solver("RK4")
    solver.model.preprocessing()
    solver.do_simulation(False)
    heart_rate = solver.model.rate_equations(solver.model.states.as_array, solver.model.time.as_unix, solver.model.parameters.as_array, solver.model.inputs.as_array)
    METACSM = solver.model.inputs.METACSM.sampled_signal
    #
    # plt.plot(heart_rate.T)
    # plt.show()
    scenario_instance.controller = scenario_controller
    return Events(magnitude=heart_rate, start_time=time*np.ones((no_subjects,1))).as_dict(),\
        Events(magnitude=METACSM, start_time=time*np.ones((no_subjects,1))).as_dict()