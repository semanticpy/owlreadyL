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


# Please change the following paths and options:

# Path to the OMOP-CDM CSV specification file
OMOP_CDM_v6_FILE  = "./abimed/omop_cdm/OMOP_CDM_v6_0.csv"

# Path where the OMOP-CDM ontology file will be created
OMOP_ONTOLOGY_FILE = "./abimed/onto/omop_cdm_v6.owl"

# If true, split the ontology in several files, corresponding to teh various part of the OMOP-CDM model (clinical, survey, etc)
MODULAR = False

# True to fix datetime datatype (e.g. datetime attribute has datetime datatype and not date). In doubt, keep the default value
FIX_DATETIME = True

# Set of relations that should be reversed. Use an empty set to reverse no relation. In doubt, keep the default value
REVERSE_RELATIONS = { "person_id", "note_id", "visit_detail_id", "visit_occurrence_id"}

# Sets of tables. Please keep the default values, unless importing OMOP-CDM in a version different than 6.0
VOCABULARIES_TABLES  = {'concept', 'vocabulary', 'domain', 'concept_class', 'concept_relationship', 'relationship', 'concept_synonym', 'concept_ancestor', 'source_to_concept_map', 'drug_strength', }
METADATA_TABLES      = {'cdm_source', 'metadata', }
CLINICAL_TABLES      = {'person', 'observation_period', 'visit_occurrence', 'visit_detail', 'condition_occurrence', 'drug_exposure', 'procedure_occurrence', 'device_exposure', 'measurement', 'note', 'note_nlp', }
SURVEY_TABLES        = {'survey_conduct', 'observation', 'specimen', 'fact_relationship', }
HEALTH_SYSTEM_TABLES = {'location', 'location_history', 'care_site', 'provider', }
ECONOMICS_TABLES     = {'payer_plan_period', 'cost', }
DERIVED_TABLES       = {'drug_era', 'dose_era', 'condition_era', }
COHORT_TABLES        = {'cohort', 'cohort_definition', }

# Set of tables to import. If needed, you may restrict the set to the part of OMOP-CDM you need (as in the commented example below).
TABLES = VOCABULARIES_TABLES | METADATA_TABLES | CLINICAL_TABLES | SURVEY_TABLES | HEALTH_SYSTEM_TABLES | ECONOMICS_TABLES | DERIVED_TABLES | COHORT_TABLES
#TABLES = CLINICAL_TABLES | HEALTH_SYSTEM_TABLES | DERIVED_TABLES



import sys, os, csv, types, datetime, operator, functools
from collections import defaultdict

from owlready2 import *


omop_cdm = get_ontology("http://www.lesfleursdunormal.fr/static/_downloads/omop_cdm_v6.owl")
if MODULAR:
  omop_cdm_vocabularies = get_ontology("http://www.lesfleursdunormal.fr/static/_downloads/omop_cdm_v6_vocabularies.owl")
  omop_cdm_metadata = get_ontology("http://www.lesfleursdunormal.fr/static/_downloads/omop_cdm_v6_metadata.owl")
  omop_cdm_clinical = get_ontology("http://www.lesfleursdunormal.fr/static/_downloads/omop_cdm_v6_clinical.owl")
  omop_cdm_survey = get_ontology("http://www.lesfleursdunormal.fr/static/_downloads/omop_cdm_v6_survey.owl")
  omop_cdm_health_system = get_ontology("http://www.lesfleursdunormal.fr/static/_downloads/omop_cdm_v6_health_system.owl")
  omop_cdm_economics = get_ontology("http://www.lesfleursdunormal.fr/static/_downloads/omop_cdm_v6_economics.owl")
  omop_cdm_derived = get_ontology("http://www.lesfleursdunormal.fr/static/_downloads/omop_cdm_v6_derived.owl")
  omop_cdm_cohort = get_ontology("http://www.lesfleursdunormal.fr/static/_downloads/omop_cdm_v6_cohort.owl")
  omop_cdm.imported_ontologies = [omop_cdm_clinical, omop_cdm_derived, omop_cdm_health_system, omop_cdm_vocabularies, omop_cdm_metadata, omop_cdm_survey, omop_cdm_economics, omop_cdm_cohort]
  
f = csv.reader(open(OMOP_CDM_v6_FILE))
lignes = list(f)[1:]

