User interface
===============

Command-line interface
--------------------------

Generally, parsers commands have the form :code:`X -y` or :code:`X --y` where X is some command and y is some input argument. The single dash - is used to indicate an abbreviation while the double dash -- is used to indicate the full word (such as :code:`-y` versus :code:`--yellow`). This is largely conventional.

At any point while using this interface, the inputs that may be entered from the command line can be displayed by entering the command followed by :code:`-h` or :code:`--help` (such as :code:`directions -h` or :code:`directions --help`)

.. list-table:: **List of available commands:**
   :widths: 15 50
   :header-rows: 1

   * - Command
     - Effect
   * - :code:`directions`
     - Can be used to query descriptions of the available features and commands. For additional help, type: :code:`directions -h`.
   * - :code:`settings`
     - Can be used to define general, simulator wide settings. For additional help, type: :code:`settings -h`.
   * - :code:`cohort`
     - Can be used to define the settings of the virtual cohort. For additional help, type: :code:`cohort -h`.
   * - :code:`inputs`
     - Can be used to define the inputs of the simulated virtual cohort. For additional help, type: :code:`inputs -h`.
   * - :code:`activity`
     - Can be used to define the activities of the simulated virtual cohort (currently only T1DM.ExtHovorka supports it). For additional help, type: :code:`inputs -h`.
   * - :code:`simulate`
     - Can be used to simulate the defined scenario and generate the results in the :code:`./SimulationResults/<results folder with datetime from simulation run time>` folder.
   * - :code:`plot`
     - Can be used to visualize the results and generate figures. For additional help, type: :code:`plot -h`.
   * - :code:`load`
     - Can be used to load a predefined scenario from the :code:`./Scenarios/` folder. For additional help, type: :code:`load -h`.
   * - :code:`reset`
     - Can be used to reset the scenario to the default one (`defaults </_autosummary/pymgipsim.Settings.DefaultSettings.html>`_).
   * - :code:`quit`
     - Quits the simulator.


Defining a scenario
----------------------------

A scenario is a unique descriptor of a simulation. Outside of the simulator a scenario is described in a JSON file. The scenario is exported and can be reused later to make a simulation reproducable.

A set of predefined scenarios can be found in the :code:`./Scenarios/` folder.

For a more detailed description of the scenario please refer :ref:`here <detailed target>`.

By running any of the (:code:`settings`, :code:`cohort`, :code:`inputs`) command, the simulator shows the current state of the scenario in a table format. It highlights the modificaitons compared to the default scenario. :code:`settings` allows the user to set broad settings such as the simulation sampling time and the duration in days. :code:`cohort` allows the user to set virtual subject characteristics such as the model and type of diabetes or number of subjects. :code:`inputs` allows the user to set model inputs such as carbohydrate intake, basal or bolus insulin therapy, or SGLT2I treatment.

.. image:: imgs/scenario_table.png
   :align: center
   :target: _images/scenario_table.png

|


There are various commands that can be used to generate simulation results. The key commands are :code:`settings`, :code:`cohort`, :code:`inputs`, and :code:`simulate`. These constitute the basic functional workflow of this interface and can be used in any order as long as :code:`simulate` is entered after the other. This is because :code:`simulate` will run a simulation with the currently defined settings.

There are several inputs available for the models. Currently, some of the inputs are common between models while others are model-specific. 

The common inputs are meal and snack carbohydrates, which are given in grams either as a single, constant value or as a range for random sampling. Meals are given between 06:00-08:00 (breakfast), 12:00-14:00 (lunch), and 18:00-20:00 (dinner) between 30-60 minutes. A morning snack can be given between 09:00-11:00 and an afternoon snack can be given between 15:00-17:00. Snacks are between 5-15 minutes long.

The type 1 diabetes-specific model inputs are basal and bolus insulin, which are simply activated or deactivated and dosed based on meals and subject characteristics. The type 2 diabetes-specific model input is a sodium-glucose cotransporter-2 inhibitor, which is given in milligrams and dosed once-daily between 06:00 and 09:00. The model inputs are selected using the :code:`inputs` command. Use :code:`inputs -h` to learn more.

.. list-table:: **Playthrough example:**
   :widths: 25 50
   :header-rows: 1

   * - Command
     - Effect
   * - :code:`settings -d 3`
     - Sets the simulation length to 3 days.
   * - :code:`cohort -mn T1DM.ExtHovorka`
     - Sets the cohort to type 1 diabetic and the model to an extended Hovorka.
   * - :code:`cohort -pn Patient_1 Patient_4`
     - Loads the patient parameters from the Patient_1 and Patient_4 files. 
   * - :code:`inputs -lcr 20 80`
     - Sets the lunch carb range to be between 20 and 80 grams.
   * - :code:`simulate`
     - Runs the defined scenario and saves the results.
   * - :code:`plot -pat 0`
     - Generates a time series plot of inputs and outputs for Patient_1.

Plots and exports
---------------------------

By running :code:`plot`, the simulator generates figures and saves them but not shows them. In order to show the figures use :code:`plot -pa`. Default figures visualize cohort wide time series plots of all the state variables of the given mathematical model.  The other options are used to change display settings such as color and figure size.

.. image:: imgs/bgc_example.png
   :align: center
   :target: _images/bgc_example.png

.. image:: imgs/states_example.png
   :align: center
   :target: _images/states_example.png

|

To visualize input-output dynamics of a single patient use :code:`plot -pat <patient index>`.

.. image:: imgs/subject_plot_example.png
   :align: center
   :target: _images/subject_plot_example.png

|

The :code:`simulate` command has a single argument for formatting the model results in Microsoft Excel format. Running :code:`simulate` will run a simulation with the currently-defined settings. If no other commands have been used, then a default simulation is run. These settings are displayed when the simulation is run.

.. csv-table:: **Example xls export**
   :file: imgs/model_state_results.csv
   :width: 40%
   :header-rows: 2

