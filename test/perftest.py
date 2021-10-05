#import os, sys, pytest, time
import os, sys, time

from owlready2 import *


# pytest ./owlready2/test/perftest.py --benchmark-max-time 0.1 --benchmark-min-rounds 1 --benchmark-warmup-iterations 1 --benchmark-calibration-precision 1


#if __name__ != "__main__":
omop_cdm_world = World(filename = "/home/jiba/tmp/quadstore_v522_data.sqlite3")
go_world       = World(filename = "/home/jiba/tmp/go.sqlite3")
list(omop_cdm_world.sparql("""SELECT  ?x  { ?x rdfs:label "xxx" . }"""))
list(go_world      .sparql("""SELECT  ?x  { ?x rdfs:label "xxx" . }"""))

FIRST = True
_ALREADYS = set()
def do(world, sparql, sql = ""):
  q = world.prepare_sparql(sparql)
  if sql: q.sql = sql
  if SHOW_SQL and not sparql in _ALREADYS:
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

def bench_go_1_static():
  q, l = do(go_world, """
SELECT ?l  { ?x rdfs:subClassOf*STATIC <http://purl.obolibrary.org/obo/GO_0005575> . ?x rdfs:label ?l }""")
  assert len(l) == 4092

def bench_go_2():
  q, l = do(go_world, """
SELECT ?l  { ?x a/rdfs:subClassOf* <http://purl.obolibrary.org/obo/GO_0005575> . ?x rdfs:label ?l }""")
  assert len(l) == 0

def bench_go_2_static():
  q, l = do(go_world, """
SELECT ?l  { ?x a/rdfs:subClassOf*STATIC <http://purl.obolibrary.org/obo/GO_0005575> . ?x rdfs:label ?l }""")
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

def bench_omop_cdm_1_static():
  q, l = do(omop_cdm_world, """
PREFIX umls: <http://PYM/>
PREFIX atc: <http://PYM/ATC/>
PREFIX snomed: <http://PYM/SNOMEDCT_US/>

SELECT ?gender ?age (COUNT(DISTINCT ?patient) as ?num_patients) {
  ?patient a omop_cdm:Person .
  ?patient omop_cdm:has_condition_era ?condition .
  ?condition omop_cdm:has_concept/a/rdfs:subClassOf*STATIC/rdfs:label "Fracture of bone of hip region" .
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

SELECT ?gender ?age (COUNT(DISTINCT ?patient) as ?num_patients) {
  ?patient omop_cdm:has_condition_era ?condition .
  ?condition omop_cdm:has_concept/a/rdfs:subClassOf*/rdfs:label "Fracture of bone of hip region" .
  ?patient omop_cdm:has_gender/a/rdfs:label ?gender .
  ?patient omop_cdm:year_of_birth ?birth_year .
  ?condition omop_cdm:start_date ?start .
BIND(YEAR(?start) - ?birth_year AS ?age) . }
GROUP BY ?gender ?age ORDER BY ?gender ?age
""")
  assert len(l) == 70

  
def bench_omop_cdm_3():
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

def bench_omop_cdm_3_static():
  q, l = do(omop_cdm_world, """
PREFIX umls: <http://PYM/>
PREFIX atc: <http://PYM/ATC/>
PREFIX snomed: <http://PYM/SNOMEDCT_US/>

SELECT ?patient ?drug_era { # SPARQL query for STOPP B1
  ?patient omop_cdm:has_drug_era ?drug_era .
  ?drug_era omop_cdm:has_concept/a/rdfs:subClassOf*STATIC atc:C01AA05 .
  ?patient omop_cdm:has_condition_era/omop_cdm:has_concept/a/rdfs:subClassOf*STATIC snomed:84114007.
}""")
  assert len(l) == 726

def bench_omop_cdm_4():
  q, l = do(omop_cdm_world, """
PREFIX umls: <http://PYM/>
PREFIX atc: <http://PYM/ATC/>
PREFIX snomed: <http://PYM/SNOMEDCT_US/>

SELECT DISTINCT ?patient {
  #?patient a omop_cdm:Person .
  ?patient omop_cdm:has_drug_era ?drug_era1 .
  ?drug_era1 omop_cdm:has_concept/a ?aspirin .
        { ?aspirin rdfs:subClassOf* atc:B01AC06 . }
  UNION { ?aspirin rdfs:subClassOf* atc:A01AD05 . }
  UNION { ?aspirin rdfs:subClassOf* atc:N01BA01 . }

  ?patient omop_cdm:has_condition_era/omop_cdm:has_concept/a/rdfs:subClassOf* snomed:13200003.
}""")
  #if FIRST: print(q.sql)
  assert len(l) == 52