table_2_owl = {}
field_2_owl = {}

def get_namespace(table):
  if not MODULAR: return omop_cdm
  
  if   table in VOCABULARIES_TABLES: onto = omop_cdm_vocabularies
  elif table in METADATA_TABLES: onto = omop_cdm_metadata
  elif table in CLINICAL_TABLES: onto = omop_cdm_clinical
  elif table in SURVEY_TABLES: onto = omop_cdm_survey
  elif table in HEALTH_SYSTEM_TABLES: onto = omop_cdm_health_system
  elif table in ECONOMICS_TABLES: onto = omop_cdm_economics
  elif table in DERIVED_TABLES: onto = omop_cdm_derived
  elif table in COHORT_TABLES: onto = omop_cdm_cohort
  return onto.get_namespace(omop_cdm.base_iri)

def get_prioritary_namespace(*namespaces):
  if not MODULAR: return omop_cdm
  return sorted(namespaces, key = lambda namespace: omop_cdm.imported_ontologies.index(namespace.ontology))[-1]
  



TABLES = set(TABLES)
prop_2_domain_2_range = defaultdict(dict)

FIELDS = { field for field, required, type, description, table in lignes }

def calcule_nom_owl(s, table):
  if   s.startswith("%s_" % table): s = s[len(table) + 1:]
  elif table.endswith("_exposure") or table.endswith("_occurrence") or table.endswith("_era"):
    if   table.endswith("_exposure"):   table_simplifiee = table.replace("_exposure",   "")
    elif table.endswith("_occurrence"): table_simplifiee = table.replace("_occurrence", "")
    elif table.endswith("_era"):        table_simplifiee = table.replace("_era",        "")
    if s.startswith("%s_" % table_simplifiee): s = s[len(table_simplifiee) + 1:]

  if table.endswith("_nlp") and s.startswith("nlp_"): s = s[4:]
  if s == "drug_concept": s = "concept"
  if s.endswith("_concept") and not s.endswith("_as_concept"):
    s2 = s[:-8]
    if not s2 in FIELDS: s = s2
  return s

if MODULAR: namespace = omop_cdm_clinical.get_namespace(omop_cdm.base_iri)
else:       namespace = omop_cdm
with namespace:
  class Concept(Thing): pass
  class OmopCDMThing(Thing): pass
  class Duration(OmopCDMThing): pass
  class DateDuration(Duration): pass
  class DatetimeDuration(Duration): pass
  class Event(OmopCDMThing): pass
  class ClinicalElement(OmopCDMThing): pass
  class Exposure(ClinicalElement): pass
  class Occurrence(ClinicalElement): pass
  class Era(ClinicalElement): pass
  class BasePerson(OmopCDMThing): pass
  class BaseVisit(Occurrence, DateDuration, DatetimeDuration): pass
  
  class omop_cdm_name(AnnotationProperty): pass

attribute_id = 0
for nom in TABLES:
  with get_namespace(nom):
    nom_owl = "".join(mot.capitalize() for mot in nom.split("_"))
    Classe = types.new_class(nom_owl, (OmopCDMThing,))
    Classe.omop_cdm_name = nom
    table_2_owl[nom] = Classe
    
    if   nom.endswith("_exposure"):   Classe.is_a = [Exposure]
    elif nom.startswith("visit_"):    Classe.is_a = [BaseVisit]
    elif nom.endswith("_occurrence"): Classe.is_a = [Occurrence]
    elif nom.endswith("_era"):        Classe.is_a = [Era]
    elif nom == "measurement":        Classe.is_a = [Occurrence]
    elif nom == "person":             Classe.is_a = [BasePerson]
    elif nom == "provider":           Classe.is_a = [BasePerson]
    elif nom == "visit_detail":       Classe.is_a = [Occurrence]
    elif nom == "note":               Classe.is_a = [ClinicalElement]
    elif nom == "observation_period": Classe.is_a = [ClinicalElement]
    
ABSTRACT_CLASSES = [ClinicalElement, BaseVisit, Exposure, Occurrence, Era, BasePerson]

