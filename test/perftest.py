import pytest, time

from owlready2 import *


# pytest ./owlready2/test/perftest.py --benchmark-max-time 0.1 --benchmark-min-rounds 1 --benchmark-warmup-iterations 1 --benchmark-calibration-precision 1


omop_cdm_world = World(filename = "/home/jiba/tmp/quadstore_v522_data.sqlite3")
go_world       = World(filename = "/home/jiba/tmp/go.sqlite3")

def bench_omop_cdm_1():
  q = omop_cdm_world.prepare_sparql("""
PREFIX umls: <http://PYM/>
PREFIX atc: <http://PYM/ATC/>
PREFIX snomed: <http://PYM/SNOMEDCT_US/>

SELECT ?gender ?age (COUNT(DISTINCT ?patient) as ?num_patients) {
?patient a omop_cdm:Person .
?patient omop_cdm:has_condition_era ?condition .
?condition omop_cdm:has_concept/a/rdfs:subClassOf*/rdfs:label "Fracture of bone of hip region" .
?patient omop_cdm:has_gender/a/rdfs:label ?gender .
?patient omop_cdm:year_of_birth ?birth_year .
?condition omop_cdm:start_date ?start .
BIND(YEAR(?start) - ?birth_year AS ?age) . }
GROUP BY ?gender ?age ORDER BY ?gender ?age
""")
  l = list(q.execute())
  assert len(l) == 70

def bench_omop_cdm_2():
  q = omop_cdm_world.prepare_sparql("""
PREFIX umls: <http://PYM/>
PREFIX atc: <http://PYM/ATC/>
PREFIX snomed: <http://PYM/SNOMEDCT_US/>

SELECT ?patient ?drug_era { # SPARQL query for STOPP B1
?patient omop_cdm:has_drug_era ?drug_era .
?drug_era omop_cdm:has_concept/a/rdfs:subClassOf* atc:C01AA05 .
?patient omop_cdm:has_condition_era/omop_cdm:has_concept/a/rdfs:subClassOf* snomed:84114007.
}""")
  l = list(q.execute())
  assert len(l) == 726

def bench_omop_cdm_3():
  q = omop_cdm_world.prepare_sparql("""
PREFIX umls: <http://PYM/>
PREFIX atc: <http://PYM/ATC/>
PREFIX snomed: <http://PYM/SNOMEDCT_US/>

SELECT ?patient { # SPARQL query for STOPP C2
  #?patient a omop_cdm:Person .
  ?patient omop_cdm:has_condition_era/omop_cdm:has_concept/a/rdfs:subClassOf* snomed:13200003.

  ?patient omop_cdm:has_drug_era ?drug_era1 .
  ?drug_era1 omop_cdm:has_concept/a ?aspirin .
  { ?aspirin rdfs:subClassOf* atc:B01AC06 . }
  UNION { ?aspirin rdfs:subClassOf* atc:A01AD05 . }
  UNION { ?aspirin rdfs:subClassOf* atc:N01BA01 . }

  FILTER NOT EXISTS {
    ?patient omop_cdm:has_drug_era ?drug_era2 .
    ?drug_era2 omop_cdm:has_concept/a/rdfs:subClassOf* atc:A02BC . # PPI
    ?drug_era1 omop_cdm:start_date ?start1 .
    ?drug_era1 omop_cdm:end_date ?end1 .
    ?drug_era2 omop_cdm:start_date ?start2 .
    ?drug_era2 omop_cdm:end_date ?end2 .
    FILTER(?start1 < ?end2 && ?start2 < ?end1) .
  }
}""")
  l = list(q.execute())
  assert len(l) == 196

  
def bench_go_1():
  q = go_world.prepare_sparql("""
SELECT ?l  { ?x rdfs:subClassOf* <http://purl.obolibrary.org/obo/GO_0005575> . ?x rdfs:label ?l }""")
  l = list(q.execute())
  assert len(l) == 4092

def bench_go_2():
  q = go_world.prepare_sparql("""
SELECT ?l  { ?x a/rdfs:subClassOf* <http://purl.obolibrary.org/obo/GO_0005575> . ?x rdfs:label ?l }""")
  l = list(q.execute())
  assert len(l) == 0

def bench_go_3():
  q = go_world.prepare_sparql("""
SELECT (STR(?x) AS ?i)  {
  ?x rdfs:subClassOf* <http://purl.obolibrary.org/obo/GO_0005575> .
  FILTER EXISTS { ?x rdfs:label ?l } }""")
  l = list(q.execute())
  assert len(l) == 4092

def bench_go_4():
  q = go_world.prepare_sparql("""
SELECT (STR(?x) AS ?i)  {
  ?x rdfs:subClassOf* <http://purl.obolibrary.org/obo/GO_0005575> .
  FILTER NOT EXISTS { ?x rdfs:label ?l } }""")
  l = list(q.execute())
  assert len(l) == 0

def bench_go_5():
  q = go_world.prepare_sparql("""
SELECT (STR(?x) AS ?i)  {
  ?x a <http://www.w3.org/2002/07/owl#Class> .
  ?x rdfs:label ?l.
  FILTER (STRSTARTS(?l, "A"))
}""")
  l = list(q.execute())
  assert len(l) == 220

def bench_go_6():
  q = go_world.prepare_sparql("""
SELECT ?l  {
        { ?x rdfs:subClassOf* <http://purl.obolibrary.org/obo/GO_0005575> . }
  UNION { ?x rdfs:subClassOf* <http://purl.obolibrary.org/obo/GO_0008150> . }
  ?x rdfs:label ?l
}""")
  l = list(q.execute())
  assert len(l) == 33643

def bench_go_7():
  q = go_world.prepare_sparql("""
SELECT (STR(?x) AS ?i)  {
  ?x a <http://www.w3.org/2002/07/owl#Class> .
  FILTER (ISIRI(?x)) .
  FILTER NOT EXISTS { ?x rdfs:label ?l } .
}""")
  l = list(q.execute())
  assert len(l) == 1981

def bench_go_8():
  q = go_world.prepare_sparql("""
SELECT (COUNT(?x) AS ?i)  { ?x a <http://www.w3.org/2002/07/owl#Class> . }""")
  l = list(q.execute())
  assert len(l) == 1
  
def bench_go_9():
  q = go_world.prepare_sparql("""
SELECT (STR(?x) AS ?i)  {
  ?x rdfs:subClassOf* <http://purl.obolibrary.org/obo/GO_0008150> .
  ?x rdfs:subClassOf* <http://purl.obolibrary.org/obo/GO_0005575> }""")
  l = list(q.execute())
  assert len(l) == 0
  

  
BENCHS = [v for (k, v) in globals().items() if k.startswith("bench_") and callable(v)]

for func in BENCHS:
  def f(benchmark, func = func):
    benchmark.pedantic(func, iterations = 1, rounds = 1)
  f.__name__ = "test_%s" % func.__name__
  globals()["test_%s" % func.__name__] = f
  
 
