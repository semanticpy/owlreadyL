Development
====================

Development installation
------------------------

Due due legacy compatibility, the development installation needs to be done with the following steps:

1. We recommend to create an virtual environment for development and activate it. 

1. Create an directory with an arbitrary name, e.g. ``mkdir owlready_dev``.

1. Move or clone the owlready2 repository into this directory and change into it.

1. run ``pip install -r requirements.txt``

1. run ``pip install -e .`` inside of this owlready directory

1. run the *setup_develop_mode.py script ``python setup_develop_mode.py`` inside of this owlready directory (there are explainations in the script, why this is necessary)

1. to test everything, cd into the tests directory and run ``python regtest.py ``