for field, required, type, description, table in lignes:
    if not table in TABLES: continue
    type = type.upper()
    
    nom_owl = field
    reverse = False
    if field.endswith("_id") and (field != "%s_id" % table): # Clef étrangère => relation
      range = Thing
      if field.endswith("_concept_id"):
        range = Concept
        
      else:
        mots = description.split()
        precedent = precedent2 = ""
        for mot in mots:
          if (mot == "table") or (mot == "table;") or (mot == "table,") or (mot == "table."):
            if   precedent.lower() in table_2_owl:
              range = table_2_owl[precedent.lower()]
              break
            elif "%s_%s" % (precedent2.lower(), precedent.lower()) in table_2_owl:
              range = table_2_owl["%s_%s" % (precedent2.lower(), precedent.lower())]
              break
          precedent2 = precedent
          precedent  = mot
          
        else:
          if field.endswith("_id"):
            s = field[:-3]
            if s in table_2_owl: range = table_2_owl[s]
             

      candidate_namepaces = [get_namespace(table)]
      if not range is Thing: candidate_namepaces.append(range.namespace)

      with get_prioritary_namespace(*candidate_namepaces):
        if field in REVERSE_RELATIONS:
          reverse = True
          nom_owl = "has_%s" % table
          Prop = types.new_class(nom_owl, (ObjectProperty,))
          if Prop.name == "note_nlp": Prop.python_name = "notes_nlp"
          else:                       Prop.python_name = Prop.name[4:] + "s"
        else:
          nom_owl = field[:-3]
          nom_owl = calcule_nom_owl(nom_owl, table)
          nom_owl = "has_%s" % nom_owl
          Prop = types.new_class(nom_owl, (ObjectProperty, FunctionalProperty,))
          Prop.python_name = Prop.name[4:]
          
        
        
    else:
      nom_owl = calcule_nom_owl(nom_owl, table)
      #if   FIX_DATETIME and field.endswith("_datetime"): range = datetime.datetime
      #elif FIX_DATETIME and field.endswith("_date"):     range = datetime.date
      if   type.startswith("INTEGER"):  range = int
      elif type.startswith("BIGINT"):   range = int
      elif type.startswith("STRING"):   range = str
      elif type.startswith("VARCHAR"):  range = str
      elif type.startswith("NVARCHAR"): range = str
      elif type.startswith("CLOB"):     range = str
      elif type.startswith("FLOAT"):    range = float
      elif type.startswith("DATETIME"):
        if FIX_DATETIME and field.endswith("_date"): nom_owl.replace("_date", "_datetime")
        range = datetime.datetime
      elif type.startswith("DATE"):
        if FIX_DATETIME and field.endswith("_datetime"): nom_owl.replace("_datetime", "_date")
        range = datetime.date
      else: raise ValueError("Unknown type %s!" % type)
      
      with get_namespace(table):
        Prop = types.new_class(nom_owl, (DataProperty, FunctionalProperty,))
      
      
    domain = table_2_owl[table]
    if Prop.name == "id":
      domain = OmopCDMThing
      range  = Or([int, str])

    if   isinstance(range, Or):         range0 = "int|str"
    elif isinstance(range, ThingClass): range0 = range.name
    else:                               range0 = range.__name__
    if reverse: domain, range = range, domain
    prop_2_domain_2_range[Prop][domain] = (range, required, reverse)
    
    if   Prop.name == "start_datetime": domain.is_a.append(DatetimeDuration)
    elif Prop.name == "start_date":     domain.is_a.append(DateDuration)
    elif Prop.name == "datetime":       domain.is_a.append(Event)
    
    attribute_id += 1
    #Prop.omop_cdm_name.append("%s.%s#%s" % (table_2_owl[table].omop_cdm_name.first(), field, attribute_id))
    Prop.omop_cdm_name.append("%s.%s#%s AS %s" % (table_2_owl[table].omop_cdm_name.first(), field, attribute_id, range0))
    if reverse: reversed_note = "reversed relation, "
    else:       reversed_note = ""
    if description: Prop.comment.en.append("(%sfor %s:) %s" % (reversed_note, table_2_owl[table].name, description))
    
    field_2_owl[field] = Prop

    
ABSTRACT_CLASSES_2_CLASSES = { abstract_class : {leaf_class
                                                 for leaf_class in abstract_class.descendants(include_self = False)
                                                 if  leaf_class.omop_cdm_name}
                               for abstract_class in ABSTRACT_CLASSES }

