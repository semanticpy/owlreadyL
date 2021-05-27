#import os, sys, pytest, time
import os, sys, time

from owlready2 import *


# pytest ./owlready2/test/perftest.py --benchmark-max-time 0.1 --benchmark-min-rounds 1 --benchmark-warmup-iterations 1 --benchmark-calibration-precision 1


#if __name__ != "__main__":
omop_cdm_world = World(filename = "/home/jiba/tmp/quadstore_v522_data.sqlite3")
go_world       = World(filename = "/home/jiba/tmp/go.sqlite3")
list(omop_cdm_world.sparql("""SELECT  ?x  { ?x rdfs:label "xxx" . }"""))
list(go_world      .sparql("""SELECT  ?x  { ?x rdfs:label "xxx" . }"""))

_ALREADYS = set()
def do(world, sparql):
  q = world.prepare_sparql(sparql)
  if ANALYSE and not sparql in _ALREADYS:
    print()
    print(q.sql)
    print()
    for i in world.graph.execute("EXPLAIN QUERY PLAN %s" % q.sql): print(i)
    print()
    _ALREADYS.add(sparql)
  l = list(q.execute())
  return q, l
  
def bench_go_1():
  q, l = do(go_world, """
SELECT ?l  { ?x rdfs:subClassOf* <http://purl.obolibrary.org/obo/GO_0005575> . ?x rdfs:label ?l }""")
  assert len(l) == 4092

def bench_go_2():
  q, l = do(go_world, """
SELECT ?l  { ?x a/rdfs:subClassOf* <http://purl.obolibrary.org/obo/GO_0005575> . ?x rdfs:label ?l }""")
  assert len(l) == 0

def bench_go_3():
  q, l = do(go_world, """
SELECT (STR(?x) AS ?i)  {
  ?x rdfs:subClassOf* <http://purl.obolibrary.org/obo/GO_0005575> .
  FILTER EXISTS { ?x rdfs:label ?l } }""")
  assert len(l) == 4092

def bench_go_4():
  q, l = do(go_world, """
SELECT (STR(?x) AS ?i)  {
  ?x rdfs:subClassOf* <http://purl.obolibrary.org/obo/GO_0005575> .
  FILTER NOT EXISTS { ?x rdfs:label ?l } }""")
  assert len(l) == 0

def bench_go_5():
  q, l = do(go_world, """
SELECT (STR(?x) AS ?i)  {
  ?x a <http://www.w3.org/2002/07/owl#Class> .
  ?x rdfs:label ?l.
  FILTER (STRSTARTS(?l, "A"))
}""")
  assert len(l) == 220
  
def bench_go_6():
  q, l = do(go_world, """
SELECT ?l  {
        { ?x rdfs:subClassOf* <http://purl.obolibrary.org/obo/GO_0005575> . }
  UNION { ?x rdfs:subClassOf* <http://purl.obolibrary.org/obo/GO_0008150> . }
  ?x rdfs:label ?l
}""")
  assert len(l) == 33643

def bench_go_7():
  q, l = do(go_world, """
SELECT (STR(?x) AS ?i)  {
  ?x a <http://www.w3.org/2002/07/owl#Class> .
  FILTER (ISIRI(?x)) .
  FILTER NOT EXISTS { ?x rdfs:label ?l } .
}""")
  assert len(l) == 1981

def bench_go_8():
  q, l = do(go_world, """
SELECT (COUNT(?x) AS ?i)  { ?x a <http://www.w3.org/2002/07/owl#Class> . }""")
  assert len(l) == 1
  
def bench_go_9():
  q, l = do(go_world, """
SELECT (STR(?x) AS ?i)  {
  ?x rdfs:subClassOf* <http://purl.obolibrary.org/obo/GO_0008150> .
  ?x rdfs:subClassOf* <http://purl.obolibrary.org/obo/GO_0005575> }""")
  assert len(l) == 0


