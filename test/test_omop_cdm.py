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

#default_world.graph.analyze()

#print(list(default_world.sparql("""SELECT (COUNT(?x) AS ?nb) {?x a owl:Class . FILTER(ISIRI(?x))}""")))
#print(list(default_world.sparql("""SELECT (COUNT(?x) AS ?nb) {?x a owl:NamedIndividual}""")))

# default_world.graph.execute("""PRAGMA analysis_limit = 1000""")
# default_world.graph.execute("""ANALYZE""")
# default_world.graph.execute("""DELETE FROM sqlite_stat1""")
# default_world.graph.execute("""INSERT INTO sqlite_stat1 VALUES ('objs', 'index_objs_op', '200712260 4 3 3 1')""")
# default_world.graph.execute("""INSERT INTO sqlite_stat1 VALUES ('objs', 'index_objs_sp', '200712260 3 2')""")
# default_world.graph.execute("""INSERT INTO sqlite_stat1 VALUES ('datas', 'index_datas_op', '108845960 4 3 3 3 1')""")
# default_world.graph.execute("""INSERT INTO sqlite_stat1 VALUES ('datas', 'index_datas_sp', '108845960 3 2')""")
# default_world.graph.execute("""ANALYZE sqlite_schema""")



# t = time.time()
# q = default_world.prepare_sparql("""
# PREFIX umls: <http://PYM/>
# PREFIX atc: <http://PYM/ATC/>
# PREFIX snomed: <http://PYM/SNOMEDCT_US/>

# SELECT ?gender ?age (COUNT(DISTINCT ?patient) as ?num_patients) {
# ?patient a omop_cdm:Person .
# ?patient omop_cdm:has_condition_era ?condition .
# ?condition omop_cdm:has_concept/a/rdfs:subClassOf*/rdfs:label "Fracture of bone of hip region" .
# ?patient omop_cdm:has_gender/a/rdfs:label ?gender .
# ?patient omop_cdm:year_of_birth ?birth_year .
# ?condition omop_cdm:start_date ?start .
# BIND(YEAR(?start) - ?birth_year AS ?age) .}
# GROUP BY ?gender ?age ORDER BY ?gender ?age
# """)
# print(q.sql)
# for i in default_world.graph.execute("""EXPLAIN QUERY PLAN %s""" % q.sql): print(i)
# l = list(q.execute())
# t = time.time() - t
# #for i in l: print(i)
# print(len(l))
# print(t)
# print()


t = time.time()
q = default_world.prepare_sparql("""
PREFIX umls: <http://PYM/>
PREFIX atc: <http://PYM/ATC/>
PREFIX snomed: <http://PYM/SNOMEDCT_US/>

SELECT ?patient ?drug_era { # SPARQL query for STOPP B1
#?patient a omop_cdm:Person .
?patient omop_cdm:has_drug_era ?drug_era .
?drug_era omop_cdm:has_concept/a/rdfs:subClassOf* atc:C01AA05 .
?patient omop_cdm:has_condition_era/omop_cdm:has_concept/a/rdfs:subClassOf* snomed:84114007.
}
""")

#print(q.sql)
#for i in default_world.graph.execute("""EXPLAIN QUERY PLAN %s""" % q.sql): print(i)
l = list(q.execute())


t = time.time() - t
#for i in l: print(i)
print(len(l))
print(t)
print()