def bench_omop_cdm_4_static():
  q, l = do(omop_cdm_world, """
PREFIX umls: <http://PYM/>
PREFIX atc: <http://PYM/ATC/>
PREFIX snomed: <http://PYM/SNOMEDCT_US/>

SELECT DISTINCT ?patient {
  #?patient a omop_cdm:Person .
  ?patient omop_cdm:has_drug_era ?drug_era1 .
  ?drug_era1 omop_cdm:has_concept/a ?aspirin .
  STATIC {
          { ?aspirin rdfs:subClassOf* atc:B01AC06 . }
    UNION { ?aspirin rdfs:subClassOf* atc:A01AD05 . }
    UNION { ?aspirin rdfs:subClassOf* atc:N01BA01 . }
  }

  ?patient omop_cdm:has_condition_era/omop_cdm:has_concept/a/rdfs:subClassOf*STATIC snomed:13200003.
}""")
  if FIRST: print(q.sql)
  q.sql = """
SELECT DISTINCT q1.s FROM objs q3 , objs q2 , objs q1 , objs q6 , objs q5 , objs q4
WHERE q1.p=1330557 AND q2.s=q1.o AND q2.p=1330495 AND q3.s=q2.o AND q3.p=6 AND q4.s=q1.s AND q4.p=1330554 AND q5.s=q4.o AND q5.p=1330495 AND q6.s=q5.o AND q6.p=6 AND q3.o IN (4411,4413,210671) AND q6.o IN (34355,14034,14110,34364,34371,42048,66628,186679,440278,579011,600200,931375,1235602,186228,1208602,1244701,66621,186533,186535,186537,186539,186541,186543,186545,186547,278742,278759,278771,307276,542347,604948,913194,1235420,1235558,1235574,1243207,1244697,1244699,1244703,1244705,1272684,169258,186609,186641,186647,186649,278627,450633,450641,549654,186618,186653,186659,186661,278624,27315,47945,171226,186171,186252,186314,186685,278630,278643,278658,323284,662247,838315,1158366,1228539,1228761,1228763,1228767,1228769,1228771,1235560,1244683,1244687,1272686,5103,186226,278542,278544,278555,278557,955689,1229661,1235430,1244681,1270644,1270646,186681,186683,307280,307283,323276,186244,186635,323278,985258,186318,186572,186584,186605,186707,186718,186740,278747,278764,323291,323293,1244685,1244689,278552,278641,278654,911242,1167274,1228765,911192,1230115,66624,76907,186564,186570,76917,186531,186556,278753,186576,186598,307278,186582,1244695,76857,186613,186615,186627,186280,186643,186645,186663,186671,186257,186673,186255,278621,450638,76986,186699,186705,76867,186621,186623,186288,186655,186657,186261,186259,323288,186736,469343,469349,476898,555618,752914,186270,186302,186316,186240,278635,323272,278648,323286,186248,278656,186320,1274324,930627,186167,278546,278548,1260168,1271589,186130,186675,186637,186677,773628,11568,186246,186276,186307,76911,186568,186596,76920,186580,186560,186603,76990,186703,186729,76999,186714,186696,186734,1259823,1259801,76923,186586,186594,186549,186566,186551,186558,278755,278757,186578,186601,76861,76877,186263,551950,186630,186632,186282,186294,186669,186667,186284,186312,186310,186727,77004,186721,186687,186701,76871,76995,186265,186290,186292,186710,186716,186738,307285,186731,307288,186273,186305,1271587,1285503,278550,76930,186592,77008,186725,186554,186590,76879,186267,186298,186300,186691,186723,186689,186712,186693)

"""
  assert len(l) == 52




