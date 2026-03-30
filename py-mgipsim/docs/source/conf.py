# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

sys.path.insert(0, os.path.abspath('../..'))

project = 'mGIPsim'
copyright = '2024, Illinois Tech'
author = 'Andy, Mate'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.napoleon', 'sphinx.ext.autodoc', 'sphinx.ext.autosummary', 'sphinx.ext.viewcode']
autodoc_default_options = {"members": True, "inherited-members": True, "show-inheritance":True}
autosummary_generate = True
autosummary_imported_members = False


templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

add_module_names = False

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

#extensions.append("maisie_sphinx_theme")
html_theme = 'sphinx_rtd_theme_mgipsim'
html_theme_path = ["_themes"]
html_extra_path = ['imgs/Flag_of_Chicago,_Illinois2.svg','imgs/Flag_of_Chicago,_Illinois2red.svg']

#html_theme = 'alabaster'
#html_static_path = ['_static']
