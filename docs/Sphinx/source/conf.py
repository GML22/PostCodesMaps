""" Configuration file of Sphinx documentation """

import os
import sys

sys.path.insert(0, os.path.join(os.path.abspath('../../..'), r"src\postcodesmaps"))

project = 'PostCodesMaps'
copyright = '2023, Mateusz Gomulski'
author = 'Mateusz Gomulski'
release = '1.0.0'
extensions = ['sphinx.ext.autodoc', 'sphinx_autodoc_typehints', 'sphinx_rtd_theme', 'sphinx.ext.coverage',
              'rst2pdf.pdfbuilder']
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_theme_options = {"navigation_depth": 4, 'collapse_navigation': True, 'sticky_navigation': False,
                      'includehidden': True, 'titles_only': False, 'prev_next_buttons_location': 'bottom',
                      'style_external_links': False, 'display_version': True}
