# Copyright (C) 2015-2016 Jean-Baptiste LAMY
# LIMICS (Laboratoire d'informatique médicale et d'ingénierie des connaissances en santé), UMR_S 1142
# University Sorbonne Paris Nord, Bobigny, France

import sys, os, time
from owlready2 import *

#default_world.set_backend(filename = "/home/jiba/tmp/quadstore_omop_sample_dataset.sqlite3")
default_world.set_backend(filename = "/home/jiba/tmp/quadstore_v522_data.sqlite3")

PYM = get_ontology("http://PYM/").load()
omop_cdm = get_ontology("http://abimed.fr/onto/omop_cdm.owl")#.load()
data     = get_ontology("http://abimed.fr/onto/omop_cdm_data.owl")#.load()

#default_world.graph.execute("""PRAGMA automatic_index = false""")
#default_world.graph.execute("""ANALYZE""")

print(len(default_world.graph))



q = default_world.prepare_sparql("""
PREFIX umls: <http://PYM/>
PREFIX atc: <http://PYM/ATC/>
PREFIX snomed: <http://PYM/SNOMEDCT_US/>

SELECT ?gender ?age (COUNT(DISTINCT ?patient) as ?num_patients) {
#?patient a omop_cdm:Person .
?patient omop_cdm:has_condition_era ?condition .
?condition omop_cdm:has_concept/a/rdfs:subClassOf*STATIC/rdfs:label "Fracture of bone of hip region" .
?patient omop_cdm:has_gender/a/rdfs:label ?gender .
?patient omop_cdm:year_of_birth ?birth_year .
?condition omop_cdm:start_date ?start .
BIND(YEAR(?start) - ?birth_year AS ?age) . }
GROUP BY ?gender ?age ORDER BY ?gender ?age

""")
t = time.perf_counter()

#print(q.sql)
#for i in default_world.graph.execute("""EXPLAIN QUERY PLAN %s""" % q.sql): print(i)
l = list(q.execute())


t = time.perf_counter() - t
for i in l: print(i)
print(len(l))
print(t)
print()


print(q.sql)


# q = default_world.prepare_sparql("""
# PREFIX umls: <http://PYM/>
# PREFIX atc: <http://PYM/ATC/>
# PREFIX snomed: <http://PYM/SNOMEDCT_US/>

# SELECT ?x {
# ?x rdfs:subClassOf*/rdfs:label "Fracture of bone" .
# }
# """)

# l = list(q.execute())
# print(len(l))
# for i in range(len(l)):
#   pass
#   #print(l[i][0].storid, end = ", ")
#   #if i % 9 == 0: print()

