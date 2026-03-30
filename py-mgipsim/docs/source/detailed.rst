For the curious ones
=====================
.. _detailed target:


Here we aim to give a little more detailed information how the simulator workflow is layed out, and what are the underlying inputs, models and methods that define the observed simulation results.


.. toctree::

	inputs
	models

A scenario is a unique descriptor of a simulation. Outside of the simulator a scenario is described in a JSON file. At the end of each simulation the scenario is exported and can be reused later to make a simulation reproducable. The core element of the simulator is the scenario JSON file/class. Between the class and the file there is a one-to-one mapping, all the fields in the file are mirrored as the scenario class attributes. For the detailed description of the fields in the scenario please refer to the `docs </py-mgipsim/_autosummary/pymgipsim.Utilities.Scenario.scenario.html>`_.

By using the command line interface, the user apply modifications to a default scenario instance (loaded from the default JSON file) (`defaults </py-mgipsim/_autosummary/pymgipsim.Settings.DefaultSettings.html>`_). Until the simulation command is not called, only the scenario instance is manipulated and saved in each module. The CLI parses inputs according to the library [argparse](https://docs.python.org/3/library/argparse.html).

.. image:: imgs/workflow.svg
   :target: _images/workflow.svg

Simulation workflow
---------------------------

**Simulation given a defined scenario**

	1. If a scenario object contains all the necessary information for a successful simulation, it can be passed to `VirtualCohort </py-mgipsim/_autosummary/pymgipsim.VirtualPatient.VirtualPatient.VirtualCohort.html>`_ class to a initialize a virtual cohort object.
	2. The VirtualCohort class (during init) will:
	    1. initialize a `model </py-mgipsim/_autosummary/pymgipsim.VirtualPatient.Models.Model.BaseModel.html>`_ object by calling the :code:`from_scenario` function of the model that was defined in the scenario objects.
	    2. The :code:`from_scenario` function of the model initializes the model given the information in the scenario (e.g. input variables, patient model parameters, time sequence).
	    3. The initialized model and the scenario object is passed to a `ModelSolver </py-mgipsim/_autosummary/pymgipsim.ModelSolver.BaseSolvers.html>`_ class.
	3. The :code:`preprocessing` function of the `model </py-mgipsim/_autosummary/pymgipsim.VirtualPatient.Models.Model.BaseModel.html>`_ object, nested in the `ModelSolver </py-mgipsim/_autosummary/pymgipsim.ModelSolver.BaseSolvers.html>`_ object, nested in the `VirtualCohort </py-mgipsim/_autosummary/pymgipsim.VirtualPatient.VirtualPatient.VirtualCohort.html>`_ object has to be called.
	4. The :code:`do_simulation` function of the `VirtualCohort </py-mgipsim/_autosummary/pymgipsim.VirtualPatient.VirtualPatient.VirtualCohort.html>`_ object can be called to run the simulation.

**Building blocks**

Time-series signal

	* Any time-series signal is represented in the `signal </py-mgipsim/_autosummary/pymgipsim.InputGeneration.signal.Signal.html>`_  class. For instances, input variables of the models are signals.

	* It holds:
		* Time, a :code:`np.array` that defines the sequence of time instances (minutes) at which the signal will sampled.
		* Sampling time (minutes).
		* Attributes of an `event </py-mgipsim/_autosummary/pymgipsim.InputGeneration.signal.Events.html>`_  object.

Events

	* `Event </py-mgipsim/_autosummary/pymgipsim.InputGeneration.signal.Events.html>`_  class represents a time-series signal before sampling it by holding the following variables:
		* Magnitudes :code:`np.array` (unit of the signal)
		* Start times :code:`np.array` (minutes)
		* Durations :code:`np.array` (minutes), if undefined zero order hold will be assumed during the sampling process. If defined, the energy (value in the magnitude variable) will be distributed equally.

**(Abstract) model**

All models have the following attributes:

	* Inputs, holds the input variables. (The inputs class itself are model specific but all of them are a container of `signal </py-mgipsim/_autosummary/pymgipsim.InputGeneration.signal.Signal.html>`_) attributes).
	* States, holds the state variables (The states class itself are model specific but all of them are a container of `signal </py-mgipsim/_autosummary/pymgipsim.InputGeneration.signal.Signal.html>`_) attributes).
	* Parameters, holds the parameters of the model.
	* Time, same as the time attribute of any of the input variables.
	* Sampling time, as as the sampling time attribute of any of the input variables.

Both inputs, states and parameters have a common function :code:`as_array` that returns the input variables, state variables or parameters as a `np.array`.

All models have a :code:`model` function that defines the differential equations.



**General settings (generate_settings.py)**

:code:`>> settings` 

.. automodule:: generate_settings
	:exclude-members: generate_simulation_settings_main

**Virtual cohort settings (generate_subjects.py)**

:code:`>> cohort` 

.. automodule:: generate_subjects
	:exclude-members: generate_virtual_subjects_main

**Input settings (generate_inputs.py)**

:code:`>> inputs` 

.. automodule:: generate_inputs

**Simulator (generate_results.py)**

:code:`>> simulate` 

.. automodule:: generate_results

**Plotting (generate_plots.py**

:code:`>> plot` 

.. automodule:: generate_plots
