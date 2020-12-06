# General Information

This directory contains the source file for the docs.

# Dependencies

To ensure you have all dependencies for building the documentation, run the followin:
```
pip install sphinx
pip install sphinx-rtd-theme
```

# Build the Docs

From the project root (where `setup.py` lives) run the folloing:

```
sphinx-build -b html doc doc/html
```

For more information see <https://www.sphinx-doc.org/en/master/usage/quickstart.html>.
