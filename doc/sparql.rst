SPARQL queries
==============

Since version 0.30, Owlready proposes 2 methods for performing SPARQL queries: the native SPARQL engine and RDFlib.


Native SPARQL engine
********************

The native SPARQL engine automatically translates SPARQL queries into SQL queries, and then run the SQL queries with SQLite3.

The native SPARQL engine has better performances than RDFlib (about 60 times faster when tested on Gene Ontology,
but it highly depends on queries and data). It also has no dependencies and it has a much shorter start-up time.

However, it currently supports only a subset of SPARQL.


SPARQL elements supported
-------------------------

* SELECT, INSERT and DELETE queries
* UNION, OPTIONAL
* FILTER, BIND, FILTER EXISTS, FILTER NOT EXISTS
* SELECT sub queries
* VALUES in SELECT queries
* All SPARQL functions and aggregation functions
* Blank nodes notations with square bracket, e.g. '[ a XXX]'
* Parameters in queries (i.e. '??')
* Property path expressions, e.g. 'a/rdfs:subClassOf*',  excepted those listed below

SPARQL elements not supported
-----------------------------

* ASK, DESCRIBE, LOAD, ADD, MOVE, COPY, CLEAR, DROP, CONSTRUCT queries
* INSERT DATA, DELETE DATA, DELETE WHERE queries (you may use INSERT or DELETE instead)
* SERVICE (Federated queries)
* GRAPH, FROM, FROM NAMED keywords
* MINUS
* Property path expressions with parentheses of the following forms:

  - nested repeats, e.g. (a/p*)*
  - sequence nested inside a repeat, e.g. (p1/p2)*
  - negative property set nested inside a repeat, e.g. (!(p1 | p2))*

  i.e. repeats cannot contain other repeats, sequences and negative property sets.


Performing SPARQL queries
-------------------------

The .sparql() methods of the World object can be used to perform a SPARQL query and obtain the results.
Notice that .sparql() returns a generator, so we used here the list() function to show the results.
The list contains one row for each result found, with one or more columns (depending on the query).

::
   
   >>> # Loads Gene Ontology (~ 170 Mb), can take a moment!
   >>> go = get_ontology("http://purl.obolibrary.org/obo/go.owl").load()
   
   >>> # Get the number of OWL Class in GO
   >>> list(default_world.sparql("""
              SELECT (COUNT(?x) AS ?nb)
              { ?x a owl:Class . }
       """))
   [[60448]]


Notice that the following prefixes are automatically pre-defined:

*  rdf: -> http://www.w3.org/1999/02/22-rdf-syntax-ns#
*  rdfs: -> http://www.w3.org/2000/01/rdf-schema#
*  owl: -> http://www.w3.org/2002/07/owl#
*  xsd: -> http://www.w3.org/2001/XMLSchema#
*  obo: -> http://purl.obolibrary.org/obo/
*  owlready: -> http://www.lesfleursdunormal.fr/static/_downloads/owlready_ontology.owl#

In addition, Owlready automatically create prefixes from the last part of ontology IRI (without .owl extension),
e.g. the ontology "http://test.org/onto.owl" with be automatically associated with the "onto:" prefix.
Consequently, in most case you don't need to define prefixes (but you can still define them if you want).

The classes counted above include OWL named classes, but also some OWL constructs. One may count only named classes
using a FILTER condition and the ISIRI function, as follows:

::
   
   >>> # Get the number of OWL Class in GO
   >>> list(default_world.sparql("""
              SELECT (COUNT(?x) AS ?nb)
              { ?x a owl:Class . FILTER(ISIRI(?x)) }
       """))
   [[48535]]


We may also search for a given concept. When a query returns an entity, it returns it as an Owlready object.

::
   
   >>> # Get the "mitochondrion inheritance" concept from GO
   >>> r = list(default_world.sparql("""
              SELECT ?x
              { ?x rdfs:label "mitochondrion inheritance" . }
       """))
   >>> r
   [[obo.GO_0000001]]
   >>> mito_inher = r[0][0]

Here, the resulting object 'mito_inher' is an Owlready object (here, a Class) that can be used as any other classes in Owlready.

Owlready support simple property path expressions, such as 'rdfs:subClassOf*' or 'a/rdfs:subClassOf*'.
For example, we can get the superclasses of "mitochondrion inheritance" as follows:

::
   
   >>> list(default_world.sparql("""
              SELECT ?y
              { ?x rdfs:label "mitochondrion inheritance" .
                ?x rdfs:subClassOf* ?y }
       """))
   [[obo.GO_0000001], [obo.GO_0048308], [obo.GO_0048311], [obo.GO_0006996], [obo.GO_0007005], [obo.GO_0051646], [obo.GO_0016043], [obo.GO_0051640], [obo.GO_0009987], [obo.GO_0071840], [obo.GO_0051641], [obo.GO_0008150], [obo.GO_0051179]]

 
Or we can search for individuals belonging to the class "mitochondrion inheritance" or one of its descendants, as follows:

::
   
   >>> list(default_world.sparql("""
              SELECT ?y
              { ?x rdfs:label "mitochondrion inheritance" .
                ?y a/rdfs:subClassOf* ?x }
       """))
   []
   
(Here, we have no results because Gene Ontology does not include individuals).



INSERT queries
--------------

The ontology in which the new RDF triples are inserted can be given using a "with ontology:" block or
using the "WITH <ontology IRI> INSERT ..." syntax in SPARQL. If both are present, the "with ontology:" block takes priority.

::
   
   >>> insertion = get_ontology("http://test.org/insertion.owl")
   >>> with insertion:
   ...     default_world.sparql("""
              INSERT { ?x rdfs:label "héritage mitochondrial"@fr }
              WHERE  { ?x rdfs:label "mitochondrion inheritance" . }
              """)
   1

INSERT / DELETE queries returns the number of matches found by the WHERE part.

When running INSERT / DELETE queries, Owlready tries to update the Python objects corresponding to the modified entities,
if they were loaded from the quadstore.

The following example shows how to create new individuals with an INSERT query. It creates an individual for each subclass
of "membrane".

::
   
   >>> insertion = get_ontology("http://test.org/insertion.owl")
   >>> with insertion:
   ...     default_world.sparql("""
              INSERT { ?n rdfs:label "New individual!" . }
              WHERE  { ?x rdfs:label "membrane" .
                       ?y rdfs:subClassOf ?x .
                       BIND(NEWINSTANCEIRI(?y) AS ?n) }
              """)
   

We use here a BIND statement in order to create a new IRI, using the NEWINSTANCEIRI() function that create a new IRI for
an individual, similar to those created automatically by Owlready. You may also use the more standard UUID() SPARQL function,
which create a random arbitrary IRI.

The following example shows how to create OWL construct like restrictions with an INSERT query.

::
   
   >>> insertion = get_ontology("http://test.org/insertion.owl")
   >>> with insertion:
   ...     default_world.sparql("""
              INSERT { ?x rdfs:subClassOf [ a owl:Restriction ;
                                            owl:onProperty obo:BFO_0000050 ;
                                            owl:someValuesFrom obo:GO_0005623 ] . }
              WHERE  { ?x rdfs:label "membrane" . }
              """)
   1
   
   >>> obo.GO_0016020.label
   ['membrane']
   >>> obo.GO_0016020.is_a
   [obo.GO_0044464, obo.BFO_0000050.some(obo.GO_0005623)]

   

DELETE queries
--------------

DELETE queries are supported; they do not need to specify the ontology from which RDF triples are deleted.

::
   
   >>> default_world.sparql("""
           DELETE { ?r ?p ?o . }
           WHERE  {
               ?x rdfs:label "membrane" .
               ?x rdfs:subClassOf ?r .
               ?r a owl:Restriction .
               ?r ?p ?o .
           }
           """)

The native SPARQL engine supports queries with both a DELETE and an INSERT statement.


Parameters in SPARQL queries
----------------------------

Parameters allow to run the same query multiple times, with different parameter values.
They have two interests. First, they increase performances since the same query can be reused, thus avoiding to
parse new queries. Second, they prevent security problems by avoiding SPARQL code injection, e.g. if a string value includes
quotation marks.

Parameters can be included in the query by using double question marks, e.g. "??". Parameter values can be Owlready entities
or datatype values (int, float, string, etc.). Parameter values are passed in a list after the query:

::
   
   >>> list(default_world.sparql("""
              SELECT ?y
              { ?? rdfs:subClassOf* ?y }
       """, [mito_inher]))
   [[obo.GO_0000001], [obo.GO_0048308], [obo.GO_0048311],
    [obo.GO_0006996], [obo.GO_0007005], [obo.GO_0051646],
    [obo.GO_0016043], [obo.GO_0051640], [obo.GO_0009987],
    [obo.GO_0071840], [obo.GO_0051641], [obo.GO_0008150],
    [obo.GO_0051179]]


Parameters can also be numbered, e.g. "??1", "??2", etc. This is particularly usefull if the same parameter is used
multiple times in the query.

::
   
   >>> list(default_world.sparql("""
              SELECT ?y
              { ??1 rdfs:subClassOf* ?y }
       """, [mito_inher]))
   [[obo.GO_0000001], [obo.GO_0048308], [obo.GO_0048311],
    [obo.GO_0006996], [obo.GO_0007005], [obo.GO_0051646],
    [obo.GO_0016043], [obo.GO_0051640], [obo.GO_0009987],
    [obo.GO_0071840], [obo.GO_0051641], [obo.GO_0008150],
    [obo.GO_0051179]]


Non-standard additions to SPARQL
--------------------------------

