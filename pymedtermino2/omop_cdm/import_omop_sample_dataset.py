# Owlready2
# Copyright (C) 2021 Jean-Baptiste LAMY
# LIMICS (Laboratoire d'informatique médicale et d'ingénierie des connaissances en santé), UMR_S 1142
# University Sorbonne Paris Nord, Bobigny, France

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


# Please change the following paths:

# A new file where the Owlready quadstore will be stored
QUADSTORE_FILE = "/home/jiba/src/abimed/omop_cdm/quadstore_omop_sample_dataset.sqlite3"

# Path to the UMLS ZIP file
UMLS_FILE = "/home/jiba/telechargements/base_med/umls-2020AA-full.zip"

# Path to the OMOP Athena CONCEPT.csv file, which can be extracted from the vocabulary ZIP file that can de downloaded from https://athena.ohdsi.org
ATHENA_CONCEPT_FILE = "/home/jiba/abimed/omop_cdm/terminos/CONCEPT.csv"

# Path to the OMOP-CDM ontology file
OMOP_ONTOLOGY_FILE = "./abimed/onto/omop_cdm_v6.owl"

# Path to the OMOP-CDM CSV v5 specification file (sample data use OMOP-CDM v5), can be downloaded from https://github.com/OHDSI/CommonDataModel/blob/v5.3.1/OMOP_CDM_v5_3_1.csv
OMOP_CDM_v5_FILE = "./abimed/omop_cdm/OMOP_CDM_v5_3_1.csv"

# Path to the OMOP sample data ZIP file, can be downloaded from http://www.ltscomputingllc.com/downloads/
OMOP_SAMPLE_DATA_FILE = "./abimed/omop_cdm/synpuf1k_omop_cdm_5.2.2.zip"

# Path to the generated OMOP sample data NT (leave empty to not generate the file; it is useful only if you want to use the data outside Owlready)
SAMPLE_DATA_NT_FILE = ""



import sys, os, csv, types, datetime, operator, functools, zipfile, io, types
from collections import defaultdict
from owlready2 import *
from owlready2.pymedtermino2 import *
from owlready2.pymedtermino2.umls import *

if os.path.exists(QUADSTORE_FILE): os.unlink(QUADSTORE_FILE)
default_world.set_backend(filename = QUADSTORE_FILE) #, sqlite_tmp_dir = TMP_DIR)


# 1) Load UMLS

import_umls(UMLS_FILE,
            terminologies = ["SNOMEDCT_US", "RXNORM", "ICD9CM", "HCPCS"],
            extract_groups = False, extract_attributes = False, extract_relations = False, extract_definitions = False,
)
default_world.save()


# 2) Load OMOP-CDM terminologies

PYM = get_ontology("http://PYM/").load()

with PYM:
  class omop_id(AnnotationProperty): pass
  
f = csv.reader(open(ATHENA_CONCEPT_FILE), delimiter = "\t")
next(f)

OMOP_TERMINOS = ["Drug Type", "Visit", "Gender", "Visit Type", "CMS Place of Service"]
OMOP_TERMINOS = { i : [] for i in OMOP_TERMINOS }

TERMINOS = {
  "SNOMED"   : PYM["SNOMEDCT_US"],
  "RxNorm"   : PYM["RXNORM"],
  "HCPCS"    : PYM["HCPCS"],
  "ICD9Proc" : PYM["ICD9CM"],
  }

default_world.graph.db.isolation_level = None
default_world.graph.db.execute("BEGIN;")

l = []
n = 0
with PYM:
  for row in f:
    omop_id, termino, code = int(row[0]), row[3], row[6]
    
    if termino in OMOP_TERMINOS:
      OMOP_TERMINOS[termino].append((omop_id, code, row[1]))
      
    pym_termino = TERMINOS.get(termino)
    if pym_termino:
      c = pym_termino[code]
      if c: c.omop_id.append(omop_id)
    n += 1
    if n % 10000 == 0: print(n)

for termino in OMOP_TERMINOS:
  with PYM.get_namespace("http://PYM/SRC/"):
    Termino = types.new_class("OMOP_%s" % termino.replace(" ", "_"), (PYM["SRC"],))
    Termino.label = ["OMOP %s" % termino]
    Termino.terminology = PYM["SRC"]
    
  with PYM.get_namespace("http://PYM/%s/" % Termino.name):
    for omop_id, code, label in OMOP_TERMINOS[termino]:
      concept = types.new_class(code, (Termino,))
      concept.label       = [label]
      concept.omop_id     = [omop_id]
      concept.terminology = Termino
      
default_world.save()


# 3) Load OMOP sample dataset

PYM = get_ontology("http://PYM/").load()
omop_cdm = get_ontology(OMOP_ONTOLOGY_FILE).load()
data     = get_ontology("http://test.org/data.owl")

f = csv.reader(open(OMOP_CDM_v5_FILE))
lignes = list(f)[1:]

table_2_fields = defaultdict(list)

for row, field, required, type, description, table, cdm in lignes:
  table_2_fields[table].append(field)

REVERSE_RELATIONS = { "person_id", "note_id", "visit_detail_id", "visit_occurrence_id"}

