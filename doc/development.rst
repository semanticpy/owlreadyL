Development
====================

Development installation
------------------------

Due due legacy compatibility, the development installation needs to be done with the following steps:


1. We recommend to create an virtual environment for development and activate it. 
   Alternatively create a src/ directory, put Owlready sources in that directory, and then add this directory to $PYTHONPATH (= traditional way).

1. Create an directory with an arbitrary name, e.g. ``mkdir owlready_dev``.

1. Move or clone the owlready2 repository into this directory and change into it.

1. run ``pip install -e .[test]`` inside of this owlready directory

1. in case *Python.h* is missing, install python3-dev (e.g. ``sudo apt-get install python3-dev``)

1. run the *setup_develop_mode.py script :
 ``python setup_develop_mode.py`` 
   inside of this owlready directory (there are explainations in the script, why this is necessary)

1. to test everything, cd into the **'test'** directory and run ``python regtest.py ``

