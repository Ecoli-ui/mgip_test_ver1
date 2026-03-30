## **mGIPsim

Metabolic simulator of 20 virtual patients with type 1 diabetes, simulates physical activity, meal intakes, and insulin therapies.
* Efficient simulation (vectorized and JIT compiled)
* Modular, easy to extend with models, controllers
* Current therapies: multiple daily injections, sensor augmented pump therapy, vanilla hybrid closed-loop
* [Docs](https://illinoistech-itm.github.io/py-mgipsim/)

## Requirements
* Python 3.12
* Dependencies can be installed via ``pip install -r requirements.txt``

## Usage
### Graphical User Interface
Provides a graphical user interface in a web app.

To run it locally:
```bash
streamlit run interface_gui.py
```

![](static/gui.gif)

### Command Line - Interactive
Provides an interactive prompt environment to set the simulation settings.

Start by running ``interface_cmd.py``.

![](static/cmd.gif)

### Command Line - single command
Simulation settings are defined in a single command line.

Start by running ``interface_cli.py [OPTIONS]``.
