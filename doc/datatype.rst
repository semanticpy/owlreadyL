Datatypes
=========

Owlready automatically recognizes and translates basic datatypes to Python, such as string, int, float, etc.


Creating custom datatypes
-------------------------

The declare_datatype() global function allows to declare a new datatype. It takes 4 arguments:

 * datatype: the Python datatype (for example, a Python type or class)
 * iri: the IRI used to represent the datatype in ontologies
 * parser: a function that takes a serialized string and returns the corresponding datatype
 * unparser: a function that takes a datatype and returns its serialization in a string

The function returns the storid associated to the datatype.

**Warning:** The datatype must be declared **BEFORE** loading any ontology that uses it.

Here is an example for adding support for the XSD "hexBinary" datatype:

::
   
   >>> class Hex(object):
   ...   def __init__(self, value):
   ...     self.value = value
   
   >>> def parser(s):
   ...   return Hex(int(s, 16))
   
   >>> def unparser(x):
   ...   h = hex(x.value)[2:]
   ...   if len(h) % 2 != 0: return "0%s" % h
   ...   return h
   
   >>> declare_datatype(Hex, "http://www.w3.org/2001/XMLSchema#hexBinary", parser, unparser)


The new datatype can then be used as any others:

::
   
   >>> onto = world.get_ontology("http://www.test.org/t.owl")
   
   >>> with onto:
   ...   class p(Thing >> Hex): pass
   
   ...   class C(Thing): pass
   
   ...   c1 = C()
   ...   c1.p.append(Hex(14))




In addition, the define_datatype_in_ontology() function allows to define the datatype in a given ontology.
This was not needed for hexBinary above, because it is already defined in XMLSchema.
However, for user-defined datatype, it is recommended to define them in an ontology
(Owlready does not strictly require that, but other tools like Protégé do).

The following example (re)define the hexBinary datatype in our ontology:

::
   
   >>> define_datatype_in_ontology(Hex, "http://www.w3.org/2001/XMLSchema#hexBinary", onto)
   
This add the (xsd:hexBinary, rdf:type, rdfs:datatype) RDF triple in the quadstore.

As said above, declare_datatype() must be called * before * using the datatype.
On the contrary, define_datatype_in_ontology() may be called after loading an ontology that use the datatype.

