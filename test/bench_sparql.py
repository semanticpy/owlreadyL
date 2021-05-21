# python ./owlready2/test/bench_sparql.py

# You need to run the benchmark twice, because the first time, GO is not loaded in memory, which favor the second
# tested SPARQL engine (which is RDFlib)

import sys, time, rdflib

import owlready2
from owlready2 import *

default_world.set_backend(filename = "/home/jiba/tmp/go.sqlite3", exclusive = True) #, profiling = True) 
go  = get_ontology ("http://purl.obolibrary.org/obo/go.owl").load()
obo = get_namespace("http://purl.obolibrary.org/obo/")
default_world.save()


PLANS = ""

def sparql_owlready(sparql):
  #global PLANS
  #q = default_world.prepare_sparql(sparql)
  #plan = list(default_world.graph.execute("""EXPLAIN QUERY PLAN %s""" % q.sql))
  #plan = "\n".join(" ".join(str(j) for j in l) for l in plan)
  #PLANS += plan + "\n\n"
  
  print(default_world.prepare_sparql(sparql).sql)
  for i in list(default_world.graph.execute("""EXPLAIN QUERY PLAN %s""" % default_world.prepare_sparql(sparql).sql)): print(i)
  
  t0 = time.time()
  r = list(default_world.sparql(sparql))
  t = time.time() - t0
  
  print("OWLREADY: %s s" % t)
  return r, t

def sparql_rdflib(sparql):
  t0 = time.time()
  r = list(default_world.sparql_query(sparql))
  t = time.time() - t0
  print("RDFLIB:   %s s" % t)
  
  return r, t

T_OWLREADY = T_RDFLIB = 0.0
def sparql(sparql):
  global T_OWLREADY, T_RDFLIB

  r1, t1 = sparql_owlready(sparql)
  r2, t2 = sparql_rdflib  (sparql)
  T_OWLREADY += t1
  T_RDFLIB   += t2
  print("Ratio: %s" % (t2 / t1))
  if len(r1) != len(r2):
    print("OWLREADY: %s" % r1)
    print("RDFLIB: %s" % r2)
    print("OWLREADY: %s results" % len(r1))
    print("RDFLIB: %s results" % len(r2))
    assert False
  else:
    print("%s results" % len(r1))
  print()

# Loads parsers
list(default_world.sparql      ("""SELECT  ?x  { ?x rdfs:label "xxx" . }"""))
list(default_world.sparql_query("""SELECT  ?x  { ?x rdfs:label "xxx" . }"""))
print()


sparql("""SELECT (STR(?x) AS ?i)  { ?x rdfs:subClassOf* <http://purl.obolibrary.org/obo/GO_0008150> . ?x rdfs:subClassOf* <http://purl.obolibrary.org/obo/GO_0005575> }""")

sparql("""SELECT ?l  { ?x rdfs:subClassOf* <http://purl.obolibrary.org/obo/GO_0005575> . ?x rdfs:label ?l }""")

sparql("""SELECT ?l  { ?x a/rdfs:subClassOf* <http://purl.obolibrary.org/obo/GO_0005575> . ?x rdfs:label ?l }""")

sparql("""SELECT (STR(?x) AS ?i)  { ?x rdfs:subClassOf* <http://purl.obolibrary.org/obo/GO_0005575> . FILTER EXISTS { ?x rdfs:label ?l } }""")

sparql("""SELECT (STR(?x) AS ?i)  { ?x rdfs:subClassOf* <http://purl.obolibrary.org/obo/GO_0005575> . FILTER NOT EXISTS { ?x rdfs:label ?l } }""")

sparql("""SELECT (STR(?x) AS ?i)  { ?x a <http://www.w3.org/2002/07/owl#Class> . ?x rdfs:label ?l. FILTER (STRSTARTS(?l, "A")) }""")

sparql("""SELECT ?l  { { ?x rdfs:subClassOf* <http://purl.obolibrary.org/obo/GO_0005575> . } UNION { ?x rdfs:subClassOf* <http://purl.obolibrary.org/obo/GO_0008150> . } ?x rdfs:label ?l }""")

sparql("""SELECT (STR(?x) AS ?i)  { ?x a <http://www.w3.org/2002/07/owl#Class> . FILTER (ISIRI(?x)) FILTER NOT EXISTS { ?x rdfs:label ?l } }""")

sparql("""SELECT (COUNT(?x) AS ?i)  { ?x a <http://www.w3.org/2002/07/owl#Class> . }""")



print()
print("# TOTAL:")
print("# OWLREADY: %s s" % T_OWLREADY)
print("# RDFLIB:   %s s" % T_RDFLIB)
print("# Mean ratio: %s" % (T_RDFLIB / T_OWLREADY))

# TOTAL:
# OWLREADY: 0.4174220561981201 s
# RDFLIB:   42.52021360397339 s
# Mean ratio: 101.863840141193


#open("/tmp/plans.txt", "w").write(PLANS)