def bench_omop_cdm_99p():
  q, l = do(omop_cdm_world, """
PREFIX umls: <http://PYM/>
PREFIX atc: <http://PYM/ATC/>
PREFIX snomed: <http://PYM/SNOMEDCT_US/>

SELECT DISTINCT ?patient {
  #?patient a omop_cdm:Person .
  ?patient omop_cdm:has_condition_era/a ?c.
  ?patient omop_cdm:has_drug_era/a ?d.
}""")
  if FIRST:
    print(q.sql)
    print(len(l))

    q.sql = """
SELECT DISTINCT q1.s FROM objs q1 , objs q2 WHERE q1.p=1330554 AND q2.s=q1.o AND q2.p=6

INTERSECT

SELECT DISTINCT q3.s FROM objs q3 , objs q4 WHERE q3.p=1330557 AND q4.s=q3.o AND q4.p=6

"""

  
def bench_omop_cdm_5():
  q, l = do(omop_cdm_world, """
PREFIX umls: <http://PYM/>
PREFIX atc: <http://PYM/ATC/>
PREFIX snomed: <http://PYM/SNOMEDCT_US/>

SELECT ?patient { # SPARQL query for STOPP C2
  #?patient a omop_cdm:Person .

  ?patient omop_cdm:has_drug_era ?drug_era1 .
  ?drug_era1 omop_cdm:has_concept/a ?aspirin .
        { ?aspirin rdfs:subClassOf* atc:B01AC06 . }
  UNION { ?aspirin rdfs:subClassOf* atc:A01AD05 . }
  UNION { ?aspirin rdfs:subClassOf* atc:N01BA01 . }
  
  ?patient omop_cdm:has_condition_era/omop_cdm:has_concept/a/rdfs:subClassOf* snomed:13200003.

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

def bench_omop_cdm_5_static():
  q, l = do(omop_cdm_world, """
PREFIX umls: <http://PYM/>
PREFIX atc: <http://PYM/ATC/>
PREFIX snomed: <http://PYM/SNOMEDCT_US/>

SELECT ?patient { # SPARQL query for STOPP C2
  #?patient a omop_cdm:Person .

  ?patient omop_cdm:has_drug_era ?drug_era1 .
  ?drug_era1 omop_cdm:has_concept/a ?aspirin .
  STATIC {
          { ?aspirin rdfs:subClassOf* atc:B01AC06 . }
    UNION { ?aspirin rdfs:subClassOf* atc:A01AD05 . }
    UNION { ?aspirin rdfs:subClassOf* atc:N01BA01 . }
  }

  ?patient omop_cdm:has_condition_era/omop_cdm:has_concept/a/rdfs:subClassOf*STATIC snomed:13200003.

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


def bench_omop_cdm_6():
  q, l = do(omop_cdm_world, """
PREFIX umls: <http://PYM/>
PREFIX atc: <http://PYM/ATC/>
PREFIX snomed: <http://PYM/SNOMEDCT_US/>

SELECT DISTINCT ?patient ?birth_year {
  ?patient omop_cdm:has_condition_era/omop_cdm:has_concept/a/rdfs:subClassOf*/rdfs:label "Fracture of bone of hip region" .
  ?patient omop_cdm:year_of_birth ?birth_year .
}
""")
  assert len(l) == 127
  
def bench_omop_cdm_6_static():
  q, l = do(omop_cdm_world, """
PREFIX umls: <http://PYM/>
PREFIX atc: <http://PYM/ATC/>
PREFIX snomed: <http://PYM/SNOMEDCT_US/>

SELECT DISTINCT ?patient ?birth_year {
  ?patient omop_cdm:has_condition_era/omop_cdm:has_concept/a/rdfs:subClassOf*STATIC/rdfs:label "Fracture of bone of hip region" .
  ?patient omop_cdm:year_of_birth ?birth_year .
}
""")
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
  SHOW_SQL = "--sql" in sys.argv
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
    global FIRST
    
    s = ""
    total_t = 0.0
    for test in TESTS or ALL_TESTS:
      func = globals()[test]
      FIRST = True
      func()
      FIRST = False
      t = time.perf_counter()
      for i in range(NB): func()
      t = (time.perf_counter() - t) / NB
      s += "test_%s %s\n" % (test, t * 1000.0)
      total_t += t
    s += "test_TOTAL %s\n" % (total_t * 1000.0)
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
