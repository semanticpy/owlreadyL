# Testing Owlready2

Automatic tests can be executed with the following commands (a Debian based operating system is assumed):

- `python3 regtest.py`
- `python3 test_mixed.py`
- `python3 test_parser.py`

A single test can be run with e.g. `python3 -m unittest regtest.Test.test_rdflib_12`.

Please note: Some tests require to execute the command `rapper` (RDF utility). On debian, ubuntu, etc this program is contained in the package `raptor2-utils`.
