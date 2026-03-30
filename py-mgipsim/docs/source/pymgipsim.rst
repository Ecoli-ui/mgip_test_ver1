For developers
=====================

Programatically run simulations
---------------------

An example is provided in :code:`manual_script.py` on how programatically defined scenarios can be simulated.


How to add a model?
-----------------------

**Defining the model**

* Define the state variables, inputs, constants, parameters, and model equations in the VirtualPatient/Models folder
* In the Parameters file:
   * Define all model parameters and their vectorization function (:code:`as_array`).
   * Define :code:`generate` function that either loads patient files or draws random samples from distributions.
* In the Inputs file:
   * Define all model inputs and their vectorization function (:code:`as_array`).
* In the Model file:
   * Define a unique name in the Model class, same name should be given to the folder.
   * Diff. equations should be defined in the :code:`model` function.
   * Initial conditions should be defined in the :code:`preprocessing` function.
   * A :code:`from_scenario` function has to be defined which passes the inputs, parameters, etc. from the scenario to the model. Unit conversions from the default units to the model specific ones is convenient to do in this function.
* Define virtual patient parameters in :code:`JSON` files in the Patients folder.

**Add model to the generate functions**

* Add functions that generate the necessary inputs of the model in :code:`generate_inputs_main` function in the generate_inputs file.
* Add model parameter generation in :code:`generate_virtual_subjects_main` function in the generate_subjects file.

.. note::
   If the added model is just an auixiliary model, it can be readily used for simulation. An example is the physical activity -> heart rate model, and the implementation can be found in :code:`pymgipsim/InputGeneration/heart_rate_settings.py`. If the added model represents the patient, the following steps are needed.

**Update VirtualCohort**

* Add the defined model to the virtual patient class in VirtualPatient/VirtualPatient.

**Update plots**

* Update plotting function with specifics of the defined model.

**Optional: Controller compatibility**
* 


How to add a controller?
-----------------------------

**Define controller class**

* Define the class similarly to already existing ones in the :code:`pymgipsim/Controllers` folder.
* The controller has to have a unique name, same as the folder name.
* :code:`run` function of the controller will be called in every sampling time of the simulation with the available data up to that point. The function has to modify inplace the current sample of the input array.

**Adding it to the solver**

* Add the controller to the :code:`set_controller` function in :code:`pymgipsim/ModelSolver/singlescale.py`.

**Update plots**

* Update plotting function with specifics of the defined controller.



PYmGIPsim package
---------------------

.. autosummary::
   :toctree:_autosummary
   :template: custom-module-template.rst
   :recursive:

   pymgipsim