The following functions are supported by Owlready, but not standard:

 * The SIMPLEREPLACE(a, b) function is a version of REPLACE() that does not support Regex. It works like Python or SQLite3 replace,
   and has better performances.

 * The NEWINSTANCEIRI() function create a new IRI for an instance of the class given as argument. This IRI is similar to those
   created by default by Owlready. Note that the function creates 2 RDF triples, asserting that the new individual is an
   OWL NamedIndividual and an instance of the desired class passed as argument.

 * The LOADED(iri) function returns True if the given IRI is currently loaded in Python, and False otherwise.

 * The STORID(iri) function returns the integer Store-ID used by Owlready in the quadstore for representing the entity.

 * The DATE(), TIME() and DATETIME() functions can be used to handle date and time. They behave as in SQLite3 (see https://www.sqlite.org/lang_datefunc.html).

 * The DATE_SUB(), DATE_ADD(), DATETIME_SUB and DATETIME_ADD() functions can be used to substract or add a time duration to a date or a datetime, for example : DATETIME_ADD(NOW(), "P1Y"^^xsd:duration)

In Owlready, INSERT and DELETE queries can have a GROUP BY, HAVING and/or ORDER BY clauses.
This is normally not allowed by the SPARQL specification.


Prepare SPARQL queries
----------------------

The .prepare_sparql() method of the World object can be used to prepare a SPARQL query. It returns a PreparedQuery object.

The .execute() method of the PreparedQuery can be used to execute the query. It takes as argument the list of parameters,
if any.

.. note::
   
   The .sparql() method calls .prepare_sparql(). Thus, there is no interest, in terms of performances, to use
   .prepare_sparql() instead of .sparql().

The PreparedQuery can be used to determine the type of query:

::

   >>> query = default_world.prepare_sparql("""SELECT (COUNT(?x) AS ?nb) { ?x a owl:Class . }""")
   >>> isinstance(query, owlready2.sparql.main.PreparedSelectQuery)
   True
   >>> isinstance(query, owlready2.sparql.main.PreparedModifyQuery) # INSERT and/or DELETE
   False

The following attributes are availble on the PreparedQuery object:

 * .nb_parameter: the number of parameters
 * .column_names: a list with the names of the columns in the query results, e.g. ["?nb"] in the example above.
 * .world: the world object for which the query has been prepared
 * .sql: the SQL translation of the SPARQL query

::

   >>> query.sql
   'SELECT  COUNT(q1.s), 43 FROM objs q1 WHERE q1.p=6 AND q1.o=11'
   
.. note::
   
   For INSERT and DELETE query, the .sql translation only involves the WHERE part. Insertions and deletions are
   performed in Python, not in SQL, in order to update the modified Owlready Python objects, if needed.


Open a SPARQL endpoint
----------------------

The owlready2.sparql.endpoint module can be used to open a SPARQL endpoint. It requires Flask or WSGI. It contains the EndPoint
class, that takes a World and can be used as a Flask page function.

The following script creates a SPARQL endpoint with Flask:

::
   
   import flask
   
   from owlready2 import *
   from owlready2.sparql.endpoint import *

   # Load one or more ontologies
   go = get_ontology("http://purl.obolibrary.org/obo/go.owl").load() # (~ 170 Mb), can take a moment!
   
   app = flask.Flask("Owlready_sparql_endpoint")
   endpoint = EndPoint(default_world)
   app.route("/sparql", methods = ["GET"])(endpoint)
   
   # Run the server with Werkzeug; you may use any other WSGI-compatible server
   import werkzeug.serving
   werkzeug.serving.run_simple("localhost", 5000, app)


And the following script does the same, but with WSGI:

::
   
   from owlready2 import *
   from owlready2.sparql.endpoint import *

   # Load one or more ontologies
   go = get_ontology("http://purl.obolibrary.org/obo/go.owl").load() # (~ 170 Mb), can take a moment!
   
   endpoint = EndPoint(default_world)
   app = endpoint.wsgi_app
   
   # Run the server with Werkzeug; you may use any other WSGI-compatible server
   import werkzeug.serving
   werkzeug.serving.run_simple("localhost", 5000, app)

   
You can then query the endpoint, e.g. by opening the following URL in your browser:

   `<http://localhost:5000/sparql?query=SELECT(COUNT(?x)AS%20?nb){?x%20a%20owl:Class.}>`_


Using RDFlib for executing SPARQL queries
*****************************************

The Owlready quadstore can be accessed as an RDFlib graph, which can be used to perform SPARQL queries:

::

   >>> graph = default_world.as_rdflib_graph()
   >>> r = list(graph.query("""SELECT ?p WHERE {
     <http://www.semanticweb.org/jiba/ontologies/2017/0/test#ma_pizza> <http://www.semanticweb.org/jiba/ontologies/2017/0/test#price> ?p .
   }"""))


The results can be automatically converted to Python and Owlready using the .query_owlready() method instead of .query():

::

   >>> r = list(graph.query_owlready("""SELECT ?p WHERE {
     <http://www.semanticweb.org/jiba/ontologies/2017/0/test#ma_pizza> <http://www.semanticweb.org/jiba/ontologies/2017/0/test#price> ?p .
   }"""))