def bench_omop_cdm_1():
  q, l = do(omop_cdm_world, """
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
  assert len(l) == 70

  
def bench_omop_cdm_2():
  q, l = do(omop_cdm_world, """
PREFIX umls: <http://PYM/>
PREFIX atc: <http://PYM/ATC/>
PREFIX snomed: <http://PYM/SNOMEDCT_US/>

SELECT ?patient ?drug_era { # SPARQL query for STOPP B1
?patient omop_cdm:has_drug_era ?drug_era .
?drug_era omop_cdm:has_concept/a/rdfs:subClassOf* atc:C01AA05 .
?patient omop_cdm:has_condition_era/omop_cdm:has_concept/a/rdfs:subClassOf* snomed:84114007.
}""")
  assert len(l) == 726

def bench_omop_cdm_3():
  q, l = do(omop_cdm_world, """
PREFIX umls: <http://PYM/>
PREFIX atc: <http://PYM/ATC/>
PREFIX snomed: <http://PYM/SNOMEDCT_US/>

SELECT ?patient {
  #?patient a omop_cdm:Person .
  ?patient omop_cdm:has_condition_era/omop_cdm:has_concept/a/rdfs:subClassOf* snomed:13200003.

  ?patient omop_cdm:has_drug_era ?drug_era1 .
  ?drug_era1 omop_cdm:has_concept/a ?aspirin .
  { ?aspirin rdfs:subClassOf* atc:B01AC06 . }
  UNION { ?aspirin rdfs:subClassOf* atc:A01AD05 . }
  UNION { ?aspirin rdfs:subClassOf* atc:N01BA01 . }
}""")
  assert len(l) == 218

def bench_omop_cdm_4():
  q, l = do(omop_cdm_world, """
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
  assert len(l) == 196


def bench_omop_cdm_5():
  q, l = do(omop_cdm_world, """
PREFIX umls: <http://PYM/>
PREFIX atc: <http://PYM/ATC/>
PREFIX snomed: <http://PYM/SNOMEDCT_US/>

SELECT DISTINCT ?patient ?birth_year {
?patient omop_cdm:has_condition_era/omop_cdm:has_concept/a/rdfs:subClassOf*/rdfs:label "Fracture of bone of hip region" .
?patient omop_cdm:year_of_birth ?birth_year .
}
""")
#   q.sql = """
# WITH RECURSIVE prelim1_objs(s, o) AS (SELECT prelim1_objs_q1.s, prelim1_objs_q1.s FROM datas prelim1_objs_q1 WHERE prelim1_objs_q1.p=40 AND prelim1_objs_q1.o='Fracture of bone of hip region' 
# UNION
# SELECT q.s, rec.o FROM objs q, prelim1_objs rec WHERE q.p=9 AND q.o=rec.s)

# SELECT q1.s, q5.o, q5.d FROM objs q1 , objs q2 , objs q3 , datas q5
# WHERE q1.p=1330554 AND q2.s=q1.o AND q2.p=1330495 AND q3.s=q2.o AND q3.p=6 AND q3.o IN (SELECT s FROM prelim1_objs) AND q5.s=q1.s AND q5.p=1330602
# """
  
  l = list(q.execute())
  assert len(l) == 127
  

NB = 3
  
BENCHS    = [v for (k, v) in globals().items() if k.startswith("bench_") and callable(v)]
ALL_TESTS = []
for func in BENCHS:
  def f(benchmark, func = func):
    benchmark.pedantic(func, iterations = 3, rounds = 1)
  f.__name__ = "test_%s" % func.__name__
  globals()["test_%s" % func.__name__] = f
  ALL_TESTS.append(func.__name__)
  
 
if __name__ == "__main__":
  ANALYSE = "--sql" in sys.argv
  TESTS = []
  for arg in sys.argv[1:]:
    if arg.startswith("-"): continue
    TESTS.append(arg)
  
  def read_results(filename):
    r = {}
    for row in open(filename).read().split("\n"):
      if row.startswith("test_"):
        cells = row.split()
        r[cells[0]] = float(cells[1].replace(",", ""))
    return r

  def run_test(filename):
    s = ""
    for test in TESTS or ALL_TESTS:
      func = globals()[test]
      t = time.perf_counter()
      for i in range(NB): func()
      t = (time.perf_counter() - t) / NB
      s += "test_%s %s\n" % (test, t * 1000.0)
    open(filename, "w").write(s)

      
  def show_results(r1, r2 = None):
    test_names  = sorted(set(r1) | set(r2 or []))
    name_length = max(len(name) for name in test_names) + 1
    
    print()
    print("TEST", " " * (name_length - 4), "TIME (ms)")
    if r2 is None:
      for name in test_names:
        t1 = r1[name]
        print(name, " " * (name_length - len(name)), "%4i" % round(t1))
    else:
      for name in test_names:
        t1 = r1.get(name, 0)
        t2 = r2.get(name, 0)
        if t1 and t2:
          delta = (t2 / t1 * 100.0) - 100.0
          if   delta < -8.0: color = "\033[32m"
          elif delta >  8.0: color = "\033[31m"
          else:              color = ""
        else:
          delta = 0
          color = ""
        print(name, " " * (name_length - len(name)), "%4i" % round(t1), "%4i" % round(t2), " ", color, "%+.2f%%" % delta, "\033[00m")
    print()

  FS = "/home/jiba/tmp/owlready_pytest_results.txt"
  if "-s" in sys.argv:
    F = FS
  else:
    F = "/tmp/owlready_pytest_results.txt"
  run_test(F)

  if os.path.exists(FS):
    r1 = read_results(FS)
    r2 = read_results(F)
  else:
    r1 = read_results(F)
    r2 = None
    
  show_results(r1, r2)