def omop_name_2_owl(s, table):
  if   s.startswith("%s_" % table): s = s[len(table) + 1:]
  elif table.endswith("_exposure") or table.endswith("_occurrence") or table.endswith("_era"):
    if   table.endswith("_exposure"):   table_simplifiee = table.replace("_exposure",   "")
    elif table.endswith("_occurrence"): table_simplifiee = table.replace("_occurrence", "")
    elif table.endswith("_era"):        table_simplifiee = table.replace("_era",        "")
    if s.startswith("%s_" % table_simplifiee): s = s[len(table_simplifiee) + 1:]

  if table.endswith("_nlp") and s.startswith("nlp_"): s = s[4:]
  if s == "drug_concept": s = "concept"
  if s.endswith("_id"): s = "has_%s" % s[:-3]
  if s.endswith("_concept") and (not s.endswith("_as_concept")) and (s != "has_concept"):
    s2 = s[:-8]
    s = s2
  return s


class_id_2_obj = {}
delayed_relations = []

default_world.graph.db.isolation_level = None
default_world.graph.db.execute("BEGIN;")

RE_OMOP_CDM_NAME = re.compile("(.*?)\.(.*?)#(.*?) AS (.*?)$")

def get_range_class(owl_prop, field):
  range_class = owl_prop.domain[0]
  if not isinstance(range_class, Or): return range_class
  for x in owl_prop.omop_cdm_name:
    match = RE_OMOP_CDM_NAME.search(x)
    x_table, x_field, x_order, x_range = match.group(1), match.group(2), match.group(3), match.group(4)
    if x_field == field:
      return omop_cdm[x_range]
  raise ValueError("Cannot find range class for property %s for field %s, range is %s!" % (owl_prop, field, range_class))

next_concept_id = 1

with data:
  with zipfile.ZipFile(OMOP_SAMPLE_DATA_FILE, "r") as z:
    def parse(table, offset = 0):
      global next_concept_id
      owl_class_name = "".join(mot.capitalize() for mot in table.split("_"))
      owl_class = omop_cdm[owl_class_name]

      print("Import", table, "with fields", table_2_fields[table])
      
      nb = 0
      for row in csv.reader(io.TextIOWrapper(z.open("%s.csv" % table, "r")), delimiter = "\t"):
        nb += 1
        
        id = row[offset]
        obj = owl_class("%s%s" % (table, id))
        class_id_2_obj[owl_class, id] = obj
        
        for i, cell in enumerate(row[offset:]):
          if not cell: continue
          
          field = table_2_fields[table][i + offset]
          
          if (i != 0) and(field in REVERSE_RELATIONS):
            reverse = True
            owl_prop_name = "has_%s" % table
          else:
            reverse = False
            owl_prop_name = omop_name_2_owl(field, table)
            
          owl_prop = omop_cdm[owl_prop_name]
          if owl_prop is None:
            raise ValueError("No property named '%s'!" % owl_prop_name)
            
          if isinstance(owl_prop, ObjectPropertyClass):
            if reverse:
              range_class = owl_prop.domain[0]
              if isinstance(range_class, Or):
                for x in owl_prop.omop_cdm_name:
                  match = RE_OMOP_CDM_NAME.search(x)
                  x_table, x_field, x_order, x_range = match.group(1), match.group(2), match.group(3), match.group(4)
                  if x_field == field:
                    range_class = omop_cdm[x_range]
                    break
              value = class_id_2_obj.get((range_class, cell))
              
              if value is None: delayed_relations.append((range_class, cell, owl_prop, None, obj))
              else:             owl_prop[value].append(obj)
            else:
              if field.endswith("_concept_id") and (not field.endswith("_source_concept_id")):
                range_class = omop_cdm.Concept
                concept = default_world.search_one(omop_id = int(cell))
                if callable(concept):
                  #value = concept("c%s" % next_concept_id)
                  value = concept()
                  l = list(default_world.graph.execute("select * from objs where s=?", (value.storid,)))
                  if len(l) > 2:
                    print(value, value.storid)
                    for k in l: print(k)
                  next_concept_id += 1
                else:
                  value = None
              else:
                range_class = owl_prop.range[0]
                value = class_id_2_obj.get((range_class, cell))
              if value is None: delayed_relations.append((None, obj, owl_prop, range_class, cell))
              else:             owl_prop[obj].append(value)
          else:
            if   int               in owl_prop.range: cell = int              (cell)
            elif float             in owl_prop.range: cell = float            (cell)
            elif datetime.datetime in owl_prop.range: cell = datetime.datetime(*[int(j) for j in cell.replace(" ", "-").replace(":", "-").split("-")])
            elif datetime.date     in owl_prop.range: cell = datetime.date    (*[int(j) for j in cell.split("-")])
            owl_prop[obj].append(cell)
      
      
    parse("person")
    parse("condition_era")
    parse("drug_era")
    parse("visit_occurrence")
    parse("condition_occurrence")
    parse("procedure_occurrence")
    parse("drug_exposure")
    parse("measurement")
    parse("provider")
    parse("care_site")
    parse("location")
    
  for s_class, s, owl_prop, o_class, o in delayed_relations:
    if not s_class is None: s = class_id_2_obj.get((s_class, s))
    if not o_class is None: o = class_id_2_obj.get((o_class, o))
    if (not s is None) and (not o is None): owl_prop[s].append(o)
      
      
default_world.save()
print(len(default_world.graph), "RDF triples")
if SAMPLE_DATA_NT_FILE: default_world.save(SAMPLE_DATA_NT_FILE)
