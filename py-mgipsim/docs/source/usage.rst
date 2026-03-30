:tocdepth: 1

Quickstart
============

Requirements
-----------------

* Python 3.12.0
* Dependencies can be installed via :code:`pip install -r requirements.txt`


Graphical User Interface
-----------------------------

Provides a graphical user interface in a web app.

To run it locally:

blocks::

> streamlit run interface_gui.py

.. image:: imgs/gui.gif
   :target: _images/gui.gif

Command Line - Interactive
--------------------------------

Provides an interactive prompt environment to set the simulation settings.

To get started run :code:`interface_cmd.py` to activate a command line interface (CLI).

* :code:`simulate` This command is used to run the simulation with the assigned settings.
* Using just :code:`simulate` generates a default scenario.
* Predefined scenarios are available in the :code:`./Scenarios/` folder. To use one of them, use :code:`load -sn <scenario name>` and :code:`simulate`. 
* Results are stored in the directory :code:`./SimulationResults/<results folder with datetime from simulation run time>`

Plot the results
------------
* :code:`plot` This command is used to generate plots from the simulation results.
* :code:`plot -h` lists the arguments that can be used with :code:`plot <arguments>`
* :code:`plot` with no arguments generates and saves all figures without displaying them.
* :code:`plot --all` both generates and displays all figures.

.. image:: imgs/cmd.gif
   :target: _images/cmd.gif

Command Line - single command
----------------------------------
Simulation settings are defined in a single command line.

Start by running :code:`interface_cli.py [OPTIONS]`.

