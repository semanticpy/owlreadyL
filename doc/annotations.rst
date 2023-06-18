Annotations
===========

In Owlready2, annotations are accessed as attributes.
For Classes, notice that annotations are **not** inherited.


Adding an annotation
--------------------

For a given entity (a Class, a Property or an Individual), the following syntax can be used to add
annotations:

::
   
   >>> from owlready2 import *
   
   >>> onto = get_ontology("http://test.org/onto.owl")
   
   >>> with onto:
   ...     class Drug(Thing):
   ...         pass
   
   >>> Drug.comment = ["A first comment on the Drug class", "A second comment"]
   
   >>> Drug.comment.append("A third comment")

The following annotations are available by default: comment, isDefinedBy, label, seeAlso,
backwardCompatibleWith, deprecated, incompatibleWith, priorVersion, versionInfo.

Owlready2 also supports annotations on relation triples, using the AnnotatedRelation class as folows:

::

   >>> with onto:
   ...     class HealthProblem(Thing):
   ...         pass

   ...     class is_prescribed_for(Drug >> HealthProblem):
   ...         pass

   >>> acetaminophen = Drug("acetaminophen")
   >>> pain = HealthProblem("pain")
   >>> acetaminophen.is_prescribed_for.append(pain)
   
   >>> AnnotatedRelation(acetaminophen, is_prescribed_for, pain).comment = ["A comment on the acetaminophen-pain relation"]

The AnnotatedRelation class constructor takes three parameters, corresponding to a subject-predicate-object triple.
Then, you can use the dotted notation on the AnnotatedRelation object to access the various annotations
(e.g., .comment, .label, etc).

.. note::

   The following, old, syntax remains supported:

   ::

      >>> comment[acetaminophen, is_prescribed_for, pain] = ["A comment on the acetaminophen-pain relation"]
   

Special pseudo-properties are provided for annotating is-a relations (rdfs_subclassof and rdf_type),
domains (rdf_domain) and ranges (rdf_range).

::

   >>> AnnotatedRelation(Drug, rdfs_subclassof, Thing).comment = ["A comment on an is-a relation"]


Annotation values are usually lists of values. However, in many cases, a single value is used.
Owlready2 accepts to set an annotation property to a single value, for example:

::
   
   >>> acetaminophen.comment = "This comment replaces all existing comments on acetaminophen"


Querying annotations
--------------------

Annotation values can be obtained using the dot notation, as if they were attributes of the entity:

::
   
   >>> print(Drug.comment)
   ['A first comment on the Drug class', 'A second comment', 'A third comment']
   
   >>> print(AnnotatedRelation(acetaminophen, is_prescribed_for, pain).comment)
   ['A comment on the acetaminophen-pain relation']
   
   >>> print(AnnotatedRelation(Drug, rdfs_subclassof, Thing).comment)
   ['A comment on an is-a relation']

If you expect a single value, the .first() method of the list can be used. It returns the first value of
the list, or None if the list is empty.

::

   >>> acetaminophen.comment.first()
   'This comment replaces all existing comments on acetaminophen'


.. note::

   The following, old, syntax remains supported:

   ::

      >>> comment[acetaminophen, is_prescribed_for, pain]


Deleting annotations
--------------------

To delete an annotation, simply remove it from the list.

::
   
   >>> Drug.comment.remove("A second comment")


For removing **all** annotations of a given type:

::
   
   >>> Drug.comment = []


Nested annotated relations
--------------------------

AnnotatedRelation can be nested if desired, as follows:

::
   
   >>> annotr = AnnotatedRelation(acetaminophen, is_prescribed_for, pain)
   >>> nested = AnnotatedRelation(annotr, comment, "A comment on the acetaminophen-pain relation")
   >>> nested.comment = ["A comment on the previous comment"]

   
Custom rendering of entities
----------------------------

The set_render_func() global function can be used to specify how Owlready2 renders entities, i.e. how they are
converted to text when printing them. set_render_func() accepts a single param, a function which takes
one entity and return a string.

The 'label' annotation is commonly used for rendering entities.
The following example renders entities using their 'label' annotation, defaulting to their name:

::
   
   >>> def render_using_label(entity):
   ...     return entity.label.first() or entity.name
   
   >>> set_render_func(render_using_label)
   
   >>> Drug    # No label defined yet => use entity.name
   Drug
   
   >>> Drug.label = "The drug class"
   
   >>> Drug
   The drug class


The following example renders entities using their IRI:

::
   
   >>> def render_using_iri(entity):
   ...     return entity.iri
   
   >>> set_render_func(render_using_iri)

   >>> Drug
   http://test.org/onto.owl#Drug


Language-specific annotations
-----------------------------

To specify the language of textual annotations, the 'locstr' (localized string) type can be used:

::
   
   >>> Drug.comment = [ locstr("Un commentaire en Français", lang = "fr"),
   ...                  locstr("A comment in English", lang = "en") ]
   >>> Drug.comment[0]
   'Un commentaire en Français'
   >>> Drug.comment[0].lang
   'fr'
   
In addition, the list of values support language-specific sublists, available as '.<language code>'
(e.g. .fr, .en, .es, .de,...).
These sublists contain normal string (not locstr), and they can be modified.

::

   >>> Drug.comment.fr
   ['Un commentaire en Français']
   
   >>> Drug.comment.en
   ['A comment in English']
   
   >>> Drug.comment.en.first()
   'A comment in English'
   
   >>> Drug.comment.en.append("A second English comment")

The get_lang() method does the same (but is easier to call if the lang is in a variable):

::

   >>> lang = "fr"
   >>> Drug.comment.get_lang(lang)
   ['Un commentaire en Français']

The get_lang_first() method return only the first language-specific string found (it is equivalent to get_lang().first()):

::

   >>> lang = "fr"
   >>> Drug.comment.get_lang_first(lang)
   'Un commentaire en Français'

.. warning::
   
   Modifying the language-specific sublist will automatically update the list of values (and the quad store).
   However, the contrary is not true: modifying the list of values does **not** update language-specific sublists.
   


Creating new classes of annotation
----------------------------------

The AnnotationProperty class can be subclasses to create a new class of annotation:

::

   >>> with onto:
   ...     class my_annotation(AnnotationProperty):
   ...         pass

You can also create a subclass of an existing annotation class:

::
   
   >>> with onto:
   ...     class pharmaceutical_comment(comment):
   ...         pass
   
   >>> acetaminophen.pharmaceutical_comment = "A comment related to pharmacology of acetaminophen"


Full-text search (FTS)
----------------------

Full-text search (FTS) can optimize search in textual properties and annotations.
FTS uses Sqlite3 FTS5 implementation.

First, FTS needs to be enabled on the desired properties, by adding them to default_world.full_text_search_properties,
for example for label:

::

   >>> default_world.full_text_search_properties.append(label)

Then, FTS can be used in search as follows:

::

   >>> default_world.search(label = FTS("keyword1 keyword2*"))

Stars can be used as joker, but only at the END of the keyword.

When using full-text search, the _bm25 argument can be used to obtain the BM25 relevance score for each entity found:

::

   >>> default_world.search(label = FTS("keyword1 keyword2*"), _bm25 = True)