for abstract_class, leaf_classes in ABSTRACT_CLASSES_2_CLASSES.items():
  common_super_classes = functools.reduce(operator.and_, [set(leaf_class.is_a) for leaf_class in leaf_classes])
  common_super_classes.discard(abstract_class)
  if common_super_classes:
    abstract_class.is_a.extend(common_super_classes)
    for leaf_class in leaf_classes:
      for common_super_class in common_super_classes:
        leaf_class.is_a.remove(common_super_class)
        
        
for Prop, domain_2_range in prop_2_domain_2_range.items():
  if   (Prop.name == "start_datetime") or (Prop.name == "end_datetime"):
    Prop.domain.reinit([DatetimeDuration])
    Prop.range .reinit([datetime.datetime])
    DatetimeDuration.is_a.append(Prop.only(datetime.datetime))
  elif (Prop.name == "start_date") or (Prop.name == "end_date"):
    Prop.domain.reinit([DateDuration])
    Prop.range .reinit([datetime.date])
    DateDuration.is_a.append(Prop.only(datetime.date))
  elif (Prop.name == "datetime") or (Prop.name == "date"):
    Prop.domain.reinit([Event])
    if Prop.name == "datetime":
      Prop.range.reinit([datetime.datetime])
      Event.is_a.append(Prop.only(datetime.datetime))
    else:
      Prop.range.reinit([datetime.date])
      Event.is_a.append(Prop.only(datetime.date))
      
  else:
    domains = set(domain_2_range.keys())
    if len(domains) > 1:
      for abstract_class, leaf_classes in ABSTRACT_CLASSES_2_CLASSES.items():
        if domains.issuperset(leaf_classes):
          abstract_class_ranges = { domain_2_range[domain] for domain in leaf_classes }
          if len(abstract_class_ranges) == 1:
            domains.difference_update(leaf_classes)
            domains.add(abstract_class)
            for leaf_class in leaf_classes: del domain_2_range[leaf_class]
            domain_2_range[abstract_class] = list(abstract_class_ranges)[0]
            
    if   len(domains) == 1:
      Prop.domain.reinit([list(domains)[0]])
    elif len(domains) > 1:
      Prop.domain.reinit([Or(list(domains))])
      
    for domain, (range, required, reverse) in domain_2_range.items():
      if domain is Thing: continue
      with get_prioritary_namespace(Prop.namespace, domain.namespace):
        domain.is_a.append(Prop.only(range))
        if required:
          if reverse:
            range.is_a.append(Inverse(Prop).some(domain))
          else:
            domain.is_a.append(Prop.some(range))
        
    #ranges = set(domain_2_range.values())
    ranges = set(range for (range, required, reverse) in domain_2_range.values())
    if   Thing in ranges:
      pass
    elif len(ranges) == 1:
      range = list(ranges)[0]
      Prop.range.reinit([range])
    
      
  
if len(omop_cdm.Concept.is_a) > 1: omop_cdm.Concept.is_a.remove(Thing)

d = {}
for Prop in omop_cdm.properties():
  n = Prop.python_name or Prop.name
  if n in d:
    print("Prop name clash for:", d[n], Prop)
  else: d[n] = Prop


omop_cdm.save(OMOP_ONTOLOGY_FILE)
if MODULAR:
  omop_cdm_vocabularies .save(OMOP_ONTOLOGY_FILE.replace(".owl", "_vocabularies.owl"))
  omop_cdm_metadata     .save(OMOP_ONTOLOGY_FILE.replace(".owl", "_metadata.owl"))
  omop_cdm_clinical     .save(OMOP_ONTOLOGY_FILE.replace(".owl", "_clinical.owl"))
  omop_cdm_survey       .save(OMOP_ONTOLOGY_FILE.replace(".owl", "_survey.owl"))
  omop_cdm_health_system.save(OMOP_ONTOLOGY_FILE.replace(".owl", "_health_system.owl"))
  omop_cdm_economics    .save(OMOP_ONTOLOGY_FILE.replace(".owl", "_economics.owl"))
  omop_cdm_derived      .save(OMOP_ONTOLOGY_FILE.replace(".owl", "_derived.owl"))
  omop_cdm_cohort       .save(OMOP_ONTOLOGY_FILE.replace(".owl", "_cohort.owl"))
  
print(len(omop_cdm.graph), "RDF triples")
