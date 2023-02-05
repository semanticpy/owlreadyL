General class axioms
====================

General class axioms are axioms of the form "A is a B" where "A" is not a named class, but a class construct
(e.g. an intersection, a union or a restriction).


Creating a general class axiom
------------------------------

One can create a general class axiom as follows:

::

   >>> with onto:
   ...     gca = GeneralClassAxiom(onto.Disorder & onto.has_location.some(onto.Heart)) # Left side
   ...     gca.is_a.append(onto.CardiacDisorder) # Right side


The GeneralClassAxiom class take as parameter the left side class construct.

The right side is available as the .is_a attribute.
Notice that one may add several right sides, by calling is_a.append multiple times.

The left side is available as the .left_side attribute.


Accessing general class axioms
------------------------------

One can list general class axioms with Ontology.general_class_axioms:


::

   >>> gcas = list(onto.general_class_axioms())

One can then test the left side by comparison, for example:



::

   >>> searched_left_side = onto.Disorder & onto.has_location.some(onto.Heart)
   >>> for gca in gcas:
   ...     if gca.left_side == searched_left_side: print("Found!")

