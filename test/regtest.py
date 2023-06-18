import sys, os, unittest, tempfile, atexit, datetime, subprocess, multiprocessing
from io import StringIO, BytesIO

"""
This file contains regression tests for Owlready2.

For testing dependencies see README.md in this directory.
"""

try:
  import rdflib
except:
  pass

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import owlready2, owlready2.util
from owlready2 import *
from owlready2.base import _universal_abbrev_2_datatype, _universal_datatype_2_abbrev
import owlready2.sparql

from owlready2.ntriples_diff import *

print("Testing Owlready2 version 2-%s located in %s" % (VERSION, owlready2.__file__))


set_log_level(0)

next_id = 0

TMPFILES = []
def remove_tmps():
  for f in TMPFILES:
    os.unlink(f)
    if os.path.exists(f + "-journal"): os.unlink(f + "-journal")
atexit.register(remove_tmps)

fileno, filename = tempfile.mkstemp()
TMPFILES.append(filename)
default_world.set_backend(filename = filename)

HERE = os.path.dirname(os.path.abspath(__file__)) or "."
onto_path.append(HERE)
get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()

SHOW_SQL = False
if "--sql" in sys.argv:
  SHOW_SQL = True
  sys.argv.remove("--sql")

  
class BaseTest(object):
  def setUp(self):
    self.nb_triple = len(default_world.graph)
    
  def assert_nb_created_triples(self, x):
    assert (len(default_world.graph) - self.nb_triple) == x
    
  def assert_triple(self, s, p, o, d = None, world = default_world):
    if d is None:
      if not world._has_obj_triple_spo(s, p, o):
        if s > 0: s = world._unabbreviate(s)
        p = world._unabbreviate(p)
        if o > 0: o = world._unabbreviate(o)
        print("MISSING TRIPLE", s, p, o)
        raise AssertionError
    else:
      if not world._has_data_triple_spod(s, p, o, d):
        if s > 0: s = world._unabbreviate(s)
        p = world._unabbreviate(p)
        print("MISSING TRIPLE", s, p, o, d)
        raise AssertionError
    
  def assert_not_triple(self, s, p, o, d = None, world = default_world):
    if d is None:
      if world._has_obj_triple_spo(s, p, o):
        if s > 0: s = world._unabbreviate(s)
        p = world._unabbreviate(p)
        if o > 0: o = world._unabbreviate(o)
        print("UNEXPECTED TRIPLE", s, p, o)
        raise AssertionError
    else:
      if world._has_data_triple_spod(s, p, o, d):
        if s > 0: s = world._unabbreviate(s)
        p = world._unabbreviate(p)
        print("UNEXPECTED TRIPLE", s, p, o, d)
        raise AssertionError
      
  def assert_ntriples_equivalent(self, nt2, nt1):
    removed, added = diff(nt1, nt2)
    
    for s,p,o, l in removed:
      if l: print("-", s, p, o, ". # line", l)
    for s,p,o, l in added:
      if l: print("+", s, p, o, ". # line", l)
      
    assert not removed
    assert not added

  def new_tmp_file(self):
    fileno, filename = tempfile.mkstemp()
    TMPFILES.append(filename)
    return filename
    
  def new_world(self, exclusive = True, enable_thread_parallelism = False):
    filename = self.new_tmp_file()
    world = World(filename = filename, exclusive = exclusive, enable_thread_parallelism = enable_thread_parallelism)
    return world
  
  def new_ontology(self):
    global next_id
    next_id += 1
    return get_ontology("http://t/o%s#" % next_id)
  
  


class Test(BaseTest, unittest.TestCase):
  def test_environment_1(self):
    e = owlready2.util.Environment()
    assert not e
    with e:
      assert e
      with e:
        assert e
      assert e
    assert not e
    
  def test_namespace_1(self):
    onto = self.new_ontology()
    n1 = onto.get_namespace("http://test/namespace/")
    n2 = onto.get_namespace("http://test/namespace/")
    assert n1 is n2
    
    onto2 = get_ontology(onto.base_iri)
    assert onto is onto2
    
  def test_namespace_2(self):
    n = get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test")
    assert not n.Pizza is None
    assert n.Pizza is n.Pizza
    assert IRIS["http://www.semanticweb.org/jiba/ontologies/2017/0/test#Pizza"] is n.Pizza
    
  def test_namespace_3(self):
    n = get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test")
    Pizza = n.Pizza
    iri   = Pizza.storid
    assert Pizza is n.Pizza
    Pizza = None
    import gc
    gc.collect(); gc.collect()
    assert iri in default_world._entities
    assert n.Pizza
    
  def test_namespace_4(self):
    n = get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test")
    x = n.Vegetable
    iri = x.storid
    assert x is n.Vegetable
    x = None
    import owlready2.namespace
    owlready2.namespace._cache = [None] * 1000
    import gc
    gc.collect(); gc.collect(); gc.collect()
    assert not iri in default_world._entities
    assert not n.Vegetable is None
    
  def test_namespace_5(self):
    n = get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test")
    pizza = n.Pizza(name = "pizza_namespace_3")
    assert pizza == n.pizza_namespace_3
    
  def test_namespace_6(self):
    n = self.new_ontology()
    class C(Thing): namespace = n
    assert C == n.C
    
  def test_namespace_7(self):
    o = self.new_ontology()
    n = o.get_namespace("http://test/test_namespace_5.owl")
    class C(Thing): namespace = n
    
    assert C is IRIS["http://test/test_namespace_5.owl#C"]
    
  def test_world_1(self):
    w1 = self.new_world()
    w2 = self.new_world()
    o1 = w1.get_ontology("http://test/test_world_1.owl")
    o2 = w2.get_ontology("http://test/test_world_1.owl")
    assert not w1 is w2
    assert not o1 is o2
    class C(Thing): namespace = o1
    C1 = C
    class C(Thing): namespace = o2
    C2 = C
    assert not C1 is C2
    assert o1.C is C1
    assert o2.C is C2
    
  def test_world_2(self):
    w1 = self.new_world()
    w2 = self.new_world()
    o1 = w1.get_ontology("http://test/test_world_2.owl")
    o2 = w2.get_ontology("http://test/test_world_2.owl")
    with o1:
      class C(Thing): pass
    
    assert C.namespace is o1
    assert C is o1.C
    assert len(w1.graph) > 0
    assert len(o1.graph) > 0
    
  def test_world_3(self):
    w1 = self.new_world()
    w2 = self.new_world()
    o1 = w1.get_ontology("http://test/test_world_3.owl")
    o2 = w2.get_ontology("http://test/test_world_3.owl")
    class C(Thing): namespace = o1
    c1 = C(name = "c1")
    with o2:
      c2 = C(name = "c2")
      
    assert c1.namespace is o1
    assert c1 is o1.c1
    assert c2.namespace is o2
    assert c2 is o2.c2
    assert len(w2.graph) > 0
    assert len(o2.graph) > 0
    
  def test_world_4(self):
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    assert set(world.classes()) == { n.Meat, n.Tomato, n.Eggplant, n.Olive, n.Vegetable, n.NonPizza, n.Pizza, n.Cheese, n.VegetarianPizza, n.Topping }
    assert set(world.data_properties()) == { n.price }
    assert set(world.object_properties()) == { n.has_topping, n.has_main_topping, n.main_topping_of, n.topping_of }
    assert set(world.annotation_properties()) == { n.annot }
    assert set(world.properties()) == { n.price, n.has_topping, n.has_main_topping, n.main_topping_of, n.topping_of, n.annot }
    assert set(world.individuals()) == { n.mon_frometon, n.ma_tomate, n.ma_pizza }
    
  def test_world_5(self):
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    world.set_backend(filename = ":memory:")
    assert set(world.classes()) == { n.Meat, n.Tomato, n.Eggplant, n.Olive, n.Vegetable, n.NonPizza, n.Pizza, n.Cheese, n.VegetarianPizza, n.Topping }
    assert set(world.data_properties()) == { n.price }
    assert set(world.object_properties()) == { n.has_topping, n.has_main_topping, n.main_topping_of, n.topping_of }
    assert set(world.annotation_properties()) == { n.annot }
    assert set(world.properties()) == { n.price, n.has_topping, n.has_main_topping, n.main_topping_of, n.topping_of, n.annot }
    assert set(world.individuals()) == { n.mon_frometon, n.ma_tomate, n.ma_pizza }
    
  def test_world_6(self):
    world = self.new_world()
    o1 = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    o2 = get_ontology("http://test/test_ontology_1_1.owl")
    o3 = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/2/test_reasoning.owl").load()
    
  def test_world_7(self):
    world = self.new_world()
    o = world.get_ontology("http://test.org/t.owl")
    A = world._abbreviate("http://test.org/t.owl#A")
    B = world._abbreviate("http://test.org/t.owl#B")
    o._add_obj_triple_spo(A, rdf_type, owl_class)
    #missing triple (B, rdf_type, owl_class)
    o._add_obj_triple_spo(A, rdfs_subclassof, B)
    
    assert isinstance(o.A, ThingClass)
    assert o.B in o.A.is_a    
    
  def test_world_8(self):
    world = self.new_world()
    o1 = world.get_ontology("http://test.org/t1.owl")
    with o1:
      class A(Thing): pass
      
    world.set_backend(filename = self.new_tmp_file())
    o2 = world.get_ontology("http://test.org/t2.owl")
    with o2:
      class B(Thing): pass
      
  def test_world_9(self):
    world = self.new_world()
    o1 = world.get_ontology("http://test.org/t1.owl")
    
    n1 = world.graph._abbreviate("xxx1")
    o1.missing_entity
    n2 = world.graph._abbreviate("xxx2")
    
    assert n2 == n1 + 1
    
  def test_world_10(self):
    import sqlite3
    tmp   = self.new_tmp_file()
    world = self.new_world()
    world.set_backend(filename = tmp)
    world.save()
    world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test")
    world.graph.db.close()
    world = None
    
    db = sqlite3.connect(tmp)
    sql = db.cursor()
    sql.execute("""SELECT * from ontologies;""")
    assert sql.fetchall() == [(1, 'http://anonymous/', 0.0)]
    
    tmp   = self.new_tmp_file()
    tmp2  = self.new_tmp_file()
    world = self.new_world()
    world.set_backend(filename = tmp)
    world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    world.get_ontology("http://www.test.org/test.owl").save(tmp2)
    world.graph.db.close()
    world = None
    
    db = sqlite3.connect(tmp)
    sql = db.cursor()
    sql.execute("""SELECT * from ontologies;""")
    assert sql.fetchall() == []
    
  def test_world_10(self):
    world = self.new_world()
    onto = world.get_ontology("http://test.org/test.owl")
    
    before = world.graph.execute("SELECT * FROM sqlite_stat1").fetchall()
    
    with onto:
      class C(Thing): pass
      for i in range(2000):
        C()
        
    assert before != world.graph.execute("SELECT * FROM sqlite_stat1").fetchall()
    
  def test_ontology_1(self):
    o1 = get_ontology("http://test/test_ontology_1_1.owl")
    o2 = get_ontology("http://test/test_ontology_1_2.owl")
    class C(Thing): namespace = o1
    c1 = C(name = "c1")
    with o2:
      c2 = C(name = "c2")
      
    assert c1.namespace is o1
    assert c1 is o1.c1
    assert c2.namespace is o2
    assert c2 is o2.c2
    assert len(o2.graph) > 0
    
  def test_ontology_2(self):
    w  = self.new_world()
    o1 = w.get_ontology("http://test/test_ontology_2_1.owl")
    o2 = w.get_ontology("http://test/test_ontology_2_2.owl")
    with o1:
      class prop(DataProperty, FunctionalProperty): pass
      class C(Thing): pass
      c1 = C(name = "c1")
    with o2:
      c1.prop = 1
      
    assert len(o2.graph) == 2
    self.assert_triple(c1.storid, prop.storid, *to_literal(1), world = o2)
    
  def test_ontology_3(self):
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    assert set(n.classes()) == { n.Meat, n.Tomato, n.Eggplant, n.Olive, n.Vegetable, n.NonPizza, n.Pizza, n.Cheese, n.VegetarianPizza, n.Topping }
    assert set(n.data_properties()) == { n.price }
    assert set(n.object_properties()) == { n.has_topping, n.has_main_topping, n.main_topping_of, n.topping_of }
    assert set(n.annotation_properties()) == { n.annot }
    assert set(n.properties()) == { n.price, n.has_topping, n.has_main_topping, n.main_topping_of, n.topping_of, n.annot }
    assert set(n.individuals()) == { n.mon_frometon, n.ma_tomate, n.ma_pizza }
    
  def test_ontology_4(self):
    world = self.new_world()
    n = world.get_ontology("test").load()
    
    assert n.base_iri == "http://www.semanticweb.org/jiba/ontologies/2017/0/test#"
    assert set(n.classes()) == { n.Meat, n.Tomato, n.Eggplant, n.Olive, n.Vegetable, n.NonPizza, n.Pizza, n.Cheese, n.VegetarianPizza, n.Topping }
    assert n.Tomato.iri == "http://www.semanticweb.org/jiba/ontologies/2017/0/test#Tomato"
    
  def test_ontology_5(self):
    filename = os.path.abspath(os.path.join(os.path.dirname(__file__), "test.owl"))
    
    onto_path_save = onto_path[:]
    for i in onto_path: onto_path.remove(i)
    
    try:
      world = self.new_world()
      n = world.get_ontology("file://" + filename).load()
      
      assert n.base_iri == "http://www.semanticweb.org/jiba/ontologies/2017/0/test#"
      assert set(n.classes()) == { n.Meat, n.Tomato, n.Eggplant, n.Olive, n.Vegetable, n.NonPizza, n.Pizza, n.Cheese, n.VegetarianPizza, n.Topping }
      assert n.Tomato.iri == "http://www.semanticweb.org/jiba/ontologies/2017/0/test#Tomato"
      
    finally:
      onto_path.extend(onto_path_save)
      
  def test_ontology_6(self):
    world = self.new_world()
    filename = os.path.abspath(os.path.join(os.path.dirname(__file__), "test.owl"))
    n1 = world.get_ontology("file://" + filename).load()
    nb_triple = len(world.graph)
    
    n2 = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    assert n2 is n1
    assert len(world.graph) == nb_triple
    
  def test_ontology_7(self):
    w = self.new_world()
    o = w.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    
    assert o._parse_bnode(o.NonPizza.is_a[-1].storid) is o.NonPizza.is_a[-1]
    
  def test_ontology_8(self):
    w  = self.new_world()
    o1 = w.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test1.owl")
    o2 = w.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test2.owl")
    o1.imported_ontologies.append(o2)
    file = BytesIO()
    o1.save(file)
    assert """<owl:imports rdf:resource="http://www.semanticweb.org/jiba/ontologies/2017/0/test2.owl"/>""" in file.getvalue().decode("utf8")
    
  def test_ontology_9(self):
    w  = self.new_world()
    o1 = w.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test1.owl")
    o2 = w.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test2.owl")
    o1.imported_ontologies = [o2]
    file = BytesIO()
    o1.save(file)
    assert """<owl:imports rdf:resource="http://www.semanticweb.org/jiba/ontologies/2017/0/test2.owl"/>""" in file.getvalue().decode("utf8")
    
  def test_ontology_10(self):
    temp_dir = tempfile.TemporaryDirectory()
    onto_path.insert(0, temp_dir.name)
    
    w  = self.new_world()
    o1 = w.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test1.owl")
    o2 = w.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test2.owl")
    o1.imported_ontologies = [o2]
    o1.save()
    o2.save()
    
    w  = self.new_world()
    o1 = w.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test1.owl").load()
    assert len(o1.imported_ontologies) == 1
    
    onto_path.remove(temp_dir.name)
    temp_dir.cleanup()
    
  def test_ontology_11(self):
    temp_dir = tempfile.TemporaryDirectory()
    onto_path.insert(0, temp_dir.name)
    
    w  = self.new_world()
    o1 = w.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test1.owl")
    o2 = w.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test2.owl")
    o1.imported_ontologies = [o2]
    o1.save()
    o2.save()
    
    w  = self.new_world()
    o1 = w.get_ontology("file://%s/test1.owl" % temp_dir.name).load()
    assert len(o1.imported_ontologies) == 1
    
    onto_path.remove(temp_dir.name)
    temp_dir.cleanup()

  def test_ontology_12(self):
    temp_dir = tempfile.TemporaryDirectory()
    onto_path.insert(0, temp_dir.name)
    
    w  = self.new_world()
    o1 = w.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test1")
    o2 = w.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test2")
    o1.imported_ontologies = [o2]
    o1.save()
    o2.save()
    
    w  = self.new_world()
    o1 = w.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test1").load()
    assert len(o1.imported_ontologies) == 1
    
    onto_path.remove(temp_dir.name)
    temp_dir.cleanup()
    
  def test_ontology_13(self):
    temp_dir = tempfile.TemporaryDirectory()
    onto_path.insert(0, temp_dir.name)
    
    w  = self.new_world()
    o1 = w.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test1")
    o2 = w.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test2")
    o1.imported_ontologies = [o2]
    o1.save()
    o2.save()
    
    w  = self.new_world()
    o1 = w.get_ontology("file://%s/test1.owl" % temp_dir.name).load()
    assert len(o1.imported_ontologies) == 1
    
    onto_path.remove(temp_dir.name)
    temp_dir.cleanup()
    
  def test_ontology_14(self):
    temp_dir = tempfile.TemporaryDirectory()
    onto_path.insert(0, temp_dir.name)
    
    w  = self.new_world()
    o1 = w.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test1/")
    o2 = w.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test2/")
    o1.imported_ontologies = [o2]
    o1.save()
    o2.save()
    
    w  = self.new_world()
    o1 = w.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test1/").load()
    assert len(o1.imported_ontologies) == 1
    
    onto_path.remove(temp_dir.name)
    temp_dir.cleanup()
    
  def test_ontology_15(self):
    temp_dir = tempfile.TemporaryDirectory()
    onto_path.insert(0, temp_dir.name)
    
    w  = self.new_world()
    o1 = w.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test1/")
    o2 = w.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test2/")
    o1.imported_ontologies = [o2]
    o1.save()
    o2.save()
    
    w  = self.new_world()
    o1 = w.get_ontology("file://%s/test1.owl" % temp_dir.name).load()
    assert len(o1.imported_ontologies) == 1
    
    onto_path.remove(temp_dir.name)
    temp_dir.cleanup()
    
  def test_ontology_16(self):
    w = self.new_world()
    o = w.get_ontology("http://test.org/test_ontoslash/").load()
    
    assert o.base_iri == "http://test.org/test_ontoslash/"
    assert o.Class1
    assert o.Class2
    assert o.Class1.iri == "http://test.org/test_ontoslash/Class1"
    assert o.Class2.iri == "http://test.org/test_ontoslash/Class2"
    
  def test_ontology_17(self):
    w = self.new_world()
    o = w.get_ontology("file://%s/test_ontoslash.owl" % HERE).load()
    
    assert o.base_iri == "http://test.org/test_ontoslash/"
    assert o.Class1
    assert o.Class2
    assert o.Class1.iri == "http://test.org/test_ontoslash/Class1"
    assert o.Class2.iri == "http://test.org/test_ontoslash/Class2"
    
  def test_ontology_18(self):
    w = self.new_world()
    o = w.get_ontology("file://%s/test_ontoslash.owl" % HERE).load()
    
    assert len(o.imported_ontologies) == 1
    
    o2 = w.get_ontology("file://%s/test_ontoslash2.owl" % HERE).load()
    
    assert len(o2.imported_ontologies) == 1
    
  def test_ontology_19(self):
    w = self.new_world()
    o = w.get_ontology("http://test.org/t.owl")
    
    o.metadata.comment = "com1"
    o.metadata.comment.append("com2")
    
    self.assert_triple(o.storid, comment.storid, *to_literal("com1"), world = w)
    self.assert_triple(o.storid, comment.storid, *to_literal("com2"), world = w)
    
  def test_ontology_20(self):
    w = self.new_world()
    o = w.get_ontology("file://%s/test_ontoslash.owl" % HERE).load()
    
    o.metadata.comment = "com1"
    o.metadata.comment.append("com2")
    
    self.assert_triple(o.storid, comment.storid, *to_literal("com1"), world = w)
    self.assert_triple(o.storid, comment.storid, *to_literal("com2"), world = w)
    
  def test_ontology_21(self):
    w = self.new_world()
    o = w.get_ontology("file://%s/test_ontoslash.owl" % HERE).load()
    
    assert o.metadata.comment == ["TEST"]
    
  def test_ontology_22(self):
    w = self.new_world()
    o = w.get_ontology("http://test.org/test.owl")

    assert o.graph.get_last_update_time() == 0.0
    
    with o:
      class C(Thing): pass
      
    assert o.graph.get_last_update_time() != 0.0
    
  def test_ontology_23(self):
    world = self.new_world()
    filename = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_gca.owl"))
    onto = world.get_ontology("file://" + filename).load()

    gcas = list(onto.general_class_axioms())
    assert len(gcas) == 1
    assert gcas[0].is_a == [onto.CriticalDisorder]
    
    with onto:
      gca = GeneralClassAxiom(onto.Disorder & onto.has_location.some(onto.Heart)).is_a = [onto.CardiacDisorder]
      
    gcas = list(onto.general_class_axioms())
    assert len(gcas) == 2
      
  def test_ontology_24(self):
    world = self.new_world()
    filename = os.path.abspath(os.path.join(os.path.dirname(__file__), "test.owl"))
    onto = world.get_ontology("file://" + filename).load()
    
    r = set(onto.get_triples(onto.Pizza.storid))
    assert r == {(306, 39, '"Comment on Pizza"@en'), (306, 6, 11)}
    
    r = set(onto.get_triples(None, rdf_type, onto.Pizza.storid))
    assert r == {(320, 6, 306)}
    
    r = set(onto.get_triples(None, None, '"9.9"^^<http://www.w3.org/2001/XMLSchema#float>'))
    assert r == {(320, 311, 9.9, 58)}
    
  def test_ontology_25(self):
    w = self.new_world()
    oi = w.get_ontology("file://%s/test_ontoslash3_imported.owl" % HERE).load()
    o = w.get_ontology("file://%s/test_ontoslash3.owl" % HERE).load()

    assert len(o.imported_ontologies) == 1
    assert o.metadata.comment == ["TEST"]
    assert o.Class1.iri == "http://test.org/test_ontoslash3#Class1"
    assert o.Class2.iri == "http://test.org/test_ontoslash3#Class2"

    assert len(oi.imported_ontologies) == 0
    assert oi.metadata.comment == ["TEST imported"]
    assert oi.ImportedClass1.iri == "http://test.org/test_ontoslash3/imported.owl#ImportedClass1"
    assert oi.ImportedClass2.iri == "http://test.org/test_ontoslash3/imported.owl#ImportedClass2"
    
  def test_ontology_26(self):
    w = self.new_world()
    o = w.get_ontology("file://%s/test_ontoslash2.owl" % HERE).load()
    
    assert o.base_iri == "http://test.org/test_ontoslash2/"
    assert o.Class1
    assert o.Class2
    assert o.Class1.iri == "http://test.org/test_ontoslash2/Class1"
    assert o.Class2.iri == "http://test.org/test_ontoslash2/Class2"

  def test_ontology_27(self):
    w = self.new_world()
    o = w.get_ontology("file://%s/test_ontoslash_owlxml.owl" % HERE).load()

    assert len(o.imported_ontologies) == 1
    assert o.base_iri == "http://test.org/test_ontoslash/"
    assert o.Class1
    assert o.Class2
    assert o.Class1.iri == "http://test.org/test_ontoslash/Class1"
    assert o.Class2.iri == "http://test.org/test_ontoslash/Class2"
    
    o2 = w.get_ontology("file://%s/test_ontoslash2_owlxml.owl" % HERE).load()
    
    assert len(o2.imported_ontologies) == 1
    assert o2.base_iri == "http://test.org/test_ontoslash2/"
    assert o2.Class1
    assert o2.Class2
    assert o2.Class1.iri == "http://test.org/test_ontoslash2/Class1"
    assert o2.Class2.iri == "http://test.org/test_ontoslash2/Class2"

  def test_ontology_28(self):
    w = self.new_world()
    oi = w.get_ontology("file://%s/test_ontoslash3_imported_owlxml.owl" % HERE).load()
    o = w.get_ontology("file://%s/test_ontoslash3_owlxml.owl" % HERE).load()
    
    assert len(o.imported_ontologies) == 1
    assert o.metadata.comment == ["TEST"]
    assert o.Class1.iri == "http://test.org/test_ontoslash3#Class1"
    assert o.Class2.iri == "http://test.org/test_ontoslash3#Class2"

    assert len(oi.imported_ontologies) == 0
    assert oi.metadata.comment == ["TEST imported"]
    assert oi.ImportedClass1.iri == "http://test.org/test_ontoslash3/imported.owl#ImportedClass1"
    assert oi.ImportedClass2.iri == "http://test.org/test_ontoslash3/imported.owl#ImportedClass2"
    
  def test_ontology_29(self):
    w = self.new_world()
    o = w.get_ontology("http://test.org/onto/")
    o.metadata.comment = ["TEST"]
    
    self.assert_triple(o.storid, comment.storid, "TEST", w._abbreviate("http://www.w3.org/2001/XMLSchema#string"), world = w)
    self.assert_triple(w._abbreviate("http://test.org/onto"), comment.storid, "TEST", w._abbreviate("http://www.w3.org/2001/XMLSchema#string"), world = w)
    
  def test_ontology_30(self):
    w = self.new_world()
    
    o = w.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    o.ma_pizza.has_topping.append(o.Tomato())
    
    assert len(o.ma_pizza.has_topping) == 3
    
    o = w.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load(reload = True)
    
    assert len(o.ma_pizza.has_topping) == 2
    
  def test_ontology_31(self):
    w  = self.new_world()
    o1 = w.get_ontology("http://www.test.org/o1.owl")
    o2 = w.get_ontology("http://www.test.org/o2.owl")
    
    with o1:
      class p(Thing >> Thing): pass
      class C(Thing): pass
      class D(C): pass
      class E(Thing): pass
      class F(Thing): pass
      class G(Thing): pass
      class H(Thing): pass
      
      i = D()
      
    with o2:
      D.is_a.append(E)
      D.is_a.append(F)
      D.is_a.append(p.some(C))
      i.is_a.append(G)
      
    assert o1.get_parents_of(D) == [C]
    assert set(o2.get_parents_of(D)) == set([E, F, p.some(C)])
    
    assert o1.get_parents_of(i) == [D]
    assert o2.get_parents_of(i) == [G]
    
    assert o1.get_children_of(E) == []
    assert o2.get_children_of(E) == [D]
    
    assert o1.get_instances_of(G) == []
    assert o2.get_instances_of(G) == [i]
    
  def test_ontology_32(self):
    w = self.new_world()
    o = w.get_ontology("http://www.test.org/o.owl")
    
    assert list(o.metadata) == []

    o.metadata.label   = ["o"]
    o.metadata.comment = ["e", "f"]
    
    assert len(list(o.metadata)) == 2
    assert set(o.metadata) == { label, comment }
    
  def test_ontology_33(self):
    w = self.new_world()
    o = w.get_ontology("http://www.test.org/o.owl#")

    with o:
      class C(Thing): pass
      c = C()
      
    assert C.iri == "http://www.test.org/o.owl#C"
    
    o.base_iri = "http://www.test2.org/onto2.owl/"
    
    assert C.iri == "http://www.test2.org/onto2.owl/C"
    
    w.forget_reference(C)
    assert o.C.iri == "http://www.test2.org/onto2.owl/C"
    
    
    w = self.new_world()
    o = w.get_ontology("http://www.test.org/o/")
    q = w.get_ontology("http://www.test.org/o/q/")
    p = w.get_ontology("http://www.test.org/o/p#")
    
    with o:
      class C(Thing): pass
      c = C()
      
    with q:
      class D(Thing): pass
      
    with p:
      class E(Thing): pass
      
    assert C.iri == "http://www.test.org/o/C"
    assert D.iri == "http://www.test.org/o/q/D"
    assert E.iri == "http://www.test.org/o/p#E"
    
    o.base_iri = "http://www.test2.org/onto2.owl#"
    
    assert C.iri == "http://www.test2.org/onto2.owl#C"
    assert D.iri == "http://www.test.org/o/q/D"
    assert E.iri == "http://www.test.org/o/p#E"
    
    w.forget_reference(C)
    w.forget_reference(D)
    w.forget_reference(E)
    assert o.C.iri == "http://www.test2.org/onto2.owl#C"
    assert q.D.iri == "http://www.test.org/o/q/D"
    assert p.E.iri == "http://www.test.org/o/p#E"
    
  def test_ontology_34(self):
    w = self.new_world()
    o = w.get_ontology("http://www.test.org/o.owl#")

    with o:
      class C(Thing): pass
      c = C()
      
    assert C.iri == "http://www.test.org/o.owl#C"
    assert C.namespace is o
    
    o.set_base_iri("http://www.test2.org/onto2.owl/", rename_entities = False)
    
    assert C.iri == "http://www.test.org/o.owl#C"
    assert not C.namespace is o
    
    w.forget_reference(C)
    assert o.C is None
    assert o.get_namespace("http://www.test.org/o.owl#").C.iri == "http://www.test.org/o.owl#C"
    

    w = self.new_world()
    o = w.get_ontology("http://www.test.org/o/")
    q = w.get_ontology("http://www.test.org/o/q/")
    p = w.get_ontology("http://www.test.org/o/p#")
    
    with o:
      class C(Thing): pass
      c = C()
      
    with q:
      class D(Thing): pass
      
    with p:
      class E(Thing): pass
      
    assert C.iri == "http://www.test.org/o/C"
    assert C.namespace is o
    assert D.iri == "http://www.test.org/o/q/D"
    assert E.iri == "http://www.test.org/o/p#E"
    
    o.set_base_iri("http://www.test2.org/onto2.owl#", rename_entities = False)
    
    assert C.iri == "http://www.test.org/o/C"
    assert not C.namespace is o
    assert D.iri == "http://www.test.org/o/q/D"
    assert E.iri == "http://www.test.org/o/p#E"
    
    w.forget_reference(C)
    w.forget_reference(D)
    w.forget_reference(E)
    assert o.get_namespace("http://www.test.org/o/").C.iri == "http://www.test.org/o/C"
    assert q.get_namespace("http://www.test.org/o/q/").D.iri == "http://www.test.org/o/q/D"
    assert p.get_namespace("http://www.test.org/o/p#").E.iri == "http://www.test.org/o/p#E"
    
  def test_ontology_35(self):
    w = self.new_world()
    o = w.get_ontology("http://www.test.org/o.owl#")
    n = o.get_namespace("http://www.test.org/namespace/")
    
    with n:
      class C(Thing): pass
      c = C()
      
    assert C.iri == "http://www.test.org/namespace/C"
    assert C.namespace is n
    
    o2 = w.get_ontology("http://www.test.org/namespace/")
    o2.base_iri = "http://www.test.org/namespace2/"
    
    assert C.iri == "http://www.test.org/namespace2/C"
    assert C.namespace is n
    assert n.C is C
    
    
  def test_class_1(self):
    n = get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test")
    assert issubclass(n.Tomato, n.Vegetable)
    assert issubclass(n.Vegetable, n.Topping)
    assert issubclass(n.Tomato, n.Topping)
    assert issubclass(n.Topping, Thing)
    
  def test_class_2(self):
    n = self.new_ontology()
    class C(Thing): namespace = n
    
    self.assert_nb_created_triples(3)
    self.assert_triple(C.storid, rdf_type, owl_class)
    self.assert_triple(C.storid, rdfs_subclassof, Thing.storid)
    
  def test_class_3(self):
    n = self.new_ontology()
    class C1(Thing):  namespace = n
    class C2(Thing):  namespace = n
    class C3(C1, C2): namespace = n
    
    self.assert_nb_created_triples(1 + 2 + 2 + 3)
    self.assert_triple(C3.storid, rdf_type, owl_class)
    self.assert_triple(C3.storid, rdfs_subclassof, C1.storid)
    self.assert_triple(C3.storid, rdfs_subclassof, C2.storid)
    
  def test_class_4(self):
    n = self.new_ontology()
    class C1(Thing):  namespace = n
    class C2(Thing):  namespace = n
    class C3(C1): namespace = n
    
    C3.is_a.append(C2)
    
    self.assert_triple(C3.storid, rdfs_subclassof, C1.storid)
    self.assert_triple(C3.storid, rdfs_subclassof, C2.storid)
    assert issubclass(C3, C1)
    assert issubclass(C3, C2)
    
  def test_class_5(self):
    n = self.new_ontology()
    class C1(Thing):  namespace = n
    class C2(Thing):  namespace = n
    class C3(C1, C2): namespace = n
    
    C3.is_a.remove(C1)
    
    self.assert_not_triple(C3.storid, rdfs_subclassof, C1.storid)
    self.assert_triple    (C3.storid, rdfs_subclassof, C2.storid)
    assert not issubclass(C3, C1)
    assert issubclass(C3, C2)
    
  def test_class_6(self):
    n = self.new_ontology()
    class C1(Thing): namespace = n
    class C2(Thing):
      namespace = n
      is_a = [C1]
      
    assert issubclass(C2, C1)
    self.assert_triple(C2.storid, rdfs_subclassof, C1.storid)
    
  def test_class_7(self):
    n = self.new_ontology()
    class C1(Thing): namespace = n
    class C2(C1): pass
    
    assert issubclass(C2, C1)
    self.assert_triple(C2.storid, rdfs_subclassof, C1.storid)
    
  def test_class_8(self):
    n = get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test")
    assert set(n.Pizza.instances()) == { n.ma_pizza }
    assert set(n.Topping.descendants(include_self = False)) == { n.Cheese, n.Meat, n.Vegetable, n.Olive, n.Tomato, n.Eggplant }
    assert set(n.Topping.descendants()) == { n.Topping, n.Cheese, n.Meat, n.Vegetable, n.Olive, n.Tomato, n.Eggplant }
    assert set(n.Tomato.ancestors(include_self = False)) == { n.Vegetable, n.Topping, Thing }
    assert set(n.Tomato.ancestors(include_self = False, include_constructs = True)) == { n.Vegetable, n.Topping, Thing, n.Eggplant | n.Olive | n.Tomato }
    assert set(n.Tomato.ancestors()) == { n.Tomato, n.Vegetable, n.Topping, Thing }
    
  def test_class_9(self):
    n = self.new_ontology()
    with n:
      class C(Thing): pass
      class C2(C): pass
      class D(Thing): pass
      class D2(D): pass
      
      C.equivalent_to.append(D)
      
    assert set(C .descendants()) == { C, C2, D, D2 }
    assert set(C2.descendants()) == { C2 }
    assert set(D .descendants()) == { C, C2, D, D2 }
    assert set(D2.descendants()) == { D2 }
    
  def test_class_10(self):
    n = self.new_ontology()
    with n:
      class C(Thing): pass
      class C2(C): pass
      class D(Thing): pass
      class D2(D): pass
      
      D.equivalent_to.indirect() # Read and define it
      C.equivalent_to.append(D)
      
    assert set(C .descendants()) == { C, C2, D, D2 }
    assert set(C2.descendants()) == { C2 }
    assert set(D .descendants()) == { C, C2, D, D2 }
    assert set(D2.descendants()) == { D2 }
    
  def test_class_11(self):
    n = self.new_ontology()
    with n:
      class C(Thing): pass
      class C2(C): pass
      class D(Thing):
        equivalent_to = [C2]
        
    assert not "equivalent_to" in D.__dict__ # Must not be set in the dict!
    
    assert set(C .descendants()) == { C, C2, D }
    assert set(C2.descendants()) == { C2, D }
    assert set(D .descendants()) == { C2, D }
    
  def test_class_12(self):
    n = self.new_ontology()
    with n:
      class C(Thing): pass
      class C2(C): pass
      class D(Thing):
        equivalent_to = [C]
      class D2(D): pass
      
    assert set(D2.ancestors()) == { D2, D, C, Thing }
    assert set(C2.ancestors()) == { C2, D, C, Thing }
    
  def test_class_13(self):
    n = self.new_ontology()
    with n:
      class C(Thing): pass
      class D(Thing):
        equivalent_to = [C]
      class E(Thing):
        equivalent_to = [D]
        
    assert set(C.equivalent_to.indirect()) == { D, E }
    assert set(D.equivalent_to.indirect()) == { C, E }
    assert set(E.equivalent_to.indirect()) == { C, D }
    assert set(C.descendants()) == { C, D, E }
    assert set(C.ancestors()) == { C, D, E, Thing }
    
  def test_class_14(self):
    n = self.new_ontology()
    with n:
      class C(Thing): pass
      class D(Thing):
        equivalent_to = [C]
      class C2(C): pass
      class D2(D): pass
      
    assert issubclass(C2, C)
    assert issubclass(D2, D)
    assert issubclass(C2, D)
    assert issubclass(D2, C)
    assert issubclass(C, D)
    assert issubclass(D, C)
    assert not issubclass(C2, D2)
    assert not issubclass(D2, C2)
    
  def test_class_15(self): # Test MRO errors
    n = self.new_ontology()
    with n:
      class C(Thing): pass
      class C2(C): pass
      class D(Thing): pass
      
      class T(D, C2, C, Thing): pass
      class T(D, C, C2, Thing): pass
    
  def test_class_16(self):
    n = self.new_ontology()
    with n:
      class C(Thing): pass
      class D(Thing): pass
      class E(Thing): pass
      
      C.equivalent_to.append(D)
      E.equivalent_to.append(D)
      
    assert set(C.equivalent_to.indirect()) == { D, E }
    assert set(D.equivalent_to.indirect()) == { C, E }
    assert set(E.equivalent_to.indirect()) == { C, D }
    
  def test_class_17(self): # test MRO
    n = self.new_ontology()
    with n:
      class GO_0044464(Thing): pass
      class GO_0044422(Thing): pass
      class GO_0044424(GO_0044464): pass
      class GO_0044446(GO_0044422, GO_0044424): pass
      class GO_0016020(GO_0044464): pass
      class GO_0031090(GO_0016020, GO_0044422): pass
      class X(GO_0044446, GO_0031090): pass
      class X(GO_0031090, GO_0044446): pass
      
  def test_class_18(self):
    world = self.new_world()
    n     = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    a     = n.Topping
    b     = n.Tomato
    
    assert set(n.Topping.descendants(only_loaded = True)) == { n.Topping, n.Vegetable, n.Tomato }
    
  def test_class_19(self):
    world = self.new_world()
    n     = world.get_ontology("http://test.org/test")
    
    with n:
      class p(ObjectProperty): pass
      class A(Thing): pass
      class B(Thing): pass
      class C(Thing): pass
      class M(Thing):
        is_a = [
          p.some(A),
          B & C
          ]

    assert set(A.constructs()) == { M.is_a[-2] }
    assert set(B.constructs()) == { M.is_a[-1] }
    assert set(C.constructs()) == { M.is_a[-1] }
    
  def test_class_20(self):
    world = self.new_world()
    n     = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()

    n.Pizza # Loads Pizza
    nb = len(world._entities)
    
    with n:
      class Pizza(Thing):
        def f(self): pass
        
    assert len(world._entities) == nb # Check that the redefinition did not load additional classes
    
  def test_class_21(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/test.owl")
    
    with onto:
      class MyClass(Thing): comment = "abc"
      
    self.assert_triple(MyClass.storid, comment.storid, *to_literal("abc"), world = world)
    
  def test_class_22(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/test.owl")
    
    with onto:
      class Parent(Thing): pass
      class MyClass(Parent): label   = ["MyClass"]
      class MyClass(Thing): comment = ["abc"]
      
    assert MyClass.is_a == [Parent]
    
  def test_class_23(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/test.owl")
    
    with onto:
      class C(Thing): pass
      class D(Thing): pass
      class E(Thing): pass
      class F(Thing): pass
      class G(Thing): pass
      class H(Thing): pass
      class I(Thing): pass
      class J(Thing): pass
      class K(Thing): pass
      class L(Thing): pass
      class M(Thing): pass
      class N(Thing): pass
      class p(Thing >> Thing): pass
      
      C.is_a.append(p.some(D))
      E.is_a.append(F & p.some(G))
      H.is_a.append(p.some(I | J))
      K.is_a.append(L & p.some(M | N))
      
    assert set(D.inverse_restrictions(p)) == set([C])
    assert set(G.inverse_restrictions(p)) == set([E])
    assert set(I.inverse_restrictions(p)) == set([H])
    assert set(M.inverse_restrictions(p)) == set([K])
    
  def test_class_24(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/test.owl")
    
    with onto:
      class C(Thing): pass
      class D(Thing): pass
      class E(Thing): pass
      class F(Thing): pass
      class G(Thing): pass
      class H(Thing): pass
      class I(Thing): pass
      class J(Thing): pass
      class K(Thing): pass
      class L(Thing): pass
      class M(Thing): pass
      class N(Thing): pass
      class p(Thing >> Thing): pass
      
      C.equivalent_to.append(p.some(D))
      E.equivalent_to.append(F & p.some(G))
      H.equivalent_to.append(p.some(I | J))
      K.equivalent_to.append(L & p.some(M | N))
      
    assert set(D.inverse_restrictions(p)) == set([C])
    assert set(G.inverse_restrictions(p)) == set([E])
    assert set(I.inverse_restrictions(p)) == set([H])
    assert set(M.inverse_restrictions(p)) == set([K])
    
  def test_class_25(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/test.owl")
    
    with onto:
      class C1(Thing): pass
      class C2(Thing): pass
      class p(Thing >> Thing, FunctionalProperty): pass
      class O1(Thing):
        is_a = [p.some(C1)]
      class O2(O1):
        is_a = [p.some(C2)]

    assert O2.p == C2
      
  def test_class_26(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/test.owl")
    
    with onto:
      class Bactery(Thing): pass
      class Grouping(Thing): pass
      class p(Bactery >> Grouping): pass
      
      
      class Listeria(Bactery):
        p = [Grouping]
        pass
      
      class Listeria(Bactery):
        is_a = [
          p.some(Grouping),
        ]
        
    assert set(Listeria.is_a) == set([Bactery, p.some(Grouping)])
    assert len(Listeria.is_a) == 2
      
  def test_class_27(self):
    w = self.new_world()
    o = w.get_ontology("http://www.test.org/test")
    with o:
      class A(Thing): pass
      class B(Thing): equivalent_to = [A]
      class C(Thing): pass
      class A2(A): pass
      class C2(C): pass
      class AC(A, C): pass
      
    assert owlready2.reasoning._keep_most_specific([A, B])    in [ {A}, {B}]
    assert owlready2.reasoning._keep_most_specific([A, C])    == {A, C}
    assert owlready2.reasoning._keep_most_specific([A, B, C]) in [ {A, C}, {B, C} ]
    
    assert owlready2.reasoning._keep_most_specific([A, B, A2]) == {A2}
    assert owlready2.reasoning._keep_most_specific([A, B, C, AC]) == {AC}
    assert owlready2.reasoning._keep_most_specific([A, B, C, AC, A2]) == {AC, A2}
    
  def test_class_27(self):
    w = self.new_world()
    o = w.get_ontology("http://www.test.org/test")
    with o:
      class A(owlready2.Thing): pass
      class B(owlready2.Thing): pass
      class C(owlready2.Thing): pass
      
      A.equivalent_to = [owlready2.Not(B)]
      C.equivalent_to = [A]
      
      assert set(A.         equivalent_to) == { Not(B) }
      assert set(A.INDIRECT_equivalent_to) == { Not(B), C }
      assert set(C.         equivalent_to) == { A }
      assert set(C.INDIRECT_equivalent_to) == { Not(B), A }
      
  def test_class_28(self):
    w = self.new_world()
    o = w.get_ontology("http://www.test.org/test")
    with o:
      class p(Thing >> Thing): pass
      class A(Thing): pass
      class B(A): pass
      class C(Thing): is_a = [p.some(A)]
      
    assert set(Thing.subclasses(world = w)) == { A, C }
    
  def test_class_29(self):
    w = self.new_world()
    o = w.get_ontology("http://www.test.org/test")
    with o:
      class Test1(Thing): pass
      class Test2(Thing): pass
      Test2.equivalent_to = [Test1]
      
    destroy_entity(Test1)
    assert Test2.equivalent_to == []
    
  def test_class_30(self):
    w = self.new_world()
    o = w.get_ontology("http://www.test.org/test")
    with o:
      class Test1(Thing): pass
      class Test2(Thing): pass
      Test2.equivalent_to = [Test1]
      
    undo = destroy_entity(Test1, undoable = True)
    assert Test2.equivalent_to == []
    
    undo()
    assert Test2.equivalent_to == [Test1]
    
    
  def test_individual_1(self):
    n = get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test")
    
    assert isinstance(n.ma_tomate, n.Tomato)
    assert isinstance(n.ma_tomate, n.Vegetable)
    assert isinstance(n.ma_tomate, n.Topping)
    assert isinstance(n.ma_tomate, Thing)
    assert not isinstance(n.ma_tomate, n.Pizza)
    assert not isinstance(None, n.Pizza)
    assert not isinstance(1, n.Pizza)
    
  def test_individual_2(self):
    n = self.new_ontology()
    class C(Thing): namespace = n
    i = C()
    
    self.assert_nb_created_triples(5)
    self.assert_triple(i.storid, rdf_type, owl_named_individual)
    self.assert_triple(i.storid, rdf_type, C.storid)
    
  def test_individual_3(self):
    n = self.new_ontology()
    class C1(Thing): namespace = n
    class C2(Thing): namespace = n
    i = C1()
    
    i.is_a = [C2]
    
    self.assert_not_triple(i.storid, rdf_type, C1.storid)
    self.assert_triple    (i.storid, rdf_type, C2.storid)
    
  def test_individual_4(self):
    n = self.new_ontology()
    class C1(Thing): namespace = n
    class C2(Thing): namespace = n
    i = C1()
    
    i.is_a.append(C2)
    
    self.assert_triple(i.storid, rdf_type, C1.storid)
    self.assert_triple(i.storid, rdf_type, C2.storid)
    assert "FusionClass" in i.__class__.__name__
    
  def test_individual_5(self):
    n = self.new_ontology()
    class C1(Thing): namespace = n
    class C2(Thing): namespace = n
    i = C1()
    
    i.is_a.remove(C1)
    
    self.assert_not_triple(i.storid, rdf_type, C1.storid)
    self.assert_not_triple(i.storid, rdf_type, C2.storid)
    assert i.__class__ is Thing
    
  def test_individual_6(self):
    n = self.new_ontology()
    with n:
      class C(Thing): pass
      
    i1 = C()
    i2 = C()
    
    assert i1.storid != i2.storid
    
    i1.equivalent_to.append(i2)
    
    assert set(i2.equivalent_to.indirect()) == { i1 }
    
    i1.equivalent_to.remove(i2)
    assert set(i2.equivalent_to.indirect()) == set()
    assert set(i1.equivalent_to.indirect()) == set()
    
  def test_individual_7(self):
    n = self.new_ontology()
    with n:
      class C(Thing): pass
    i1 = C()
    i2 = C()
    i3 = C()
    i4 = C()
    
    i1.equivalent_to.append(i2)
    i2.equivalent_to.append(i3)
    i3.equivalent_to.append(i4)
    
    assert set(i1.equivalent_to.indirect()) == { i2, i3, i4 }
    assert set(i2.equivalent_to.indirect()) == { i1, i3, i4 }
    assert set(i3.equivalent_to.indirect()) == { i1, i2, i4 }
    assert set(i4.equivalent_to.indirect()) == { i1, i2, i3 }
    
  def test_individual_8(self):
    n = self.new_ontology()
    with n:
      class C (Thing): pass
      class C1(C): pass
      class D (Thing):
        equivalent_to = [C]
      class D1(D): pass
      class E (Thing): pass
    i = C()
    
    assert isinstance(i, C)
    assert isinstance(i, D)
    assert not isinstance(i, C1)
    assert not isinstance(i, D1)
    assert not isinstance(i, E)
    
  def test_individual_9(self):
    n = self.new_ontology()
    with n:
      class C(Thing): pass
      class D(Thing): pass
      class prop(ObjectProperty): pass
      class propf(ObjectProperty, FunctionalProperty): pass
      class propi(DataProperty): range = [int]
      class propif(DataProperty, FunctionalProperty): range = [int]
    d1 = D()
    d2 = D()
    d3 = D()
    c = C("mon_c", prop = [d1, d2], propf = d3, propi = [1, 2], propif = 3)
    
    assert c.name == "mon_c"
    self.assert_triple(d1.storid, rdf_type, D.storid)
    self.assert_triple(c.storid, rdf_type, C.storid)
    self.assert_triple(c.storid, prop.storid, d1.storid)
    self.assert_triple(c.storid, propf.storid, d3.storid)
    self.assert_triple(c.storid, propi.storid, *to_literal(1))
    self.assert_triple(c.storid, propi.storid, *to_literal(2))
    self.assert_triple(c.storid, propif.storid, *to_literal(3))
    
  def test_individual_10(self):
    world   = self.new_world()
    onto    = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/2/test_reasoning.owl").load()
    
    assert len(onto.pizza_tomato.is_a) == 2
    
  def test_individual_11(self):
    world   = self.new_world()
    o       = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    
    assert set(o.ma_pizza.get_properties()) == { o.price, o.annot, comment, o.has_topping, o.has_main_topping }
    assert set(o.ma_tomate.get_inverse_properties()) == { (o.ma_pizza, o.has_topping), (o.ma_pizza, o.has_main_topping) }
    
  def test_individual_12(self):
    world   = self.new_world()
    o       = world.get_ontology("http://www.test.org/test.owl")

    with o:
      class O(Thing): pass
      class p(O >> O, TransitiveProperty): pass
      
      o1 = O()
      o2 = O(p = [o1])
      o3 = O(p = [o2])
      o4 = O(p = [o3])

    r = set(o3.p.indirect())
    assert r == { o1, o2 }
    
  def test_individual_13(self):
    world   = self.new_world()
    o       = world.get_ontology("http://www.test.org/test.owl")

    with o:
      class O(Thing): pass
      class p(O >> O, TransitiveProperty): pass
      class i(O >> O, TransitiveProperty): inverse = p
      
      o1 = O()
      o2 = O(p = [o1])
      o3 = O(p = [o2])
      o4 = O(i = [o3])
      o6 = O()
      o5 = O(i = [o4], p = [o6])
      o7 = O()
      
    r = set(o3.p.indirect())
    assert r == { o1, o2, o4, o5, o6 }
    
  def test_individual_14(self):
    world   = self.new_world()
    o       = world.get_ontology("http://www.test.org/test.owl")
    
    with o:
      class O(Thing): pass
      class p(O >> O, TransitiveProperty, SymmetricProperty): pass
      
      o1 = O()
      o2 = O(p = [o1])
      o3 = O(p = [o2])
      o4 = O(p = [o3])
      o5 = O()
      o6 = O(p = [o5])
      o7 = O()
      
    r = set(o3.p.indirect())
    assert r == { o3, o1, o2, o4 }
    
  def test_individual_15(self):
    world   = self.new_world()
    o       = world.get_ontology("http://www.test.org/test.owl")

    with o:
      class O(Thing): pass
      class p(O >> O, TransitiveProperty): pass
      class q(p): pass
      class s(q): pass
      
      o1 = O()
      o2 = O()
      o3 = O()
      o4 = O(s = [o3])
      o5 = O(q = [o4])
      o6 = O(s = [o5], q = [o1], p = [o2])
      o7 = O()
      o8 = O(s = [o5])
      
    r = set(o6.q.indirect())
    assert r == { o5, o1, o4, o3 }
    
  def test_individual_16(self):
    world   = self.new_world()
    o       = world.get_ontology("http://www.test.org/test.owl")

    with o:
      class BodyPart(Thing): pass
      class part_of(BodyPart >> BodyPart, TransitiveProperty): pass
      abdomen          = BodyPart("abdomen")
      heart            = BodyPart("heart"           , part_of = [abdomen])
      left_ventricular = BodyPart("left_ventricular", part_of = [heart])
      kidney           = BodyPart("kidney"          , part_of = [abdomen])
      
    assert left_ventricular.part_of == [heart]
    assert set(left_ventricular.INDIRECT_part_of) == { heart, abdomen }
    
  def test_individual_17(self):
    world   = self.new_world()
    onto = get_ontology("http://test.org/t.owl")
    with onto:
      class Emp(Thing): pass
      class Emp2(Thing): pass
      class p1(Thing >> int): pass
      class p2(Thing >> int): pass
      
    e1 = Emp("e")
    e2 = Emp("e")
    
    assert e1 is e2
    
    f1 = Emp("f")
    f2 = Emp2("f")
    
    assert f1 is f2
    assert isinstance(f1, Emp)
    assert isinstance(f2, Emp2)
    
    g1 = Emp("g", p1 = [1])
    g2 = Emp("g", p2 = [2])
    
    assert g1 is g2
    assert g1.p1 == [1]
    assert g1.p2 == [2]
    
  def test_individual_18(self):
    world   = self.new_world()
    onto = get_ontology("http://test.org/t.owl")
    with onto:
      class Emp1(Thing):
        def f1(self): pass
      class Emp2(Thing):
        def f2(self): pass

    e = Emp1()
    Emp2(e)
    
    e.f1()
    e.f2()
    
    assert isinstance(e, Emp1)
    assert isinstance(e, Emp2)
    
  def test_individual_19(self):
    world   = self.new_world()
    onto = get_ontology("http://test.org/test_undeclared_entity.owl").load()
    
    # Can guest it is a class
    assert [i.iri for i in onto.C.hasRelatedSynonym] == ["http://test.org/test_undeclared_entity.owl#genid1217"]
    
    assert onto.i.hasRelatedSynonym == ["http://test.org/test_undeclared_entity.owl#genid1219"]
    
  def test_individual_20(self):
    world   = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()

    nb_triples = len(n.graph)
    
    o2 = n.Cheese("mon_frometon")
    o1 = n.Cheese("mon_frometon")
    assert o1 is o2
    assert o1 is n.mon_frometon
    
    assert len(n.graph) == nb_triples
    
  def test_individual_21(self):
    world   = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()

    o = n.Cheese(0)
    o.label = ["anonymous cheese"]
    
    assert o.storid < 0
    assert o.name  == ""
    assert o.iri   == ""
    assert o.label == ["anonymous cheese"]

    p = n.Pizza("mapiz", has_topping = [o])
    
    buf = BytesIO()
    n.save(buf)
    
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load(fileobj = BytesIO(buf.getvalue()))
    
    p = n.mapiz
    o = p.has_topping[0]
    
    assert o.storid < 0
    assert o.name  == ""
    assert o.iri   == ""
    assert o.label == ["anonymous cheese"]
    
  def test_individual_22(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/onto.owl")

    with onto:
      class C(Thing): pass
      class p(C >> C): pass
      class i(C >> C): inverse = p
      
    c1 = C()
    c2 = C(p = [c1])
    
    assert set(c2.get_properties()) == set([p])
    assert set(c1.get_properties()) == set([i])
      
    c3 = C()
    c4 = C()
    c3.i = [c4]
    c4.p = [c3]
    
    assert len(c3.get_properties()) == 1
    
  def test_individual_23(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/onto.owl")
    
    with onto:
      class C(Thing): pass
      class C2(C): pass
      class C3(C2): pass
      class C4(C2): pass
      class p(C >> int): pass
      
    c = C3()
    
    assert set(c.INDIRECT_is_a) == { Thing, C, C2, C3 }

    c = C4()
    c.is_a.append(p.value(2))
    
    assert set(c.INDIRECT_is_instance_of) == { Thing, C, C2, C4, p.value(2) }
    
  def test_individual_24(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/onto.owl")
    
    with onto:
      class Person(Thing): pass
      class love(Person >> Person):
        pass

      Person.is_a.append(love.some(Person))  # a person loves someone.
      
      x = Person('x')
      y = Person('y')
      x.is_a.append(love.value(y))

    assert set(x.INDIRECT_is_a) == set([Person, love.value(y), Thing, love.some(Person)])
    assert set(Person.ancestors()) == set([Person, Thing])
    assert set(Person.ancestors(include_constructs = True)) == set([Person, Thing, love.some(Person)])
    
  def test_individual_24(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/onto.owl")
    
    with onto:
      class C(Thing): pass

    c = C()

    assert list(Thing.instances(world)) == [c]

  def test_individual_25(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/onto.owl")
    with onto:
      class C(Thing): pass
      class C1(Thing): pass
      
      C()
      C1()
      for i in range(13): C()
      C1()
      
    for i in world.individuals():
      l = list(world.graph.execute("select o from objs where s=? and p=6", (i.storid,)))
      assert len(l) == 2
      
  def test_individual_26(self):
    world1 = self.new_world()
    onto1  = world1.get_ontology("http://test.org/onto.owl")
    
    with onto1:
      class C(Thing): pass
      class D(Thing): pass
      x1 = C()
      x1.is_a.append(D)
      
    world2 = self.new_world()
    onto2  = world2.get_ontology("http://test.org/onto.owl")
    
    with onto2:
      class C(Thing): pass
      class D(Thing): pass
      x2 = C()
      x2.is_a.append(D)
      
    assert not x1.__class__ is x2.__class__
      
  def test_individual_27(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/onto.owl")
    
    with onto:
      class C(Thing): pass
      class p(ObjectProperty, FunctionalProperty): pass
      class i(ObjectProperty): inverse = p
      c1 = C()
      c2 = C(i = [c1])

    assert c2.i == [c1]
    
    with onto:
      c3 = C("c3", p = c2)

    assert c2.i == [c1, c3]
    del c2.i
    assert c2.i == [c1, c3]
    
    with onto:
      c3_2 = C("c3", p = None)
      assert c3_2 is c3
      
    assert c2.i == [c1]
    del c2.i
    assert c2.i == [c1]
    
  def test_individual_28(self):
    world = self.new_world()
    onto = world.get_ontology("http://dl-learner.org/benchmark/dataset/animals").load()
    assert set(onto.croco01.is_a) == { onto.Animal, onto.HasEggs }
    
    
  def test_prop_1(self):
    n = get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test")
    assert "has_topping" in default_world._props
    assert "price" in default_world._props
    assert default_world._props["has_topping"] is n.has_topping
    assert default_world._props["price"] is n.price
    assert n.has_topping.__class__ is ObjectPropertyClass
    assert n.price.__class__ is DataPropertyClass
    assert n.has_topping.__bases__ == (ObjectProperty,)
    assert set(n.price.__bases__) == { DataProperty, FunctionalProperty }
    
  def test_prop_2(self):
    n = get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test")
    assert set(n.ma_pizza.has_topping) == { n.ma_tomate, n.mon_frometon }
    
  def test_prop_3(self):
    n = get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test")
    assert n.ma_pizza.price == 9.9

  def test_prop_4(self):
    n = get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test")
    pizza = n.Pizza()
    assert pizza.has_topping == []
    assert pizza.price is None
    
  def test_prop_5(self):
    n = get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test")
    pizza = n.Pizza()
    assert default_world._get_data_triple_sp_od(pizza.storid, n.price.storid) is None
    pizza.price = 8.0

    assert from_literal(*default_world._get_data_triple_sp_od(pizza.storid, n.price.storid)) == 8.0
    pizza.price = 9.0
    assert from_literal(*default_world._get_data_triple_sp_od(pizza.storid, n.price.storid)) == 9.0
    pizza.price = None
    assert default_world._get_data_triple_sp_od(pizza.storid, n.price.storid) is None
    
  def test_prop_6(self):
    n = get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test")
    pizza = n.Pizza()
    assert pizza.has_topping == []
    tomato = n.Tomato()
    cheese = n.Cheese()
    pizza.has_topping = [tomato]
    assert default_world._get_obj_triple_sp_o(pizza.storid, n.has_topping.storid) == tomato.storid
    pizza.has_topping.append(cheese)
    self.assert_triple(pizza.storid, n.has_topping.storid, tomato.storid)
    self.assert_triple(pizza.storid, n.has_topping.storid, cheese.storid)
    pizza.has_topping.remove(tomato)
    assert default_world._get_obj_triple_sp_o(pizza.storid, n.has_topping.storid) == cheese.storid
    
  def test_prop_7(self):
    n = self.new_ontology()
    with n:
      class C(Thing): pass
      class prop (DataProperty): pass
      class propf(DataProperty, FunctionalProperty): pass
    c = C()
    c.prop  = [0, 1]
    c.propf = 2
    
    self.assert_triple(c.storid, prop .storid, *to_literal(0))
    self.assert_triple(c.storid, prop .storid, *to_literal(1))
    self.assert_triple(c.storid, propf.storid, *to_literal(2))
    
  def test_prop_8(self):
    n = get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test")
    
    assert n.has_topping.domain == [n.Pizza]
    assert n.has_topping.range  == [n.Topping]
    
    assert n.price.domain == [n.Pizza]
    assert n.price.range  == [float]
    
  def test_prop_9(self):
    n = self.new_ontology()
    with n:
      class C(Thing): pass
      class prop(DataProperty):
        range = [int]
        
    self.assert_triple(prop.storid, rdf_range, n._abbreviate("http://www.w3.org/2001/XMLSchema#integer"))
    assert isinstance(prop.range, util.CallbackList)
    
    prop.range.append(float)
    self.assert_triple(prop.storid, rdf_range, n._abbreviate("http://www.w3.org/2001/XMLSchema#decimal"))
    
    prop.range.remove(int)
    self.assert_not_triple(prop.storid, rdf_range, n._abbreviate("http://www.w3.org/2001/XMLSchema#integer"))
    
  def test_prop_10(self):
    n = self.new_ontology()
    with n:
      class C1(Thing): pass
      class C2(Thing): pass
      class prop(ObjectProperty):
        domain = [C1]
        
    self.assert_triple(prop.storid, rdf_domain, C1.storid)
    assert isinstance(prop.domain, util.CallbackList)
    
    prop.domain = [C2]
    self.assert_triple    (prop.storid, rdf_domain, C2.storid)
    self.assert_not_triple(prop.storid, rdf_domain, C1.storid)
    
  def test_prop_11(self):
    owlready2.prop.RESTRICTIONS_AS_FUNCTIONAL_PROPERTIES = True
    try:
      n = self.new_ontology()
      with n:
        class D (Thing): pass
        class R (Thing): pass
        class prop(ObjectProperty):
          domain = [D]
          range  = [R]
        class D2(Thing):
          is_a = [prop.max(1, R)]
        
      d  = D()
      d2 = D2()
      
      assert d .prop == []
      assert d2.prop == None
    finally:
      owlready2.prop.RESTRICTIONS_AS_FUNCTIONAL_PROPERTIES = False
    
  def test_prop_11_2(self):
    n = self.new_ontology()
    with n:
      class D (Thing): pass
      class R (Thing): pass
      class prop(ObjectProperty):
        domain = [D]
        range  = [R]
      class D2(Thing):
        is_a = [prop.max(1, R)]
        
    d  = D()
    d2 = D2()

    assert d .prop == []
    assert d2.prop == []
    
  def test_prop_12(self):
    n = self.new_ontology()
    with n:
      class prop1(ObjectProperty): pass
      class prop2(prop1): pass
      
    self.assert_triple(prop2.storid, rdfs_subpropertyof, prop1.storid)
    
  def test_prop_13(self):
    n = self.new_ontology()
    with n:
      class C(Thing): pass
      class prop(DataProperty):
        range = [str]
        
    c1 = C()
    c1.prop = [locstr("English", "en"), locstr("Français", "fr")]
    assert c1.prop.fr == ["Français"]
    
    c1.prop.fr.append("French")
    c1.prop.en = "Anglais"
    
    values = set()
    for s,p,o,d in n._get_data_triples_spod_spod(c1.storid, prop.storid, None): values.add((o,d))
    assert values == { to_literal(locstr("Anglais", "en")), to_literal(locstr("French", "fr")), to_literal(locstr("Français", "fr")) }
    
  def test_prop_14(self):
    w = self.new_world()
    n = w.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    assert set(n.ma_pizza ._get_instance_possible_relations()) == { n.has_main_topping, n.has_topping, n.price }
    assert set(n.Topping()._get_instance_possible_relations()) == { n.main_topping_of, n.topping_of }
    
  def test_prop_15(self):
    n = self.new_ontology()
    with n:
      class prop1(DataProperty): pass
      class prop2(ObjectProperty): pass
      class prop3(ObjectProperty, FunctionalProperty): pass
      class prop4(AnnotationProperty): pass
      class prop5(prop2): pass
      
    def get_types(prop):
      for s,p,o in n._get_obj_triples_spo_spo(prop.storid, rdf_type, None): yield o
      
    assert set(get_types(prop1)) == { owl_data_property }
    assert set(get_types(prop2)) == { owl_object_property }
    assert set(get_types(prop3)) == { owl_object_property, n._abbreviate("http://www.w3.org/2002/07/owl#FunctionalProperty") }
    assert set(get_types(prop4)) == { owl_annotation_property }
    assert set(get_types(prop5)) == { owl_object_property }
    
    def get_subclasses(prop):
      for s,p,o in n._get_obj_triples_spo_spo(prop.storid, rdfs_subpropertyof, None): yield o
      
    assert set(get_subclasses(prop1)) == set()
    assert set(get_subclasses(prop2)) == set()
    assert set(get_subclasses(prop3)) == set()
    assert set(get_subclasses(prop4)) == set()
    assert set(get_subclasses(prop5)) == { prop2.storid }
    
  def test_prop_16(self):
    n = self.new_ontology()
    with n:
      class C(Thing): pass
      class D(Thing): pass
      class prop1(C >> D): pass
      class prop2(C >> D, FunctionalProperty): pass
      class prop3(C >> int): pass
      class prop4(ObjectProperty): pass
      
    assert (prop1.domain, prop1.range) == ([C], [D])
    assert (prop2.domain, prop2.range) == ([C], [D])
    assert (prop3.domain, prop3.range) == ([C], [int])
    assert (prop4.domain, prop4.range) == ([ ], [ ])
    assert issubclass(prop2, FunctionalProperty)
    
  def test_prop_17(self):
    n = self.new_ontology()
    with n:
      class C(Thing): pass
      class D(Thing): pass
      class prop1(C >> D): pass
      class prop2(prop1): pass
      
    assert prop1.domain == [C]
    assert prop1.range  == [D]
    assert prop2.domain == []
    assert prop2.range  == []
    
  def test_prop_18(self):
    w = self.new_world()
    n = w.get_ontology("http://test.org/t")
    with n:
      class C(Thing): pass
      class D(Thing): pass
      class has_prop(C >> D): pass
      
    c = C()
    assert c.has_prop == []
    assert not hasattr(c, "props")
    
    has_prop.python_name = "props"
    self.assert_triple(has_prop.storid, owlready_python_name, *to_literal("props"), world = w)
    
    c = C()
    assert c.props == []
    assert not hasattr(c, "has_prop")
    
  def test_prop_19(self):
    w = self.new_world()
    n = w.get_ontology("http://test.org/t")
    with n:
      class C(Thing): pass
      class D(Thing): pass
      class has_prop(C >> D):
        python_name = "props"
        
    c = C()
    assert c.props == []
    assert not hasattr(c, "has_prop")
    
    self.assert_triple(has_prop.storid, owlready_python_name, *to_literal("props"), world = w)
    
  def test_prop_20(self):
    n = self.new_ontology()
    with n:
      class C(Thing): pass
      class D(Thing): pass
      class p(C >> D): pass
      
      C.is_a.append(p.exactly(1))
      
    assert not p.is_functional_for(C)
    assert p.is_functional_for(C, True)
    
  def test_prop_21(self):
    n = self.new_ontology()
    with n:
      class C(Thing): pass
      class C2(C): pass
      class p(C >> C): pass
      
      C.is_a.append(p.exactly(1, C))
      
    assert not p.is_functional_for(C)
    assert not p.is_functional_for(C2)
    assert p.is_functional_for(C, True)
    assert p.is_functional_for(C2, True)
    
  def test_prop_22(self):
    n = self.new_ontology()
    with n:
      class C(Thing): pass
      class C2(C): pass
      class p(C >> C): pass
      
      C.is_a.append(p.max(1, C2))
      
    assert not p.is_functional_for(C, True)
    assert not p.is_functional_for(C2, True)
    
  def test_prop_23(self):
    owlready2.prop.RESTRICTIONS_AS_FUNCTIONAL_PROPERTIES = True
    try:
      n = self.new_ontology()
      with n:
        class C(Thing): pass
        class C2(C): pass
        class p(C >> C): pass
      
      assert not p.is_functional_for(C, True)
      assert not p.is_functional_for(C2, True)
      assert C().p == []
      
      C.is_a.append(p.max(1, C))
      
      assert p.is_functional_for(C, True)
      assert p.is_functional_for(C2, True)
      assert C().p == None
      
      del C.is_a[-1]
      
      assert not p.is_functional_for(C, True)
      assert not p.is_functional_for(C2, True)
      assert C().p == []
      
      C2.is_a.append(p.max(1, C))
      
      assert not p.is_functional_for(C, True)
      assert p.is_functional_for(C2, True)
      assert C ().p == []
      assert C2().p == None
    finally:
      owlready2.prop.RESTRICTIONS_AS_FUNCTIONAL_PROPERTIES = False
      
  def test_prop_24(self):
    n = self.new_ontology()
    with n:
      class p(ObjectProperty): pass
      class p2(p): pass
      class d(DataProperty): pass
      class d2(d): pass
      
    p2.is_a.remove(p)
    d2.is_a.remove(d)
    
    assert p2.is_a == [ObjectProperty]
    assert d2.is_a == [DataProperty]
    
  def test_prop_24(self):
    ok = False
    o = get_ontology("test_multiple_base_prop.owl").load()
    
  def test_prop_25(self):
    world   = self.new_world()
    o       = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    
    assert set(o.price.get_relations()) == { (o.ma_pizza, 9.9) }
    assert set(o.has_topping.get_relations()) == { (o.ma_pizza, o.mon_frometon), (o.ma_pizza, o.ma_tomate) }
    
  def test_prop_26(self):
    world   = self.new_world()
    n       = world.get_ontology("http://www.semanticweb.org/test.owl")
    
    with n:
      class O(Thing): pass
      class C(Thing): pass
      o = O()
      
      class p(Thing >> Thing): pass
        
      class Q(Thing):
        is_a = [p.value(o), p.some(C)]
        
        
      q = Q()

    assert q.p == []
    assert set(q.p.indirect()) == { o, C }
    
  def test_prop_27(self):
    world   = self.new_world()
    n       = world.get_ontology("http://www.semanticweb.org/test.owl")
    
    with n:
      class O(Thing): pass
      class C(Thing): pass
      o = O()
      
      class p(Thing >> Thing): pass
      
      class Q(Thing):
        is_a = [p.value(o), p.some(C)]
        
      class Q2(Thing): pass
        
        
      q = Q()
      q.is_a.append(Q2)

    assert q.p == []
    assert set(q.p.indirect()) == { o, C }
    
  def test_prop_28(self):
    world   = self.new_world()
    n       = world.get_ontology("http://www.semanticweb.org/test.owl")
    
    with n:
      class p(Thing >> Thing, TransitiveProperty): pass
      
      class C1(Thing): pass
      class C2(Thing): pass
      class C3(Thing): pass
      class C4(Thing): pass
      c1 = C1()
      c2 = C2()
      c3 = C3()
      
      c1.p = [c2]
      c2.p = [c3]
      
      C3.is_a = [p.some(C4)]
      
    assert c1.p == [c2]
    assert set(c1.p.indirect()) == { c2, c3, C4 }
    
  def test_prop_29(self):
    world   = self.new_world()
    n       = world.get_ontology("http://www.semanticweb.org/test.owl")
    
    with n:
      class Ingredient(Thing): pass
      class Kale(Ingredient): pass
      
      class Taste(Thing): pass
      class Bitter(Taste): pass
      
      class has_taste(Ingredient >> Taste): pass
      
      bitter = Bitter()
      Kale.is_a.append(has_taste.some(Bitter))
      
      kale = Kale()
      
    assert kale.has_taste == []
    assert set(kale.has_taste.indirect()) == { Bitter }
    
  def test_prop_30(self):
    world   = self.new_world()
    n       = world.get_ontology("http://www.semanticweb.org/test.owl")
    
    with n:
      class Ingredient(Thing): pass
      class Kale(Ingredient): pass
      
      class Taste(Thing): pass
      
      class has_taste(Ingredient >> Taste): pass
      
      bitter = Taste()
      Kale.is_a.append(has_taste.value(bitter))
      
      kale = Kale()
      
    assert kale.has_taste == []
    assert set(kale.has_taste.indirect()) == { bitter }
    
  def test_prop_31(self):
    world   = self.new_world()
    o       = world.get_ontology("http://www.semanticweb.org/test.owl")
    
    with o:
      class C(Thing): pass
      class p(Thing >> Thing): pass
      class q(Thing >> Thing, FunctionalProperty): pass
      class p2(Thing >> str): pass
      class q2(Thing >> str, FunctionalProperty): pass

    c1 = C()
    c2 = C()
    c3 = C()
    c4 = C()
    
    c1.p = [c2, c3]
    assert set(p[c1]) == set([c2, c3])
    assert p[c1] is c1.p
      
    p[c1] = [c2, c4]
    assert set(p[c1]) == set([c2, c4])
    assert set(c1.p) == set([c2, c4])
    assert p[c1] is c1.p

    p[c2] = [c4, c3]
    assert set(p[c2]) == set([c4, c3])
    assert p[c2] is c2.p
    
    c1.p2 = ["c2", "c3"]
    assert set(p2[c1]) == set(["c2", "c3"])
    assert p2[c1] is c1.p2
    
    p2[c1] = ["c2", "c4"]
    assert set(p2[c1]) == set(["c2", "c4"])
    assert set(c1.p2) == set(["c2", "c4"])
    assert p2[c1] is c1.p2
    
    c1.q = c2
    assert q[c1] == [c2]

    q[c1] = [c4]
    assert c1.q == c4
     
    c1.q2 = "c2"
    assert q2[c1] == ["c2"]

    q2[c1] = ["c4"]
    assert c1.q2 == "c4"

    C.label.append("a")
    C.label.append("b")
    C.label = ["c", "d"]
    assert set(C.label) == set(["c", "d"])

    C.label.append("a")
    C.label.append("b")
    label[C] = ["c", "d"]
    assert set(C.label) == set(["c", "d"])
    
  def test_prop_31_2(self):
    world   = self.new_world()
    o       = world.get_ontology("http://www.semanticweb.org/test.owl")
    
    with o:
      class C(Thing): pass
      class D(Thing): pass
      class E(Thing): pass
      class F(Thing): pass
      class G(Thing): pass
      class H(Thing): pass
      class I(Thing): pass
      class J(Thing): pass
      class p(Thing >> Thing, TransitiveProperty): pass
      
    c = C()
    d = D()
    e = E()
    f = F()
    g = G()
    h = H()
    i = I()
    j = J()
    c.p = [d]
    D.is_a.append(p.some(E))
    E.is_a.append(p.value(f))
    G.equivalent_to.append(E)
    G.is_a.append(p.value(h))
    i.equivalent_to.append(h)
    h.p = [j]
    
    assert set(c.INDIRECT_p) == set([d, E, f, G, h, i, j])
    assert set(d.INDIRECT_p) == set([E, f, G, h, i, j])
    assert set(e.INDIRECT_p) == set([f, G, h, i, j])
    
  def test_prop_32(self):
    world   = self.new_world()
    o       = world.get_ontology("http://www.semanticweb.org/test.owl")
    
    with o:
      class C(Thing): pass
      class D(Thing): pass
      class E(Thing): pass
      class F(Thing): pass
      class G(Thing): pass
      class H(Thing): pass
      class I(Thing): pass
      class J(Thing): pass
      class p(Thing >> Thing, TransitiveProperty, SymmetricProperty): pass
      
    c = C()
    d = D()
    e = E()
    f = F()
    g = G()
    h = H()
    i = I()
    j = J()
    c.p = [d]
    D.is_a.append(p.some(E))
    E.is_a.append(p.value(f))
    G.equivalent_to.append(E)
    G.is_a.append(p.value(h))
    i.equivalent_to.append(h)
    h.p = [j]
    
    assert set(c.INDIRECT_p) == set([c, d, E, f, G, h, i, j])
    assert set(d.INDIRECT_p) == set([c, d, E, f, G, h, i, j])
    assert set(e.INDIRECT_p) == set([f, G, h, i, j])
    
  def test_prop_33(self):
    world   = self.new_world()
    o       = world.get_ontology("http://www.semanticweb.org/test.owl")
    
    with o:
      class C(Thing): pass
      class D(Thing): pass
      class E(Thing): pass
      class F(Thing): pass
      class J(Thing): pass
      class p(Thing >> Thing): pass
      
    c = C()
    d = D()
    e = E()
    f = F()
    j = J()
    c.p = [d]
    c.equivalent_to.append(e)
    F.equivalent_to.append(E)
    F.is_a.append(p.some(j))
    
    assert set(e.INDIRECT_p) == set([d, j])
    
  def test_prop_34(self):
    world   = self.new_world()
    o       = world.get_ontology("http://www.semanticweb.org/test.owl")
    
    with o:
      class C(Thing): pass
      class D(Thing): pass
      class E(Thing): pass
      class F(Thing): pass
      class J(Thing): pass
      class p(Thing >> str): pass
      
    c = C()
    d = D()
    e = E()
    f = F()
    j = J()
    c.p = ["1"]
    c.equivalent_to.append(e)
    F.equivalent_to.append(E)
    F.is_a.append(p.value("2"))
    
    c.label = "c"
    e.label = "e"
    
    assert set(e.INDIRECT_p) == set(["1", "2"])
    assert c.label == ["c"]
    assert e.label == ["e"]
    assert c.INDIRECT_label == ["c"]
    assert e.INDIRECT_label == ["e"]
    
  def test_prop_35(self):
    world   = self.new_world()
    o       = world.get_ontology("http://www.semanticweb.org/test.owl")
    
    with o:
      class C(Thing): pass
      class p(C >> int): pass

    assert p.range_iri == ["http://www.w3.org/2001/XMLSchema#integer"]
    assert p.range == [int]
    
    p.range_iri = ["http://www.w3.org/2001/XMLSchema#float"]

    assert p.range_iri == ["http://www.w3.org/2001/XMLSchema#float"]
    assert p.range == [float]
    
    
    p.range_iri = ["http://www.w3.org/2001/XMLSchema#int"]
    assert p.range_iri == ["http://www.w3.org/2001/XMLSchema#int"]
    assert p.range == [int]
    
  def test_prop_36(self):
    world   = self.new_world()
    o       = world.get_ontology("http://www.semanticweb.org/test.owl")
    
    with o:
      class C(Thing): pass
      class p(C >> int): pass
      
    assert p.range_iri == ["http://www.w3.org/2001/XMLSchema#integer"]
    assert p.range == [int]
    
    p.range = [float]
    
    assert p.range_iri == ["http://www.w3.org/2001/XMLSchema#decimal"]
    assert p.range == [float]
    
    p.range = [int]
    assert p.range_iri == ["http://www.w3.org/2001/XMLSchema#integer"]
    assert p.range == [int]
    
  def test_prop_37(self):
    world   = self.new_world()
    o       = world.get_ontology("http://www.semanticweb.org/test.owl")
    
    with o:
      class C(Thing): pass
      class D(Thing): pass
      class p(C >> (C & D)): pass
      
    assert p.range_iri[0].startswith("_:")
    
  def test_prop_38(self):
    tmp = self.new_tmp_file()
    
    world = self.new_world()
    world.set_backend(filename = tmp)
    o1    = world.get_ontology("http://www.semanticweb.org/test1.owl")
    o2    = world.get_ontology("http://www.semanticweb.org/test2.owl")
    with o1:
      class p1(Thing >> Thing): pass
    with o2:
      class p2(Thing >> Thing): inverse = p1
    world.save()
    world.close()
    
    world = self.new_world()
    world.set_backend(filename = tmp)
    o2    = world.get_ontology("http://www.semanticweb.org/test2.owl").load()
    o1    = world.get_ontology("http://www.semanticweb.org/test1.owl").load()
    assert o2.p2.inverse is o1.p1
    assert o1.p1.inverse is o2.p2
    
  def test_prop_39(self):
    tmp = self.new_tmp_file()
    
    world = self.new_world()
    world.set_backend(filename = tmp)
    o1    = world.get_ontology("http://www.semanticweb.org/test1.owl")
    o2    = world.get_ontology("http://www.semanticweb.org/test2.owl")
    with o1:
      class p1(Thing >> Thing): pass
    with o2:
      class p2(p1): pass
    world.save()
    world.close()
    
    world = self.new_world()
    world.set_backend(filename = tmp)
    o2    = world.get_ontology("http://www.semanticweb.org/test2.owl").load()
    assert issubclass(p2, p1)
    
  def test_prop_40(self):
    world = self.new_world()
    onto  = world.get_ontology("http://www.semanticweb.org/test1.owl")
    with onto:
      class i(Thing >> Thing, SymmetricProperty): pass

    assert i.inverse_property is i
    assert i.inverse is i
    
  def test_prop_40(self):
    world = self.new_world()
    onto  = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    onto.has_topping.inverse = None
    assert onto.has_topping.inverse is None
    assert onto.topping_of.inverse is None
    
  def test_prop_41(self):
    world = self.new_world()
    onto  = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    
    onto.has_topping.inverse_property = None
    
    assert onto.ma_tomate.INVERSE_has_topping == [onto.ma_pizza]
    assert onto.ma_pizza .INVERSE_topping_of  == []
    
  def test_prop_42(self):
    world = self.new_world()
    onto  = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    
    assert onto.ma_tomate.INVERSE_has_topping == [onto.ma_pizza]
    assert onto.ma_pizza .INVERSE_topping_of  == [onto.ma_tomate, onto.mon_frometon]
    
  def test_prop_43(self):
    world = self.new_world()
    onto  = world.get_ontology("http://www.test.org/onto.owl")

    with onto:
      class D(Thing): pass
      class R(Thing): pass
      class p(D >> R): pass
      d1 = D()
      d2 = D()
      r1 = R()
      r2 = R()
      d1.p = [r1, r2]
      d2.p = [r1]
      
    assert set(r1.INVERSE_p) == set([d1, d2])
    assert set(r2.INVERSE_p) == set([d1])
    r1.INVERSE_p.remove(d1)
    r2.INVERSE_p.append(d2)
    assert set(r1.INVERSE_p) == set([d2])
    assert set(r2.INVERSE_p) == set([d1, d2])
    assert set(d1.p) == set([r2])
    assert set(d2.p) == set([r1, r2])
    
  def test_prop_44(self):
    world = self.new_world()
    onto  = world.get_ontology("http://www.test.org/onto.owl")

    with onto:
      class D(Thing): pass
      class R(Thing): pass
      class p(D >> R, FunctionalProperty): pass
      d1 = D()
      d2 = D()
      r1 = R()
      r2 = R()
      d1.p = r1
      d2.p = r1

    assert set(r1.INVERSE_p) == set([d1, d2])
    assert set(r2.INVERSE_p) == set([])
    r1.INVERSE_p.remove(d1)
    assert set(r1.INVERSE_p) == set([d2])
    assert set(r2.INVERSE_p) == set([])
    assert d1.p == None
    assert d2.p == r1
    r2.INVERSE_p.append(d2)
    assert set(r1.INVERSE_p) == set([])
    assert set(r2.INVERSE_p) == set([d2])
    assert d1.p == None
    assert d2.p == r2
    
  def test_prop_45(self):
    world = self.new_world()
    onto  = world.get_ontology("http://www.test.org/onto.owl")

    with onto:
      class D(Thing): pass
      class R(Thing): pass
      class p(D >> R, InverseFunctionalProperty): pass
      d1 = D()
      d2 = D()
      r1 = R()
      r2 = R()
      d1.p = [r1]
      d2.p = [r2]
      
    assert r1.INVERSE_p == d1
    assert r2.INVERSE_p == d2
    r1.INVERSE_p = d2
    assert r1.INVERSE_p == d2
    assert r2.INVERSE_p == d2
    assert set(d1.p) == set([])
    assert set(d2.p) == set([r2, r1])
    r2.INVERSE_p = None
    assert r1.INVERSE_p == d2
    assert r2.INVERSE_p == None
    assert set(d1.p) == set([])
    assert set(d2.p) == set([r1])
    
  def test_prop_46(self):
    world = self.new_world()
    onto  = world.get_ontology("http://www.test.org/onto.owl")

    with onto:
      class D(Thing): pass
      class R(Thing): pass
      class p(D >> R, FunctionalProperty, InverseFunctionalProperty): pass
      d1 = D()
      d2 = D()
      r1 = R()
      r2 = R()
      d1.p = r1
      d2.p = r2
      
    assert r1.INVERSE_p == d1
    assert r2.INVERSE_p == d2
    r1.INVERSE_p = d2
    assert r1.INVERSE_p == d2
    assert r2.INVERSE_p == None
    assert d1.p == None
    assert d2.p == r1
    
  def test_prop_47(self):
    world = self.new_world()
    onto  = world.get_ontology("http://www.test.org/onto.owl")
    
    with onto:
      class C(Thing): pass
      class p(C >> C, ReflexiveProperty): pass
      c1 = C()
      c2 = C(p = [c1])
      
    assert set(c1.p) == set([])
    assert set(c2.p) == set([c1])
    assert set(c1.INDIRECT_p) == set([c1])
    assert set(c2.INDIRECT_p) == set([c1, c2])
      
  def test_prop_48(self):
    world = self.new_world()
    onto  = world.get_ontology("http://www.test.org/onto.owl")
    
    with onto:
      class C(Thing): pass
      class p(C >> C): pass
      C.is_a.append(p.only(Nothing))

    sync_reasoner(world, debug = 0)
    assert p.equivalent_to == [bottomObjectProperty]

  def test_prop_49(self):
    w1 = self.new_world()
    onto1 = w1.get_ontology("http://test.org/t1.owl")
    onto2 = w1.get_ontology("http://test.org/t2.owl")
    
    with onto1:
      class p(Thing >> Thing): pass
      class i(Thing >> Thing): pass
      class C(Thing): pass
      
    o1 = BytesIO()
    onto1.save(o1)
    
    with onto2:
      p.inverse = i
      p.range.append(C)
      p.domain.append(C)
      p.python_name = "my_prop"
      
    o2 = BytesIO()
    onto2.save(o2)
    
    w2 = self.new_world()
    onto1 = w2.get_ontology("http://test.org/t1.owl").load(fileobj = BytesIO(o1.getvalue()))
    onto2 = w2.get_ontology("http://test.org/t2.owl").load(fileobj = BytesIO(o2.getvalue()))
    
    assert onto1.C in onto1.p.range
    assert onto1.C in onto1.p.domain
    assert onto1.p.python_name == "my_prop"
    assert onto1.p.inverse     is  onto1.i
    
  def test_prop_50(self):
    w = self.new_world()
    o = w.get_ontology("http://test.org/o.owl")
    with o:
      class p(ObjectProperty, FunctionalProperty): pass
      class C(Thing): pass
      c = C()
    assert p[c] == []
    assert p[C] == []
        
  def test_prop_51(self):
    w = self.new_world()
    o = w.get_ontology("http://test.org/o.owl")
    with o:
      class p (ObjectProperty): pass
      class p2(p): pass
      class q (ObjectProperty): pass
      
      class dp (DataProperty): pass
      class dp2(dp): pass
      class dq (DataProperty): pass
      
      class ap (AnnotationProperty): pass
      class ap2(ap): pass
      class aq (AnnotationProperty): pass
      
    assert set(ObjectProperty.descendants(world = w)) == { ObjectProperty, p, p2, q }
    assert set(ObjectProperty.descendants(world = w, include_self = False)) == { p, p2, q }
    
    assert set(DataProperty.descendants(world = w)) == { DataProperty, dp, dp2, dq }
    assert set(DataProperty.descendants(world = w, include_self = False)) == { dp, dp2, dq }
    
    assert set(AnnotationProperty.descendants(world = w)) == { AnnotationProperty, ap, ap2, aq, versionInfo, comment, priorVersion, seeAlso, backwardCompatibleWith, deprecated, label, incompatibleWith, isDefinedBy }
    assert set(AnnotationProperty.descendants(world = w, include_self = False)) == { ap, ap2, aq, versionInfo, comment, priorVersion, seeAlso, backwardCompatibleWith, deprecated, label, incompatibleWith, isDefinedBy }
    
    assert set(ObjectProperty    .subclasses(world = w)) == { p , q  }
    assert set(DataProperty      .subclasses(world = w)) == { dp, dq }
    assert set(AnnotationProperty.subclasses(world = w)) == { ap, aq, versionInfo, comment, priorVersion, seeAlso, backwardCompatibleWith, deprecated, label, incompatibleWith, isDefinedBy }
    
  def test_prop_52(self):
    n = self.new_ontology()
    with n:
      class C(Thing): pass
      class prop(DataProperty):
        range = [str]
        
    c1 = C()
    c1.prop = [locstr("Français 1", "fr"), locstr("Français 2", "fr-FR"), locstr("Français 3", "fr_be"), locstr("Anglais", "en")]
    assert c1.prop.fr    == ["Français 1"]
    assert c1.prop.fr_FR == ["Français 2"]
    assert c1.prop.fr_BE == ["Français 3"]
    assert set(c1.prop.fr_any) == { "Français 1", "Français 2", "Français 3" }
    
  def test_prop_53(self):
    w  = self.new_world()
    o1 = w.get_ontology("http://test.org/o1.owl")
    o2 = w.get_ontology("http://test.org/o2.owl")
    
    with o1:
      class C(Thing): pass
      class p(Thing >> Thing): pass
      
      c1 = C()
      c2 = C()
      c3 = C(p = [c1])
      
    with o2:
      c3.p.append(c2)
      
    c3.p.remove(c1)
    c3.p.remove(c2)
    
    assert len(c3.p) == 0
    del c3.p
    assert len(c3.p) == 0
    
  def test_prop_54(self):
    w  = self.new_world()
    o1 = w.get_ontology("http://test.org/o1.owl")
    o2 = w.get_ontology("http://test.org/o2.owl")
    
    with o1:
      class C(Thing): pass
      class p(Thing >> Thing, FunctionalProperty): pass
      
      c1 = C()
      c2 = C()
      
    with o2:
      c2.p = c1
      
    c2.p = None
    
    assert c2.p is None
    del c2.p
    assert c2.p is None
    
  def test_prop_55(self):
    w  = self.new_world()
    o1 = w.get_ontology("http://test.org/o1.owl")
    o2 = w.get_ontology("http://test.org/o2.owl")
    
    with o1:
      class C(Thing): pass
      class p(Thing >> Thing): pass
      
      c1 = C()
      c2 = C()
      c3 = C()
      c4 = C()
      
      c1.p = [c2, c3]
      
    with o2:
      c1.p = [c2, c4]
      
    assert c1.p == [c2, c4]
    
    self.assert_triple    (c1.storid, p.storid, c2.storid, world = w)
    self.assert_not_triple(c1.storid, p.storid, c3.storid, world = w)
    self.assert_triple    (c1.storid, p.storid, c4.storid, world = w)
    
  def test_prop_56(self):
    w  = self.new_world()
    o1 = w.get_ontology("http://test.org/o1.owl")
    with o1:
      class C(Thing): pass
      class i(C >> int): pass
      class p(AnnotationProperty): pass
      
      c1 = C(p = [locstr("Test", "en"), locstr("Test", "fr")])
      
      c1.p.remove(locstr("Test", "en"))
      assert c1.p == [locstr("Test", "fr")]
      del c1.p
      assert c1.p == [locstr("Test", "fr")]
      
  def test_prop_57(self):
    w1 = self.new_world()
    o  = w1.get_ontology("http://test.org/o.owl")
    with o:
      class C(Thing): pass
      c1 = C()
      c2 = C()
    with o.get_namespace("http://test.org/o/prop/"):
      class p(C >> C): pass
    c1.p = [c2]
    temp = self.new_tmp_file()
    o.save(temp)
    
    w2 = self.new_world()
    o  = w2.get_ontology(temp).load()
    assert o.c1.p == [o.c2]
    
  def test_prop_inverse_1(self):
    n = get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test")
    assert n.price.inverse_property is None
    assert n.has_topping.inverse_property is n.topping_of
    assert n.topping_of.inverse_property is n.has_topping
    
  def test_prop_inverse_2(self):
    n = get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test")
    assert n.ma_tomate.topping_of      == [n.ma_pizza]
    assert n.ma_tomate.main_topping_of == [n.ma_pizza]
    
  def test_prop_inverse_3(self):
    n = get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test")
    pizza  = n.Pizza()
    pizza2 = n.Pizza()
    tomato = n.Tomato()
    pizza.has_topping = [tomato]
    assert tomato.topping_of == [pizza]
    pizza2.has_topping.append(tomato)
    assert set(tomato.topping_of) == { pizza, pizza2 }
    tomato.topping_of.remove(pizza)
    assert pizza.has_topping == []
    
  def test_prop_inverse_4(self):
    n = get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test")
    pizza  = n.Pizza()
    pizza2 = n.Pizza()
    tomato = n.Tomato()
    pizza.has_main_topping = tomato
    assert tomato.main_topping_of == [pizza]
    tomato.main_topping_of.append(pizza2)
    assert pizza2.has_main_topping is tomato
    tomato.main_topping_of.remove(pizza)
    assert pizza.has_main_topping is None
    
  def test_prop_inverse_5(self):
    n = get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test")
    pizza  = n.Pizza()
    pizza2 = n.Pizza()
    tomato = n.Tomato()
    pizza.has_main_topping = tomato
    assert tomato.main_topping_of == [pizza]
    pizza.has_main_topping = None
    assert tomato.main_topping_of == []
    
  def test_prop_inverse_6(self):
    n = self.new_ontology()
    class C(Thing): namespace = n
    class prop (ObjectProperty): namespace = n
    class iprop(ObjectProperty): namespace = n
    iprop.inverse_property # Load it
    prop.inverse_property = iprop
    self.assert_triple(prop.storid, owl_inverse_property, iprop.storid)
    
    c1 = C()
    c2 = C()
    c1.prop = [c2]
    assert iprop.inverse_property == prop
    assert c2.iprop == [c1]
    
  def test_prop_inverse_7(self):
    n = self.new_ontology()
    class C(Thing): namespace = n
    class prop (ObjectProperty): namespace = n
    class iprop(ObjectProperty):
      namespace = n
      inverse_property = prop
    self.assert_triple(iprop.storid, owl_inverse_property, prop.storid)
    
    c1 = C()
    c2 = C()
    c1.prop = [c2]
    assert iprop.inverse_property == prop
    assert c2.iprop == [c1]
    
  def test_prop_inverse_8(self):
    w = self.new_world()
    o = w.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    assert o.has_topping._inverse_storid == o.topping_of.storid
    assert o.topping_of._inverse_storid == o.has_topping.storid

    with o:
      class s(ObjectProperty, SymmetricProperty): pass
      
    assert s._inverse_storid == s.storid
    
    with o:
      class p(ObjectProperty): pass
      
    assert p._inverse_storid == 0
    
    p.is_a.append(SymmetricProperty)
    
    assert p._inverse_storid == p.storid
    
    p.is_a.remove(SymmetricProperty)
      
    assert p._inverse_storid == 0
    
  def test_prop_inverse_9(self):
    w = self.new_world()
    o = w.get_ontology("http://www.test.org/onto.owl")

    with o:
      class sym_prop(ObjectProperty, SymmetricProperty): pass
      class sub_prop(sym_prop): pass

      class C(Thing): pass
      c1 = C()
      c2 = C()
      c3 = C()

    assert sym_prop.inverse is sym_prop
    assert sub_prop.inverse is None

    c1.sym_prop = [c2]
    c1.sub_prop = [c3]

    assert c2.sym_prop == [c1]
    assert c2.sub_prop == []
    assert c3.sym_prop == []
    assert c3.sub_prop == []
    
  def test_prop_inverse_10(self):
    w = self.new_world()
    o = w.get_ontology("http://www.test.org/onto.owl")
    
    with o:
      class prop (ObjectProperty): pass
      class iprop(ObjectProperty): inverse_property = prop
      class C(Thing): pass

      c1 = C()
      c2 = C()
      c3 = C()
      c1.prop.append(c2)
      c2.prop.append(c3)
      
      assert c2.iprop == [c1]
      assert list( prop.get_relations()) == [(c1, c2), (c2, c3)]
      assert list(iprop.get_relations()) == [(c2, c1), (c3, c2)]
      
      
  def test_construct_not_1(self):
    n = get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test")
    assert n.NonPizza.__bases__ == (Thing,)
    for p in n.NonPizza.is_a:
      if isinstance(p, Construct):
        assert p.__class__ is Not
        assert p.Class is n.Pizza
        break
    else: assert False
    self.assert_nb_created_triples(0)
    
  def test_construct_not_2(self):
    n = self.new_ontology()
    class C1(Thing): namespace = n
    class C2(Thing):
      namespace = n
      is_a      = [Not(C1)]
      
    for p in C2.is_a:
      if isinstance(p, Construct): bnode = p.storid; break
      
    self.assert_triple(bnode, rdf_type, owl_class)
    self.assert_triple(bnode, owl_complementof, C1.storid)
    
  def test_construct_not_3(self):
    n = self.new_ontology()
    class C1 (Thing): namespace = n
    class C1b(Thing): namespace = n
    class C2 (Thing):
      namespace = n
      is_a      = [Not(C1)]
      
    for p in C2.is_a:
      if isinstance(p, Construct): bnode = p.storid; break
      
    p.Class = C1b
    
    self.assert_triple    (bnode, rdf_type, owl_class)
    self.assert_triple    (bnode, owl_complementof, C1b.storid)
    self.assert_not_triple(bnode, owl_complementof, C1.storid)

  def test_construct_not_4(self):
    n = self.new_ontology()
    class C1(Thing): namespace = n
    class C2(Thing): namespace = n
    class C3(Thing): namespace = n
    
    NOT = Not(C1)
    C2.is_a.append(NOT)
    self.assert_triple(NOT.storid, rdf_type, owl_class)
    self.assert_triple(NOT.storid, owl_complementof, C1.storid)
    self.assert_triple(C2.storid, rdfs_subclassof, NOT.storid)
     
  def test_construct_restriction_1(self):
    n = get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test")
    assert len(n.VegetarianPizza.is_a) == 2
    for p in n.VegetarianPizza.is_a:
      if isinstance(p, Not): r = p.Class; break
    assert isinstance(r, Restriction)
    assert r.type  == SOME
    assert r.property == n.has_topping
    assert r.value == n.Meat
    assert r.cardinality is None
    assert len(list(default_world._get_obj_triples_spo_spo(r.storid, None, None))) == 3
    
  def test_construct_restriction_2(self):
    n = self.new_ontology()
    class C1(Thing): namespace = n
    class C2(Thing): namespace = n
    class C3(Thing): namespace = n
    class P1(ObjectProperty): namespace = n
    class P2(ObjectProperty): namespace = n
    
    C1.is_a.append(P1.only(C2))
    
    r     = C1.is_a[-1]
    bnode = r.storid
    self.assert_triple(bnode, rdf_type, owl_restriction)
    self.assert_triple(bnode, owl_onproperty, P1.storid)
    self.assert_triple(bnode, ONLY, C2.storid)
    assert len(list(default_world._get_triples_spod_spod(bnode, None, None, None))) == 3
    
    r.value = C3
    self.assert_triple(bnode, rdf_type, owl_restriction)
    self.assert_triple(bnode, owl_onproperty, P1.storid)
    self.assert_triple(bnode, ONLY, C3.storid)
    assert len(list(default_world._get_triples_spod_spod(bnode, None, None, None))) == 3
    
    r.property = P2
    self.assert_triple(bnode, rdf_type, owl_restriction)
    self.assert_triple(bnode, owl_onproperty, P2.storid)
    self.assert_triple(bnode, ONLY, C3.storid)
    assert len(list(default_world._get_triples_spod_spod(bnode, None, None, None))) == 3
    
    r.type        = EXACTLY
    r.cardinality = 2
    self.assert_triple(bnode, rdf_type, owl_restriction)
    self.assert_triple(bnode, owl_onproperty, P2.storid)
    self.assert_triple(bnode, owl_onclass, C3.storid)
    self.assert_triple(bnode, EXACTLY, 2, n._abbreviate("http://www.w3.org/2001/XMLSchema#nonNegativeInteger"))
    assert len(list(default_world._get_triples_spod_spod(bnode, None, None, None))) == 4
    
    r.type        = MIN
    r.cardinality = 3
    self.assert_triple(bnode, rdf_type, owl_restriction)
    self.assert_triple(bnode, owl_onproperty, P2.storid)
    self.assert_triple(bnode, owl_onclass, C3.storid)
    self.assert_triple(bnode, MIN, 3, n._abbreviate("http://www.w3.org/2001/XMLSchema#nonNegativeInteger"))
    assert len(list(default_world._get_triples_spod_spod(bnode, None, None, None))) == 4
    
    r.value = None
    self.assert_triple(bnode, rdf_type, owl_restriction)
    self.assert_triple(bnode, owl_onproperty, P2.storid)
    self.assert_triple(bnode, owl_min_cardinality, 3, n._abbreviate("http://www.w3.org/2001/XMLSchema#nonNegativeInteger"))
    assert len(list(default_world._get_triples_spod_spod(bnode, None, None, None))) == 3
    
    r.type = MAX
    self.assert_triple(bnode, rdf_type, owl_restriction)
    self.assert_triple(bnode, owl_onproperty, P2.storid)
    self.assert_triple(bnode, owl_max_cardinality, 3, n._abbreviate("http://www.w3.org/2001/XMLSchema#nonNegativeInteger"))
    assert len(list(default_world._get_triples_spod_spod(bnode, None, None, None))) == 3
    
    r.value = C2
    self.assert_triple(bnode, rdf_type, owl_restriction)
    self.assert_triple(bnode, owl_onproperty, P2.storid)
    self.assert_triple(bnode, owl_onclass, C2.storid)
    self.assert_triple(bnode, MAX, 3, n._abbreviate("http://www.w3.org/2001/XMLSchema#nonNegativeInteger"))
    assert len(list(default_world._get_triples_spod_spod(bnode, None, None, None))) == 4
    
    r.type = EXACTLY
    self.assert_triple(bnode, rdf_type, owl_restriction)
    self.assert_triple(bnode, owl_onproperty, P2.storid)
    self.assert_triple(bnode, owl_onclass, C2.storid)
    self.assert_triple(bnode, EXACTLY, 3, n._abbreviate("http://www.w3.org/2001/XMLSchema#nonNegativeInteger"))
    assert len(list(default_world._get_triples_spod_spod(bnode, None, None, None))) == 4
    
  def test_construct_restriction_3(self):
    n = self.new_ontology()
    class C1(Thing): namespace = n
    class C2(Thing): namespace = n
    class P(ObjectProperty): namespace = n
    
    c1 = C1()
    c1.is_a.append(P.some(C2))
    
    r     = c1.is_a[-1]
    bnode = r.storid
    self.assert_triple(bnode, rdf_type, owl_restriction)
    self.assert_triple(bnode, owl_onproperty, P.storid)
    self.assert_triple(bnode, SOME, C2.storid)
    
  def test_construct_restriction_4(self):
    n = self.new_ontology()
    class C1(Thing): namespace = n
    class P1(DataProperty): namespace = n
    
    C1.is_a.append(P1.only(int))
    
    r     = C1.is_a[-1]
    bnode = r.storid
    self.assert_triple(bnode, rdf_type, owl_restriction)
    self.assert_triple(bnode, owl_onproperty, P1.storid)
    self.assert_triple(bnode, ONLY, n._abbreviate("http://www.w3.org/2001/XMLSchema#integer"))
    assert len(list(default_world._get_triples_spod_spod(bnode, None, None, None))) == 3
    
    r.value       = float
    r.type        = EXACTLY
    r.cardinality = 5
    self.assert_triple(bnode, rdf_type, owl_restriction)
    self.assert_triple(bnode, owl_onproperty, P1.storid)
    self.assert_triple(bnode, EXACTLY, 5, n._abbreviate("http://www.w3.org/2001/XMLSchema#nonNegativeInteger"))
    self.assert_triple(bnode, owl_ondatarange, n._abbreviate("http://www.w3.org/2001/XMLSchema#decimal"))
    assert len(list(default_world._get_triples_spod_spod(bnode, None, None, None))) == 4
    
  def test_construct_restriction_5(self):
    n = get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test")
    a = n.has_topping.some(n.Vegetable)
    b = n.has_topping.some(n.Vegetable)
    
    assert a == b
    
  def test_construct_restriction_6(self):
    n = get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test")
    
    assert Not(n.has_topping.some(n.Meat)) in n.VegetarianPizza.is_a
    
  def test_construct_restriction_7(self):
    w = self.new_world()
    o = w.get_ontology("http://test.org/onto.owl")
    
    with o:
      class p(Thing >> Thing): pass
      class C(Thing): pass
      class D(Thing):
        is_a = [p.some(C)]
        
    assert D.is_a[1].value is C
    
    D.is_a[1].type        = MIN
    D.is_a[1].cardinality = 2
    
    assert D.is_a[1].value is C
    
    
  def test_and_or_1(self):
    n = get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test")
    
    assert len(n.Vegetable.is_a) == 2
    assert isinstance(n.Vegetable.is_a[-1], Or)
    assert set(n.Vegetable.is_a[-1].Classes) == { n.Tomato, n.Eggplant, n.Olive }
    
  def test_and_or_2(self):
    n = self.new_ontology()
    class C1(Thing): namespace = n
    class C2(Thing): namespace = n
    class C3(Thing): namespace = n
    class C4(Thing): namespace = n
    
    C1.is_a.append(C2 | C3)
    c = C1.is_a[-1]
    assert isinstance(c, Or)
    assert len(c.Classes) == 2
    assert set(c.Classes) == { C2, C3 }
    self.assert_triple(c.storid, rdf_type, owl_class)
    self.assert_triple(c.storid, owl_unionof, c._list_bnode)
    assert set(n._parse_list(c._list_bnode)) == { C2, C3 }
    
    c.Classes.append(C4)
    assert len(c.Classes) == 3
    assert set(c.Classes) == { C2, C3, C4 }
    self.assert_triple(c.storid, rdf_type, owl_class)
    self.assert_triple(c.storid, owl_unionof, c._list_bnode)
    assert set(n._parse_list(c._list_bnode)) == { C2, C3, C4 }
    
    c.Classes.remove(C3)
    assert len(c.Classes) == 2
    assert set(c.Classes) == { C2, C4 }
    self.assert_triple(c.storid, rdf_type, owl_class)
    self.assert_triple(c.storid, owl_unionof, c._list_bnode)
    assert set(n._parse_list(c._list_bnode)) == { C2, C4 }
    
  def test_and_or_3(self):
    n = self.new_ontology()
    with n:
      class p(DataProperty): pass
      class C(Thing):
        is_a = [p.some(Or([int, float]))]
        
    bnode = C.is_a[-1].value.storid
    self.assert_triple(bnode, rdf_type, rdfs_datatype)
    
  def test_and_or_4(self):
    w = self.new_world()
    o = w.get_ontology("http://www.test.org/test.owl")
    
    with o:
      class C1(Thing): pass
      class C2(Thing): pass
      class C3(Thing): pass
      
    assert repr(C1 | C2 | C3) == "test.C1 | test.C2 | test.C3"
    assert repr(C1 & C2 & C3) == "test.C1 & test.C2 & test.C3"
    
  def test_and_or_5(self):
    import copy
    
    w  = self.new_world()
    o1 = w.get_ontology("http://www.test.org/test.owl")
    o2 = w.get_ontology("http://www.test.org/test.owl")
    
    with o1:
      class p(Thing >> Thing): pass
      class C1(Thing): pass
      class C2(Thing): pass
      class C3(Thing):
        is_a = [p.some(C1) & C2]
    
    with o2:
      class D(Thing): pass
      for p in C3.is_a:
        D.is_a.append(p)
    
      
    
  def test_one_of_1(self):
    n = self.new_ontology()
    class C(Thing): namespace = n
    c1 = C()
    c2 = C()
    c3 = C()
    oneof = OneOf([c1, c2, c3])
    C.is_a.append(oneof)
    self.assert_triple(C.storid, rdfs_subclassof, oneof.storid)
    self.assert_triple(oneof.storid, owl_oneof, oneof._list_bnode)
    assert n._parse_list(oneof._list_bnode) == [c1, c2, c3]

  def test_one_of_2(self):
    w = self.new_world()
    o = w.get_ontology("http://www.test.org/test.owl")
    
    with o:
      class p(DataProperty):
        range = [OneOf([1, "abc", locstr("texte", "fr")])]

    filename = self.new_tmp_file()
    o.save(filename)

    w = self.new_world()
    o = w.get_ontology(filename).load()
    
    assert o.p.range[0] == OneOf([1, "abc", locstr("texte", "fr")])
    
  def test_one_of_3(self):
    w = self.new_world()
    o = w.get_ontology("http://www.test.org/test.owl")
    
    with o:
      class p(DataProperty): pass
      p.range = [OneOf([1, 2, 3, 4, 5, 6, 7])]
      
    filename = self.new_tmp_file()
    o.save(filename)
    
    w = self.new_world()
    o = w.get_ontology(filename).load()
    
    list_bn = w.graph._get_obj_triple_sp_o(o.p.range[0].storid, owl_oneof)
    
    assert set(o.p.range[0].instances) == { 1, 2, 3, 4, 5, 6, 7 }
    assert set(w._parse_list_as_rdf(list_bn)) == {(7, 43), (2, 43), (3, 43), (5, 43), (6, 43), (1, 43), (4, 43)}

    
  def test_method_1(self):
    n = self.new_ontology()
    ok = []
    class C1(Thing):
      namespace = n
      def test(self): ok.append(1)

    C1().test()
    assert ok
    
  def test_method_2(self):
    n = self.new_ontology()
    ok = []
    class C1(Thing):
      namespace = n
      def test(self): pass
    class C2(C1):
      namespace = n
      def test(self): ok.append(1)
      
    C2().test()
    assert ok
    
  def test_reasoning_1(self):
    world   = self.new_world()
    onto    = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/2/test_reasoning.owl").load()
    results = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/2/test_reasoning_reasoning.owl")
    
    with results:
      sync_reasoner(world, debug = 0)
      
    self.assert_triple(onto.VegetalianPizza.storid, rdfs_subclassof, onto.VegetarianPizza.storid, None, world)
    self.assert_triple(onto.pizza_tomato.storid, rdf_type, onto.VegetalianPizza.storid, None, world)
    self.assert_triple(onto.pizza_tomato_cheese.storid, rdf_type, onto.VegetarianPizza.storid, None, world)
    
    assert onto.VegetarianPizza in onto.VegetalianPizza.__bases__
    assert onto.pizza_tomato.__class__ is onto.VegetalianPizza
    assert onto.pizza_tomato_cheese.__class__ is onto.VegetarianPizza
    
    assert len(results.graph) == 4
    
  def test_reasoning_2(self):
    world = self.new_world()
    onto  = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/2/test_reasoning.owl").load()
    
    # Store them in memory
    entities = [onto.VegetalianPizza, onto.VegetarianPizza, onto.pizza_tomato, onto.pizza_tomato_cheese, onto.pizza_tomato_meat] 
    sync_reasoner(world, debug = 0)
    
    assert entities == [onto.VegetalianPizza, onto.VegetarianPizza, onto.pizza_tomato, onto.pizza_tomato_cheese, onto.pizza_tomato_meat] 
    assert onto.VegetarianPizza in onto.VegetalianPizza.__bases__
    assert onto.pizza_tomato.__class__ is onto.VegetalianPizza
    assert onto.pizza_tomato_cheese.__class__ is onto.VegetarianPizza
    
  def test_reasoning_3(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/drug.owl")

    output = ""
    def print(s):
      nonlocal output
      output += s + "\n"
      
    with onto:
        class Drug(Thing):
            def take(self): print("I took a drug")

        class ActivePrinciple(Thing):
            pass

        class has_for_active_principle(Drug >> ActivePrinciple):
            python_name = "active_principles"
            
        class Placebo(Drug):
            equivalent_to = [Drug & Not(has_for_active_principle.some(ActivePrinciple))]
            def take(self): print("I took a placebo")
            
        class SingleActivePrincipleDrug(Drug):
            equivalent_to = [Drug & has_for_active_principle.exactly(1, ActivePrinciple)]
            def take(self): print("I took a drug with a single active principle")
            
        class DrugAssociation(Drug):
            equivalent_to = [Drug & has_for_active_principle.min(2, ActivePrinciple)]
            def take(self): print("I took a drug with %s active principles" % len(self.active_principles))
            
    acetaminophen   = ActivePrinciple("acetaminophen")
    amoxicillin     = ActivePrinciple("amoxicillin")
    clavulanic_acid = ActivePrinciple("clavulanic_acid")
    
    AllDifferent([acetaminophen, amoxicillin, clavulanic_acid])
    
    drug1 = Drug(active_principles = [acetaminophen])
    drug2 = Drug(active_principles = [amoxicillin, clavulanic_acid])
    drug3 = Drug(active_principles = [])

    close_world(Drug)
    
    # Running the reasoner
    with onto:
      sync_reasoner(world, debug = 0)
        
    # Results of the automatic classification
    drug1.take()
    drug2.take()
    drug3.take()
    
    assert drug1.__class__ is onto.SingleActivePrincipleDrug
    assert drug2.__class__ is onto.DrugAssociation
    assert drug3.__class__ is onto.Placebo
    
    assert output == """I took a drug with a single active principle
I took a drug with 2 active principles
I took a placebo
"""
    
  def test_reasoning_4(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/test.owl")
    
    with onto:
      class C(Thing): pass
      class D(Thing): pass
      class E(Thing): pass
      class p(ObjectProperty, FunctionalProperty):
        domain = [C]
        range  = [D]
        
      class F(C):
        is_a = [p.some(E)]
        
      AllDisjoint([C, D, E])
      
    sync_reasoner(world, debug = 0)
    
    assert Nothing in F.equivalent_to
    assert F in list(world.inconsistent_classes())
    
  def test_reasoning_5(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/test.owl")
    
    with onto:
      class C(Thing): pass
      class D(Thing): pass
      class E(Thing): pass
      class p(ObjectProperty, FunctionalProperty):
        domain = [C]
        range  = [D]
        
      class F(C):
        is_a = [p.some(E)]
        
      f = F()
      AllDisjoint([C, D, E])

    try:
      sync_reasoner(world, debug = 0)
    except OwlReadyInconsistentOntologyError:
      return

    assert False
     
  def test_reasoning_6(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/test.owl#")
    
    with onto:
      class Personne(Thing): pass
      
      class age   (Personne >> int  , FunctionalProperty): pass
      class taille(Personne >> float, FunctionalProperty): pass
      
      class PersonneAgée(Personne):
        equivalent_to = [
          Personne & (age >= 65)
        ]
        
      class PersonneGrande(Personne):
        equivalent_to = [
          Personne & taille.some(ConstrainedDatatype(float, min_inclusive = 1.8))
        ]
        
      p1 = Personne(age = 25, taille = 2.0)
      p2 = Personne(age = 39, taille = 1.7)
      p3 = Personne(age = 65, taille = 1.6)
      p4 = Personne(age = 71, taille = 1.9)
      
    sync_reasoner(world, debug = 0)

    assert set(p1.is_a) == {PersonneGrande}
    assert set(p2.is_a) == {Personne}
    assert set(p3.is_a) == {PersonneAgée}
    assert set(p4.is_a) == {PersonneAgée, PersonneGrande}
    
  def test_reasoning_7(self):
    world = self.new_world()
    onto  = world.get_ontology("onto2.owl").load()

    assert onto.t2 .prop == []
    assert onto.t22.prop == []
    
    sync_reasoner(world, infer_property_values = True, debug = 0)

    assert onto.t2 .prop == [onto.o]
    assert onto.t22.prop == [onto.o]
    
  def test_reasoning_8(self):
    world = self.new_world()
    onto  = world.get_ontology("http://www.lesfleursdunormal.fr/static/_downloads/pizza_onto.owl").load()
    
    assert onto.pizza1.has_topping == [onto.meatTopping1]
    assert onto.pizza2.has_topping == []
    
    sync_reasoner(world, infer_property_values = True, debug = 0)
    
    assert onto.pizza1.has_topping == [onto.meatTopping1]
    assert onto.pizza2.has_topping == [onto.meatTopping1]
    
  def test_reasoning_9(self):
    world = self.new_world()
    onto  = world.get_ontology("test_rule.owl").load()
    
    assert set(onto.e.is_a) == set([onto.E])
    assert set(onto.e.prop) == set([])
    
    sync_reasoner(world, infer_property_values = True, debug = 0)
    
    assert set(onto.e.is_a) == set([onto.E, onto.S])
    assert set(onto.e.prop) == set([onto.obj])
    
  def test_reasoning_10(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/test.owl")
    
    with onto:
      class C(Thing): pass
      class D(Thing): pass
      class E(Thing): pass
      class p(ObjectProperty, FunctionalProperty):
        domain = [C]
        range  = [D]
        
      class F(C):
        is_a = [p.some(E)]
        
      f = F()
      AllDisjoint([C, D, E])

    with onto:
      try:
        sync_reasoner(world, debug = 0)
      except OwlReadyInconsistentOntologyError:
        return
      
    assert False
    
  def test_reasoning_11(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/test.owl")
    
    with onto:
      class C(Thing): pass
      class p1(C >> float, FunctionalProperty): pass
      class p2(C >> float, FunctionalProperty): label = "p"
      class p3(C >> float, FunctionalProperty): python_name = "py"
      
    sync_reasoner(world, debug = 0)
    
    assert p1.is_a == [DataProperty, FunctionalProperty]
    assert p2.is_a == [DataProperty, FunctionalProperty]
    assert p3.is_a == [DataProperty, FunctionalProperty]
    
     
  def test_pellet_reasoning_1(self):
    world = self.new_world()
    onto  = world.get_ontology("test_rule.owl").load()
    
    sync_reasoner_pellet(world, infer_property_values = True, infer_data_property_values = True, debug = 0)

    assert set(onto.e.is_a) == set([onto.E, onto.S])
    assert set(onto.e.prop) == set([onto.obj])

    assert set(onto.e.data_prop) == set([1.0, locstr("english", "en"), True])
    assert len(onto.e.data_prop) == 3
    
    i = [i for i in onto.e.data_prop if isinstance(i, str)][0]
    assert i.lang == "en"
    
  def test_pellet_reasoning_2(self):
    world = self.new_world()
    onto  = world.get_ontology("test_rule.owl").load()
    
    onto.e.data_prop = [1.0, locstr("english", "en"), True]
    
    sync_reasoner_pellet(world, infer_property_values = True, infer_data_property_values = True, debug = 0)
    
    assert set(onto.e.is_a) == set([onto.E, onto.S])
    assert set(onto.e.prop) == set([onto.obj])
    assert set(onto.e.data_prop) == set([1.0, locstr("english", "en"), True])
    assert len(onto.e.data_prop) == 3
    
    i = [i for i in onto.e.data_prop if isinstance(i, str)][0]
    assert i.lang == "en"
    
  def test_pellet_reasoning_3(self):
    world = self.new_world()
    onto  = world.get_ontology("test.owl")
    
    with onto:
      class C(Thing): pass
      class D(Thing):
        equivalent_to = [C]

      c1 = C()
      ca = C(0)

    sync_reasoner_pellet(world, debug = 0)
    
    assert isinstance(c1, D)
    assert isinstance(ca, D)
    assert set(C.instances()) == { c1, ca }


  def test_pellet_reasoning_4(self):
    world = self.new_world()
    onto  = world.get_ontology("test.owl")
    
    with onto:
      class C(Thing): pass
      class p(Thing >> str): pass
  
      c1 = C()
      c1.p.append("a,b")
      
      c2 = C()
      c2.p.append("a")
      c2.p.append("b")
      
      sync_reasoner_pellet(world, infer_property_values = True, infer_data_property_values = True, debug = 0)
      
      assert len(c1.p) == 1
      assert len(c2.p) == 2
    
    
  def test_hermit_reasoning_1(self):
    world = self.new_world()
    ontoA = world.get_ontology("A.owl").load()
    ontoB = world.get_ontology("B.owl").load()
    ontoC = world.get_ontology("C.owl").load()
    
    sync_reasoner_hermit(world, debug = 0)
    
    
  def test_disjoint_1(self):
    world = self.new_world()
    n     = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/2/test_reasoning.owl").load()
    assert len(list(n.disjoints())) == 1
    assert set(list(n.disjoints())[0].entities) == { n.Cheese, n.Meat, n.Vegetable }
    
  def test_disjoint_2(self):
    n = self.new_ontology()
    with n:
      class C1(Thing): pass
      class C2(Thing): pass
      class C3(Thing): pass
      d = AllDisjoint([C1, C2])
      
    assert not d._list_bnode
    self.assert_triple(C1.storid, owl_disjointwith, C2.storid)
    
    d.entities.append(C3)
    
    self.assert_not_triple(C1.storid, owl_disjointwith, C2.storid)
    assert set(n._parse_list(d._list_bnode)) == { C1, C2, C3 }
    
  def test_disjoint_3(self):
    n = self.new_ontology()
    with n:
      class P1(ObjectProperty): pass
      class P2(ObjectProperty): pass
      class P3(ObjectProperty): pass
      d = AllDisjoint([P1, P2])
      
    assert not d._list_bnode
    self.assert_triple(P1.storid, owl_propdisjointwith, P2.storid)
    
    d.entities.append(P3)
    
    self.assert_not_triple(P1.storid, owl_disjointwith, P2.storid)
    assert set(n._parse_list(d._list_bnode)) == { P1, P2, P3 }
    
  def test_disjoint_4(self):
    n = self.new_ontology()
    with n:
      class C(Thing): pass
      c1 = C()
      c2 = C()
      c3 = C()
      d = AllDisjoint([c1, c2])
      
    assert set(n._parse_list(d._list_bnode)) == { c1, c2 }
    
    d.entities.append(c3)
    
    assert set(n._parse_list(d._list_bnode)) == { c1, c2, c3 }
    
  def test_disjoint_5(self):
    n = self.new_ontology()
    with n:
      class C(Thing): pass
      class D(Thing): pass
      class E(Thing): pass
      class F(Thing): pass
      class G(Thing): pass
      AllDisjoint([C, D])
      AllDisjoint([C, E, F])
      AllDisjoint([G, F])
      AllDisjoint([E, F, G])
      
    s = set(frozenset(d.entities) for d in C.disjoints())
    
    assert s == { frozenset([C, D]), frozenset([C, E, F]) }
    
  def test_disjoint_6(self):
    n = self.new_ontology()
    with n:
      class O(Thing): pass
      c = O()
      d = O()
      e = O()
      f = O()
      g = O()
      AllDisjoint([c, d])
      AllDisjoint([c, e, f])
      AllDisjoint([g, f])
      AllDisjoint([e, f, g])
      
    s = set(frozenset(d.entities) for d in c.differents())
    assert s == { frozenset([c, d]), frozenset([c, e, f]) }
    
  def test_disjoint_7(self):
    n = self.new_ontology()
    with n:
      class C(Thing): pass
      class D(Thing): pass
      class E(Thing): pass
      class F(Thing): pass
      AllDisjoint([C, D])
      AllDisjoint([C, E, F])
      
      class P1(ObjectProperty): pass
      class P2(ObjectProperty): pass
      class P3(ObjectProperty): pass
      class P4(ObjectProperty): pass
      AllDisjoint([P1, P2])
      AllDisjoint([P1, P3, P4])
      
      class O(Thing): pass
      c = O()
      d = O()
      e = O()
      f = O()
      AllDisjoint([c, d])
      AllDisjoint([c, e, f])
      
    s = set(frozenset(d.entities) for d in n.disjoint_classes())
    assert s == { frozenset([C, D]), frozenset([C, E, F]) }
    
    s = set(frozenset(d.entities) for d in n.disjoint_properties())
    assert s == { frozenset([P1, P2]), frozenset([P1, P3, P4]) }
    
    s = set(frozenset(d.entities) for d in n.different_individuals())
    assert s == { frozenset([c, d]), frozenset([c, e, f]) }
    
    s = set(frozenset(d.entities) for d in n.disjoints())
    assert s == { frozenset([C, D]),   frozenset([C, E, F]),
                  frozenset([P1, P2]), frozenset([P1, P3, P4]),
                  frozenset([c, d]),   frozenset([c, e, f]) }
    
  def test_disjoint_7(self):
    n = self.new_ontology()
    with n:
      class C(Thing): pass
      class D(Thing): pass
      class E(Thing): pass
      class F(Thing): pass
      class p(Thing >> Thing): pass
      
      AllDisjoint([C, D & E])
      AllDisjoint([C, D | E, p.some(F)])
      
  def test_annotation_1(self):
    n = get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test")
    
    assert issubclass(n.annot, AnnotationProperty)
    assert isinstance(n.annot, AnnotationPropertyClass)
    assert n.ma_pizza.annot == ["Test annot"]
    assert set(n.ma_pizza.comment) == { locstr("Commentaire", "fr"), locstr("Comment", "en") }
    assert n.Pizza.comment == [locstr("Comment on Pizza", "en")]
    
  def test_annotation_2(self):
    n = get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test")

    assert set(comment[n.ma_pizza, rdf_type, n.Pizza]) == { locstr('Comment on a triple', 'en'), locstr('Commentaire sur un triplet', 'fr') }
    assert comment[n.ma_pizza, rdf_type, n.Pizza].fr == ["Commentaire sur un triplet"]

    assert set(AnnotatedRelation(n.ma_pizza, rdf_type, n.Pizza).comment) == { locstr('Comment on a triple', 'en'), locstr('Commentaire sur un triplet', 'fr') }
    assert AnnotatedRelation(n.ma_pizza, rdf_type, n.Pizza).comment.fr == ["Commentaire sur un triplet"]
    
  def test_annotation_3(self):
    n = self.new_ontology()
    with n:
      class C1(Thing): pass
      class C2(Thing): pass
      class prop(ObjectProperty): pass
      class annot(AnnotationProperty): pass
      class annot2(AnnotationProperty): pass
      
    c1 = C1()
    c2 = C2()
    c1.prop.append(c2)
    assert annot[c1, prop, c2] == []
    
    annot[c1, prop, c2].append("Test")
    
    annots = None
    for bnode, p, o in n._get_obj_triples_spo_spo(None, rdf_type, owl_axiom):
      if ((n._get_obj_triple_sp_o(bnode, owl_annotatedsource  ) == c1.storid) and
          (n._get_obj_triple_sp_o(bnode, owl_annotatedproperty) == prop.storid) and
          (n._get_obj_triple_sp_o(bnode, owl_annotatedtarget  ) == c2.storid)):
        annots = { (p, n._to_python(o,d)) for s,p,o,d in n._get_triples_spod_spod(bnode, None, None, None) if not p in [rdf_type, owl_annotatedsource, owl_annotatedproperty, owl_annotatedtarget] }
        break
    assert annots == { (annot.storid, "Test") }
      
    annot[c1, prop, c2].append("Test1")
    annots = None
    for bnode, p, o in n._get_obj_triples_spo_spo(None, rdf_type, owl_axiom):
      if ((n._get_obj_triple_sp_o(bnode, owl_annotatedsource  ) == c1.storid) and
          (n._get_obj_triple_sp_o(bnode, owl_annotatedproperty) == prop.storid) and
          (n._get_obj_triple_sp_o(bnode, owl_annotatedtarget  ) == c2.storid)):
        annots = { (p, n._to_python(o,d)) for s,p,o,d in n._get_triples_spod_spod(bnode, None, None) if not p in [rdf_type, owl_annotatedsource, owl_annotatedproperty, owl_annotatedtarget] }
        break
    assert annots == { (annot.storid, "Test"), (annot.storid, "Test1") }
    
    annot2[c1, prop, c2].append("Test2")
    
    annots = None
    for bnode, p, o in n._get_obj_triples_spo_spo(None, rdf_type, owl_axiom):
      if ((n._get_obj_triple_sp_o(bnode, owl_annotatedsource  ) == c1.storid) and
          (n._get_obj_triple_sp_o(bnode, owl_annotatedproperty) == prop.storid) and
          (n._get_obj_triple_sp_o(bnode, owl_annotatedtarget  ) == c2.storid)):
        annots = { (p, n._to_python(o,d)) for s,p,o,d in n._get_triples_spod_spod(bnode, None, None) if not p in [rdf_type, owl_annotatedsource, owl_annotatedproperty, owl_annotatedtarget] }
        break
      
    assert annots == { (annot.storid, "Test"), (annot.storid, "Test1"), (annot2.storid, "Test2") }
    
    annot[c1, prop, c2].remove("Test")
    annots = None
    for bnode, p, o in n._get_obj_triples_spo_spo(None, rdf_type, owl_axiom):
      if ((n._get_obj_triple_sp_o(bnode, owl_annotatedsource  ) == c1.storid) and
          (n._get_obj_triple_sp_o(bnode, owl_annotatedproperty) == prop.storid) and
          (n._get_obj_triple_sp_o(bnode, owl_annotatedtarget  ) == c2.storid)):
        annots = { (p, n._to_python(o,d)) for s,p,o,d in n._get_triples_spod_spod(bnode, None, None) if not p in [rdf_type, owl_annotatedsource, owl_annotatedproperty, owl_annotatedtarget] }
        break
      
    assert annots == { (annot.storid, "Test1"), (annot2.storid, "Test2") }
    
  def test_annotation_4(self):
    n = self.new_ontology()
    with n:
      class C1(Thing): pass
      class C2(Thing): pass
      class prop(ObjectProperty): pass
      class annot(AnnotationProperty): pass
      
    c1 = C1()
    c2 = C2()
    c1.prop.append(c2)
    
    annot[c1, prop, c2].append(locstr("Un test", "fr"))
    annot[c1, prop, c2].append(locstr("A test", "en"))
    annots = None
    for bnode, p, o in n._get_obj_triples_spo_spo(None, rdf_type, owl_axiom):
      if ((n._get_obj_triple_sp_o(bnode, owl_annotatedsource  ) == c1.storid) and
          (n._get_obj_triple_sp_o(bnode, owl_annotatedproperty) == prop.storid) and
          (n._get_obj_triple_sp_o(bnode, owl_annotatedtarget  ) == c2.storid)):
        annots = { (p, n._to_python(o,d)) for s,p,o,d in n._get_triples_spod_spod(bnode, None, None, None) if not p in [rdf_type, owl_annotatedsource, owl_annotatedproperty, owl_annotatedtarget] }
        break
    assert annots == { (annot.storid, locstr("Un test", "fr")), (annot.storid, locstr("A test", "en")) }
    
    assert set(annot[c1, prop, c2])  == { locstr("Un test", "fr"), locstr("A test", "en") }
    assert annot[c1, prop, c2].fr == ["Un test"]
    assert annot[c1, prop, c2].en == ["A test"]
    
    annot[c1, prop, c2].fr.append("Un second test")
    annots = None
    for bnode, p, o in n._get_obj_triples_spo_spo(None, rdf_type, owl_axiom):
      if ((n._get_obj_triple_sp_o(bnode, owl_annotatedsource  ) == c1.storid) and
          (n._get_obj_triple_sp_o(bnode, owl_annotatedproperty) == prop.storid) and
          (n._get_obj_triple_sp_o(bnode, owl_annotatedtarget  ) == c2.storid)):
        annots = { (p, n._to_python(o,d)) for s,p,o,d in n._get_triples_spod_spod(bnode, None, None, None) if not p in [rdf_type, owl_annotatedsource, owl_annotatedproperty, owl_annotatedtarget] }
        break
    assert annots == { (annot.storid, locstr("Un test", "fr")), (annot.storid, locstr("Un second test", "fr")), (annot.storid, locstr("A test", "en")) }

    annot[c1, prop, c2].fr.remove("Un test")
    annots = None
    for bnode, p, o in n._get_obj_triples_spo_spo(None, rdf_type, owl_axiom):
      if ((n._get_obj_triple_sp_o(bnode, owl_annotatedsource  ) == c1.storid) and
          (n._get_obj_triple_sp_o(bnode, owl_annotatedproperty) == prop.storid) and
          (n._get_obj_triple_sp_o(bnode, owl_annotatedtarget  ) == c2.storid)):
        annots = { (p, n._to_python(o,d)) for s,p,o,d in n._get_triples_spod_spod(bnode, None, None, None) if not p in [rdf_type, owl_annotatedsource, owl_annotatedproperty, owl_annotatedtarget] }
        break
    assert annots == { (annot.storid, locstr("Un second test", "fr")), (annot.storid, locstr("A test", "en")) }
    
    annot[c1, prop, c2].fr = "Un test 2"
    annots = None
    for bnode, p, o in n._get_obj_triples_spo_spo(None, rdf_type, owl_axiom):
      if ((n._get_obj_triple_sp_o(bnode, owl_annotatedsource  ) == c1.storid) and
          (n._get_obj_triple_sp_o(bnode, owl_annotatedproperty) == prop.storid) and
          (n._get_obj_triple_sp_o(bnode, owl_annotatedtarget  ) == c2.storid)):
        annots = { (p, n._to_python(o,d)) for s,p,o,d in n._get_triples_spod_spod(bnode, None, None, None) if not p in [rdf_type, owl_annotatedsource, owl_annotatedproperty, owl_annotatedtarget] }
        break
    assert annots == { (annot.storid, locstr("Un test 2", "fr")), (annot.storid, locstr("A test", "en")) }
    
    annot[c1, prop, c2].fr = ["Un test 3", "Un test 4"]
    annots = None
    for bnode, p, o in n._get_obj_triples_spo_spo(None, rdf_type, owl_axiom):
      if ((n._get_obj_triple_sp_o(bnode, owl_annotatedsource  ) == c1.storid) and
          (n._get_obj_triple_sp_o(bnode, owl_annotatedproperty) == prop.storid) and
          (n._get_obj_triple_sp_o(bnode, owl_annotatedtarget  ) == c2.storid)):
        annots = { (p, n._to_python(o,d)) for s,p,o,d in n._get_triples_spod_spod(bnode, None, None, None) if not p in [rdf_type, owl_annotatedsource, owl_annotatedproperty, owl_annotatedtarget] }
        break
    assert annots == { (annot.storid, locstr("Un test 3", "fr")), (annot.storid, locstr("Un test 4", "fr")), (annot.storid, locstr("A test", "en")) }
    
  def test_annotation_5(self):
    n = self.new_ontology()
    with n:
      class C1(Thing): pass
      class C2(Thing): pass
      class prop(ObjectProperty): pass
      class annot(AnnotationProperty): pass
      
    c1 = C1()
    c2 = C2()
    c1.prop.append(c2)
    
    annot[c1, prop, c2].append(locstr("Un test", "fr"))
    annot[c1, prop, c2].append(locstr("A test", "en"))
    
    annot[c1, prop, c2] = ["Test"]
    annots = None
    for bnode, p, o in n._get_obj_triples_spo_spo(None, rdf_type, owl_axiom):
      if ((n._get_obj_triple_sp_o(bnode, owl_annotatedsource  ) == c1.storid) and
          (n._get_obj_triple_sp_o(bnode, owl_annotatedproperty) == prop.storid) and
          (n._get_obj_triple_sp_o(bnode, owl_annotatedtarget  ) == c2.storid)):
        annots = { (p, n._to_python(o,d)) for s,p,o,d in n._get_triples_spod_spod(bnode, None, None, None) if not p in [rdf_type, owl_annotatedsource, owl_annotatedproperty, owl_annotatedtarget] }
        break
    assert annots == { (annot.storid, "Test") }
    
    annot[c1, prop, c2] = []
    annots = None
    for bnode, p, o in n._get_obj_triples_spo_spo(None, rdf_type, owl_axiom):
      if ((n._get_obj_triple_sp_o(bnode, owl_annotatedsource  ) == c1.storid) and
          (n._get_obj_triple_sp_o(bnode, owl_annotatedproperty) == prop.storid) and
          (n._get_obj_triple_sp_o(bnode, owl_annotatedtarget  ) == c2.storid)):
        annots = { (p, n._to_python(o,d)) for s,p,o,d in n._get_triples_spod_spod(bnode, None, None, None) if not p in [rdf_type, owl_annotatedsource, owl_annotatedproperty, owl_annotatedtarget] }
        break
    assert annots is None
    
  def test_annotation_6(self):
    n = self.new_ontology()
    with n:
      class C1(Thing): pass
      class C2(Thing): pass
      class prop(ObjectProperty): pass
      class annot(AnnotationProperty): pass
      
    c1 = C1()
    c2 = C2()
    c1.prop.append(c2)
    
    annot[c1, prop, c2].en.append("A test")
    annot[c1, prop, c2].fr = "Un test"
    annots = None
    for bnode, p, o in n._get_obj_triples_spo_spo(None, rdf_type, owl_axiom):
      if ((n._get_obj_triple_sp_o(bnode, owl_annotatedsource  ) == c1.storid) and
          (n._get_obj_triple_sp_o(bnode, owl_annotatedproperty) == prop.storid) and
          (n._get_obj_triple_sp_o(bnode, owl_annotatedtarget  ) == c2.storid)):
        annots = { (p, n._to_python(o,d)) for s,p,o,d in n._get_triples_spod_spod(bnode, None, None) if not p in [rdf_type, owl_annotatedsource, owl_annotatedproperty, owl_annotatedtarget] }
        break
    assert annots == { (annot.storid, locstr("Un test", "fr")), (annot.storid, locstr("A test", "en")) }
    
  def test_annotation_7(self):
    n = self.new_ontology()
    with n:
      class prop(ObjectProperty): pass
      
    assert prop.comment == []
    assert prop.comment.fr == []
    
    prop.comment.append(locstr("ENGLISH", "en"))
    prop.comment
    prop.comment.fr.append("FRENCH")
    
    values = set()
    for s,p,o,d in n._get_triples_spod_spod(prop.storid, comment.storid, None, None): values.add((o,d))
    assert values == { to_literal(locstr("ENGLISH", "en")), to_literal(locstr("FRENCH", "fr")) }
    
  def test_annotation_8(self):
    n = self.new_ontology()
    with n:
      class C(Thing): pass
      class annot(AnnotationProperty): pass
      
    C.annot.fr = "FRENCH"
    C.annot.en = "ENGLISH"
    
    values = set()
    for s,p,o,d in n._get_triples_spod_spod(C.storid, annot.storid, None, None): values.add((o,d))
    assert values == { to_literal(locstr("ENGLISH", "en")), to_literal(locstr("FRENCH", "fr")) }
    
  def test_annotation_9(self):
    n = self.new_ontology()
    with n:
      class C1(Thing): pass
      class C2(C1): pass
      class annot(AnnotationProperty): pass
      
    C1.annot.fr = "FRENCH"
    C1.annot.en = "ENGLISH"
    
    assert C2.annot == []
    assert C1().annot == []
    assert C2().annot == []
    
  def test_annotation_10(self):
    n = self.new_ontology()
    with n:
      class P1(ObjectProperty): pass
      class P2(P1): pass
      class annot(AnnotationProperty): pass
      
    P1.annot.fr = "FRENCH"
    P1.annot.en = "ENGLISH"
    
    assert P2.annot == []
    
  def test_annotation_11(self):
    n = self.new_ontology()
    with n:
      class P1(ObjectProperty): pass
      class P2(DataProperty): pass
      class P3(AnnotationProperty): pass
      class C (Thing): pass
      i = C()
    P1.comment = "annot1"
    P2.comment = "annot2"
    P3.comment = "annot3"
    C .comment = "annot4"
    i .comment = "annot5"
    
    assert P1.comment == ["annot1"]
    assert P2.comment == ["annot2"]
    assert P3.comment == ["annot3"]
    assert C .comment == ["annot4"]
    assert i .comment == ["annot5"]
    
    P1.comment = None
    P2.comment = None
    P3.comment = None
    C .comment = None
    i .comment = None
    
    assert P1.comment == []
    assert P2.comment == []
    assert P3.comment == []
    assert C .comment == []
    assert i .comment == []
    
  def test_annotation_12(self):
    n = get_ontology("http://www.test.org/test_annot_literal.owl").load()
    
    assert set(n.C.classDescription) == { locstr("Annotation value"), 8, locstr("Annotation with lang", "en") }
    
  def test_annotation_13(self):
    n = self.new_ontology()
    with n:
      class C(Thing): pass
      C.comment.append(8)
      C.comment.append("eee")
      C.comment.append(locstr("plain literal"))
      C.comment.append(locstr("literal with lang", "en"))
      
    self.assert_triple(C.storid, comment.storid, 8, n._abbreviate("http://www.w3.org/2001/XMLSchema#integer"))
    self.assert_triple(C.storid, comment.storid, "eee", n._abbreviate("http://www.w3.org/2001/XMLSchema#string"))
    self.assert_triple(C.storid, comment.storid, "plain literal", n._abbreviate("http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral"))
    self.assert_triple(C.storid, comment.storid, "literal with lang", "@en")
    
  def test_annotation_14(self):
    onto = self.new_ontology()
    with onto:
      class C(Thing): pass
      class p(C >> int): pass
      c = C(p = [1, 2])
      comment[c, p, 1] = ["Commentaire"]
      
    assert comment[c, p, 1] == ["Commentaire"]
    assert comment[c, p, 2] == []

    C.is_a.append(p.only(OneOf([1, 2, 3])))
    
  def test_annotation_15(self):
    world = self.new_world()
    onto = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2018/10/test_datatype_one_of.owl").load()
    
    assert comment[onto.d1, onto.p, 1] == ["Annotation on a triple with a datatype value."]
    assert onto.d1.p == [1]
    assert onto.D.is_a[1].value.instances == [1, 2, 3]
    
  def test_annotation_16(self):
    world = self.new_world()
    onto = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2018/10/test_datatype_one_of_owlxml.owl").load()

    assert onto.d1.p == [1]
    assert comment[onto.d1, onto.p, 1] == [locstr("Annotation on a triple with a datatype value.")]
    assert onto.D.is_a[1].value.instances == [1, 2, 3]
    
  def test_annotation_17(self):
    w = self.new_world()
    o = w.get_ontology("http://test.org/onto.owl")

    with o:
      class C1(Thing): pass
      class C2(C1): pass
      class label2(label): pass

    assert isinstance(Thing.storid, int)
    assert isinstance(Property.storid, int)
    assert isinstance(ObjectProperty.storid, int)
    assert isinstance(DataProperty.storid, int)
    assert isinstance(AnnotationProperty.storid, int)
    assert set(label2.ancestors()) == set([Property, AnnotationProperty, label, label2])
    
    C1.label  = ["label A",  "label B" ]
    C1.label2 = ["label2 A", "label2 B"]
    
    assert set(C1.label ) == set(["label A",  "label B" ])
    assert set(C1.label2) == set(["label2 A", "label2 B"])
    
    assert set(C1.INDIRECT_label ) == set(["label A",  "label B", "label2 A", "label2 B"])
    assert set(C1.INDIRECT_label2) == set(["label2 A", "label2 B"])
    assert set(C2.label ) == set()
    assert set(C2.label2) == set()
    assert set(C2.INDIRECT_label ) == set()
    assert set(C2.INDIRECT_label2) == set()

    c = C1()
    c.label  = ["l A",  "l B" ]
    c.label2 = ["l2 A", "l2 B"]
    assert set(c.label ) == set(["l A",  "l B" ])
    assert set(c.label2) == set(["l2 A", "l2 B"])
    assert set(c.INDIRECT_label ) == set(["l A",  "l B", "l2 A", "l2 B"])
    assert set(c.INDIRECT_label2) == set(["l2 A", "l2 B"])
    
  def test_annotation_18(self):
    w = self.new_world()
    o = w.get_ontology("http://test.org/onto.owl")

    with o:
      class p(ObjectProperty): pass
      class C(Thing):
        is_a = [p.some(Thing)]
        
      comment[C.is_a[-1]].append("A comment on a restriction.")

    assert comment[C.is_a[-1]] == ["A comment on a restriction."]
    
  def test_annotation_19_0(self):
    w = self.new_world()
    o = w.get_ontology("http://test.org/onto.owl")
    
    with o:
      class p(Thing >> Thing): pass
      class C(Thing): pass
      
      c1 = C()
      c2 = C()
      c1.p.append(c2)
      comment[c1, p, c2].append("commentaire")
      comment[c1, p, c2].append("commentaire 2")
      
      a = AnnotatedRelation(AnnotatedRelation(c1, p, c2), comment, "commentaire")
      a.comment.append("commentaire d'un commentaire")
      
      b = comment[a, comment, "commentaire d'un commentaire"]
      b.append("commentaire d'un commentaire d'un commentaire")

      assert comment[a, comment, "commentaire d'un commentaire"] == comment[a.comment, comment, "commentaire d'un commentaire"]
      
      self.assert_triple(-3, comment.storid, *o._to_rdf("commentaire d'un commentaire d'un commentaire"), world = w)
      
  def test_annotation_19(self):
    w = self.new_world()
    o = w.get_ontology("http://test.org/onto.owl")
    
    with o:
      class C(Thing): pass
      class p(AnnotationProperty): pass
      class i(C >> int): pass
      c1 = C()
      c1.i = [1]
      p[c1, i, 1] = [locstr("Test", "en")]
      p[c1, i, 1].append(locstr("Test", "fr"))
      assert set(p[c1, i, 1]) == { locstr("Test", "en"), locstr("Test", "fr") }
      p[c1, i, 1].remove(locstr("Test", "en"))
      assert p[c1, i, 1] == [locstr("Test", "fr")]
  
  def test_annotation_20(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/onto.owl")
    with onto:
      class C(Thing): pass
      class D(C): pass
      c1 = C()
      
    C.comment = ["C"]
    assert C.comment == ["C"]
    assert D.comment == []
    assert c1.comment == []
    
    D.comment = ["D"]
    assert C.comment == ["C"]
    assert D.comment == ["D"]
    assert c1.comment == []
    
    c1.comment = ["c1"]
    assert C.comment == ["C"]
    assert D.comment == ["D"]
    assert c1.comment == ["c1"]
    
  def test_annotation_21(self):
    world = self.new_world()
    onto1 = world.get_ontology("http://test.org/onto1.owl")
    onto2 = world.get_ontology("http://test.org/onto2.owl")
    with onto1:
      class C(Thing): pass
      class p(C >> int): pass
      c1 = C(p = [1])
      comment[c1, p, 1].append("com1")
      
    with onto2:
      comment[c1, p, 1].append("com2")
      
    assert set(comment[c1, p, 1]) == { "com1", "com2" }
    assert set(AnnotatedRelation(c1, p, 1)._bnodes) == { -1, -2 }
    
  def test_annotation_22(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/onto.owl")
    with onto:
      class C(Thing): pass
      C.label = ["C label"]
      AnnotatedRelation(C, label, "C label").comment = ["Provisoire"]
      AnnotatedRelation(AnnotatedRelation(C, label, "C label"), comment, "Provisoire").comment = ["1/1/2023"]
      
    assert AnnotatedRelation(AnnotatedRelation(C, label, "C label"), comment, "Provisoire").comment == ["1/1/2023"]
    
    self.assert_triple(-2, owl_annotatedsource, -1, world = world)
    self.assert_triple(-2, owl_annotatedproperty, comment.storid, world = world)
    
    
  def test_import_1(self):
    n = get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/2/test_mixed.owl").load()
    
    assert n.Parent in n.Child.is_a
    assert n.Parent in n.Child.__bases__
    
    assert n.Parent().test() == "ok1"
    assert n.Child ().test() == "ok2"
    
    o = n.Parent()
    o.is_a.append(n.Child)
    assert o.test() == "ok2"
    
    assert n.Parent().test_inherited() == "ok"
    assert n.Child ().test_inherited() == "ok"
    
    
  def test_close_1(self):
    w = self.new_world()
    n = w.get_ontology("http://test.org/test.owl")
    class O(Thing): namespace = n
    class P(Thing): namespace = n
    class has_for_p(ObjectProperty):
      namespace = n
      domain    = [O]
      range     = [P]
    o  = O()
    p1 = P()
    p2 = P()
    o.has_for_p = [p1, p2]
    
    close_world(o)
    
    restr = [c for c in o.is_a if not c is O][0]
    assert restr.property is has_for_p
    assert restr.type == ONLY
    assert isinstance(restr.value, OneOf) and set(restr.value.instances) == {p1, p2}
    
  def test_close_2(self):
    w = self.new_world()
    n = w.get_ontology("http://test.org/test.owl")
    class O(Thing): namespace = n
    class P(Thing): namespace = n
    class has_for_p(ObjectProperty):
      namespace = n
      domain    = [O]
      range     = [P]
    o  = O()
    p1 = P()
    p2 = P()
    o.is_a.append(has_for_p.some(P))
    close_world(o)
    
    assert o.is_a[-1].property is has_for_p
    assert o.is_a[-1].type == ONLY
    assert o.is_a[-1].value is P
    
  def test_close_3(self):
    w = self.new_world()
    n = w.get_ontology("http://test.org/test.owl")
    class O(Thing): namespace = n
    class P(Thing): namespace = n
    class has_for_p(ObjectProperty):
      namespace = n
      domain    = [O]
      range     = [P]
    O.is_a.append(has_for_p.some(P))
    o = O()
    close_world(o)
    
    assert o.is_a[-1].property is has_for_p
    assert o.is_a[-1].type == ONLY
    assert o.is_a[-1].value is P
    
  def test_close_4(self):
    w = self.new_world()
    n = w.get_ontology("http://test.org/test.owl")
    class O(Thing): namespace = n
    class P(Thing): namespace = n
    class has_for_p(ObjectProperty):
      namespace = n
      domain    = [O]
      range     = [P]
    o1 = O()
    o2 = O()
    close_world(O)
    
    restr = [c for c in O.is_a if isinstance(c, OneOf)][0]
    assert set(restr.instances) == { o1, o2 }
    restr = [c for c in O.is_a if isinstance(c, Restriction)][0]
    assert restr.property is has_for_p
    assert restr.type == ONLY
    assert restr.value is Nothing
    
  def test_close_5(self):
    w = self.new_world()
    n = w.get_ontology("http://test.org/test.owl")
    class O(Thing): namespace = n
    class P(Thing): namespace = n
    class Q(Thing): namespace = n
    class rel(ObjectProperty):
      namespace = n
      domain    = [O]
    p1 = P()
    p2 = P()
    q1 = Q()
    O.is_a.append(rel.value(p1))
    O.is_a.append(rel.value(p2))
    O.is_a.append(rel.some(Q))
    close_world(O)
    
    restr = O.is_a[-1]
    assert restr.property is rel
    assert restr.type == ONLY
    assert Q in restr.value.Classes
    x = list(restr.value.Classes)
    x.remove(Q)
    x = x[0]
    assert isinstance(x, OneOf) and (set(x.instances) == { p1, p2 })

  def test_close_6(self):
    w = self.new_world()
    n = w.get_ontology("http://test.org/test.owl")
    class O(Thing): namespace = n
    class O2(O):    namespace = n
    class P(Thing): namespace = n
    class has_for_p(ObjectProperty):
      namespace = n
      domain    = [O]
      range     = [P]
    O.is_a.append(has_for_p.some(P))
    close_world(O2)
    
    assert O2.is_a[-1].property is has_for_p
    assert O2.is_a[-1].type == ONLY
    assert O2.is_a[-1].value is P
    
  def test_close_7(self):
    w = self.new_world()
    n = w.get_ontology("http://test.org/test.owl")
    class O(Thing): namespace = n
    class O2(O):    namespace = n
    class P(Thing): namespace = n
    class has_for_p(ObjectProperty):
      namespace = n
      domain    = [O]
      range     = [P]
    o = O()
    p = P()
    O2.is_a.append(has_for_p.some(P))
    o .has_for_p = [p]
    close_world(O)
    
    assert repr(O.is_a) == repr([Thing, OneOf([o]), has_for_p.only((P | OneOf([p])))])

    
  def test_class_prop_1(self):
    onto = self.new_ontology()
    with onto:
      class O(Thing): pass
      class rel(DataProperty):
        domain   = [O]
        range    = [str]
    O.is_a.append(rel.value("test"))
    assert O.rel == ["test"]
    
    bnode = O.is_a[-1].storid
    self.assert_triple(O.storid, rdfs_subclassof, bnode)
    self.assert_triple(bnode, rdf_type, owl_restriction)
    self.assert_triple(bnode, owl_onproperty, rel.storid)
    self.assert_triple(bnode, VALUE, *to_literal("test"))
    
  def test_class_prop_2(self):
    onto = self.new_ontology()
    with onto:
      class O(Thing): pass
      class rel(DataProperty, FunctionalProperty):
        domain   = [O]
        range    = [str]
    O.is_a.append(rel.value("test"))
    assert O.rel == "test"
    
    bnode = O.is_a[-1].storid
    self.assert_triple(O.storid, rdfs_subclassof, bnode)
    self.assert_triple(bnode, rdf_type, owl_restriction)
    self.assert_triple(bnode, owl_onproperty, rel.storid)
    self.assert_triple(bnode, VALUE, *to_literal("test"))
    
  def test_class_prop_3(self):
    onto = self.new_ontology()
    with onto:
      class O(Thing): pass
      class rel(DataProperty, FunctionalProperty):
        domain   = [O]
        range    = [str]
    O.rel = "test"
    
    assert O.is_a[-1].property is rel
    assert O.is_a[-1].type == VALUE
    assert O.is_a[-1].value == "test"

    bnode = O.is_a[-1].storid
    self.assert_triple(O.storid, rdfs_subclassof, bnode)
    self.assert_triple(bnode, rdf_type, owl_restriction)
    self.assert_triple(bnode, owl_onproperty, rel.storid)
    self.assert_triple(bnode, VALUE, *to_literal("test"))
    
    O.rel = None
    assert O.is_a == [Thing]

    self.assert_not_triple(O.storid, rdfs_subclassof, bnode)
    self.assert_not_triple(bnode, rdf_type, owl_restriction)
    self.assert_not_triple(bnode, owl_onproperty, rel.storid)
    self.assert_not_triple(bnode, VALUE, *to_literal("test"))
    
  def test_class_prop_4(self):
    onto = self.new_ontology()
    with onto:
      class O(Thing): pass
      class rel(DataProperty):
        domain   = [O]
        range    = [str]
        
    O.rel = ["a", "b"]
    
    assert len(O.is_a) == 3
    assert O.is_a[-2].property is rel
    assert O.is_a[-2].type == VALUE
    assert O.is_a[-1].property is rel
    assert O.is_a[-1].type == VALUE
    assert { O.is_a[-2].value, O.is_a[-1].value } == { "a", "b" }
    
    O.rel = ["a", "c"]
    
    assert len(O.is_a) == 3
    assert O.is_a[-2].property is rel
    assert O.is_a[-2].type == VALUE
    assert O.is_a[-1].property is rel
    assert O.is_a[-1].type == VALUE
    assert { O.is_a[-2].value, O.is_a[-1].value } == { "a", "c" }
    
  def test_class_prop_5(self):
    onto = self.new_ontology()
    with onto:
      class O(Thing): pass
      class rel(DataProperty):
        domain   = [O]
        range    = [str]
        
    O.rel.append("a")
    O.rel.append("b")
    O.rel.append("c")
    O.rel.remove("b")

    assert len(O.is_a) == 3
    assert O.is_a[-2].property is rel
    assert O.is_a[-2].type == VALUE
    assert O.is_a[-1].property is rel
    assert O.is_a[-1].type == VALUE
    assert { O.is_a[-2].value, O.is_a[-1].value } == { "a", "c" }
    
  def test_class_prop_6(self):
    onto = self.new_ontology()
    with onto:
      class O(Thing): pass
      class P(Thing): pass
      class rel(ObjectProperty, FunctionalProperty):
        domain   = [O]
        range    = [P]
      class inv(ObjectProperty, InverseFunctionalProperty):
        domain   = [P]
        range    = [O]
        inverse_property = rel
    p = P()
    O.rel = p
    
    assert O.is_a[-1].property is rel
    assert O.is_a[-1].type == VALUE
    assert O.is_a[-1].value == p
    
    assert len(p.is_a) == 2
    assert p.is_a[-1].property is inv
    assert p.is_a[-1].type == SOME
    assert p.is_a[-1].value is O
    
    
  def test_class_prop_7(self):
    onto = self.new_ontology()
    with onto:
      class O(Thing): pass
      class P(Thing): pass
      class rel(ObjectProperty):
        domain   = [O]
        range    = [P]
      class inv(ObjectProperty):
        domain   = [P]
        range    = [O]
        inverse_property = rel
    p = P()
    O.rel.append(p)
    
    assert O.is_a[-1].property is rel
    assert O.is_a[-1].type == VALUE
    assert O.is_a[-1].value == p

    assert len(p.is_a) == 2
    assert p.is_a[-1].property is inv
    assert p.is_a[-1].type == SOME
    assert p.is_a[-1].value is O
    
    O.rel.remove(p)
    assert len(O.is_a) == 1
    assert len(p.is_a) == 1
      
  def test_class_prop_8(self):
    n = self.new_ontology()
    with n:
      class p(Thing >> int): pass
      class C(Thing):
        p = [1, 2]
    assert len(C.is_a) == 3
    assert C.is_a[-1].property is p
    assert C.is_a[-1].type == VALUE
    assert C.is_a[-2].property is p
    assert C.is_a[-2].type == VALUE
    assert { C.is_a[-1].value, C.is_a[-2].value } == { 1, 2 }
    
  def test_class_prop_9(self):
    n = self.new_ontology()
    with n:
      class p(Thing >> Thing): pass
      class D(Thing): pass
      d = D()
      class C(Thing):
        p = [d]
        
    assert len(C.is_a) == 2
    assert C.is_a[-1].property is p
    assert C.is_a[-1].type == VALUE
    assert C.is_a[-1].value is d
    
    assert len(d.is_a) == 2
    assert isinstance(d.is_a[-1].property, Inverse)
    assert d.is_a[-1].property.property is p
    assert d.is_a[-1].type == SOME
    assert d.is_a[-1].value is C
    
    C.p = []
    assert len(C.is_a) == 1
    assert len(d.is_a) == 1
    
  def test_class_prop_10(self):
    onto = self.new_ontology()
    with onto:
      class D(Thing): pass
      class R(Thing): pass
      class rel(ObjectProperty):
        domain   = [D]
        range    = [R]
    D.is_a.append(rel.some(R))
    
    assert D.rel == [R]
    
    D.rel.remove(R)
    
    assert D.rel == []
    
    assert D.is_a == [Thing]
    
  def test_class_prop_11(self):
    onto = self.new_ontology()
    with onto:
      class D(Thing): pass
      class R(Thing): pass
      class rel(ObjectProperty):
        domain   = [D]
        range    = [R]
    D.rel = [R]
    
    assert D.rel == [R]
    assert rel.some(R) in D.is_a
    
    bnode = D.is_a[-1].storid
    self.assert_triple(D.storid, rdfs_subclassof, bnode)
    self.assert_triple(bnode, rdf_type, owl_restriction)
    self.assert_triple(bnode, owl_onproperty, rel.storid)
    self.assert_triple(bnode, SOME, R.storid)

    del D.is_a[-1]

    assert D.rel == []
    
  def test_class_prop_12(self):
    onto = self.new_ontology()
    with onto:
      class p1(ObjectProperty): pass
      class p2(ObjectProperty):
        class_property_type = ["only"]
        
    assert p1.class_property_type == []
    assert p1._class_property_only == False
    assert p1._class_property_some == True
    
    assert p2.class_property_type == ["only"]
    assert p2._class_property_only == True
    assert p2._class_property_some == False
    
    self.assert_triple(p2.storid, owlready_class_property_type, "only", 0)
    
    p1.class_property_type.append("only")
    assert p1._class_property_only == True
    assert p1._class_property_some == False
    self.assert_triple(p1.storid, owlready_class_property_type, "only", 0)
    
    p1.class_property_type.append("some")
    assert p1._class_property_only == True
    assert p1._class_property_some == True
    self.assert_triple(p1.storid, owlready_class_property_type, "some", 0)
    
  def test_class_prop_13(self):
    onto = self.new_ontology()
    with onto:
      class p(ObjectProperty): class_property_type = ["only"]
      class C1(Thing): pass
      class C2(Thing): pass
      c11 = C1()
      c12 = C1()
      class C3(Thing):
        is_a = [p.only(C1)]
      class C4(Thing):
        is_a = [p.only(Or([C1, C2]))]
      class C5(Thing):
        is_a = [p.only(Or([OneOf([c11, c12]), C2]))]
        
    assert set(C1.p) == set([])
    assert set(C2.p) == set([])
    assert set(C3.p) == set([C1])
    assert set(C4.p) == set([C1, C2])
    assert set(C5.p) == set([c11, c12, C2])
    
  def test_class_prop_14(self):
    onto = self.new_ontology()
    with onto:
      class p(ObjectProperty): class_property_type = ["only"]
      class d(DataProperty):   class_property_type = ["only"]
      class C1(Thing): pass
      class C2(Thing): pass
      c11 = C1()
      c12 = C1()
      class C3(Thing): pass
      
    C3.p = [C1]
    assert p.only(C1) in C3.is_a
    assert not p.some(C1) in C3.is_a
    
    C3.p.append(C2)
    assert p.only(Or([C1, C2])) in C3.is_a
    
    C3.p.append(c11)
    assert p.only(Or([C1, C2, OneOf([c11])])) in C3.is_a
    
    C3.p.append(c12)
    assert p.only(Or([C1, C2, OneOf([c11, c12])])) in C3.is_a
    
    C3.p.remove(C1)
    assert p.only(Or([C2, OneOf([c11, c12])])) in C3.is_a
    
    C3.p.remove(C2)
    assert p.only(OneOf([c11, c12])) in C3.is_a
    
    C3.p.remove(c11)
    assert p.only(OneOf([c12])) in C3.is_a
    
    C3.p.remove(c12)
    assert C3.is_a == [Thing]

    C3.d = ["abc", "def"]
    assert d.only(OneOf(["abc", "def"])) in C3.is_a
    
  def test_class_prop_15(self):
    onto = self.new_ontology()
    with onto:
      class p(ObjectProperty): class_property_type = ["some", "only"]
      class C1(Thing): pass
      class C2(Thing): pass
      c11 = C1()
      c12 = C1()
      class C3(Thing): pass
      
    C3.p = [C1]
    assert p.only(C1) in C3.is_a
    assert p.some(C1) in C3.is_a
    assert not p.some(C2) in C3.is_a
    assert not p.some(c11) in C3.is_a
    
    C3.p.append(C2)
    assert p.only(Or([C1, C2])) in C3.is_a
    assert p.some(C1) in C3.is_a
    assert p.some(C2) in C3.is_a
    
    C3.p.append(c11)
    C3.p.append(c12)
    assert p.only(Or([C1, C2, OneOf([c11, c12])])) in C3.is_a
    assert p.some(C1) in C3.is_a
    assert p.some(C2) in C3.is_a
    assert p.value(c11) in C3.is_a
    assert p.value(c12) in C3.is_a
    
    C3.p.remove(C1)
    C3.p.remove(c11)
    assert p.only(Or([C2, OneOf([c12])])) in C3.is_a
    assert not p.some(C1) in C3.is_a
    assert p.some(C2) in C3.is_a
    assert not p.value(c11) in C3.is_a
    assert p.value(c12) in C3.is_a
    
  def test_class_prop_16(self):
    onto = self.new_ontology()
    with onto:
      class p(ObjectProperty): class_property_type = ["relation"]
      class d(DataProperty):   class_property_type = ["relation"]
      class C1(Thing): pass
      class C2(Thing): pass
      c11 = C1()
      c12 = C1()
      class C3(Thing): pass
      
    assert C3.p == []

    C3.p = [C1, c11]
    
    self.assert_triple(C3.storid, p.storid, C1.storid)
    self.assert_triple(C3.storid, p.storid, c11.storid)
    self.assert_not_triple(C3.storid, p.storid, C2.storid)
    self.assert_not_triple(C3.storid, p.storid, c12.storid)
    
    C3.d = [1, 2]
    
    self.assert_triple(C3.storid, d.storid, 1, default_world._abbreviate("http://www.w3.org/2001/XMLSchema#integer"))
    self.assert_triple(C3.storid, d.storid, 2, default_world._abbreviate("http://www.w3.org/2001/XMLSchema#integer"))
    self.assert_not_triple(C3.storid, d.storid, 3, default_world._abbreviate("http://www.w3.org/2001/XMLSchema#integer"))
    
    C3.d.remove(2)
    C3.d.append(3)
    
    self.assert_triple(C3.storid, d.storid, 1, default_world._abbreviate("http://www.w3.org/2001/XMLSchema#integer"))
    self.assert_not_triple(C3.storid, d.storid, 2, default_world._abbreviate("http://www.w3.org/2001/XMLSchema#integer"))
    self.assert_triple(C3.storid, d.storid, 3, default_world._abbreviate("http://www.w3.org/2001/XMLSchema#integer"))
    
  def test_class_prop_17(self):
    onto = self.new_ontology()
    with onto:
      class p(ObjectProperty, FunctionalProperty): class_property_type = ["only"]
      class d(DataProperty, FunctionalProperty):   class_property_type = ["only"]
      class C1(Thing): pass
      class C2(Thing): pass
      c11 = C1()
      c12 = C1()
      class C3(Thing): pass
      
    C3.p = C1
    assert p.only(C1) in C3.is_a
    
    C3.p = C2
    assert p.only(C2) in C3.is_a
    assert not p.only(C1) in C3.is_a
    
    C3.p = c11
    assert p.only(OneOf([c11])) in C3.is_a
    assert not p.only(C1) in C3.is_a
    assert not p.only(C2) in C3.is_a
    
    C3.d = 1
    assert d.only(OneOf([1])) in C3.is_a
    assert not d.only(OneOf([2])) in C3.is_a
    
    C3.d = 2
    assert not d.only(OneOf([1])) in C3.is_a
    assert d.only(OneOf([2])) in C3.is_a
    
  def test_class_prop_18(self):
    onto = self.new_ontology()
    with onto:
      class p(ObjectProperty): class_property_type = ["only"]
      class d(DataProperty):   class_property_type = ["only"]
      class C1(Thing): pass
      class C2(Thing): pass
      class O(Thing): pass
      c11 = C1()
      c12 = C1()
      o1 = O()
      o2 = O()
      class C3(Thing): pass
      class C4(C3): pass
      class C5(C4): pass
      
    C3.p = [C1, C2, o1, o2]
    C4.p = [C1, o1, c12]
    
    assert C5.p == []
    assert set(C5.p.indirect()) == set([C1, o1, c12])
      
    C3.p = [C3, O]
    C4.p = [C4, o1, o2]
    
    assert C5.p == []
    assert set(C5.p.indirect()) == set([C4, o1, o2])
    
  def test_class_prop_19(self):
    onto = self.new_ontology()
    with onto:
      class p(ObjectProperty): class_property_type = ["some"]
      class q(ObjectProperty): class_property_type = ["only"]
      class d(DataProperty):   class_property_type = ["some"]
      class C1(Thing): pass
      class C2(Thing): pass
      class C3(Thing): pass
      class C4(C1):
        equivalent_to = [C1 & p.some(C2)]
      c11 = C1()

    assert C4.defined_class == False
    C4.defined_class = True
    assert C4.defined_class == True
    type.__delattr__(C4, "__defined_class")
    assert C4.defined_class == True

    C4.defined_class = False
    assert C4.defined_class == False
    type.__delattr__(C4, "__defined_class")
    
    assert C4.defined_class == False
    
    C4.defined_class = True
    
    assert C4.p == [C2]
    
    C4.p = [C2, C3]
    assert C4.equivalent_to == [C1 & p.some(C2) & p.some(C3)]
    
    C4.p.remove(C2)
    assert C4.equivalent_to == [C1 & p.some(C3)]
    
    C4.d.append(1)
    assert C4.equivalent_to == [C1 & p.some(C3) & d.value(1)]
    
    C4.d.append(2)
    assert C4.equivalent_to == [C1 & p.some(C3) & d.value(1) & d.value(2)]
    
    C4.q.append(C1)
    assert C4.equivalent_to == [C1 & p.some(C3) & d.value(1) & d.value(2) & q.only(C1)]
    
    C4.q.append(C2)
    assert C4.equivalent_to == [C1 & p.some(C3) & d.value(1) & d.value(2) & q.only(C1 | C2)]
    
    C4.q.append(c11)
    #print(C4.equivalent_to)
    assert C4.equivalent_to == [C1 & p.some(C3) & d.value(1) & d.value(2) & q.only(C1 | C2 | OneOf([c11]))]

  def test_class_prop_20(self):
    onto = self.new_ontology()
   
    with onto:
      class Drug(Thing): pass
      class ActivePrinciple(Thing): pass
      class has_for_active_principle(Drug >> ActivePrinciple): pass
      
      class HeathCondition(Thing): pass
      class Pain(HeathCondition): pass
      class ModeratePain(Pain): pass
      class CardiacDisorder(HeathCondition): pass
      class Hypertension(CardiacDisorder): pass
      
      class Pregnancy(HeathCondition): pass
      class Child(HeathCondition): pass
      class Bleeding(HeathCondition): pass
      
      class has_for_indications      (Drug >> HeathCondition): class_property_type = ["some"]
      class has_for_contraindications(Drug >> HeathCondition): class_property_type = ["only"]
  
      class Antalgic(Drug): 
        defined_class = True
        has_for_indications = [Pain]
        has_for_contraindications = [Pregnancy, Child, Bleeding]
        
      class Aspirin(Antalgic):
        defined_class = True
        has_for_indications = [ModeratePain]
        has_for_contraindications = [Pregnancy, Bleeding]

      class Antihypertensive(Drug):
        equivalent_to = [Drug
                         & has_for_indications.some(Hypertension)
                         &has_for_contraindications.only(Pregnancy)]
        
    assert Antalgic.equivalent_to == [Drug & has_for_indications.some(Pain) & has_for_contraindications.only(Pregnancy | Child | Bleeding)]
    assert Aspirin .equivalent_to == [Antalgic & has_for_indications.some(ModeratePain) & has_for_contraindications.only(Pregnancy | Bleeding)]

    assert Antihypertensive.has_for_indications       == [Hypertension]
    assert Antihypertensive.has_for_contraindications == [Pregnancy]

  def test_class_prop_21(self):
    onto = self.new_ontology()
    
    with onto:
      class C(Thing): pass
      class D(Thing): pass
      class E(Thing): pass
      class p(Thing >> Thing): pass
      class p2(p): pass

    C.p2 = [D, E]
    assert set(C.p2) == set([D, E])
    assert set(C.p) == set()
    assert set(C.INDIRECT_p) == set([D, E])
    assert isinstance(C.INDIRECT_p, list)

  def test_class_prop_22(self):
    onto = self.new_ontology()
    
    with onto:
      class C1(Thing): pass
      class C2(C1): pass
      class C3(C2): pass
      class E(Thing): pass
      class p(Thing >> Thing, FunctionalProperty): pass
      
    e = E()
    C1.p = E
    C2.p = e
    assert C1.p == E
    assert C2.p == e
    assert C3.p == None
    assert C1.INDIRECT_p == E
    assert C2.INDIRECT_p == e
    assert C3.INDIRECT_p == e

  def test_class_prop_23(self):
    onto = self.new_ontology()
    
    with onto:
      class C1(Thing): pass
      class C2(C1): pass
      class C3(C2): pass
      class E(Thing): pass
      class p(Thing >> Thing, FunctionalProperty): pass
      class p2(p): pass
      
    e = E()
    C1.p = E
    C2.p2 = e
    assert C1.p == E
    assert C2.p == None
    assert C3.p == None
    assert C1.INDIRECT_p == E
    assert C2.INDIRECT_p == e
    assert C3.INDIRECT_p == e
    assert C1.p2 == None
    assert C2.p2 == e
    assert C3.p2 == None
    assert C1.INDIRECT_p2 == None
    assert C2.INDIRECT_p2 == e
    assert C3.INDIRECT_p2 == e

    c = C1()
    assert c.p == None
    assert c.INDIRECT_p == E
    assert c.p2 == None
    assert c.INDIRECT_p2 == None

    c = C1(p = e)
    assert c.p == e
    assert c.INDIRECT_p == e
    assert c.p2 == None
    assert c.INDIRECT_p2 == None

    c = C1(p2 = e)
    assert c.p == None
    assert c.INDIRECT_p == e
    assert c.p2 == e
    assert c.INDIRECT_p2 == e

    c = C3()
    assert c.p == None
    assert c.INDIRECT_p == e
    assert c.p2 == None
    assert c.INDIRECT_p2 == e
    
  def test_class_prop_24(self):
    onto = self.new_ontology()
    
    with onto:
      class Form(Thing): pass
      class Round(Form): pass
      class Color(Thing): pass
      class Bactery(Thing): pass
      class has_form(Bactery >> Form): pass
      class has_color(Bactery >> Color): pass
      class Coque(Bactery):
        is_a = [has_color.some(Color)]
      class Staph(Coque):
        equivalent_to = [Coque & has_form.some(Round)]
        comment = ["Test"]
        
    staph = Staph()
    staph.label = "my staph"
    
    assert set(Staph.get_class_properties()) == set([comment, has_form])
    assert set(Staph.INDIRECT_get_class_properties()) == set([comment, has_form, has_color])
    assert set(staph.INDIRECT_get_properties()) == set([label, comment, has_form, has_color])
    assert Staph.has_form == [Round]
    assert Staph.has_color == []
    assert Staph.INDIRECT_has_form == [Round]
    assert Staph.INDIRECT_has_color == [Color]
    
  def test_class_prop_25(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/onto.owl#")
    
    with onto:
      class A(Thing): pass
      class B(Thing): pass
      class p(A >> B): class_property_type = ["only"]
      class B1(B): pass
      class B2(B): pass
      class B3(B): pass

      A.p.append(B1)
      A.p.append(B2)
      A.p.append(B3)

    assert len(A.p) == 3
    assert len(world.graph) == 28
      
    tmp = self.new_tmp_file()
    onto.save(tmp)
    
    world = self.new_world()
    onto  = world.get_ontology(tmp).load()

    assert len(onto.A.p) == 3
    
  def test_class_prop_26(self):
    w  = self.new_world()
    o1 = w.get_ontology("http://test.org/o1.owl")
    o2 = w.get_ontology("http://test.org/o2.owl")
    
    with o1:
      class A(Thing): pass
      class C(Thing): pass
      class p(Thing >> Thing): pass
      
      c1 = C()
      c2 = C()
      c3 = C()
      c4 = C()
      
      A.p = [c2, c3]
      
    with o2:
      A.p = [c2, c4]

    assert set(A.p) == { c2, c4 }
    
  def test_class_prop_27(self):
    w  = self.new_world()
    o1 = w.get_ontology("http://test.org/o1.owl")
    o2 = w.get_ontology("http://test.org/o2.owl")
    
    with o1:
      class A(Thing): pass
      class C(Thing): pass
      class p(Thing >> Thing): pass
      class i(Thing >> Thing): inverse = p
      
      c1 = C()
      c2 = C()
      c3 = C()
      c4 = C()
      
      A.p = [c2, c3]
      
    with o2:
      A.p = [c2, c4]

    assert set(A.p) == { c2, c4 }
    
  def test_class_prop_28(self):
    w  = self.new_world()
    o = w.get_ontology("http://test.org/o.owl")
    
    with o:
      class A(Thing): pass
      class C(Thing): pass
      class C2(C): pass
      class p(Thing >> Thing): pass
      class p2(Thing >> Thing): pass
      
      C .is_a.append(Inverse(p ).some(A))
      C2.is_a.append(Inverse(p2).some(A))

    assert C.         get_class_properties() == { Inverse(p) }
    assert C.INDIRECT_get_class_properties() == { Inverse(p) }
    
    assert C2.         get_class_properties() == { Inverse(p2) }
    assert C2.INDIRECT_get_class_properties() == { Inverse(p ), Inverse(p2) }
    
  def test_format_1(self):
    from owlready2.triplelite import _guess_format
    
    f = open(os.path.join(HERE, "test_owlxml.ntriples"), "r")
    assert _guess_format(f) == "ntriples"
    f.close()
    
    f = open(os.path.join(HERE, "test.owl"), "r")
    assert _guess_format(f) == "rdfxml"
    f.close()
    
    f = open(os.path.join(HERE, "test_owlxml.owl"), "r")
    assert _guess_format(f) == "owlxml"
    f.close()
    
  def test_format_2(self):
    import re, owlready2.owlxml_2_ntriples
    
    triples1 = ""
    def on_prepare_triple(s,p,o):
      nonlocal triples1
      if not s.startswith("_"): s = "<%s>" % s
      p = "<%s>" % p
      if not o.startswith("_"): o = "<%s>" % o
      triples1 += "%s %s %s .\n" % (s,p,o)
    def on_prepare_data(s,p,o,d):
      nonlocal triples1
      if not s.startswith("_"): s = "<%s>" % s
      p = "<%s>" % p
      if   isinstance(d, str) and d.startswith("@"): o = '"%s"%s' % (o, d)
      elif d:                                        o = '"%s"^^<%s>' % (o, d)
      else:                                          o = '"%s"' % o
      triples1 += "%s %s %s .\n" % (s,p,o)
    #owlready2.driver.parse_owlxml(os.path.join(HERE, "test_owlxml.owl"), on_prepare_triple, on_prepare_data)
    
    f = open(os.path.join(HERE, "test_owlxml.ntriples"), "rb")
    triples2 = f.read().decode("unicode-escape")
    f.close()
    
    #self.assert_ntriples_equivalent(triples1, triples2)
    
    
    triples1 = ""
    owlready2.owlxml_2_ntriples.parse(os.path.join(HERE, "test_owlxml.owl"), on_prepare_triple, on_prepare_data)
     
    self.assert_ntriples_equivalent(triples1, triples2)
    
    
  def test_format_3(self):
    world = self.new_world()
    onto = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/3/test_owlxml.owl").load()
    
    assert issubclass(onto.C2, onto.C)
    assert onto.p3.range == [onto.D]
    assert issubclass(onto.d, FunctionalProperty)
    
  def test_format_4(self):
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    
    assert set(world.data_properties()) == { n.price }
    assert set(world.classes()) == { n.Meat, n.Tomato, n.Eggplant, n.Olive, n.Vegetable, n.NonPizza, n.Pizza, n.Cheese, n.VegetarianPizza, n.Topping }
    assert set(world.object_properties()) == { n.has_topping, n.has_main_topping, n.main_topping_of, n.topping_of }
    assert set(world.annotation_properties()) == { n.annot }
    assert set(world.properties()) == { n.price, n.has_topping, n.has_main_topping, n.main_topping_of, n.topping_of, n.annot }
    assert set(world.individuals()) == { n.mon_frometon, n.ma_tomate, n.ma_pizza }
    
  def test_format_5(self):
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test_ntriples").load()
    
    assert set(world.data_properties()) == { n.price }
    assert set(world.classes()) == { n.Meat, n.Tomato, n.Eggplant, n.Olive, n.Vegetable, n.NonPizza, n.Pizza, n.Cheese, n.VegetarianPizza, n.Topping }
    assert set(world.object_properties()) == { n.has_topping, n.has_main_topping, n.main_topping_of, n.topping_of }
    assert set(world.annotation_properties()) == { n.annot }
    assert set(world.properties()) == { n.price, n.has_topping, n.has_main_topping, n.main_topping_of, n.topping_of, n.annot }
    assert set(world.individuals()) == { n.mon_frometon, n.ma_tomate, n.ma_pizza }
    
  def test_format_6(self):
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    
    import subprocess
    rapper = subprocess.Popen(["rapper", "-q", "-g", os.path.join(HERE, "test.owl")], stdout = subprocess.PIPE)
    triples1 = rapper.stdout.read().decode("unicode-escape")
    rapper.stdout.close()
    rapper.wait()
    
    rapper = subprocess.Popen(["rapper", "-q", "-g", "-", "http://test/xxx.owl"], stdin = subprocess.PIPE, stdout = subprocess.PIPE)
    n.save(rapper.stdin, "rdfxml")
    rapper.stdin.close()
    triples2 = rapper.stdout.read().decode("unicode-escape")
    rapper.stdout.close()
    rapper.wait()
    
    self.assert_ntriples_equivalent(triples1, triples2)
    
  def test_format_8(self):
    import re, owlready2.owlxml_2_ntriples
    
    triples1 = ""
    def on_prepare_triple(s,p,o):
      nonlocal triples1
      if not s.startswith("_"): s = "<%s>" % s
      p = "<%s>" % p
      if not o.startswith("_"): o = "<%s>" % o
      triples1 += "%s %s %s .\n" % (s,p,o)
    def on_prepare_data(s,p,o,d):
      nonlocal triples1
      if not s.startswith("_"): s = "<%s>" % s
      p = "<%s>" % p
      if   isinstance(d, str) and d.startswith("@"): o = '"%s"%s' % (o, d)
      elif d:                                        o = '"%s"^^<%s>' % (o, d)
      else:                                          o = '"%s"' % o
      triples1 += "%s %s %s .\n" % (s,p,o)
    
    f = open(os.path.join(HERE, "test_owlxml_2.ntriples"), "rb")
    triples2 = f.read().decode("unicode-escape")
    f.close()
    
    triples1 = ""
    owlready2.owlxml_2_ntriples.parse(os.path.join(HERE, "test_owlxml_2.owl"), on_prepare_triple, on_prepare_data)
    
    self.assert_ntriples_equivalent(triples2, triples1)
    
  def test_format_9(self):
    world = self.new_world()
    onto = world.get_ontology("http://test.org/test_owlxml_2.owl").load()
    
    d = onto.C.equivalent_to[0].value
    
    assert isinstance(d, ConstrainedDatatype)
    assert d.base_datatype is float
    assert d.min_inclusive == 100.0
    assert d.max_exclusive == 110.0
    
    c = onto.C.is_a[-1].property
    
    assert isinstance(c, Inverse)
    assert c.property is onto.P2
    
  def test_format_10(self):
    world = self.new_world()
    nb_triple = len(world.graph)
    onto  = world.get_ontology("http://test.org/test_owlxml_bug.owl")
    ok    = 0
    try:
      onto.load()
    except OwlReadyOntologyParsingError:
      ok = 1
    
    assert ok == 1
    assert not onto.loaded
    assert len(world.graph) == 1 + nb_triple
    
  def test_format_11(self):
    world = self.new_world()
    nb_triple = len(world.graph)
    onto  = world.get_ontology("http://test.org/test_rdfxml_bug.owl")
    ok    = 0
    try:
      onto.load()
    except OwlReadyOntologyParsingError:
      ok = 1
      
    assert ok == 1
    assert not onto.loaded
    assert len(world.graph) == 1 + nb_triple
    
  def test_format_13(self):
    world = self.new_world()
    nb_triple = len(world.graph)
    onto  = world.get_ontology("http://test.org/test_ntriples_bug.ntriples")
    ok    = 0
    try:
      onto.load()
    except OwlReadyOntologyParsingError:
      ok = 1
      
    assert ok == 1
    assert not onto.loaded
    assert len(world.graph) == 1 + nb_triple
    
  def test_format_14(self):
    import re, owlready2.owlxml_2_ntriples
    
    triples1 = ""
    def on_prepare_triple(s,p,o):
      nonlocal triples1
      if not s.startswith("_"): s = "<%s>" % s
      p = "<%s>" % p
      if not o.startswith("_"): o = "<%s>" % o
      triples1 += "%s %s %s .\n" % (s,p,o)
    def on_prepare_data(s,p,o,d):
      nonlocal triples1
      if not s.startswith("_"): s = "<%s>" % s
      p = "<%s>" % p
      if   isinstance(d, str) and d.startswith("@"): o = '"%s"%s' % (o, d)
      elif d:                                        o = '"%s"^^<%s>' % (o, d)
      else:                                          o = '"%s"' % o
      triples1 += "%s %s %s .\n" % (s,p,o)
    #owlready2.driver.parse_owlxml(os.path.join(HERE, "test_propchain_owlxml.owl"), on_prepare_triple, on_prepare_data)
    
    f = open(os.path.join(HERE, "test_propchain.ntriples"), "rb")
    triples2 = f.read().decode("unicode-escape")
    f.close()
    
    #self.assert_ntriples_equivalent(triples1, triples2)

    
    triples1 = ""
    owlready2.owlxml_2_ntriples.parse(os.path.join(HERE, "test_propchain_owlxml.owl"), on_prepare_triple, on_prepare_data)
    
    self.assert_ntriples_equivalent(triples1, triples2)
    
  def test_format_15(self):
    world = self.new_world()
    onto  = world.get_ontology("http://www.test.org/test_breakline.owl").load()

    assert onto.C.comment.first() == locstr(r"""Comment long
on
multiple lines with " and ’ and \ and & and < and > and é.""", "en")
    
    f = BytesIO()
    onto.save(f, format = "ntriples")
    s = f.getvalue().decode("utf8")

    assert s.count("\n") <= 4
    assert s == """<http://www.test.org/test_breakline.owl> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Ontology> .
<http://www.test.org/test_breakline.owl#C> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .
<http://www.test.org/test_breakline.owl#C> <http://www.w3.org/2000/01/rdf-schema#comment> "Comment long\\non\\nmultiple lines with \\" and ’ and \\\\ and & and < and > and é."@en .
"""
    
  def test_format_16(self):
    world = self.new_world()
    onto  = world.get_ontology("http://www.test.org/test_annot_on_bn.owl").load()

    assert len(onto.graph) == 16
    
    s = comment[onto.C, owl_equivalentclass, onto.C.equivalent_to[0]].first()
    assert s == "Test"
    
  def test_format_17(self):
    world = self.new_world()
    onto  = world.get_ontology("http://www.test.org/test_annot_on_bn2.owl").load()
    
    assert len(onto.graph) == 29
    
    c = comment[onto.C, rdfs_subclassof, onto.C.is_a[-1]].first()
    d = comment[onto.D, rdfs_subclassof, onto.D.is_a[-1]].first()
    assert c == "Annot on C"
    assert d == "Annot on D"
    
  def test_format_18(self):
    world1 = self.new_world()
    onto1  = world1.get_ontology("http://www.test.org/test_annotated_axiom1.owl").load()
    world2 = self.new_world()
    onto2  = world2.get_ontology("http://www.test.org/test_annotated_axiom2.owl").load()
    
    assert len(onto1.graph) == 20
    assert len(onto2.graph) == 20
    
  def test_format_19(self):
    world = self.new_world()
    onto  = world.get_ontology("http://www.test.org/test_annotated_axiom3.owl").load()
    
    assert len(onto.graph) == 9
    
  def test_format_20(self):
    import owlready2.rdfxml_2_ntriples
    world = self.new_world()
    n = world.get_ontology("http://www.test.org/test_ns.owl").load()
    
    import subprocess
    rapper = subprocess.Popen(["rapper", "-q", "-g", os.path.join(HERE, "test_ns.owl")], stdout = subprocess.PIPE)
    triples2 = rapper.stdout.read().decode("unicode-escape")
    rapper.stdout.close()
    rapper.wait()
    
    triples1 = ""
    def on_prepare_triple(s,p,o):
      nonlocal triples1
      if not s.startswith("_"): s = "<%s>" % s
      p = "<%s>" % p
      if not o.startswith("_"): o = "<%s>" % o
      triples1 += "%s %s %s .\n" % (s,p,o)
    def on_prepare_data(s,p,o,d):
      nonlocal triples1
      if not s.startswith("_"): s = "<%s>" % s
      p = "<%s>" % p
      if   isinstance(d, str) and d.startswith("@"): o = '"%s"%s' % (o, d)
      elif d:                                        o = '"%s"^^<%s>' % (o, d)
      else:                                          o = '"%s"' % o
      triples1 += "%s %s %s .\n" % (s,p,o)
    #owlready2.driver.parse_rdfxml(os.path.join(HERE, "test_ns.owl"), on_prepare_triple, on_prepare_data)
    
    #self.assert_ntriples_equivalent(triples1, triples2)
    
    
    triples1 = ""
    owlready2.rdfxml_2_ntriples.parse(os.path.join(HERE, "test_ns.owl"), on_prepare_triple, on_prepare_data)
    
    self.assert_ntriples_equivalent(triples1, triples2)
    
  def test_format_21(self):
    world = self.new_world()
    o = world.get_ontology("http://www.test.org/test_id.owl").load()
    
    assert issubclass(o.Prop1, ObjectProperty)
    assert issubclass(o.Prop2, ObjectProperty)
    assert o.Prop1.namespace == o
    assert o.Prop2.namespace == o
    assert o.Prop1.iri == "http://www.test.org/test_id.owl#Prop1"
    assert o.Prop2.iri == "http://www.test.org/test_id.owl#Prop2"
    
  def test_format_22(self):
    world = self.new_world()
    o = world.get_ontology("http://www.test.org/test_url").load()
    
    assert o.O
    assert o.O2
    assert o.O3
    assert issubclass(o.O2, o.O)
    assert issubclass(o.O3, o.O2)
    assert set(o.search(subclass_of = o.O)) == { o.O, o.O2, o.O3 }
    
  def test_format_23(self):
    world = self.new_world()
    n = world.get_ontology("http://www.test.org/test_url").load()
    
    import subprocess
    rapper = subprocess.Popen(["rapper", "-q", "-g", os.path.join(HERE, "test_url.owl")], stdout = subprocess.PIPE)
    triples1 = rapper.stdout.read().decode("unicode-escape")
    rapper.stdout.close()
    rapper.wait()
    
    rapper = subprocess.Popen(["rapper", "-q", "-g", "-", "http://www.test.org/test_url"], stdin = subprocess.PIPE, stdout = subprocess.PIPE)
    n.save(rapper.stdin, "rdfxml")
    rapper.stdin.close()
    triples2 = rapper.stdout.read().decode("unicode-escape")
    rapper.stdout.close()
    rapper.wait()
    
    # Rapper does not remove trailing / at the end of the ontology IRI
    triples1 = triples1.replace("<http://www.test.org/testurl/>", "<http://www.test.org/testurl>")
    self.assert_ntriples_equivalent(triples1, triples2)
    
  def test_format_24(self):
    quadstore = os.path.join(HERE, "test_quadstore_slash.sqlite3")
    assert os.path.exists(quadstore)
    world = self.new_world()
    world.set_backend(filename = quadstore)
    onto = world.get_ontology("http://test.org/test_slash/").load()
    assert onto.C is not None
    world.close()
    
  def test_format_25(self):
    world = self.new_world()
    world.set_backend(filename = os.path.join(HERE, "test_quadstore_slash.sqlite3"))
    onto = world.get_ontology("http://test.org/test_slash")
    assert onto.C is not None
    world.close()
    
  def test_format_26(self):
    world = self.new_world()
    nb_triple = len(world.graph)
    onto = world.get_ontology("http://test.org/test.org#")
    self.assert_triple(onto.storid, rdf_type, owl_ontology, None, world)
    
    s = """<http://test.org/test.org#A> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class>."""
    onto.load(fileobj = BytesIO(s.encode("utf8")))
    
    self.assert_triple(onto.storid, rdf_type, owl_ontology, None, world)
    assert len(world.graph) == 2 + nb_triple
    
  def test_format_27(self):
    # Verify that Cython PYX version is used
    import owlready2_optimized
    
  def test_format_28(self):
    world = self.new_world()
    onto = get_ontology("https://test.org/o#")
    
    with onto:
      class C(Thing): pass
      class p(Thing >> str): pass
      
      c = C()
      c.p = ["sss"]
      
      C.name = "TEST:C"
      p.name = "TEST:p"

    tmp = self.new_tmp_file()
    onto.save(tmp)

    world = self.new_world()
    onto = get_ontology(tmp).load()

    c = list(onto.individuals())[0]
    assert c.__class__.iri == "https://test.org/o#TEST:C"
    
  def test_format_29(self):
    world = self.new_world()
    onto  = get_ontology("https://test.org/o#")
    onto2 = get_ontology("https://test.org/o2#")
    
    with onto2:
      class D(Thing): pass
      D.name = "456"
      
    with onto:
      class C(Thing): pass
      C.name = "123"
      c = C("1")
      d = D("2")
      
    tmp = self.new_tmp_file()
    onto.save(tmp)
    
    #print(open(tmp).read())
    world = self.new_world()
    onto = get_ontology(tmp).load()
    
    assert onto["1"].is_a == [onto["123"]]
    assert isinstance(onto["1"], onto["123"])
    
  def test_format_30(self):
    world = self.new_world()
    onto = world.get_ontology("http://knowledge.graph/wind/")
    
    with onto:
      class DO(Thing): pass
      d = DO("d")
      
    tmp = self.new_tmp_file()
    onto.save(tmp)
    
    world = self.new_world()
    onto = get_ontology(tmp).load()
    
    assert onto.DO.iri == "http://knowledge.graph/wind/DO"
    assert onto.d .iri == "http://knowledge.graph/wind/d"
    
  def test_search_1(self):
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    
    l = n.search(iri = "*Pizza")
    assert set(l) == { n.Pizza, n.NonPizza, n.VegetarianPizza }
    
    l = n.search(has_topping = n.ma_tomate)
    assert set(l) == { n.ma_pizza }
    
  def test_search_2(self):
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    
    l = n.search(has_topping = [n.ma_tomate, n.mon_frometon])
    assert set(l) == { n.ma_pizza }
    
    l = n.search(has_topping = [n.ma_tomate, n.Cheese()])
    assert set(l) == set()
    
  def test_search_3(self):
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    
    l = n.search(is_a = n.Pizza)
    assert set(l) == { n.Pizza, n.ma_pizza, n.VegetarianPizza }
    
    l = n.search(type = n.Pizza)
    assert set(l) == { n.ma_pizza }
    
    l = n.search(subclass_of = n.Pizza)
    assert set(l) == { n.Pizza, n.VegetarianPizza }
    
  def test_search_4(self):
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    
    l = n.search(type = n.Pizza, has_topping = None)
    assert set(l) == set()
    
    n.ma_pizza.price = 9.9
    n.Pizza("pizzvide")
    n.Pizza("pizzvide2", price = 9.9)
    
    l = n.search(type = n.Pizza, has_topping = None)
    assert set(l) == { n.pizzvide, n.pizzvide2 }
    
    l = n.search(type = n.Pizza, price = 9.9, has_topping = None)
    assert set(l) == { n.pizzvide2 }
    
  def test_search_5(self):
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    n.Tomato()
    
    l = n.search(type = n.Tomato, topping_of = n.ma_pizza)
    assert set(l) == { n.ma_tomate }
    
    l = n.search(topping_of = n.ma_pizza)
    assert set(l) == { n.ma_tomate, n.mon_frometon }
    
  def test_search_6(self):
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    
    l = n.search(type = n.Tomato)
    assert set(l) == { n.ma_tomate }
    
    l = n.search(type = n.Topping)
    assert set(l) == { n.ma_tomate, n.mon_frometon }
    
    l = n.search(subclass_of = n.Tomato)
    assert set(l) == { n.Tomato }
    
    l = n.search(is_a = n.Tomato)
    assert set(l) == { n.Tomato, n.ma_tomate }
    
    l = n.search(subclass_of = n.Topping)
    assert set(l) == { n.Topping, n.Tomato, n.Cheese, n.Meat, n.Vegetable, n.Eggplant, n.Olive }
    
    l = n.search(is_a = n.Topping)
    assert set(l) == { n.Topping, n.ma_tomate, n.mon_frometon, n.Tomato, n.Cheese, n.Meat, n.Vegetable, n.Eggplant, n.Olive }
    
  def test_search_7(self):
    world = self.new_world()
    n = world.get_ontology("http://test.org/test.owl")
    with n:
      class O(Thing): pass
      class p(O >> str): pass

    o1 = O(p = ["ABCD"])
    o2 = O(p = ["ABC"])
    o3 = O(p = ["AB", "EF"])
    o4 = O(p = ["EFG"])

    l = n.search(p = "ABC*")
    assert set(l) == { o1, o2 }
    
    l = n.search(p = "EF*")
    assert set(l) == { o3, o4 }
    
  def test_search_8(self):
    world = self.new_world()
    onto = world.get_ontology("http://test.org/test.owl")
    with onto:
      class O(Thing): pass
      class q(O >> str): pass
      class p(O >> O): pass
      class i(O >> O):
        inverse = p
        
    o1 = O()
    o2 = O()
    o3 = O()
    o4 = O()

    o1.p = [o2, o3]
    o4.p = [o2]

    assert onto.search(p = [o2, o3]) == [o1]
    
    o1 = O()
    o2 = O()
    o3 = O()
    o4 = O()

    o1.p = [o2]
    o3.i = [o1]
    
    assert onto.search(p = [o2, o3]) == [o1]
    
    o1 = O()
    o2 = O()
    o3 = O()
    o4 = O()

    o2.i = [o1, o4]
    o3.i = [o1]
    
    assert world.search(p = [o2, o3]) == [o1]
    
    o1 = O(q = ["x"])
    o2 = O(q = ["x"])
    o3 = O(q = ["y"])
    o4 = O()

    o1.p = [o2, o3]
    o4.p = [o2]
    
    assert onto.search(q = "x", p = [o2, o3]) == [o1]
    
  def test_search_9(self):
    world = self.new_world()
    onto = world.get_ontology("http://test.org/test.owl")
    with onto:
      class O(Thing): pass
      class i(O >> int,   FunctionalProperty): pass
      class f(O >> float, FunctionalProperty): pass

      o1 = O(i = 1, f = 2.3)
      o2 = O(i = 3, f = 0.3)
      o3 = O(i = 4, f = -2.3)
      o4 = O(i = 7, f = 4.6)

    assert set(onto.search(i = NumS(">" , 3  ))) == set([o3, o4])
    assert set(onto.search(f = NumS("<=", 0.3))) == set([o2, o3])
    
  def test_search_10(self):
    world = self.new_world()
    onto = world.get_ontology("http://test.org/test.owl")
    with onto:
      class O(Thing): pass
      class i(O >> int): pass

      o1 = O(i = [1])
      o2 = O(i = [3])
      o3 = O(i = [4])
      o4 = O(i = [7, 1])

    assert set(onto.search(i = NumS("<=", 3))) == set([o1, o2, o4])
    assert set(onto.search(i = NumS("=" , 1))) == set([o1, o4])
    assert set(onto.search(i = NumS(">" , 1, "<", 4))) == set([o2])
    
  def test_search_11(self):
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    
    l = world.search(type = n.Pizza, has_topping = world.search(type = n.Tomato))
    assert set(l) == { n.ma_pizza }
    
    l = world.search(type = n.Tomato, topping_of = world.search(has_topping = n.mon_frometon))
    assert set(l) == { n.ma_tomate }

    sl = world.search(has_topping = n.mon_frometon)
    l = world.search(type = n.Tomato, topping_of = sl)
    assert set(l) == { n.ma_tomate }
    assert isinstance(sl, owlready2.triplelite._SearchList)
    
  def test_search_12(self):
    world = self.new_world()
    o = world.get_ontology("http://test.org/onto.owl")
    
    with o:
      class Actor(Thing): pass
      class Locality(Thing): pass
      class isAt(ObjectProperty): pass
      
      for name in ('actor1', 'actor2'):
        loc = o.Locality(name + '_loc')
        actor = o.Actor(name, isAt = [loc])
        
      AllDisjoint(o.Actor.instances())
      AllDisjoint(o.Locality.instances())
      
    assert set(world.search(isAt = "*")) == {o.actor1, o.actor2}
    
  def test_search_13(self):
    world = self.new_world()
    o = world.get_ontology("http://test.org/onto.owl")
    
    with o:
      class C(Thing): pass
      class p(AnnotationProperty): pass
      
      c1 = C()
      c2 = C(p = ["a", "b"])
      c3 = C(p = [1, 2])
      c4 = C(p = [c1])
      
    assert set(world.search(p = "a")) == {c2}
    assert set(world.search(p = "b")) == {c2}
    assert set(world.search(p = "c")) == set()
    assert set(world.search(p = 1)) == {c3}
    assert set(world.search(p = 2)) == {c3}
    assert set(world.search(p = c1)) == {c4}
    assert set(world.search(p = 3)) == set()
    assert set(world.search(p = "*")) == {c2, c3, c4}
    assert set(world.search(type = C, p = None)) == {c1}
    
  def test_search_14(self):
    world = self.new_world()
    o = world.get_ontology("http://test.org/onto.owl")
    
    with o:
      class C(Thing): pass
      class p(DataProperty): pass
      
      c1 = C()
      c2 = C(p = ["a", "b"])
      c3 = C(p = [1, 2])
      
    assert set(world.search(p = "a")) == {c2}
    assert set(world.search(p = "b")) == {c2}
    assert set(world.search(p = "c")) == set()
    assert set(world.search(p = 1)) == {c3}
    assert set(world.search(p = 2)) == {c3}
    assert set(world.search(p = 3)) == set()
    assert set(world.search(p = "*")) == {c2, c3}
    assert set(world.search(type = C, p = None)) == {c1}
    
  def test_search_15(self):
    world = self.new_world()
    o = world.get_ontology("http://test.org/onto.owl")
    
    with o:
      class C(Thing): pass
      class p(ObjectProperty): pass
      class q(ObjectProperty): pass
      class i(ObjectProperty): inverse = q
      
      c1 = C()
      c2 = C(p = [c1])
      c3 = C(p = [c1, c2])
      
    c1.q.append(c2)
    c2.i.append(c3)
    c3.q.append(c1)
    
    assert set(world.search(p = c1)) == {c2, c3}
    assert set(world.search(p = c2)) == {c3}
    assert set(world.search(p = c3)) == set()
    assert set(world.search(p = "*")) == {c2, c3}
    assert set(world.search(type = C, p = None)) == {c1}
    
    assert set(world.search(q = c1)) == {c3}
    assert set(world.search(q = c2)) == {c1, c3}
    assert set(world.search(q = c3)) == set()
    assert set(world.search(q = "*")) == {c1, c3}
    
  def test_search_16(self):
    world = self.new_world()
    o = world.get_ontology("http://test.org/onto.owl")
    
    with o:
      class MyClass1(Thing): pass
      class MYCLASS2(Thing): pass
      
    assert set(world.search(iri = "*MyClass*")) == set([MyClass1])
    assert set(world.search(iri = "*MYCLASS*")) == set([MYCLASS2])
    assert set(world.search(iri = "*myclass*")) == set([])
    
    assert set(world.search(iri = "*MyClass*", _case_sensitive = False)) == set([MyClass1, MYCLASS2])
    assert set(world.search(iri = "*MYCLASS*", _case_sensitive = False)) == set([MyClass1, MYCLASS2])
    assert set(world.search(iri = "*myclass*", _case_sensitive = False)) == set([MyClass1, MYCLASS2])
    
  def test_search_17(self):
    world = self.new_world()
    o = world.get_ontology("http://test.org/onto.owl")
    
    with o:
      class C(Thing): pass
      c1 = C(comment = ["Comment"])
      c2 = C(comment = ["COMMENT"])
      c3 = C(comment = ["comment"])
      
    assert set(world.search(comment = "*Comment*")) == set([c1])
    assert set(world.search(comment = "*COMMENT*")) == set([c2])
    assert set(world.search(comment = "*comment*")) == set([c3])
    assert set(world.search(comment = "Comment")) == set([c1])
    assert set(world.search(comment = "COMMENT")) == set([c2])
    assert set(world.search(comment = "comment")) == set([c3])
    
    assert set(world.search(comment = "*Comment*", _case_sensitive = False)) == set([c1, c2, c3])
    assert set(world.search(comment = "*COMMENT*", _case_sensitive = False)) == set([c1, c2, c3])
    assert set(world.search(comment = "*comment*", _case_sensitive = False)) == set([c1, c2, c3])
    assert set(world.search(comment = "Comment", _case_sensitive = False)) == set([c1, c2, c3])
    assert set(world.search(comment = "COMMENT", _case_sensitive = False)) == set([c1, c2, c3])
    assert set(world.search(comment = "comment", _case_sensitive = False)) == set([c1, c2, c3])
    
  def test_search_18(self):
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    
    l = world.search(type = n.Pizza) | world.search(type = n.Tomato)
    assert set(l) == { n.ma_pizza, n.ma_tomate }
    
    l = world.search(has_topping = world.search(type = n.Cheese) | world.search(type = n.Tomato))
    assert set(l) == { n.ma_pizza }
    
    l = world.search(has_topping = world.search(type = Or([n.Cheese, n.Tomato])))
    assert set(l) == { n.ma_pizza }
    
  def test_search_18(self):
    world = self.new_world()
    onto = world.get_ontology("http://test.org/test.owl")
    with onto:
      class C(Thing): pass
      class D(Thing): pass
      class p(Thing >> Thing): pass
      class i(Thing >> Thing): inverse = p
      
      c1 = C()
      c2 = C(p = [D()])
      d2 = D()
      d4 = D(p = [D()])
      c3 = C()
      d5 = D(i = [c3])
      
    r = onto.search(type = C, p = "*")
    assert r == [c2, c3]
    
    r = onto.search(type = onto.search(iri = "*C"), p = "*")
    assert r == [c2, c3]
    
    r = onto.search(iri = "*C") | onto.search(iri = "*D")
    assert r == [C, D]
    
    r = onto.search(type = onto.search(iri = "*C") | onto.search(iri = "*D"))
    assert len(r) == 8
    
    r = onto.search(type = onto.search(iri = "*C") | onto.search(iri = "*D"), p = "*")
    assert r == [c2, c3, d4]
    
    r = onto.search(is_a = onto.search(iri = "*C") | onto.search(iri = "*D"), p = "*")
    assert r == [c2, c3, d4]
    
    
  def test_rdflib_1(self):
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    g = world.as_rdflib_graph()
    
    assert (list(g.objects(rdflib.URIRef("http://www.semanticweb.org/jiba/ontologies/2017/0/test#ma_pizza"),
                           rdflib.URIRef("http://www.semanticweb.org/jiba/ontologies/2017/0/test#price")))[0].toPython()
            == 9.9)
    
    assert (set(g.objects(rdflib.URIRef("http://www.semanticweb.org/jiba/ontologies/2017/0/test#ma_pizza"),
                          rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")))
            == { rdflib.URIRef("http://www.semanticweb.org/jiba/ontologies/2017/0/test#Pizza"),
                 rdflib.URIRef("http://www.w3.org/2002/07/owl#NamedIndividual"),
            })
    
    tomato = n.Tomato()
    
    nb = len(world.graph)
    
    g.store.context_graphs[n].add(
      (rdflib.URIRef("http://www.semanticweb.org/jiba/ontologies/2017/0/test#ma_pizza"),
       rdflib.URIRef("http://www.semanticweb.org/jiba/ontologies/2017/0/test#has_topping"),
       rdflib.URIRef(tomato.iri),
    ))
    
    assert len(world.graph) == nb + 1
    
    g.store.context_graphs[n].remove(
      (rdflib.URIRef("http://www.semanticweb.org/jiba/ontologies/2017/0/test#ma_pizza"),
       rdflib.URIRef("http://www.semanticweb.org/jiba/ontologies/2017/0/test#has_topping"),
       None,
    ))
    
    assert len(world.graph) == nb - 2
    
  def test_rdflib_2(self):
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    g = world.as_rdflib_graph()
    
    r = g.query("""SELECT ?p WHERE {
    <http://www.semanticweb.org/jiba/ontologies/2017/0/test#ma_pizza> <http://www.semanticweb.org/jiba/ontologies/2017/0/test#price> ?p .
    }
    """)
    
    assert list(r)[0][0].toPython() == 9.9
    
  def test_rdflib_3(self):
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/test.owl")
    with n:
      class O(Thing): pass
      class p(Thing >> str): pass
      o = O("o")
      o.p = ["D"]
      
    g = world.as_rdflib_graph()
    
    r = g.query_owlready("""
    PREFIX P: <http://www.semanticweb.org/test.owl#>
    SELECT ?x WHERE {
    ?x P:p "D".
    }
    """)
    assert list(r)[0][0] is o
    
    r = g.query_owlready("""
    PREFIX P: <http://www.semanticweb.org/test.owl#>
    SELECT ?x WHERE {
    ?x P:p "E".
    }
    """)
    assert not list(r)
    
    r = g.query_owlready("""
    PREFIX P: <http://www.semanticweb.org/test.owl#>
    SELECT ?x WHERE {
    P:o P:p ?x.
    }
    """)
    assert list(r) == [["D"]]

  def test_rdflib_4(self):
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/test.owl")
    with n:
      class O(Thing): pass
      class p(Thing >> bool, FunctionalProperty): pass
      class i(Thing >> int , FunctionalProperty): pass
      o1 = O(p = False, i = 1)
      o2 = O(p = True , i = 1)
      o3 = O(p = True , i = 2)
      
    g = world.as_rdflib_graph()
    
    r = list(g.query_owlready("""
    PREFIX P: <http://www.semanticweb.org/test.owl#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    SELECT ?s WHERE {
    ?s P:i "1"^^xsd:int.
    }
    """))
    assert set(l[0] for l in r) == { o1, o2 }
    
    r = list(g.query_owlready("""
    PREFIX P: <http://www.semanticweb.org/test.owl#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    SELECT ?s WHERE {
    ?s P:p "true"^^xsd:boolean.
    }
    """))
    assert set(l[0] for l in r) == { o2, o3 }
    
    r = list(g.query_owlready("""
    PREFIX P: <http://www.semanticweb.org/test.owl#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    SELECT ?s WHERE {
    ?s P:p "true".
    }
    """))
    assert set(l[0] for l in r) == { o2, o3 }
    
    r = list(g.query_owlready("""
    PREFIX P: <http://www.semanticweb.org/test.owl#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    SELECT ?o WHERE {
    P:o3 P:i ?o.
    }
    """))
    assert set(l[0] for l in r) == { 2 }
    
    r = list(g.query_owlready("""
    PREFIX P: <http://www.semanticweb.org/test.owl#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    SELECT ?o WHERE {
    P:o1 P:p ?o.
    }
    """))
    assert set(l[0] for l in r) == { False }
    assert type(r[0][0]) is bool

  def test_rdflib_5(self):
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/test.owl")
    with n:
      class O(Thing): pass
      class p(Thing >> str): pass
      o1 = O(p = ["1", "2"])
      n._add_data_triple_spod(o1.storid, p.storid, "3", 0)
      
    g = world.as_rdflib_graph()
    s = set(g.triples((rdflib.URIRef(o1.iri), None, None)))
    assert len(s) == 5
    
  def test_rdflib_6(self):
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/test.owl")
    with n:
      class O(Thing): pass
      class p(Thing >> str): pass

    g = world.as_rdflib_graph()
    g.bind("ex", "http://www.semanticweb.org/test.owl#")
    
    r = g.query("""
    SELECT ?b WHERE {
    ex:O
    <http://www.w3.org/1999/02/22-rdf-syntax-ns#type>
    ?b .
    }""")
    assert list(r) == [(rdflib.URIRef("http://www.w3.org/2002/07/owl#Class"),)]
    
  def test_rdflib_7(self):
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/test.owl")
    with n:
      class O(Thing): pass
      class p(Thing >> Thing): pass
      class i(Thing >> Thing): inverse = p
      o1 = O()
      o2 = O(p = [o1])
      
    g = world.as_rdflib_graph()
    
    r = set(g.triples((rdflib.URIRef(o2.iri), rdflib.URIRef(p.iri), None)))
    assert r == set([(rdflib.URIRef(o2.iri), rdflib.URIRef(p.iri), rdflib.URIRef(o1.iri))])
    r = set(g.triples((rdflib.URIRef(o2.iri), rdflib.URIRef(p.iri), rdflib.URIRef(o1.iri))))
    assert r == set([(rdflib.URIRef(o2.iri), rdflib.URIRef(p.iri), rdflib.URIRef(o1.iri))])
    
    r = set(g.triples((rdflib.URIRef(o1.iri), rdflib.URIRef(i.iri), None)))
    assert r == set([(rdflib.URIRef(o1.iri), rdflib.URIRef(i.iri), rdflib.URIRef(o2.iri))])
    r = set(g.triples((rdflib.URIRef(o1.iri), rdflib.URIRef(i.iri), rdflib.URIRef(o2.iri))))
    assert r == set([(rdflib.URIRef(o1.iri), rdflib.URIRef(i.iri), rdflib.URIRef(o2.iri))])
    
    r = set(g.triples((rdflib.URIRef(o1.iri), None, None)))
    assert r > set([(rdflib.URIRef(o1.iri), rdflib.URIRef(i.iri), rdflib.URIRef(o2.iri))])
    r = set(g.triples((rdflib.URIRef(o1.iri), None, rdflib.URIRef(o2.iri))))
    assert r == set([(rdflib.URIRef(o1.iri), rdflib.URIRef(i.iri), rdflib.URIRef(o2.iri))])
    
  def test_rdflib_8(self):
    world = self.new_world()
    o = world.get_ontology("http://www.semanticweb.org/onto.owl")
    g = world.as_rdflib_graph()
    g.bind("onto", "http://www.semanticweb.org/onto.owl#")

    with o:
      r = g.update("""
      INSERT {
      onto:C
      <http://www.w3.org/1999/02/22-rdf-syntax-ns#type>
      <http://www.w3.org/2002/07/owl#Class> .
      } WHERE {}""")

    assert g.get_context(o) is g.get_context(rdflib.URIRef("http://www.semanticweb.org/onto.owl"))
    assert g.get_context(o) is g.get_context(rdflib.URIRef("http://www.semanticweb.org/onto.owl#"))
    
    g2 = g.get_context(o)
    r = g2.update("""
    INSERT {
    onto:D
    <http://www.w3.org/1999/02/22-rdf-syntax-ns#type>
    <http://www.w3.org/2002/07/owl#Class> .
    } WHERE {}""")
    
    self.assert_triple(world._abbreviate("http://www.semanticweb.org/onto.owl#C"), rdf_type, owl_class, world = world)
    self.assert_triple(world._abbreviate("http://www.semanticweb.org/onto.owl#D"), rdf_type, owl_class, world = world)
    
  def test_rdflib_9(self):
    world = self.new_world()
    o = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    g = world.as_rdflib_graph()
    g.bind("onto", "http://www.semanticweb.org/jiba/ontologies/2017/0/test#")

    with o:
      r = g.update("""
      DELETE {
      onto:ma_pizza
      <http://www.w3.org/1999/02/22-rdf-syntax-ns#type>
      onto:Pizza .
      } WHERE {}""")
      
    self.assert_not_triple(world._abbreviate("http://www.semanticweb.org/onto.owl#ma_pizza"), rdf_type, world._abbreviate("http://www.semanticweb.org/onto.owl#Pizza"), world = world)
    
  def test_rdflib_10(self):
    world = self.new_world()
    o = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    g = world.as_rdflib_graph()
    g.bind("onto", "http://www.semanticweb.org/jiba/ontologies/2017/0/test#")

    r = g.update("""
    DELETE {
    onto:ma_pizza
    <http://www.w3.org/1999/02/22-rdf-syntax-ns#type>
    onto:Pizza .
    } WHERE {}""")
    
    self.assert_not_triple(world._abbreviate("http://www.semanticweb.org/onto.owl#ma_pizza"), rdf_type, world._abbreviate("http://www.semanticweb.org/onto.owl#Pizza"), world = world)
    
  def test_rdflib_11(self):
    world = self.new_world()
    o = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    g = world.as_rdflib_graph()
    g.bind("onto", "http://www.semanticweb.org/jiba/ontologies/2017/0/test#")
    
    p2 = o.Pizza("ma_pizza2")
    storid = p2.storid
    p2.price
    p2.is_a
    p2.has_topping
    assert p2 in owlready2.namespace._cache
    
    with o:
      r = g.update("""
      INSERT {
      onto:ma_pizza2
      onto:price
      12.9 .
      } WHERE {}""")
      
    assert p2.price == 12.9
    
    with o:
      r = g.update("""
      INSERT {
      onto:ma_pizza2
      a
      onto:Cheese .
      } WHERE {}""")
      
    assert o.Cheese in p2.is_a
    
    with o:
      r = g.update("""
      INSERT {
      onto:ma_pizza2
      onto:has_topping
      onto:ma_tomate .
      } WHERE {}""")
      
    assert p2.has_topping == [o.ma_tomate]

    with o:
      r = g.update("""
      DELETE {
      onto:ma_pizza2
      onto:price
      12.9 .
      } WHERE {}""")
      
    assert p2.price == None
    
    with o:
      r = g.update("""
      DELETE {
      onto:ma_pizza2
      a
      onto:Cheese .
      } WHERE {}""")
      
    assert p2.is_a == [o.Pizza]
    
    with o:
      r = g.update("""
      DELETE {
      onto:ma_pizza2
      onto:has_topping
      onto:ma_tomate .
      } WHERE {}""")
      
    assert p2.has_topping == []
    
  def test_rdflib_11a(self):
    world = self.new_world()
    onto = world.get_ontology("http://test.org/onto.owl")
    with onto:
      class C(Thing): pass
      class p(Thing >> Thing): pass
      c1 = C()
      c2 = C(p = [c1])
      comment[c2, p, c1] = ["XYZ"]
      
    graph = world.as_rdflib_graph()
    
    graph.bind("owl", "http://www.w3.org/2002/07/owl#")
    graph.bind("rdfs", "http://www.w3.org/2000/01/rdf-schema#")
    graph.bind("onto", onto.base_iri)
    
    query = """
SELECT ?label WHERE {
?annotation owl:annotatedSource onto:c2 .
?annotation owl:annotatedTarget onto:c1 .
?annotation rdfs:comment ?label .
}"""
    
    result = list(graph.query(query))
    assert len(result) == 1
    assert str(result[0][0]) == "XYZ"
    
  def test_rdflib_12(self):
    world = self.new_world()
    onto = world.get_ontology("http://test.org/onto.owl")
    with onto:
      class C(Thing): pass
      class p(Thing >> Thing): pass
      c1 = C()
      c2 = C(p = [c1])
      comment[c2, p, c1] = ["XYZ"]
      
    graph = world.as_rdflib_graph()
    
    graph.bind("owl", "http://www.w3.org/2002/07/owl#")
    graph.bind("rdfs", "http://www.w3.org/2000/01/rdf-schema#")
    graph.bind("onto", onto.base_iri)
    
    query = """
DELETE {
    ?annotation ?p ?o .
}
WHERE {
    ?annotation owl:annotatedSource onto:c2 .
    ?annotation owl:annotatedProperty onto:p .
    ?annotation owl:annotatedTarget onto:c1 .
    ?annotation ?p ?o .  
}"""

    l = comment[c2, p, c1]
    graph.update(query)
    
    assert comment[c2, p, c1] == []
    
  def test_rdflib_12a(self):
    world = self.new_world()
    onto1 = world.get_ontology("http://test.org/onto1.owl")

    graph = world.as_rdflib_graph()
    assert not graph.get_context(onto1) is None
    
    onto2 = world.get_ontology("http://test.org/onto2.owl")
    assert not graph.get_context(onto2) is None

  def test_rdflib_13(self):
    world = self.new_world()
    onto = world.get_ontology("http://test.org/onto.owl")
    with onto:
      class C1(Thing): pass
      class C2(Thing): pass
      class C2b(C2): pass

    graph = world.as_rdflib_graph()

    rq_template = """
prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
prefix : <http://test.org/onto.owl#>

ask where
{{
    :{} rdfs:subClassOf :{} .
}}
"""

    res1 = list(graph.query(rq_template.format("C2b", "C2")))
    assert res1 == [True]

    res2 = list(graph.query(rq_template.format("C2", "C1")))
    assert res2 == [False]

    res3 = list(graph.query_owlready(rq_template.format("C2b", "C2")))
    assert res3 == [True]

    res4 = list(graph.query_owlready(rq_template.format("C2", "C1")))
    assert res4 == [False]

  def test_rdflib_14(self):
    node = rdflib.BNode()
    graph_rdflib = rdflib.Graph()
    graph_rdflib.add((node, rdflib.namespace.RDF.type, rdflib.namespace.OWL.Class))
    
    world = self.new_world()
    graph_owlready = world.as_rdflib_graph()
    
    with world.get_ontology('http://test.org/t.owl'):
      graph_owlready += graph_rdflib

    assert len(world.graph) == 3
    self.assert_triple(-1, rdf_type, owl_class, world = world)
    
  def test_refactor_1(self):
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    
    p = n.ma_pizza
    n.ma_pizza.name = "ma_pizza_2"
    assert n.ma_pizza is None
    assert n.ma_pizza_2 is p
    assert set(n.ma_pizza_2.has_topping) == { n.ma_tomate, n.mon_frometon }
    assert p.iri == "http://www.semanticweb.org/jiba/ontologies/2017/0/test#ma_pizza_2"
    assert world["http://www.semanticweb.org/jiba/ontologies/2017/0/test#ma_pizza_2"] is p
    
  def test_refactor_2(self):
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    
    p = n.ma_pizza
    n.ma_pizza.iri = "http://t/p"
    assert n.ma_pizza is None
    assert set(p.has_topping) == { n.ma_tomate, n.mon_frometon }
    assert p.iri == "http://t/p"
    assert world["http://t/p"] is p
    assert n.get_namespace("http://t/").p is p
        
  def test_refactor_3(self):
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    
    p = n.Pizza
    n.Pizza.name = "Pizza_2"
    assert n.Pizza is None
    assert n.Pizza_2 is p
    assert p.iri == "http://www.semanticweb.org/jiba/ontologies/2017/0/test#Pizza_2"
    assert world["http://www.semanticweb.org/jiba/ontologies/2017/0/test#Pizza_2"] is p
    
  def test_refactor_4(self):
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    
    p = n.Pizza
    n.Pizza.iri = "http://t/p"
    assert n.Pizza is None
    assert p.iri == "http://t/p"
    assert world["http://t/p"] is p
    assert n.get_namespace("http://t/").p is p
    
    
  def test_date_1(self):
    n = self.new_ontology()
    with n:
      class C(Thing): pass
      class has_datetime(C >> datetime.datetime, FunctionalProperty): pass
      
    c = C()
    d = datetime.datetime(2017, 4, 19, 11, 28, 0)
    c.has_datetime = d

    self.assert_triple(c.storid, has_datetime.storid, "2017-04-19T11:28:00.000",  _universal_datatype_2_abbrev[datetime.datetime])
    
    del c.has_datetime
    assert c.has_datetime == d
    
  def test_date_2(self):
    n = self.new_ontology()
    with n:
      class C(Thing): pass
      class has_date(C >> datetime.date, FunctionalProperty): pass
      
    c = C()
    d = datetime.date(2017, 4, 19)
    c.has_date = d
    self.assert_triple(c.storid, has_date.storid, "2017-04-19", _universal_datatype_2_abbrev[datetime.date])
    
    del c.has_date
    assert c.has_date == d
    
  def test_date_3(self):
    n = self.new_ontology()
    with n:
      class C(Thing): pass
      class has_time(C >> datetime.time, FunctionalProperty): pass
      
    c = C()
    d = datetime.time(11, 28, 0)
    c.has_time = d
    self.assert_triple(c.storid, has_time.storid, "11:28:00", _universal_datatype_2_abbrev[datetime.time])
    
    del c.has_time
    assert c.has_time == d
    
  def test_date_4(self):
    world = self.new_world()
    onto = world.get_ontology("./owlready2/test/test_datetime.owl").load()
    
    assert set(onto.c1.d) == set([
      datetime.datetime(2017, 9, 17, 13, 52, 24, tzinfo=datetime.timezone.utc),
      datetime.datetime(2019, 7, 26, 17, 44, 50, 984100),
      datetime.datetime(2019, 7, 26, 17, 44, 50, 984100, tzinfo=datetime.timezone.utc),
      datetime.datetime(2019, 7, 26, 17, 44, 50)
    ])
    
    
  def test_datatype_1(self):
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/3/test_datatype.owl").load()
    
    d = n.p.range[0]
    assert d.base_datatype is float
    assert d.min_exclusive == 10.0
    assert d.max_exclusive == 20.0
    
    d.base_datatype = int
    
    self.assert_triple(d.storid, owl_ondatatype, _universal_datatype_2_abbrev[int], None, world)
    
    d.min_exclusive = 15
    d.max_exclusive = 20
    
    list_bnode = world._get_obj_triple_sp_o(d.storid, owl_withrestrictions)
    l = list(n._parse_list_as_rdf(list_bnode))
    s = set()
    for i, ii in l:
      t = world._get_data_triples_s_pod(i)
      assert len(t) == 1
      p,o,d = t[0]
      o = from_literal(o,d)
      s.add((p,o))
    assert s == { (xmls_minexclusive, 15),
                  (xmls_maxexclusive, 20) }
    
  def test_datatype_2(self):
    world = self.new_world()
    n = world.get_ontology("http://www.test.org/test.owl")
    
    with n:
      class C(Thing): pass
      class P(DataProperty):
        range = [
          ConstrainedDatatype(str, max_length = 8),
        ]

    d = P.range[0]
    
    self.assert_triple(d.storid, owl_ondatatype, _universal_datatype_2_abbrev[str], None,  world)
    
    list_bnode = world._get_obj_triple_sp_o(d.storid, owl_withrestrictions)
    l = list(n._parse_list_as_rdf(list_bnode))
    s = set()
    for i, ii in l:
      t = world._get_data_triples_s_pod(i)
      assert len(t) == 1
      p,o,d = t[0]
      o = from_literal(o,d)
      s.add((p,o))
    assert s == { (xmls_maxlength, 8) }

  def test_datatype_3(self):
    class Hex(object):
      def __init__(self, value):
        self.value = value
    
    def parser(s): return Hex(int(s, 16))
    def unparser(x):
      h = hex(x.value)[2:]
      if len(h) % 2 != 0: return "0%s" % h
      return h
    
    world = self.new_world()
    onto = world.get_ontology("http://www.test.org/t.owl")
    
    hex_storid = declare_datatype(Hex, "http://www.w3.org/2001/XMLSchema#hexBinary", parser, unparser)
    define_datatype_in_ontology(Hex, "http://www.w3.org/2001/XMLSchema#hexBinary", onto)
    
    with onto:
      class p(Thing >> Hex): pass
      
      class C(Thing): pass

      c1 = C()
      c1.p.append(Hex(14))
      
    self.assert_triple(c1.storid, p.storid, "0e", hex_storid, world)

    c1 = C = None
    import owlready2.namespace
    owlready2.namespace._cache = [None] * 1000
    import gc
    gc.collect(); gc.collect(); gc.collect()
    
    assert onto.c1.p[0].value == 14

  def test_datatype_4(self):
    class AnyURI(object):
      def __init__(self, value):
        self.value = value
    
    def parser  (s): return AnyURI(s)
    def unparser(x): return x.value
    
    world1 = self.new_world()
    world2 = self.new_world()
    onto1  = world1.get_ontology("http://www.test.org/t.owl")
    
    anyuri_storid = declare_datatype(AnyURI, "http://www.w3.org/2001/XMLSchema#anyURI", parser, unparser)
    
    with onto1:
      class p(Thing >> AnyURI): pass
      
      class C(Thing): pass

      c1 = C()
      c1.p.append(AnyURI("xxx"))
      
    self.assert_triple(c1.storid, p.storid, "xxx", anyuri_storid, world1)

    f = self.new_tmp_file()
    onto1.save(f)
    
    onto2 = world2.get_ontology(f).load()
    x = onto2.c1.p[0]
    assert isinstance(x, AnyURI)
    assert x.value == "xxx"
    
    
  def test_inverse_1(self):
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/3/test_inverse.owl").load()
    
    r = n.C.is_a[-1]
    assert isinstance(r.property, Inverse)
    assert r.property.property is n.P
    
  def test_inverse_2(self):
    world = self.new_world()
    n = world.get_ontology("http://www.test.org/test.owl")
    
    with n:
      class P(ObjectProperty): pass
      class C(Thing): pass
      class D(Thing):
        is_a = [Inverse(P).some(C)]
        
    r = D.is_a[-1]
    assert isinstance(r.property, Inverse)
    self.assert_triple(r.property.storid, owl_inverse_property, P.storid, None,  world)
    
  def test_inverse_3(self):
    world = self.new_world()
    n = world.get_ontology("http://www.test.org/test.owl")
    
    with n:
      class P1(ObjectProperty): pass
      class P2(ObjectProperty): pass
      class IP2(ObjectProperty):
        inverse_property = P2
        
    assert Inverse(Inverse(P1)) is P1
    assert Inverse(P2) is IP2
    assert Inverse(IP2) is P2
    
  def test_inverse_4(self):
    world = self.new_world()
    onto  = world.get_ontology("http://www.test.org/test.owl")
    
    with onto:
      class prop(ObjectProperty):
        python_name = "p"
      class C(Thing): pass

      c1 = C()
      c2 = C()
      c3 = C()
      c4 = C()
      
    c2.p = [c1]
    c3.p = [c1]

    assert set(c1.INVERSE_p) == { c2, c3 }
    
    c4.p = [c1]
    assert set(c1.INVERSE_p) == { c2, c3, c4 }

    with onto:
      c5 = C(p = [c1])
    assert set(c1.INVERSE_p) == { c2, c3, c4, c5 }
    
  def test_inverse_5(self):
    world = self.new_world()
    onto  = world.get_ontology("http://www.test.org/test.owl")
    
    with onto:
      class p(ObjectProperty, FunctionalProperty): pass
      class C(Thing): pass
      
      c1 = C()
      c2 = C()
      c3 = C()
      c4 = C()
      
    c2.p = c1
    c3.p = c1

    assert set(c1.INVERSE_p) == { c2, c3 }
    
    c4.p = c1
    assert set(c1.INVERSE_p) == { c2, c3, c4 }

    with onto:
      c5 = C(p = c1)
    assert set(c1.INVERSE_p) == { c2, c3, c4, c5 }
    
    
  def test_propchain_1(self):
    w = self.new_world()
    o = w.get_ontology("http://test/test_propchain.owl").load()
    
    obo = o.get_namespace("http://purl.obolibrary.org/obo/")
    
    assert len(obo.BFO_0000066.property_chain) == 1
    assert obo.BFO_0000066.property_chain[0].properties == [obo.BFO_0000050, obo.BFO_0000066]
    
  def test_propchain_2(self):
    w = self.new_world()
    o = w.get_ontology("http://test/test_propchain.owl")

    with o:
      class C(Thing): pass
      
      class P1(C >> C): pass
      class P2(C >> C): pass
      class P3(C >> C): pass
      class P4(C >> C): pass
      
      class P(C >> C): pass
      
    P.property_chain.append(PropertyChain([P1, P2]))
    
    bns = list(w._get_obj_triples_sp_o(P.storid, owl_propertychain))
    assert len(bns) == 1
    assert o._parse_list(bns[0]) == [P1, P2]
    
    P.property_chain.append(PropertyChain([P3, P4]))
    
    bns = list(w._get_obj_triples_sp_o(P.storid, owl_propertychain))
    assert len(bns) == 2
    assert o._parse_list(bns[0]) == [P1, P2]
    assert o._parse_list(bns[1]) == [P3, P4]
    
    del P.property_chain[0]
    
    bns = list(w._get_obj_triples_sp_o(P.storid, owl_propertychain))
    assert len(bns) == 1
    assert o._parse_list(bns[0]) == [P3, P4]
    
  def test_propchain_3(self):
    w = self.new_world()
    o = w.get_ontology("http://test/test_propchain.owl")
    
    with o:
      class p1(ObjectProperty): pass
      class p2(ObjectProperty): pass
      class p (ObjectProperty): pass
      
    p.property_chain.append(PropertyChain([p1, p2]))
    
    destroy_entity(p1)
    self.assert_not_triple(p1.storid, rdf_type, ObjectProperty.storid, world = w)
    self.assert_triple    (p2.storid, rdf_type, ObjectProperty.storid, world = w)
    self.assert_triple    (p .storid, rdf_type, ObjectProperty.storid, world = w)
    assert len(o.graph) == 3
    assert p.property_chain == []
    
  def test_propchain_4(self):
    w = self.new_world()
    o = w.get_ontology("http://test/test_propchain.owl")
    
    with o:
      class p1(ObjectProperty): pass
      class p2(ObjectProperty): pass
      class p (ObjectProperty): pass
      
    p.property_chain.append(PropertyChain([p1, p2]))
    
    destroy_entity(p)
    self.assert_triple    (p1.storid, rdf_type, ObjectProperty.storid, world = w)
    self.assert_triple    (p2.storid, rdf_type, ObjectProperty.storid, world = w)
    self.assert_not_triple(p .storid, rdf_type, ObjectProperty.storid, world = w)
    assert len(o.graph) == 3
    
    
  def test_destroy_1(self):
    w = self.new_world()
    nb = len(w.graph)
    o = w.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    
    destroy_entity(o.Pizza)
    
    assert len(w.graph) == 58 + nb
    
  def test_destroy_2(self):
    w = self.new_world()
    nb = len(w.graph)
    o = w.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    
    o.Pizza
    o.NonPizza
    assert o.Pizza
    assert len(o.NonPizza.is_a) == 2
    assert isinstance(o.NonPizza.is_a[-1], Not)
    assert o.NonPizza.is_a[-1].Class is o.Pizza
    
    destroy_entity(o.Pizza)
    
    assert len(w.graph) == 58 + nb
    assert o.Pizza is None
    assert len(o.NonPizza.is_a) == 1
    assert o.NonPizza.is_a[0] is Thing
    
  def test_destroy_3(self):
    w = self.new_world()
    nb = len(w.graph)
    o = w.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/0/test").load()
    
    destroy_entity(o.Meat)

    assert len(w.graph) == 68 + nb
    
  def test_destroy_4(self):
    w = self.new_world()
    o = w.get_ontology("http://www.test.org/test.owl")
    
    with o:
      class C(Thing): pass
      class D(C):     pass
    
    destroy_entity(C)
    
    assert D.is_a == [Thing]
    assert o.C is None
    assert not o.D is None
    
  def test_destroy_5(self):
    w = self.new_world()
    nb = len(w.graph)
    o = w.get_ontology("http://www.test.org/test.owl")
    
    with o:
      class C1(Thing): pass
      class C2(Thing): pass
      class C3(Thing): pass
      
      class D(Thing):
        is_a = [C1 | C2 | C3]
        
    destroy_entity(C2)
    
    assert len(w.graph) == 7 + nb
    assert D.is_a == [Thing]
    
  def test_destroy_6(self):
    w = self.new_world()
    o = w.get_ontology("http://www.test.org/test.owl")
    
    with o:
      class C(Thing): pass
      
      class p(C >> C): pass

    assert p.range  == [C]
    assert p.domain == [C]
    
    destroy_entity(C)
    
    assert p.range  == []
    assert p.domain == []
    
  def test_destroy_7(self):
    w = self.new_world()
    nb = len(w.graph)
    o = w.get_ontology("http://www.test.org/test.owl")
    
    with o:
      class C(Thing): pass

    c = C()
    
    assert len(w.graph) == 5 + nb
    
    undestroy = destroy_entity(C, undoable = True)
    
    assert c.is_a  == [Thing]
    assert len(w.graph) == 2 + nb
    
    undestroy()
    
    assert len(w.graph) == 5 + nb
    assert c.is_a  == [C]
    
  def test_destroy_8(self):
    w = self.new_world()
    nb = len(w.graph)
    o = w.get_ontology("http://www.test.org/test.owl")
    
    with o:
      class C(Thing): pass
      class D(Thing): pass
      class E(Thing): pass
      AllDisjoint([C, D, E])
      
    destroy_entity(C)
    
    assert len(w.graph) == 5 + nb
    assert len(list(o.disjoints())) == 0
    
  def test_destroy_9(self):
    w = self.new_world()
    nb = len(w.graph)
    o = w.get_ontology("http://www.test.org/test.owl")
    
    with o:
      class C(Thing): pass
      c1 = C()
      c2 = C()
      c3 = C()
      AllDisjoint([c1, c2, c3])
      C.is_a.append(OneOf([c1, c2, c3]))
      
    destroy_entity(c1)
    
    assert len(w.graph) == 7 + nb
    assert len(list(o.disjoints())) == 0
    
  def test_destroy_10(self):
    w = self.new_world()
    nb = len(w.graph)
    o = w.get_ontology("http://www.test.org/test.owl")
    
    with o:
      class C(Thing): pass
      class D(C): pass
      label[D, rdfs_subclassof, D] = "Test"
      
    destroy_entity(D)
    
    assert len(w.graph) == 3 + nb
    
  def test_destroy_11(self):
    w = self.new_world()
    nb = len(w.graph)
    o = w.get_ontology("http://www.test.org/test.owl")
    
    with o:
      class C(Thing): pass
      class D(Thing): pass
      class E(Thing): pass
      
      C.equivalent_to.append(D)
      D.equivalent_to.append(E)
      
    destroy_entity(D)
    
    assert list(C.equivalent_to.indirect()) == []
    assert list(E.equivalent_to.indirect()) == []
    assert len(w.graph) == 5 + nb
    
  def test_destroy_12(self):
    w = self.new_world()
    nb = len(w.graph)
    o = w.get_ontology("http://www.test.org/test.owl")
    
    with o:
      class C(Thing): pass
      class D(Thing): pass
      class p(ObjectProperty): pass
      
      D.is_a.append(p.some(C))
      
    destroy_entity(C)
    
    assert len(w.graph) == 4 + nb
    
  def test_destroy_13(self):
    w = self.new_world()
    nb = len(w.graph)
    o = w.get_ontology("http://www.test.org/test.owl")
    
    with o:
      class C(Thing): pass
      class D(Thing): pass
      class p(ObjectProperty): pass
      class q(ObjectProperty): pass
      
      D.is_a.append(p.some(q.only(Not(C))))
      
    destroy_entity(C)
    
    assert D.is_a == [Thing]
    assert len(w.graph) == 5 + nb
    
  def test_destroy_14(self):
    w = self.new_world()
    nb = len(w.graph)
    o = w.get_ontology("http://www.test.org/test.owl")
    
    with o:
      class C(Thing): pass
      class p(ObjectProperty): pass
      c1 = C()
      C.is_a.append(p.value(c1))
      
    destroy_entity(c1)
    
    assert C.is_a == [Thing]
    assert len(w.graph) == 4 + nb
    
  def test_destroy_15(self):
    w = self.new_world()
    nb = len(w.graph)
    o = w.get_ontology("http://www.test.org/test.owl")
    
    with o:
      class C(Thing): pass
      class p(ObjectProperty): pass
      c1 = C()
      C.is_a.append(p.value(c1))
      c1.p = [c1]
      
    destroy_entity(p)
    
    assert C.is_a == [Thing]
    assert getattr(c1, "p", None) == None
    assert len(w.graph) == 5 + nb
    
  def test_destroy_16(self):
    w = self.new_world()
    o = w.get_ontology("http://www.test.org/test.owl")
    
    with o:
      class C(Thing): pass
      class p(AnnotationProperty): pass
      
    destroy_entity(p)
    
  def test_destroy_17(self):
    w = self.new_world()
    o = w.get_ontology("http://www.test.org/test.owl")
    
    with o:
      class C(Thing): pass
      class p(Thing >> Thing): pass
      c1 = C()
      c2 = C()
      c1.p = [c2]

    undestroy = destroy_entity(c2, undoable = True)
    assert c1.p == []
    assert o.c2 is None
    
    undestroy()
    assert o.c2 is not None
    assert o.c2 is c2
    assert c1.p == [c2]
    
  def test_destroy_18(self):
    w = self.new_world()
    o = w.get_ontology("http://www.test.org/test.owl")
    
    with o:
      class C(Thing): pass
      c1 = C("c1")
      
      destroy_entity(c1, undoable = 1)
      
      c1 = C()
      c1.name = "c1"
    
  def test_destroy_19(self):
    w = self.new_world()
    o = w.get_ontology("http://www.test.org/test.owl")
    
    with o:
      class p(Thing >> Thing): pass
      class C(Thing): pass
      C.is_a.append(p.some(Thing))
      
    destroy_entity(C)
    assert w.graph.execute("SELECT COUNT() FROM quads WHERE s<0").fetchone()[0] == 0
    
  def test_destroy_20(self):
    w = self.new_world()
    o = w.get_ontology("http://www.test.org/test.owl")
    
    with o:
      class p(Thing >> Thing): pass
      class C(Thing): pass
      class D(Thing): pass
      C.is_a.append(p.some(Thing))
      w.graph.execute("INSERT INTO objs VALUES (?,?,?,?)", (1, D.storid, 9, -1))
      
    destroy_entity(C)
    assert w.graph.execute("SELECT COUNT() FROM quads WHERE s<0").fetchone()[0] != 0
    
  def test_destroy_21(self):
    w = self.new_world()
    o = w.get_ontology("http://www.test.org/test.owl")
    
    with o:
      class p(Thing >> float): pass
      class C(Thing): pass
      class D(Thing): equivalent_to = [ C & (p >= 5.0) ]
      
    destroy_entity(p)
    assert w.graph.execute("SELECT COUNT() FROM quads WHERE s<0").fetchone()[0] == 0
    
  def test_destroy_22(self):
    w = self.new_world()
    o = w.get_ontology("http://www.test.org/test.owl")
    
    with o:
      class p(Thing >> float): pass
      class C(Thing): pass
      class D(Thing): equivalent_to = [ C & (p >= 5.0) ]
      
    destroy_entity(D)
    assert w.graph.execute("SELECT COUNT() FROM quads WHERE s<0").fetchone()[0] == 0
    
  def test_destroy_23(self):
    w = self.new_world()
    o = w.get_ontology("http://www.test.org/test.owl")
    
    with o:
      class p(Thing >> float): pass
      class C(Thing): pass
      class D(Thing): equivalent_to = [ (p >= 5.0) ]
      
    D.equivalent_to = []
    assert w.graph.execute("SELECT COUNT() FROM quads WHERE s<0").fetchone()[0] == 0
    
  def test_destroy_24(self):
    w = self.new_world()
    o = w.get_ontology("http://www.test.org/test.owl")
    
    with o:
      class p(Thing >> float): pass
      class C(Thing): pass
      class D(Thing): equivalent_to = [ C & (p >= 5.0) ]
      
    destroy_entity(C)
    assert w.graph.execute("SELECT COUNT() FROM quads WHERE s<0").fetchone()[0] == 0
    
  def test_destroy_25(self):
    w  = self.new_world()
    o1 = w.get_ontology("http://www.test.org/test1.owl")
    o2 = w.get_ontology("http://www.test.org/test2.owl")
    
    with o1:
      class r(Thing >> Thing): pass
      class p(Thing >> int): pass
      class C(Thing): pass
      c1 = C(p = [1])
      c2 = C()
      
    with o2:
      c1.p.append(2)
      c2.p.append(2)
      c3 = C("c3", p = [3])
      
    del c2
    assert c1.p == [1, 2]
    
    o2.destroy(True)
    
    assert c1.p == [1]
    
  def test_destroy_26(self):
    w  = self.new_world()
    o1 = w.get_ontology("http://test.org/test")

    with o1:
      class B(Thing): pass
      class C(Thing): pass

      class b_to_c(ObjectProperty): pass
      class c_to_b(ObjectProperty): inverse_property = b_to_c
      
      b = B()
      c = C()
      
    b.b_to_c = [c]
    assert c.c_to_b == [b]
    
    destroy_entity(b)
    
    assert c.c_to_b == []  # asserts to False
    
    
    
  def test_observe_1(self):
    import owlready2.observe

    w = self.new_world()
    onto = w.get_ontology("http://test.org/t.owl")
    
    with onto:
      class C(Thing): pass
      class D(Thing): pass
      class p(C >> str, FunctionalProperty): pass
      class ps(C >> int): pass
      
    c = C()

    before_func = onto._add_obj_triple_raw_spo
    
    listened = "\n"
    def listener(o, ps):
      nonlocal listened
      listened += "%s %s\n" % (w._unabbreviate(o), " ".join(w._unabbreviate(p) for p in sorted(ps)))
    owlready2.observe.start_observing(onto)
    owlready2.observe.observe(c, listener)
    
    c.ps = [1, 2, 3]
    
    c.ps.remove(2)
    c.ps.append(4)
    
    c.p = "test"
    
    c.is_a = [D]
    
    owlready2.observe.unobserve(c, listener)
    
    c.ps = [0]

    assert listened == """
http://test.org/t.owl#c1 http://test.org/t.owl#ps
http://test.org/t.owl#c1 http://test.org/t.owl#ps
http://test.org/t.owl#c1 http://test.org/t.owl#ps
http://test.org/t.owl#c1 http://test.org/t.owl#ps
http://test.org/t.owl#c1 http://test.org/t.owl#ps
http://test.org/t.owl#c1 http://test.org/t.owl#p
http://test.org/t.owl#c1 http://www.w3.org/1999/02/22-rdf-syntax-ns#type
http://test.org/t.owl#c1 http://www.w3.org/1999/02/22-rdf-syntax-ns#type
"""
    
    owlready2.observe.stop_observing(onto)
    assert onto._add_obj_triple_raw_spo == before_func
    
  def disabled_test_observe_4(self):
    import owlready2.observe
    
    w = self.new_world()
    onto = w.get_ontology("http://test.org/t.owl")
    
    with onto:
      class C(Thing): pass
      
    c1 = C()
    c2 = C()
    
    listened = []
    def listener(o, p):
      listened.append((o, p))
    l = owlready2.observe.InstancesOfClass(C, use_observe = True)
    owlready2.observe.start_observing(onto)
    owlready2.observe.observe(l, listener)
    
    c3 = C()

    assert listened[0][0] is l
    assert listened[0][1] == "Inverse(http://www.w3.org/1999/02/22-rdf-syntax-ns#type)"
    assert list(listened[0][2]) == [c1, c2, c3]
    assert list(listened[0][3]) == [c1, c2]
    
    assert list(l) == [c1, c2, c3]
    
  def disabled_test_observe_5(self):
    import owlready2.observe
    
    w = self.new_world()
    onto = w.get_ontology("http://test.org/t.owl")
    
    with onto:
      class C(Thing): pass
      
    c1 = C()
    c2 = C()
    
    listened = []
    def listener(o, p, new, old):
      listened.append((o, p, new, old))
    l = owlready2.observe.InstancesOfClass(C, use_observe = True)
    len(l)
    owlready2.observe.start_observing(onto)
    owlready2.observe.observe(l, listener)
    
    c3 = C()

    assert listened[0][0] is l
    assert listened[0][1] == "Inverse(http://www.w3.org/1999/02/22-rdf-syntax-ns#type)"
    assert list(listened[0][2]) == [c1, c2, c3]
    assert list(listened[0][3]) == [c1, c2]
    
    assert list(l) == [c1, c2, c3]
    
  def disabled_test_observe_6(self):
    import owlready2.observe
    
    w = self.new_world()
    onto = w.get_ontology("http://test.org/t.owl")
    
    with onto:
      class C(Thing): pass
      
    c1 = C()
    c2 = C()
    
    listened = []
    
    def listener(o, diffs):
      listened.extend(diffs)
    l = owlready2.observe.InstancesOfClass(C, use_observe = True)
    owlready2.observe.start_observing(onto)
    owlready2.observe.observe(l, listener, None, True)
    
    c3 = C()
    c4 = C()
    
    assert listened == []
    owlready2.observe.emit_collapsed_changes()
    
    assert listened[0][0] == "Inverse(http://www.w3.org/1999/02/22-rdf-syntax-ns#type)"
    assert list(listened[0][1]) == [c1, c2, c3, c4]
    assert list(listened[0][2]) == [c1, c2]
    
    assert list(l) == [c1, c2, c3, c4]
    
  def test_observe_7(self):
    import owlready2.observe
    
    w = self.new_world()
    onto = w.get_ontology("http://test.org/t.owl")
    
    with onto:
      class C(Thing): pass
      c1 = C()
      c2 = C()
      c2.label.en = "AAA ?"
      c2.label.fr = "Paracétamol"
      c3 = C()
      c3.label.en = "Asprine"
      c3.label.fr = "Asprin"
      
    l = owlready2.observe.InstancesOfClass(C, order_by = "label", lang = "fr", use_observe = True)
    assert list(l) == [c1, c3, c2]
    
    l = owlready2.observe.InstancesOfClass(C, order_by = "label", lang = "en", use_observe = True)
    assert list(l) == [c1, c2, c3]
    
  def test_observe_8(self):
    import owlready2.observe
    
    w = self.new_world()
    onto = w.get_ontology("http://test.org/t.owl")
    
    with onto:
      class C(Thing): pass
      class p(Thing >> Thing): pass
      class i(Thing >> Thing): inverse = p
      c1 = C()
      c2 = C()
      
    listened = "\n"
    def listener(o, ps):
      nonlocal listened
      listened += "%s %s\n" % (w._unabbreviate(o), " ".join(w._unabbreviate(p) for p in sorted(ps)))
    owlready2.observe.start_observing(onto)
    owlready2.observe.observe(c2, listener)
    
    c1.p.append(c2)

    assert listened == """\nhttp://test.org/t.owl#c2 http://test.org/t.owl#i\n"""
    
  def test_observe_9(self):
    import owlready2.observe
    
    w = self.new_world()
    onto = w.get_ontology("http://test.org/t.owl")
    
    with onto:
      class C(Thing): pass
      class p(C >> int): pass
      c1 = C(p = [1])
      
    listened = "\n"
    def unabbreviate(o):
      if isinstance(o, tuple):
        o2 = [None] * 3
        o2[0] = unabbreviate(o[0])
        if not o[1] is None: o2[1] = w._unabbreviate(o[1])
        if not o[2] is None: o2[2] = w._to_python(o[2], o[3])
        return tuple(o2)
      else:
        return w._unabbreviate(o)
    def listener(o, ps):
      nonlocal listened
      o2 = unabbreviate(o)
      listened += "(%s) %s\n" % (" ".join(str(i) for i in o2), " ".join(w._unabbreviate(p) for p in sorted(ps)))
    owlready2.observe.observe((c1, p, 1), listener)
    
    comment[c1, p, 1] = ["ok"]
    assert listened == '\n(http://test.org/t.owl#c1 http://test.org/t.owl#p 1) http://www.w3.org/2000/01/rdf-schema#comment\n'
    
    listened = "\n"
    comment[c1, p, 1].append(C)
    assert listened == '\n(http://test.org/t.owl#c1 http://test.org/t.owl#p 1) http://www.w3.org/2000/01/rdf-schema#comment\n'
    
    listened = "\n"
    comment[c1, p, 1] = []
    assert listened == '\n(http://test.org/t.owl#c1 http://test.org/t.owl#p 1) http://www.w3.org/2000/01/rdf-schema#comment\n(http://test.org/t.owl#c1 http://test.org/t.owl#p 1) http://www.w3.org/2000/01/rdf-schema#comment\n'
    
    owlready2.observe.unobserve((c1, p, 1), listener)
    
    listened = "\n"
    comment[c1, p, 1].append("x")
    assert listened == """\n"""
    
    owlready2.observe.observe((c1, None, None), listener)
    
    listened = "\n"
    label[c1, p, 1].append("ok")
    assert listened == '\n(http://test.org/t.owl#c1 None None) http://test.org/t.owl#p\n'
    
    owlready2.observe.observe(((c1, p, 1), label, "ok"), listener)
    
    listened = "\n"
    comment[AnnotatedRelation(c1, p, 1), label, "ok"] = ["ok2"]
    assert listened == """\n(('http://test.org/t.owl#c1', 'http://test.org/t.owl#p', 1) http://www.w3.org/2000/01/rdf-schema#label ok) http://www.w3.org/2000/01/rdf-schema#comment\n"""
    
            
  def test_observe_10(self):
    import owlready2.observe
    
    w = self.new_world()
    onto = w.get_ontology("http://test.org/t.owl")
    owlready2.observe.start_observing(w)
    
    with onto:
      class C(Thing): pass
      class p(C >> int): pass
      class q(C >> int): pass
      c1 = C(p = [1])
      
    listened = "\n"
    def listener(o, ps):
      nonlocal listened
      listened += "%s %s\n" % (w._unabbreviate(o), " ".join(w._unabbreviate(p) for p in sorted(ps)))
    owlready2.observe.observe(c1, listener)
    
    c1.p.append(2)
    assert listened == """\nhttp://test.org/t.owl#c1 http://test.org/t.owl#p\n"""
    
    c1.q.append(3)
    assert listened == """\nhttp://test.org/t.owl#c1 http://test.org/t.owl#p\nhttp://test.org/t.owl#c1 http://test.org/t.owl#q\n"""
    
    listened = "\n"
    
    with owlready2.observe.coalesced_observations:
      c1.p.append(4)
      c1.q.append(5)
      c1.q.append(6)
      
      assert listened == """\n"""
      
    assert listened == """\nhttp://test.org/t.owl#c1 http://test.org/t.owl#p http://test.org/t.owl#q\n"""
    
    
    
    
  def test_fts_1(self):
    world = self.new_world()
    onto = world.get_ontology("http://test.org/t.owl")
    with onto:
      class C(Thing): pass
      
      c1 = C(label = ["Maladies du rein"])
      c2 = C(label = ["Cander du rein", "Cancer rénal"])
      c3 = C(label = ["Insuffisance rénale"])
      c4 = C(label = ["Insuffisance cardiaque"])
      
    world.full_text_search_properties.append(label)
    
    # Normal search
    assert set(world.search(label = "Maladies du rein")) == { c1 }
    assert set(world.search(label = "rein")) == set()
    
    # FTS search
    assert set(world.search(label = FTS("rein"))) == { c1, c2 }
    assert set(world.search(label = FTS("rénal"))) == { c2 }
    assert set(world.search(label = FTS("rénale"))) == { c3 }
    assert set(world.search(label = FTS("rénal*"))) == { c2, c3 }
    assert set(world.search(label = FTS("insuffisance*"))) == { c3, c4 }
    assert set(world.search(label = FTS("maladies rein"))) == { c1 }
    
    world.full_text_search_properties.remove(label)
    
  def test_fts_2(self):
    world = self.new_world()
    onto = world.get_ontology("http://test.org/t.owl")
    with onto:
      class C(Thing): pass
      class p(C >> str): pass
      
    world.full_text_search_properties.append(p)
    
    c1 = C(p = ["Maladies du rein"])
    c2 = C(p = ["Cander du rein", "Cancer rénal"])
    c3 = C(p = ["Insuffisance rénale"])
    c4 = C(p = ["Insuffisance cardiaque"])
    
    # Normal search
    assert set(world.search(p = "Maladies du rein")) == { c1 }
    assert set(world.search(p = "rein")) == set()
    
    # FTS search
    assert set(world.search(p = FTS("rein"))) == { c1, c2 }
    assert set(world.search(p = FTS("rénal"))) == { c2 }
    assert set(world.search(p = FTS("rénale"))) == { c3 }
    assert set(world.search(p = FTS("rénal*"))) == { c2, c3 }
    assert set(world.search(p = FTS("insuffisance*"))) == { c3, c4 }
    assert set(world.search(p = FTS("maladies rein"))) == { c1 }
    
    destroy_entity(c2)
    assert set(world.search(p = FTS("rénal*"))) == { c3 }
    
    c4.p = ["Insuffisance hépatique"]
    
    assert set(world.search(p = FTS("insuffisance cardi*"))) == set()
    assert set(world.search(p = FTS("insuffisance"))) == { c3, c4 }
    assert set(world.search(p = FTS("hépatique"))) == { c4 }
    
    world.full_text_search_properties.remove(p)

  def test_fts_3(self):
    tmp   = self.new_tmp_file()
    world = self.new_world()
    world.set_backend(filename = tmp)
    onto = world.get_ontology("http://test.org/t.owl#")
    with onto:
      class C(Thing): pass
      class p(C >> str): pass
      
    world.full_text_search_properties.append(p)
    world.full_text_search_properties.append(label)
    
    C("c1", p = ["Maladies du rein"])
    C("c2", p = ["Cander du rein", "Cancer rénal"])
    C("c3", label = ["Insuffisance rénale"])
    C("c4", label = ["Insuffisance cardiaque"])

    S = p.storid
    
    world.save()
    world.close()
    world = None
    
    world2 = self.new_world()
    world2.set_backend(filename = tmp)
    assert set(world2.full_text_search_properties) == { world2["http://test.org/t.owl#p"], label }
    
    assert set(world2.search(p = FTS("rein"))) == { world2["http://test.org/t.owl#c1"], world2["http://test.org/t.owl#c2"] }
    assert set(world2.search(label = FTS("insuffisance*"))) == { world2["http://test.org/t.owl#c3"], world2["http://test.org/t.owl#c4"] }
    
  def test_fts_4(self):
    world = self.new_world()
    onto = world.get_ontology("http://test.org/t.owl#")
    with onto:
      class C(Thing): pass
      class p(C >> str): pass
      class q(C >> str): pass
      
    world.full_text_search_properties.append(p)
    
    c1 = C(p = ["Maladies du rein"])
    c2 = C(q = ["Maladies du rein"])
    
    assert set(world.search(p = FTS("rein"))) == { c1 }
    
    destroy_entity(c1)
    
    assert set(world.search(p = FTS("rein"))) == set()
    
  def test_fts_5(self):
    world = self.new_world()
    onto = world.get_ontology("http://test.org/t.owl#")
    with onto:
      class C(Thing): pass
      class p(C >> str, FunctionalProperty): pass
      
    world.full_text_search_properties.append(p)
    
    c1 = C(p = "Maladies du coeur")
    c1.p = "Maladies du rein"
    
    assert set(world.search(p = FTS("rein"))) == { c1 }
    
  def test_fts_6(self):
    world = self.new_world()
    onto = world.get_ontology("http://test.org/t.owl#")
    with onto:
      class C(Thing): pass
      
    c1 = C(label = [locstr("Maladies du coeur", "fr"), locstr("Heart disorders", "en")])
    
    world.full_text_search_properties.append(label)
    
    c2 = C(label = [locstr("Maladies du rein", "fr"), locstr("Kidney disorders", "en")])
    
    assert set(world.search(label = FTS("coeur")))  == { c1 }
    assert set(world.search(label = FTS("heart")))  == { c1 }
    assert set(world.search(label = FTS("rein")))   == { c2 }
    assert set(world.search(label = FTS("kidney"))) == { c2 }
    
    assert set(world.search(label = FTS("coeur", "fr"))) == { c1 }
    assert set(world.search(label = FTS("coeur", "en"))) == set()
    assert set(world.search(label = FTS("heart", "fr"))) == set()
    assert set(world.search(label = FTS("heart", "en"))) == { c1 }

    
  def test_swrl_1(self):
    world = self.new_world()
    onto = world.get_ontology("http://test.org/t.owl#")
    with onto:
      class Person(Thing): pass
      class size  (Person >> float, FunctionalProperty): pass
      class weight(Person >> float, FunctionalProperty): pass
      
    rules = [
      """Person(?p), size(?p, ?s) -> weight(?p, ?s)""",
      """Person(?p), Person(?q), size(?p, ?s), SameAs(?p, ?s) -> size(?q, ?s)""",
      """Person(?p), size(?p, ?s), add(?r, ?s, 2) -> weight(?q, ?r)""",
      """Person(?p), size(?p, ?s), add(?r, ?s, 2.0) -> weight(?q, ?r)""",
      """Person(?p), size(?p, ?s), add(?r, ?s, ?s) -> weight(?q, ?r)""",
      """Person(?p), size(?p, ?s), add(?r, ?s, ?s) -> weight(?q, 'abc')""",
      """Person(?p), size(?p, ?s), int(?s) -> weight(?q, 'abc')""",
      """Person(?p), size(?p, ?s), decimal(?s) -> weight(?q, 'abc')""",
    ]
    for rule in rules:
      with onto:
        imp = Imp().set_as_rule(rule)
        assert rule == str(imp)
        
    with onto:
      imp = Imp().set_as_rule("""http://test.org/t.owl#Person(?p), http://test.org/t.owl#size(?p, ?s) -> http://test.org/t.owl#weight(?p, ?s)""")
      assert str(imp) == """Person(?p), size(?p, ?s) -> weight(?p, ?s)"""

  def test_swrl_2(self):
    world = self.new_world()
    onto = world.get_ontology("http://test.org/t.owl#")
    with onto:
      class Person(Thing): pass
      class size  (Person >> float, FunctionalProperty): pass
      class weight(Person >> float, FunctionalProperty): pass
      class imc   (Person >> float, FunctionalProperty): pass
      Imp().set_as_rule("""Person(?x), weight(?x, ?p), size(?x, ?t), divide(?i, ?p, ?tt), multiply(?tt, ?t, ?t) -> imc(?x, ?i)""")
      
      p1 = Person(size = 2.0, weight = 100.0)

    sync_reasoner_pellet(world, infer_property_values = True, infer_data_property_values = True, debug = 0)
    
    assert p1.imc == 25.0
    
  def test_swrl_3(self):
    world = self.new_world()
    onto_perso = world.get_ontology("http://test.org/personne2.owl#")
    
    with onto_perso:
      class Personne(Thing): pass
      class poids (Personne >> float, FunctionalProperty): pass
      class taille(Personne >> float, FunctionalProperty): pass
      class imc   (Personne >> float, FunctionalProperty): pass
      
    with onto_perso:
      imp = Imp()
      imp.set_as_rule("Personne(?x), poids(?x, ?p), taille(?x, ?t),multiply(?t2, ?t, ?t), divide(?i, ?p, ?t2)-> imc(?x, ?i)")
      
    with onto_perso:
      class Obèse(Personne):
        equivalent_to = [Personne & (imc >= 30.0)]

    p1 = Personne(taille = 1.7, poids = 65.0)
    p2 = Personne(taille = 1.7, poids = 90.0)
    
    sync_reasoner_pellet(world, infer_property_values = True, infer_data_property_values = True, debug = 0)
    
    assert 22 < p1.imc < 23
    
  def test_swrl_4(self):
    world = self.new_world()
    onto = world.get_ontology("http://test.org/t.owl#")
    with onto:
      class C(Thing): pass
      class p1(C >> C): pass
      class p2(C >> C): pass
      Imp().set_as_rule("""p1(?x, ?y) -> p2(?x, ?y)""")
      
      c1 = C()
      c2 = C(p1 = [c1])
      
    sync_reasoner_pellet(world, infer_property_values = True, infer_data_property_values = True, debug = 0)
    
    assert c2.p2 == [c1]
    
  def test_swrl_5(self):
    world = self.new_world()
    onto = world.get_ontology("http://test.org/t.owl#")
    with onto:
      class C(Thing): pass
      class p(C >> float): pass
      Imp().set_as_rule("""C(?x) -> p(?x, 1.0)""")
      
      c = C()
      
    sync_reasoner_pellet(world, infer_property_values = True, infer_data_property_values = True, debug = 0)
    
    assert c.p == [1.0]
    
  def test_swrl_6(self):
    world = self.new_world()
    onto = world.get_ontology("http://test.org/t.owl#")
    with onto:
      class C(Thing): pass
      class R(Thing): pass
      class p(C >> str): pass
      Imp().set_as_rule("""p(?x, ?y), matches(?y, "ab.*") -> R(?x)""")
      
      c1 = C(p = ["abcde"])
      c2 = C(p = ["abe"])
      c3 = C(p = ["bcde"])
      c4 = C(p = [])

    sync_reasoner_pellet(world, infer_property_values = True, infer_data_property_values = True, debug = 0)
    
    assert R in c1.is_a
    assert R in c2.is_a
    assert not R in c3.is_a
    assert not R in c4.is_a

  def test_swrl_7(self):
    world = self.new_world()
    onto = world.get_ontology("http://test.org/t.owl#")
    
    with onto:
      class C(Thing): pass
      class D(Thing): pass
      
      r1 = Imp()
      r1.set_as_rule("""C(?x), C(?y) -> D(?x)""")
      
      r2 = Imp()
      r2.set_as_rule("""C(?y) -> D(?y)""")
      
    assert len(list(world.variables())) == 2
    
    destroy_entity(r1)

    assert len(list(world.variables())) == 1
    
    destroy_entity(r2)
    
    assert len(list(world.variables())) == 0

  def test_swrl_8(self):
    world = self.new_world()
    onto = world.get_ontology("http://test.org/t.owl#")
    
    with onto:
      class Cé(Thing): pass
      class D(Thing): pass

      c = Cé()
      
      r1 = Imp()
      r1.set_as_rule("""Cé(?x) -> D(?x)""")

    sync_reasoner_pellet(world, debug = 0)
    
    assert set(c.is_a) == { Cé, D }
    
    
  def test_dl_render_1(self):
    world = self.new_world()
    n = world.get_ontology("http://www.semanticweb.org/jiba/ontologies/2017/2/test_reasoning.owl").load()
    from owlready2.dl_render import dl_render_class_str
    assert set(dl_render_class_str(n.Cheese).split("\n")) == set("""Cheese ⊑ Topping
Cheese ⊓ Meat ⊑ ⊥
Cheese ⊓ Vegetable ⊑ ⊥""".split("\n"))


  def test_dc_1(self):
    world = self.new_world()
    onto  = world.get_ontology("http://www.test.org/onto.owl")
    onto.imported_ontologies.append(world.get_ontology("http://purl.org/dc/elements/1.1").load())
    with onto:
      class C(Thing): pass
      C.creator.append("JBL")
      C.coverage.append("test")


  def test_parallel_1(self):
    q  = self.new_tmp_file()
    world = World(filename = q, exclusive = False)
    world.save()
    world.close()
    
    py = self.new_tmp_file()
    f = open(py, "w")
    f.write("""
from owlready2 import *

world = World(filename = "%s", exclusive = False)

onto = world.get_ontology("http://test.org/onto.owl")

with onto:
  class Drug(Thing): pass
  class p(Thing >> Thing): pass
    
  for i in range(200):
    drug = onto.Drug(label = ["eee"])
    drug.is_a.append(p.some(Drug))
    
  world.save()
""" % q)
    f.close()

    NB = 5
    ps = []
    rs = []
    for i in range(NB): ps.append(subprocess.Popen([sys.executable, py]))
    for p in ps: rs.append(p.wait())
    for r in rs: assert r == 0
    
    world = World(filename = q, exclusive = False)
    s = world.graph.execute("SELECT MAX(storid) FROM resources").fetchone()[0]
    assert s == 300 + 4 + 200 * NB
    
  def test_parallel_2(self):
    q  = self.new_tmp_file()
    world = World(filename = q, exclusive = False)
    world.save()
    world.close()
    
    py = self.new_tmp_file()
    f = open(py, "w")
    f.write("""
import os, time
from owlready2 import *

world = World(filename = "%s", exclusive = False)

onto = world.get_ontology("http://test.org/onto.owl")

with onto:
  class Drug(Thing): pass
  class p(Thing >> Thing): pass
  world.save()
    
for i in range(500):
  with onto:
    drug = onto.Drug(label = ["lab" + str(os.getpid())])
    drug.is_a.append(p.some(Drug))
    
    world.save()
  time.sleep(0.0001)

""" % q)
    f.close()

    NB = 5
    ps = []
    rs = []
    for i in range(NB): ps.append(subprocess.Popen([sys.executable, py]))
    for p in ps: rs.append(p.wait())
    for r in rs: assert r == 0
    
    world = World(filename = q, exclusive = False)
    s = world.graph.execute("SELECT MAX(storid) FROM resources").fetchone()[0]
    assert s == 300 + 4 + 500 * NB
    
    onto = world.get_ontology("http://test.org/onto.owl")
    labels = [onto["drug%s" % (i + 1)].label.first() for i in range(500)]
    assert len(set(labels)) > 1
    
  def test_parallel_3(self):
    q  = self.new_tmp_file()
    world = World(filename = q, exclusive = False)
    
    onto = world.get_ontology("http://test.org/onto.owl")
    world.save()
    
    def do_test():
      with onto:
        class Drug(Thing): pass
        class p(Thing >> Thing): pass
        
        for i in range(1000):
          drug = onto.Drug(label = ["eee"])
          drug.is_a.append(p.some(Drug))
          
        world.save()
        
    NB = 5
    ps = []
    for i in range(NB): ps.append(multiprocessing.Process(target = do_test, args = ()))
    for p in ps: p.start()
    for p in ps: p.join()
    for p in ps: assert p.exitcode == 0
    
    s = world.graph.execute("SELECT MAX(storid) FROM resources").fetchone()[0]
    assert s == 300 + 4 + 1000 * NB

  def test_parallel_4(self):
    q  = self.new_tmp_file()
    world = World(filename = q, exclusive = False)
    
    onto = world.get_ontology("http://test.org/onto.owl")
    world.save()
    
    def do_test(label):
      with onto:
        class Drug(Thing): pass
        class p(Thing >> Thing): pass
        world.save()
        
      for i in range(500):
        with onto:
          drug = onto.Drug(label = [label])
          drug.is_a.append(p.some(Drug))
        world.save()
        time.sleep(0.0001)
    NB = 2
    ps = []
    for i in range(NB): ps.append(multiprocessing.Process(target = do_test, args = ("lab%s" % i,)))
    for p in ps: p.start()
    for p in ps: p.join()
    for p in ps: assert p.exitcode == 0
    
    s = world.graph.execute("SELECT MAX(storid) FROM resources").fetchone()[0]
    assert s == 300 + 4 + 500 * NB
    
    labels = [onto["drug%s" % (i + 1)].label.first() for i in range(500)]
    assert len(set(labels)) > 1
    
  def test_parallel_5(self):
    q  = self.new_tmp_file()
    world = World(filename = q, exclusive = False)
    world.save()
    
    def do_test():
      onto = world.get_ontology("http://test.org/onto.owl")
      
      with onto:
        class Drug(Thing): pass
        class p(Thing >> Thing): pass
        
        for i in range(200):
          drug = onto.Drug(label = "eee")
          drug.is_a.append(p.some(Drug))
          
      world.save()
      
    NB = 5
    ps = []
    for i in range(NB): ps.append(multiprocessing.Process(target = do_test, args = ()))
    for p in ps: p.start()
    for p in ps: p.join()
    for p in ps: assert p.exitcode == 0
    
    s = world.graph.execute("SELECT MAX(storid) FROM resources").fetchone()[0]
    assert s == 300 + 4 + 200 * NB
    
  def test_parallel_6(self):
    world = self.new_world(exclusive = False, enable_thread_parallelism = True)
    onto  = world.get_ontology("http://test.org/onto.owl")
    with onto:
      class C(Thing): pass
      for i in range(1000): c = C(label = "C item %s" % (i + 1))
    world.save()
    
    qs = []
    for i in range(10):
      for j in range(10):
        q = world.prepare_sparql("""SELECT ?x { ?x rdfs:label ?l . FILTER(LIKE(?l, "C item %s%%%s")) }""" % (i, j))
        qs.append(q)
        
    for q in qs:list(q.execute())
    
    import gevent.hub
    gevent_spawn = gevent.hub.get_hub().threadpool.apply_async
    
    r = [list(i) for i in owlready2.sparql.execute_many(onto, qs, [[]] * len(qs), gevent_spawn)]
    
    #qs = qs * 9
    
    r1 = []
    t = time.time()
    for q in qs: r1.append(list(q.execute()))
    t_mono = time.time() - t
    
    t = time.time()
    r2 = [list(i) for i in owlready2.sparql.execute_many(onto, qs, [[]] * len(qs))]
    t_para = time.time() - t
    #print("%s s VS %s s with thread parallelization" % (t_mono, t_para))

    t = time.time()
    r2 = [list(i) for i in owlready2.sparql.execute_many(onto, qs, [[]] * len(qs), gevent_spawn)]
    t_para = time.time() - t
    #print("%s s VS %s s with GEvent threadpool parallelization" % (t_mono, t_para))
    
    assert r1 == r2
    assert t_para < t_mono
    
  def xxx_test_parallel_7(self):
    world = World(filename = "/home/jiba/tmp/pym.sqlite3", exclusive = False, enable_thread_parallelism = True)
    #q = world.prepare_sparql("""SELECT (COUNT(?x) AS ?nb) { ?x a owl:Class . }""")
    q0 = world.prepare_sparql("""SELECT (COUNT(?x) AS ?nb) { ?x a* owl:ObjectProperty . }""")
    q1 = world.prepare_sparql("""SELECT (COUNT(?x) AS ?nb) { ?x a* owl:AnnotationProperty . }""")
    q2 = world.prepare_sparql("""SELECT (COUNT(?x) AS ?nb) { ?x a* owl:DatatypeProperty . }""")
    
    def task0(x = None): return list(q0.execute())
    
    def task0_para(x = None): return list(q0.execute(spawn = True))
    
    def task1(x = None): return list(q1.execute())
    
    def task1_para(x = None): return list(q1.execute(spawn = True))
    
    def task2(x = None): return list(q2.execute())
    
    def task2_para(x = None): return list(q2.execute(spawn = True))
    
    def task3(x = None):
      for i in range(150000): 2+3
      
    import gevent
    t = time.time()
    g1 = gevent.spawn(task1)
    g2 = gevent.spawn(task3)
    r1 = g1.get()
    r2 = g2.get()
    t_mono = time.time() - t
    
    gevent.spawn(task0_para).join()
    
    t = time.time()
    g1 = gevent.spawn(task1_para)
    g2 = gevent.spawn(task3)
    r1_para = g1.get()
    r2_para = g2.get()
    t_para = time.time() - t
    print("%s s VS %s s with thread parallelization" % (t_mono, t_para))

    import gevent.hub
    gevent_spawn = gevent.hub.get_hub().threadpool.apply_async
    def task1_para(x = None): return list(q1.execute(spawn = gevent_spawn))

    g1 = gevent.spawn(task1_para)
    g2 = gevent.spawn(task3)
    r1_para = g1.get()
    r2_para = g2.get()
    
    t = time.time()
    g1 = gevent.spawn(task1_para)
    g2 = gevent.spawn(task3)
    r1_para = g1.get()
    r2_para = g2.get()
    t_para = time.time() - t
    print("%s s VS %s s with GEvent threadpool parallelization" % (t_mono, t_para))
    
    assert r1_para == r1
    #assert t_para < t_mono
    
    
class Paper(BaseTest, unittest.TestCase):
  def test_reasoning_paper_ic2017(self):
    world = self.new_world()
    onto = world.get_ontology("http://www.lesfleursdunormal.fr/static/_downloads/paper_ic2017.owl")
    
    with onto:
      class Origine(Thing): pass
      class Acquise(Origine): pass
      class Constitutionnelle(Origine): pass
      Origine.is_a.append(Acquise | Constitutionnelle)
      AllDisjoint([Acquise, Constitutionnelle])
      
      
      class aPourOrigine(ObjectProperty): pass
      
      class Maladie(Thing):
        is_a = [aPourOrigine.some(Origine),
                aPourOrigine.only(Origine)]
        
      class MaladieHémorragique(Maladie): pass
      
      class MHAcquise(MaladieHémorragique):
        equivalent_to = [MaladieHémorragique & aPourOrigine.some(Acquise)]
        
      class MHConsti(MaladieHémorragique):
        equivalent_to = [MaladieHémorragique & aPourOrigine.some(Constitutionnelle)]
        
        
      class Médicament(Thing): pass
      class ContreIndication(Thing): pass
      
      class aPourContreIndication(ObjectProperty): pass
      class contreIndicationDe(ObjectProperty):
        inverse_property = aPourContreIndication
        
      class aPourMaladie(ObjectProperty): pass
      class maladieDe(ObjectProperty):
        inverse_property = aPourMaladie
        
      ciA = ContreIndication("ciA")
      ciA.is_a.append(aPourMaladie.some(MHAcquise))
      ciA.is_a.append(aPourMaladie.only(MHAcquise))
      ciC = ContreIndication("ciC")
      ciC.is_a.append(aPourMaladie.some(MHConsti))
      ciC.is_a.append(aPourMaladie.only(MHConsti))
      
      MHAcquise.is_a.append(maladieDe.value(ciA))
      MHConsti .is_a.append(maladieDe.value(ciC))
      
      m = Médicament("m")
      m.aPourContreIndication = [ciA, ciC]
      m.is_a.append(aPourContreIndication.only(OneOf([ciA, ciC])))
      
      
      class Maladie_CI_avec_m(Maladie):
        equivalent_to = [Maladie & maladieDe.some(contreIndicationDe.some(OneOf([m])))]
    
      sync_reasoner(world, debug = 0)
    
    assert MaladieHémorragique in Maladie_CI_avec_m.equivalent_to.indirect()
    assert issubclass(MaladieHémorragique, Maladie_CI_avec_m)
    
  def test_reasoning_paper_5(self):
    world = self.new_world()
    onto = world.get_ontology("http://www.lesfleursdunormal.fr/static/_downloads/paper_5.owl")
    
    with onto:
      class Disorder(Thing): pass
      class Drug(Thing): pass
      class Contraindication(Thing): pass
      
      AllDisjoint([Disorder, Drug, Contraindication])
      
      
      class has_for_drug(ObjectProperty):
        domain   = [Contraindication]
        range    = [Drug]

      class has_for_disorder(ObjectProperty):
        domain   = [Contraindication]
        range    = [Disorder]

      class contraindicated_with(ObjectProperty):
        domain           = [Drug]
        range            = [Contraindication]
        inverse_property = has_for_drug

      class contraindicates(ObjectProperty):
        domain           = [Disorder]
        range            = [Contraindication]
        inverse_property = has_for_disorder

      class HemorrhagicDisorder(Disorder): pass

      class AcquiredHemorrhagicDisorder(HemorrhagicDisorder): pass

      class ConstitutiveHemorrhagicDisorder(HemorrhagicDisorder): pass

      partition(HemorrhagicDisorder, [AcquiredHemorrhagicDisorder, ConstitutiveHemorrhagicDisorder])

      class Heparin(Drug): pass

      class AntiplateletDrug(Drug): pass

      class Ticagrelor(AntiplateletDrug): pass

      class Aspirin(AntiplateletDrug): pass

      AllDisjoint([Heparin, AntiplateletDrug])
      AllDisjoint([Heparin, Ticagrelor, Aspirin])


      # Create the four contraindications (step 1 in the paper)

      ci1 = Contraindication()
      ci2 = Contraindication()
      ci3 = Contraindication()
      ci4 = Contraindication()


      # Relate drug classes to contraindications (step 2 in the paper)

      Ticagrelor.contraindicated_with = [ci1]
      Heparin   .contraindicated_with = [ci2]
      Aspirin   .contraindicated_with = [ci3, ci4]


      # Relate disorder classes to contraindications (step 3 in the paper)

      HemorrhagicDisorder            .contraindicates = [ci1]
      AcquiredHemorrhagicDisorder    .contraindicates = [ci3]
      ConstitutiveHemorrhagicDisorder.contraindicates = [ci2, ci4]


      # Assert that everything is known about contraindications (step 4 in the paper)

      close_world(Contraindication)


      # Assert that everything is known about drugs (step 5 in the paper)

      close_world(Drug)


      # Create classes for reasoning and execute the reasoner

      class DisorderContraindicatingAspirin(Disorder):
        equivalent_to = [Disorder & contraindicates.some(has_for_drug.some(Aspirin))]

      class DisorderContraindicatingTicagrelor(Disorder):
        equivalent_to = [Disorder & contraindicates.some(has_for_drug.some(Ticagrelor))]

      class DisorderContraindicatingHeparin(Disorder):
        equivalent_to = [Disorder & contraindicates.some(has_for_drug.some(Heparin))]


      class DisorderOKWithAspirin(Disorder):
        equivalent_to = [Disorder & Not(contraindicates.some(has_for_drug.some(Aspirin)))]

      class DisorderOKWithTicagrelor(Disorder):
        equivalent_to = [Disorder & Not(contraindicates.some(has_for_drug.some(Ticagrelor)))]

      class DisorderOKWithHeparin(Disorder):
        equivalent_to = [Disorder & Not(contraindicates.some(has_for_drug.some(Heparin)))]
        
    sync_reasoner(world, debug = 0)
    
    CI   = "CI   "
    OK   = "Ok   "
    CIOK = "CI/Ok"
    
    t = []
    for disorder_class in [HemorrhagicDisorder, AcquiredHemorrhagicDisorder, ConstitutiveHemorrhagicDisorder]:
      for contraindicating_class, ok_class in [
          (DisorderContraindicatingAspirin, DisorderOKWithAspirin),
          (DisorderContraindicatingHeparin, DisorderOKWithHeparin),
          (DisorderContraindicatingTicagrelor, DisorderOKWithTicagrelor),
      ]:
        if   issubclass(disorder_class, contraindicating_class): t.append(CI)
        elif issubclass(disorder_class, ok_class):               t.append(OK)
        else:                                                    t.append(CIOK)

    x  = "\n"
    x += "                                  ticagrelor heparin aspirin\n"
    x += "             hemorrhagic disorder %s      %s   %s\n" % (t[0], t[1], t[2])
    x += "    acquired hemorrhagic disorder %s      %s   %s\n" % (t[3], t[4], t[5])
    x += "constitutive hemorrhagic disorder %s      %s   %s\n" % (t[6], t[7], t[8])

    assert x.strip() == """
                                  ticagrelor heparin aspirin
             hemorrhagic disorder CI         CI/Ok   CI   
    acquired hemorrhagic disorder CI         Ok      CI   
constitutive hemorrhagic disorder CI         CI      CI   """.strip()

  def test_reasoning_paper_ic2015(self):
    world = self.new_world()
    onto = world.get_ontology("http://www.lesfleursdunormal.fr/static/_downloads/crepes_et_galettes.owl")
    onto.load()
    
    ma_galette = onto.Galette()
    ma_galette.a_pour_garniture = [ onto.Tomate(),
                                    onto.Viande() ]
    
    ok = 0
    class GaletteNonVégétarienne(onto.Galette):
      equivalent_to = [
        onto.Galette
        & ( onto.a_pour_garniture.some(onto.Viande)
          | onto.a_pour_garniture.some(onto.Poisson)
        ) ]
      def manger(self):
        nonlocal ok
        ok = 1
      
    sync_reasoner(world, debug = 0)
    
    assert ma_galette.__class__ is GaletteNonVégétarienne
    
    ma_galette.manger()
    
    assert ok == 1




class TestSPARQL(BaseTest, unittest.TestCase):
  def prepare1(self):
    world = self.new_world()
    onto = world.get_ontology("http://test.org/onto.owl#")
    with onto:
      class A(Thing): pass
      class A1(A): pass
      class A11(A1): pass
      class A2(A): pass
      class B(Thing): pass
      class C(Thing): pass

      class price(Thing >> float): label = "price"
      class price_vat_free(price): pass
      class rel(ObjectProperty): label = "rel"
      class subrel(rel): pass
      class annot(AnnotationProperty): pass
      
      A.label.append("Classe A")
      A1.label.append("Classe A1")
      
      b1 = B(label = [locstr("label_b", "en")])
      b2 = B(label = [locstr("label_b", "en")])
      b3 = B(label = [locstr("label_b", "fr")])
      a1 = A(label = [locstr("label_a", "en")], price = [10.0], price_vat_free = [8.0], rel = [b2], subrel = [b3])
    return world, onto
  
  def sparql(self, world, sparql, params = (), compare_with_rdflib = True):
    if SHOW_SQL:
      t0 = time.time()
    #q = Translator(world).parse(sparql)
    q = world.prepare_sparql(sparql)
    if SHOW_SQL:
      t = time.time() - t0
      print()
      print()
      print(sparql)
      print()
      print()
      print(q.sql + ";")
      print()
      print()
      print("prepared in %s s" % t)
      t0 = time.time()
      
    if isinstance(q, owlready2.sparql.main.PreparedSelectQuery):
      r = list(q.execute(params))
    else:
      r = [q.execute(params)]
      compare_with_rdflib = False
      
    if SHOW_SQL:
      print("executed in %s s" % (time.time() - t0))
      if len(r) > 100: print("len(r) =", len(r))
      else:            print("r =", r)

    if compare_with_rdflib:
      r2 = list(world.sparql_query("""PREFIX owl: <http://www.w3.org/2002/07/owl#>\nPREFIX onto: <http://test.org/onto.owl#>\n""" + sparql))
      
      z  = { tuple(i) for i in r  }
      z2 = { tuple(i) for i in r2 }
      if (len(r) != len(r2)) or (z != z2):
        print("Results differ with Owlready and RDFlib:")
        print("OWLREADY:", r)
        print("RDFLIB:  ", r2)
        assert False
        
    return q, r
  
  def sparql_rdflib(self, world, sparql):
    l = list(world.sparql_query(s))
    return r
  
  
  def test_1(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x ?y  { ?x a onto:A .  ?x rdfs:label ?y . }""")
    assert len(r) == 1
    assert r == [[onto.a1, locstr("label_a", "en")]]
    assert q.column_names == ["?x", "?y"]
    
  def test_2(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x  { onto:a1 rdfs:label ?x . }""")
    assert len(r) == 1
    assert r == [[locstr("label_a", "en")]]
  
  def test_3(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x  { ?x rdfs:subClassOf* onto:A . }""")
    assert len(r) == 4
    assert { x[0] for x in r } == { onto.A, onto.A1, onto.A11, onto.A2 }
  
  def test_4(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x  { ?x a/rdfs:subClassOf* onto:A . }""")
    assert len(r) == 1
    assert r == [[onto.a1]]

  def test_5(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x  { ?C rdfs:label "Classe A" .  ?x rdfs:subClassOf* ?C . }""")
    assert len(r) == 4
    assert { x[0] for x in r } == { onto.A, onto.A1, onto.A11, onto.A2 }
    
  def test_6(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x  { onto:a1 rdfs:label ?x . }""")
    assert len(r) == 1
    assert r == [[locstr("label_a", "en")]]
    assert r[0][0].lang == "en"
    
  def test_7(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x  { ?x rdfs:label "label_a" . }""")
    assert len(r) == 1
    assert r == [[onto.a1]]
    
  def test_8(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x  { ?x rdfs:label "label_a"@en . }""")
    assert len(r) == 1
    assert r == [[onto.a1]]
    
  def test_9(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?y  { onto:b1 rdfs:label ?x . ?y rdfs:label ?x . }""", compare_with_rdflib = False)
    assert len(r) == 2
    assert { x[0] for x in r } == { onto.b1, onto.b2 }
    q, r = self.sparql(world, """SELECT  ?y  { onto:b1 rdfs:label ?x1 . ?y rdfs:label ?x2 . FILTER(STR(?x1) = STR(?x2)) }""")
    assert len(r) == 3
    assert { x[0] for x in r } == { onto.b1, onto.b2, onto.b3 }
    
  def test_10(self):
    world, onto = self.prepare1()
    try:
      q, r = self.sparql(world, """SELECT  ?y  { onto:b1 onto:price ?y . ?y a onto:A . }""")
    except ValueError as e:
      assert "cannot be both datas and objs" in str(e)
    else: assert False
    
  def test_11(self):
    world, onto = self.prepare1()
    onto.b1.annot.append(10.0)
    q, r = self.sparql(world, """SELECT  ?y  { onto:a1 onto:price ?x . ?y onto:annot ?x . }""")
    assert len(r) == 1
    assert { x[0] for x in r } == { onto.b1 }
    assert not "quads" in q.sql
    assert q.sql.count("datas ") == 2
    #assert not "INDEXED BY" in q.sql
    
  def test_12(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x  { ?x rdfs:subClassOf+ onto:A . }""")
    assert len(r) == 3
    assert { x[0] for x in r } == { onto.A1, onto.A11, onto.A2 }
    
  def test_13(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?p ?x  { ?p rdfs:label "price" . onto:a1 ?p ?x . }""")
    assert len(r) == 1
    assert r == [[onto.price, 10.0]]
    
  def test_14(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?p ?x  { ?p rdfs:subPropertyOf* onto:price . onto:a1 ?p ?x . }""")
    assert len(r) == 2
    assert { tuple(i) for i in r } == { (onto.price, 10.0), (onto.price_vat_free, 8.0) }
    assert not "quads" in q.sql
    assert "datas" in q.sql
    
  def test_15(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?p ?x  { ?p rdfs:label "rel" . onto:a1 ?p ?x . }""")
    assert len(r) == 1
    assert r == [[onto.rel, onto.b2]]
    
  def test_16(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?p ?x  { ?p rdfs:subPropertyOf* onto:rel . onto:a1 ?p ?x . }""")
    assert len(r) == 2
    assert { tuple(i) for i in r } == { (onto.rel, onto.b2), (onto.subrel, onto.b3) }
    assert not "quads" in q.sql
    assert "objs" in q.sql    
    
  def test_17(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x ?y  { ?x rdfs:subClassOf* onto:A . ?y rdfs:subClassOf* ?x . }""")
    assert len(r) == 8
    assert { tuple(i) for i in r } == { (onto.A, onto.A), (onto.A, onto.A1), (onto.A, onto.A11), (onto.A, onto.A2), (onto.A1, onto.A1), (onto.A1, onto.A11), (onto.A2, onto.A2), (onto.A11, onto.A11) }

  def test_18(self):
    world, onto = self.prepare1()
    q, r1 = self.sparql(world, """SELECT  ?x  { ?C rdfs:label "Classe A" . ?x rdfs:subClassOf* ?C . } LIMIT 2""")
    q, r2 = self.sparql(world, """SELECT  ?x  { ?C rdfs:label "Classe A" . ?x rdfs:subClassOf* ?C . } LIMIT 2 OFFSET 2""")
    assert len(r1) == 2
    assert len(r2) == 2
    assert { i[0] for i in r1 + r2 } == { onto.A, onto.A1, onto.A11, onto.A2 }
    
  def test_19(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x  { ?x ^rdfs:label onto:a1 . }""")
    assert len(r) == 1
    assert r == [[locstr("label_a", "en")]]
    assert r[0][0].lang == "en"
    
  def test_20(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x  { onto:A ^rdfs:subClassOf* ?x . }""")
    assert len(r) == 4
    assert { x[0] for x in r } == { onto.A, onto.A1, onto.A11, onto.A2 }
    
  def test_21(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x  { ?x ^rdfs:subClassOf* onto:A11 ; rdfs:label "Classe A" }""")
    assert len(r) == 1
    assert { x[0] for x in r } == { onto.A }
    
  def test_22(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x  { ?x ^rdfs:subClassOf* onto:A11 ; rdfs:label "Missing label" }""")
    assert len(r) == 0
    
  def test_23(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x  { ?x a/rdfs:subClassOf* onto:A ; rdfs:label "label_a"@en }""")
    assert len(r) == 1
    assert { x[0] for x in r } == { onto.a1 }
    
  def test_24(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x  { ?x a/rdfs:subClassOf* onto:A ; rdfs:label "Missing label" }""")
    assert len(r) == 0
    
  def test_25(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x ?y  { ?x a onto:A . ?x onto:price ?p .  BIND (?p * 2.0 AS ?y) }""")
    assert len(r) == 1
    assert r == [[onto.a1, 20.0]]
    assert type(r[0][1]) is float

  def test_26(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x ?y2  { ?x a onto:A . ?x onto:price ?p .  BIND (?p * 2.0 AS ?y)  BIND (?y * 2.0 AS ?y2) }""")
    assert len(r) == 1
    assert r == [[onto.a1, 40.0]]
    assert type(r[0][1]) is float

  def test_27(self):
    world, onto = self.prepare1()
    with onto:
      aa = onto.A("aa")
      aa.price = [12.3]
    q, r = self.sparql(world, """SELECT  ?y  { onto:aa onto:price ?p .  BIND (ROUND(?p) AS ?y) }""")
    assert len(r) == 1
    assert r == [[12]]
    assert type(r[0][0]) is int
    
  def test_28(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x (?p * 2.0 AS ?y)  { ?x a onto:A . ?x onto:price ?p . }""")
    assert len(r) == 1
    assert r == [[onto.a1, 20.0]]
    assert type(r[0][1]) is float
    
  def test_29(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?p  { [ a onto:A ] onto:price ?p . }""", compare_with_rdflib = False)
    assert len(r) == 1
    assert r == [[10.0]]
    q, r = self.sparql(world, """SELECT  ?p  { [ onto:price ?p ] a onto:A . }""", compare_with_rdflib = False)
    assert len(r) == 1
    assert r == [[10.0]]

  def test_30(self):
    world, onto = self.prepare1()
    onto.a1.price = [5.0, 8.0, 10.0, 20.0]
    q, r = self.sparql(world, """SELECT  ?p  { onto:a1 onto:price ?p . FILTER (?p > 10.0) }""")
    assert len(r) == 1
    assert r == [[20.0]]
    q, r = self.sparql(world, """SELECT  ?p  { onto:a1 onto:price ?p . FILTER (?p >= 10.0) }""")
    assert len(r) == 2
    assert { i[0] for i in r } == { 10.0, 20.0 }
    q, r = self.sparql(world, """SELECT  ?p  { onto:a1 onto:price ?p . FILTER (?p < 0.0) }""")
    assert len(r) == 0
    q, r = self.sparql(world, """SELECT  ?p  { onto:a1 onto:price ?p . FILTER (?p <= 10.0) }""")
    assert len(r) == 3
    assert { i[0] for i in r } == { 5.0, 8.0, 10.0 }
    
  def test_31(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  (UCASE(?x) AS ?l)  { onto:a1 rdfs:label ?x . }""")
    assert len(r) == 1
    assert r == [[locstr("LABEL_A", "en")]]
    onto.a1.label = ["XxX"]
    q, r = self.sparql(world, """SELECT  (LCASE(?x) AS ?l)  { onto:a1 rdfs:label ?x . }""")
    assert len(r) == 1
    assert r == [["xxx"]]
    
  def test_32(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  (STRLEN(?x) AS ?l)  { onto:a1 rdfs:label ?x . }""")
    assert len(r) == 1
    assert r == [[7]]
    
    q, r = self.sparql(world, """SELECT  (CONTAINS(?x, "abel") AS ?l)  { onto:a1 rdfs:label ?x . }""")
    assert len(r) == 1
    assert r == [[True]]
    q, r = self.sparql(world, """SELECT  (CONTAINS(?x, "yyy") AS ?l)  { onto:a1 rdfs:label ?x . }""")
    assert len(r) == 1
    assert r == [[False]]
    q, r = self.sparql(world, """SELECT  (CONTAINS("xxxlabel_axxx", ?x) AS ?l)  { onto:a1 rdfs:label ?x . }""", compare_with_rdflib = False)
    assert len(r) == 1
    assert r == [[True]]
    q, r = self.sparql(world, """SELECT  (CONTAINS("xxx", ?x) AS ?l)  { onto:a1 rdfs:label ?x . }""", compare_with_rdflib = False)
    assert len(r) == 1
    assert r == [[False]]
    
    q, r = self.sparql(world, """SELECT  (STRSTARTS(?x, "label") AS ?l)  { onto:a1 rdfs:label ?x . }""")
    assert len(r) == 1
    assert r == [[True]]
    q, r = self.sparql(world, """SELECT  (STRSTARTS(?x, "abel") AS ?l)  { onto:a1 rdfs:label ?x . }""")
    assert len(r) == 1
    assert r == [[False]]
    
    q, r = self.sparql(world, """SELECT  (STRENDS(?x, "l_a") AS ?l)  { onto:a1 rdfs:label ?x . }""")
    assert len(r) == 1
    assert r == [[True]]
    q, r = self.sparql(world, """SELECT  (STRENDS(?x, "bel") AS ?l)  { onto:a1 rdfs:label ?x . }""")
    assert len(r) == 1
    assert r == [[False]]
    
    q, r = self.sparql(world, """SELECT  (STRBEFORE(?x, "_") AS ?l)  { onto:a1 rdfs:label ?x . }""")
    assert len(r) == 1
    assert r == [[locstr("label", "en")]]
    q, r = self.sparql(world, """SELECT  (STRBEFORE(?x, "zzz") AS ?l)  { onto:a1 rdfs:label ?x . }""", compare_with_rdflib = False)
    assert len(r) == 1
    assert r == [[locstr("", "en")]]
    
    q, r = self.sparql(world, """SELECT  (STRAFTER(?x, "b") AS ?l)  { onto:a1 rdfs:label ?x . }""")
    assert len(r) == 1
    assert r == [[locstr("el_a", "en")]]
    q, r = self.sparql(world, """SELECT  (STRAFTER(?x, "zzz") AS ?l)  { onto:a1 rdfs:label ?x . }""", compare_with_rdflib = False)
    assert len(r) == 1
    assert r == [[locstr("", "en")]]

    q, r = self.sparql(world, """SELECT  (SUBSTR(?x, 2, 4) AS ?l)  { onto:a1 rdfs:label ?x . }""")
    assert len(r) == 1
    assert r == [[locstr("abel", "en")]]
    
    q, r = self.sparql(world, """SELECT  (SIMPLEREPLACE(?x, "_", "-") AS ?l)  { onto:a1 rdfs:label ?x . }""", compare_with_rdflib = False)
    assert len(r) == 1
    assert r == [[locstr("label-a", "en")]]
    
    q, r = self.sparql(world, """SELECT  (CONCAT("before", ?x, "after") AS ?l)  { onto:a1 rdfs:label ?x . }""", compare_with_rdflib = False)
    assert len(r) == 1
    assert r == [[locstr("beforelabel_aafter", "en")]]
    
  def test_33(self):
    world, onto = self.prepare1()
    onto.a1.annot = ["123", 6, 7.6, "abc", onto.b1]
    q, r = self.sparql(world, """SELECT  (STR(?x) AS ?l)  { onto:a1 onto:annot ?x . }""")
    assert len(r) == 5
    assert { x[0] for x in r } == { "123", "6", "7.6", "abc", "%s" % onto.b1.iri }
    
  def test_34(self):
    world, onto = self.prepare1()
    onto.a1.annot = [locstr("lesson", "en"), locstr("leçon", "fr"), "xxx", 1.2, onto.b1]
    q, r = self.sparql(world, """SELECT  ?x (LANG(?x) AS ?l)  { onto:a1 onto:annot ?x . }""", compare_with_rdflib = False)
    assert len(r) == 5
    assert { tuple(x) for x in r } == { (locstr("lesson", "en"), "en"), (locstr("leçon", "fr"), "fr"), ("xxx", ""), (1.2, ""), (onto.b1, "") }
    
  def test_35(self):
    world, onto = self.prepare1()
    onto.A1.is_a.append(onto.price.value(10.0))
    onto.a1.annot = ["xxx", 1.2, onto.b1, onto.A1.is_a[-1]]
    q, r = self.sparql(world, """SELECT  ?x (ISIRI(?x) AS ?l1) (ISBLANK(?x) AS ?l2) (ISLITERAL(?x) AS ?l3) (ISNUMERIC(?x) AS ?l4) { onto:a1 onto:annot ?x . }""")
    assert len(r) == 4
    assert { tuple(x) for x in r } == { ("xxx", False, False, True, False), (1.2, False, False, True, True), (onto.b1, True, False, False, False), (onto.A1.is_a[-1], False, True, False, False) }
    
  def test_36(self):
    world, onto = self.prepare1()
    onto.a1.annot = [onto.b1]
    q, r = self.sparql(world, """SELECT  ?x (SAMETERM(?x, onto:b1) AS ?l1) { onto:a1 onto:annot ?x . }""")
    assert len(r) == 1
    assert r == [[onto.b1, True]]
    
  def test_37(self):
    world, onto = self.prepare1()
    onto.a1.annot = ["#b1"]
    q, r = self.sparql(world, """SELECT  (IRI(CONCAT("http://test.org/onto.owl", ?x)) AS ?l1) { onto:a1 onto:annot ?x . }""")
    assert len(r) == 1
    assert r == [[onto.b1]]
    
  def test_38(self):
    world, onto = self.prepare1()
    onto.a1.annot = [8.0, "eee", 4, locstr("xxx", "fr")]
    q, r = self.sparql(world, """SELECT  ?x (DATATYPE(?x) AS ?l1) { onto:a1 onto:annot ?x . }""")
    assert len(r) == 4
    assert { tuple(x) for x in r } == { (locstr("xxx", "fr"), locstr), (8.0, float), (4, int), ("eee", str) }
    
  def test_39(self):
    world, onto = self.prepare1()
    onto.a1.annot = [datetime.datetime(2021, 2, 19, 10, 41, 3, 123000), datetime.date(2020, 9, 2)]
    q, r = self.sparql(world, """SELECT  ?x (YEAR(?x) AS ?l1) (MONTH(?x) AS ?l2) (DAY(?x) AS ?l3) (HOURS(?x) AS ?l4) (MINUTES(?x) AS ?l5) (SECONDS(?x) AS ?l6) { onto:a1 onto:annot ?x . }""", compare_with_rdflib = False)
    assert len(r) == 2
    assert { tuple(x) for x in r } == { (datetime.datetime(2021, 2, 19, 10, 41, 3, 123000), 2021, 2, 19, 10, 41, 3.123), (datetime.date(2020, 9, 2), 2020, 9, 2, 0, 0, 0.0) }

  def test_40(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  (CEIL(10.5) AS ?l1) (CEIL(-10.5) AS ?l2) (CEIL(5.0) AS ?l3) (CEIL(-5.0) AS ?l4) { }""")
    assert len(r) == 1
    assert r == [[11.0, -10.0, 5.0, -5.0]]
    assert(type(r[0][0]) is float)
    q, r = self.sparql(world, """SELECT  (FLOOR(10.5) AS ?l1) (FLOOR(-10.5) AS ?l2) (FLOOR(5.0) AS ?l3) (FLOOR(-5.0) AS ?l4) { }""")
    assert len(r) == 1
    assert r == [[10.0, -11.0, 5.0, -5.0]]
    assert(type(r[0][0]) is float)
    
  def test_41(self):
    world, onto = self.prepare1()
    onto.a1.annot = ["abc", "def"]
    q, r = self.sparql(world, """SELECT  ?x (IF(?x = "abc", "ghi", ?x) AS ?l1) { onto:a1 onto:annot ?x }""")
    assert len(r) == 2
    assert { tuple(x) for x in r } == { ("abc", "ghi"), ("def", "def") }
    onto.a1.annot = ["abc", 9]
    q, r = self.sparql(world, """SELECT  ?x (IF(?x = "abc", "ghi", ?x) AS ?l1) { onto:a1 onto:annot ?x }""")
    assert len(r) == 2
    assert { tuple(x) for x in r } == { ("abc", "ghi"), (9, 9) }

  def test_42(self):
    world, onto = self.prepare1()
    onto.a1.annot = [locstr("abc", "en"), locstr("def", "fr"), "ghi"]
    q, r = self.sparql(world, """SELECT  ?x (LANGMATCHES(?x, "*") AS ?l1) { onto:a1 onto:annot ?x }""", compare_with_rdflib = False)
    assert len(r) == 3
    assert { tuple(x) for x in r } == { (locstr('abc', 'en'), True), (locstr('def', 'fr'), True), ("ghi", False) }
    q, r = self.sparql(world, """SELECT  ?x (LANGMATCHES(?x, "FR") AS ?l1) { onto:a1 onto:annot ?x }""", compare_with_rdflib = False)
    assert len(r) == 3
    assert { tuple(x) for x in r } == { (locstr('abc', 'en'), False), (locstr('def', 'fr'), True), ("ghi", False) }
    
  def test_43(self):
    world, onto = self.prepare1()
    onto.a1.annot = ["abc"]
    q, r = self.sparql(world, """SELECT  (MD5(?x) AS ?l1) { onto:a1 onto:annot ?x }""")
    assert len(r) == 1
    assert r == [["900150983cd24fb0d6963f7d28e17f72"]]
    q, r = self.sparql(world, """SELECT  (SHA1(?x) AS ?l1) { onto:a1 onto:annot ?x }""")
    assert len(r) == 1
    assert r == [["a9993e364706816aba3e25717850c26c9cd0d89d"]]
    q, r = self.sparql(world, """SELECT  (SHA256(?x) AS ?l1) { onto:a1 onto:annot ?x }""")
    assert len(r) == 1
    assert r == [["ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"]]
    q, r = self.sparql(world, """SELECT  (SHA384(?x) AS ?l1) { onto:a1 onto:annot ?x }""")
    assert len(r) == 1
    assert r == [["cb00753f45a35e8bb5a03d699ac65007272c32ab0eded1631a8b605a43ff5bed8086072ba1e7cc2358baeca134c825a7"]]
    q, r = self.sparql(world, """SELECT  (SHA512(?x) AS ?l1) { onto:a1 onto:annot ?x }""")
    assert len(r) == 1
    assert r == [["ddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a2192992a274fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f"]]
    
  def test_44(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x (NOW() AS ?n) { ?x ?p ?y }""", compare_with_rdflib = False)
    assert len({ i[1] for i in r }) == 1    
    
  def test_45(self):
    world, onto = self.prepare1()
    onto.a1.annot = [owlready2.base._parse_datetime("2011-01-10T14:45:13.815-05:00")]
    q, r = self.sparql(world, """SELECT  (TZ(?x) AS ?l1) { onto:a1 onto:annot ?x . }""")
    assert len(r) == 1
    assert r == [["-05:00"]]  
    q, r = self.sparql(world, """SELECT  (STR(TIMEZONE(?x)) AS ?l1) { onto:a1 onto:annot ?x . }""")
    assert len(r) == 1
    assert r == [["-PT5H"]]  
    
  def test_46(self):
    world, onto = self.prepare1()
    onto.a1.annot = ["Los Angeles"]
    q, r = self.sparql(world, """SELECT  (ENCODE_FOR_URI(?x) AS ?l1) { onto:a1 onto:annot ?x . }""")
    assert len(r) == 1
    assert r == [["Los%20Angeles"]]

  def test_47(self):
    world, onto = self.prepare1()
    onto.a1.annot = [1]
    q, r = self.sparql(world, """SELECT  (STRDT(?x, xsd:decimal) AS ?l1) { onto:a1 onto:annot ?x . }""")
    assert len(r) == 1
    assert r == [[1]]  
    assert type(r[0][0]) is float
    onto.a1.annot = ["abc", locstr("def", "en")]
    q, r = self.sparql(world, """SELECT  (STRLANG(?x, "fr") AS ?l1) { onto:a1 onto:annot ?x . }""", compare_with_rdflib = False)
    assert len(r) == 2
    r = sorted([x[0] for x in r])
    assert r == [locstr("abc", "fr"), locstr("def", "fr")]  
    assert r[0].lang == "fr"
    assert r[1].lang == "fr"

  def test_48(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  (STR(NEWINSTANCEIRI(?x)) AS ?r)  { ?x rdfs:subClassOf onto:A . }""", compare_with_rdflib = False)
    assert len(r) == 2
    assert r == [["http://test.org/onto.owl#a11"], ["http://test.org/onto.owl#a21"]]
    
  def test_49(self):
    world, onto = self.prepare1()
    onto.a1.annot = ["Alice", "Yyopeajp", "eeAli"]
    q, r = self.sparql(world, """SELECT  ?x (REGEX(?x, "^Ali", "i") AS ?r)  { onto:a1 onto:annot ?x . }""")
    assert len(r) == 3
    assert { tuple(x) for x in r } == { ("Alice", True), ("Yyopeajp", False), ("eeAli", False) }
    
  def test_50(self):
    world, onto = self.prepare1()
    onto.a1.annot = ["Alice", "Yyopeajp", "eeAzi"]
    q, r = self.sparql(world, """SELECT  ?x (REPLACE(?x, "A.i", "XXX", "i") AS ?r)  { onto:a1 onto:annot ?x . }""")
    assert len(r) == 3
    assert { tuple(x) for x in r } == { ("Alice", "XXXce"), ("Yyopeajp", "Yyopeajp"), ("eeAzi", "eeXXX") }
    
  def test_51(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?p ?x  { onto:a1 ?p ?x . }""")
    assert len(r) == 7
    assert { tuple(x) for x in r } == { (rdf_type, NamedIndividual), (rdf_type, onto.A), (onto.rel, onto.b2), (onto.subrel, onto.b3), (label, locstr("label_a", "en")), (onto.price, 10.0), (onto.price_vat_free, 8.0) }
  
  def test_52(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x  { onto:a1 !rdfs:label ?x . }""")
    assert len(r) == 6
    assert { tuple(x)[0] for x in r } == { NamedIndividual, onto.A, onto.b2, onto.b3, 10.0, 8.0 }
    
  def test_53(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x  { onto:a1 !(rdfs:label | rdf:type) ?x . }""")
    assert len(r) == 4
    assert { tuple(x)[0] for x in r } == { onto.b2, onto.b3, 10.0, 8.0 }

  def test_54(self):
    world, onto = self.prepare1()
    b4 = onto.B()
    b5 = onto.B()
    onto.b3.rel = [b4]
    onto.b4.rel = [b5]
    q, r = self.sparql(world, """SELECT  ?x  { onto:a1 !(rdfs:label | rdf:type)+ ?x . }""")
    assert len(r) == 6
    assert { tuple(x)[0] for x in r } == { onto.b2, onto.b3, onto.b4, onto.b5, 10.0, 8.0 }

  def test_55(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  *  { ?x a onto:A . ?x rdfs:label ?l . }""", compare_with_rdflib = False)
    assert len(r) == 1
    assert { tuple(x) for x in r } == { (onto.a1, locstr("label_a", "en")) }
    assert q.column_names == ["?x", "?l"]
    q, r = self.sparql(world, """SELECT  *  { ?x rdfs:label ?l . ?x a onto:A . }""", compare_with_rdflib = False)
    assert len(r) == 1
    assert { tuple(x) for x in r } == { (onto.a1, locstr("label_a", "en")) }
    assert q.column_names == ["?x", "?l"]
    q, r = self.sparql(world, """SELECT  *  { ?l ^rdfs:label ?x . ?x a onto:A . }""", compare_with_rdflib = False)
    assert len(r) == 1
    assert { tuple(x) for x in r } == { (locstr("label_a", "en"), onto.a1) }
    assert q.column_names == ["?l", "?x"]

  def test_56(self):
    world, onto = self.prepare1()
    q, r1 = self.sparql(world, """SELECT  ?x ?l  { ?x a onto:A . ?x rdfs:label ?l . }""")
    assert not "WITH" in q.sql
    q, r2 = self.sparql(world, """SELECT  ?x ?l  { ?x a onto:A . BIND(?x AS ?y) ?x rdfs:label ?l . }""")
    assert not "WITH" in q.sql
    q, r3 = self.sparql(world, """SELECT  ?x ?l  { { ?x a onto:A . } ?x rdfs:label ?l . }""")
    assert "WITH" in q.sql
    q, r4 = self.sparql(world, """SELECT  ?x ?l  { ?x a onto:A . { ?x rdfs:label ?l . } }""")
    assert "WITH" in q.sql
    q, r5 = self.sparql(world, """SELECT  *  { ?x a onto:A . { ?x rdfs:label ?l . } }""", compare_with_rdflib = False)
    assert "WITH" in q.sql
    q, r6 = self.sparql(world, """SELECT  ?x ?l  { { ?x a onto:A . } { ?x rdfs:label ?l . } }""")
    assert "WITH" in q.sql
    assert "prelim2" in q.sql
    q, r7 = self.sparql(world, """SELECT  ?x ?l  { { { ?x a onto:A . } } ?x rdfs:label ?l . }""")
    assert "WITH" in q.sql
    assert len(r1) == 1
    assert len(r2) == 1
    assert len(r3) == 1
    assert len(r4) == 1
    assert len(r5) == 1
    assert len(r6) == 1
    assert len(r7) == 1
    r1 = frozenset({ tuple(x) for x in r1 })
    r2 = frozenset({ tuple(x) for x in r2 })
    r3 = frozenset({ tuple(x) for x in r3 })
    r4 = frozenset({ tuple(x) for x in r4 })
    r5 = frozenset({ tuple(x) for x in r5 })
    r6 = frozenset({ tuple(x) for x in r6 })
    r7 = frozenset({ tuple(x) for x in r6 })
    assert len({r1, r2, r3, r4, r5, r6, r7}) == 1
    
  def test_57(self):
    world, onto = self.prepare1()
    onto.a1.comment = ["comm"]
    q, r = self.sparql(world, """SELECT  ?x ?l  { ?x a onto:A . { ?x rdfs:label ?l } UNION { ?x rdfs:comment ?l } . }""")
    assert not "WITH" in q.sql
    assert " IN " in q.sql
    assert len(r) == 2
    assert { tuple(x) for x in r } == { (onto.a1, locstr("label_a", "en")), (onto.a1, "comm") }
    
  def test_58(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?l  { { onto:a1 rdfs:label ?l } UNION { onto:b1 rdfs:label  ?l } . }""")
    assert not "WITH" in q.sql
    assert " IN " in q.sql
    assert len(r) == 2
    assert { tuple(x) for x in r } == { (locstr("label_a", "en"),), (locstr("label_b", "en"),) }
    
  def test_59(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x  { { ?x a onto:B . } UNION { ?x rdfs:subClassOf onto:A . } }""")
    assert len(r) == 5
    assert { x[0] for x in r } == { onto.b1, onto.b2, onto.b3, onto.A1, onto.A2 }
    
  def test_60(self):
    world, onto = self.prepare1()
    onto.b2.comment = onto.A1.comment = ["ok"]
    q, r = self.sparql(world, """SELECT  ?x  { ?x rdfs:comment "ok". { ?x a onto:B . } UNION { ?x rdfs:subClassOf onto:A . } }""")
    assert len(r) == 2
    assert { x[0] for x in r } == { onto.b2, onto.A1 }
    
  def test_61(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x  { { ?x a/rdfs:subClassOf* onto:A . } UNION { ?x a/rdfs:subClassOf* onto:B } . }""")
    assert not "prelim2" in q.sql
    assert len(r) == 4
    assert { x[0] for x in r } == { onto.a1, onto.b1, onto.b2, onto.b3 }

  def test_62(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  *  { ?x a/rdfs:subClassOf* onto:A . }""")
    assert r == [[onto.a1]]
    
  def test_63(self):
    world, onto = self.prepare1()
    onto.b2.label.append("ok")
    q, r = self.sparql(world, """SELECT  *  { ?x a/rdfs:subClassOf* onto:B . FILTER EXISTS { ?x rdfs:label "ok" . } }""")
    assert r == [[onto.b2]]
    
  def test_64(self):
    world, onto = self.prepare1()
    onto.b2.label.append("ok")
    onto.b3.label.reinit([])
    q, r = self.sparql(world, """SELECT  *  { ?x a onto:B . FILTER EXISTS { ?x rdfs:label ?y . } }""", compare_with_rdflib = False)
    assert len(r) == 2
    assert { tuple(x) for x in r } == { (onto.b1,), (onto.b2,) }
    
  def test_65(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x  { { onto:a1 onto:rel ?x . } UNION { onto:a1 onto:price ?x } . }""")
    assert len(r) == 2
    assert { x[0] for x in r } == { onto.b2, 10.0 }
    
  def test_66(self):
    world, onto = self.prepare1()
    onto.b2.label.append("ok")
    #for i in range(5000):
    #  onto.B(label = ["abc"])
    #  onto.B(label = ["ok"])
    #world.graph.analyze()
    q, r = self.sparql(world, """SELECT  *  { ?x a onto:B . FILTER NOT EXISTS { ?x rdfs:label "ok" . } }""")
    #assert "INDEXED BY index_datas_sp" in q.sql
    assert len(r) == 2
    assert { x[0] for x in r } == { onto.b1, onto.b3 }
    
  def test_67(self):
    world, onto = self.prepare1()
    onto.b2.label.append("ok")
    q, r = self.sparql(world, """SELECT  *  { ?x a/rdfs:subClassOf* onto:B . FILTER NOT EXISTS { ?x rdfs:label "ok" . } }""")
    assert len(r) == 2
    assert { x[0] for x in r } == { onto.b1, onto.b3 }
    
  def test_68(self):
    world, onto = self.prepare1()
    onto.b1.label = ["abc"]
    onto.b2.label = ["ok"]
    onto.b3.label = []
    q, r = self.sparql(world, """SELECT  *  { ?x a/rdfs:subClassOf* onto:B . FILTER EXISTS { ?x rdfs:label ?y . } FILTER NOT EXISTS { ?x rdfs:label "ok" . } }""", compare_with_rdflib = False)
    assert len(r) == 1
    assert { x[0] for x in r } == { onto.b1 }
    
  def test_69(self):
    world, onto = self.prepare1()
    r = world.sparql("""SELECT  ?x ?y  { ?x a onto:A .  ?x rdfs:label ?y . }""")
    r = list(r)
    assert len(r) == 1
    assert r == [[onto.a1, locstr("label_a", "en")]]
    q1 = world.prepare_sparql("""SELECT  ?x ?y  { ?x a onto:A .  ?x rdfs:label ?y . }""")
    q2 = world.prepare_sparql("""SELECT  ?x ?y  { ?x a onto:A .  ?x rdfs:label ?y . }""")
    assert q1 is q2
    
  def test_70(self):
    world = self.new_world()
    onto = world.get_ontology("http://test.org/onto.owl#")
    with onto:
      class prop(Thing >> Thing): pass
      class C(Thing):
        is_a = [prop.some(Thing)]
    q, r = self.sparql(world, """SELECT  ?x  { onto:C rdfs:subClassOf ?x . }""")
    r2 = list(world.sparql_query("""SELECT  ?x  { <http://test.org/onto.owl#C> rdfs:subClassOf ?x . }"""))
    assert r == r2
    
  def test_71(self):
    world, onto = self.prepare1()
    onto.b2.label.append("ok")
    #for i in range(5000):
    #  onto.B(label = ["abc"])
    #  onto.B(label = ["ok"])
    q, r = self.sparql(world, """SELECT  *  { ?x a onto:B . ?x rdfs:label "ok" . }""")
    #assert "INDEXED BY index_datas_sp" in q.sql
    assert len(r) == 1
    assert { x[0] for x in r } == { onto.b2 }

  def test_72(self):
    world, onto = self.prepare1()
    onto.A.is_a.append(onto.rel.some(Thing))
    q, r = self.sparql(world, """SELECT (STR(?x) AS ?i)  { ?x a <http://www.w3.org/2002/07/owl#Class> . FILTER (ISIRI(?x)) }""")
    assert len(r) == 6
    assert { x[0] for x in r } == { 'http://test.org/onto.owl#A', 'http://test.org/onto.owl#A1', 'http://test.org/onto.owl#A11', 'http://test.org/onto.owl#A2', 'http://test.org/onto.owl#B', 'http://test.org/onto.owl#C' }
    
  def test_73(self):
    world, onto = self.prepare1()
    onto.a1.annot = ["abc", 9, onto.b1]
    q, r = self.sparql(world, """SELECT  ?x (STR(?x) AS ?l) { onto:a1 onto:annot ?x }""")
    assert len(r) == 3
    assert { tuple(x) for x in r } == { ("abc", "abc"), (9, "9"), (onto.b1, "http://test.org/onto.owl#b1") }
    
  def test_74(self):
    world, onto = self.prepare1()
    onto.a1.annot = [3, 5.9]
    q, r = self.sparql(world, """SELECT  ?x (datatype(ABS(?x)) AS ?y) { onto:a1 onto:annot ?x }""")
    assert len(r) == 2
    assert { tuple(x) for x in r } == { (3, int), (5.9, float) }
    
  def test_75(self):
    world, onto = self.prepare1()
    onto.a1.annot = [3, 5.9]
    q, r = self.sparql(world, """SELECT  ?x (datatype(?x) AS ?y) (datatype(2 * ?x) AS ?z) (datatype(2.5 * ?x) AS ?z2) { onto:a1 onto:annot ?x }""", compare_with_rdflib = False)
    assert len(r) == 2
    assert { tuple(x) for x in r } == { (3, int, int, float), (5.9, float, float, float) }
    
  def test_76(self):
    world, onto = self.prepare1()
    q1, r = self.sparql(world, """SELECT  ?l { ?? rdfs:label ?l }""", [onto.a1], compare_with_rdflib = False)
    assert q1.nb_parameter == 1
    assert len(q1.parameter_datatypes) == 0
    assert len(r) == 1
    assert { x[0] for x in r } == { locstr("label_a", "en") }
    q2, r = self.sparql(world, """SELECT  ?l { ?? rdfs:label ?l }""", [onto.b1], compare_with_rdflib = False)
    assert len(r) == 1
    assert { x[0] for x in r } == { locstr("label_b", "en") }
    assert q1 is q2
    
  def test_77(self):
    world, onto = self.prepare1()
    q1, r = self.sparql(world, """SELECT  (CONCAT(??, ?l) AS ?l2) { onto:a1 rdfs:label ?l }""", [locstr("test_", "fr")], compare_with_rdflib = False)
    assert q1.nb_parameter == 1
    assert len(r) == 1
    assert { x[0] for x in r } == { locstr("test_label_a", "fr") }
    assert isinstance(r[0][0], locstr)
    assert r[0][0].lang == "fr"
    q2, r = self.sparql(world, """SELECT  (CONCAT(??, ?l) AS ?l2) { onto:a1 rdfs:label ?l }""", [locstr("test_", "en")], compare_with_rdflib = False)
    assert q2.nb_parameter == 1
    assert len(r) == 1
    assert { x[0] for x in r } == { locstr("test_label_a", "en") }
    assert isinstance(r[0][0], locstr)
    assert r[0][0].lang == "en"
    assert q1 is q2
    
  def test_78(self):
    world, onto = self.prepare1()
    onto.a1.annot = [3]
    q1, r = self.sparql(world, """SELECT  (?? + ?l AS ?l2) { onto:a1 onto:annot ?l }""", [2], compare_with_rdflib = False)
    assert len(r) == 1
    assert { x[0] for x in r } == { 5 }
    assert isinstance(r[0][0], int)
    q2, r = self.sparql(world, """SELECT  (?? + ?l AS ?l2) { onto:a1 onto:annot ?l }""", [2.0], compare_with_rdflib = False)
    assert len(r) == 1
    assert { x[0] for x in r } == { 5.0 }
    assert isinstance(r[0][0], float)
    assert q1 is q2
    
  def test_79(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?l { ??2 ??1 ?l }""", [label, onto.a1], compare_with_rdflib = False)
    assert q.nb_parameter == 2
    assert len(q.parameter_datatypes) == 0
    assert len(r) == 1
    assert { x[0] for x in r } == { locstr("label_a", "en") }
    
  def test_80(self):
    world, onto = self.prepare1()
    onto.b2.label = []
    q, r = self.sparql(world, """SELECT  ?x ?l  { ?x a onto:B . OPTIONAL { ?x rdfs:label ?l . } }""")
    assert len(r) == 3
    assert { tuple(x) for x in r } == { (onto.b1, locstr("label_b", "en")), (onto.b2, None), (onto.b3, locstr("label_b", "fr")) }
    
  def test_81(self):
    world, onto = self.prepare1()
    onto.a1.comment = ["test"]
    q, r = self.sparql(world, """SELECT  ?l  { onto:a1 rdfs:label|rdfs:comment ?l . }""")
    assert len(r) == 2
    assert { x[0] for x in r } == { locstr("label_a", "en"), "test" }
    assert " IN " in q.sql

  def test_82(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  (COUNT(?x) AS ?nb)  { ?x a onto:B . }""")
    assert len(r) == 1
    assert r == [[3]]
    onto.a1.label = ["1", "2", "3"]
    q, r = self.sparql(world, """SELECT  (COUNT(?x) AS ?nb)  { ?x rdfs:label ?l . }""")
    assert len(r) == 1
    assert r == [[10]]
    q, r = self.sparql(world, """SELECT  (COUNT(DISTINCT ?x) AS ?nb)  { ?x rdfs:label ?l . }""")
    assert len(r) == 1
    assert r == [[8]]

  def test_83(self):
    world, onto = self.prepare1()
    onto.b2.price = [12.0]
    q, r = self.sparql(world, """SELECT  (SUM(?y) AS ?nb)  { ?x onto:price ?y . }""")
    assert len(r) == 1
    assert r == [[22.0]]
    q, r = self.sparql(world, """SELECT  (MIN(?y) AS ?nb)  { ?x onto:price ?y . }""")
    assert len(r) == 1
    assert r == [[10.0]]
    q, r = self.sparql(world, """SELECT  (MAX(?y) AS ?nb)  { ?x onto:price ?y . }""")
    assert len(r) == 1
    assert r == [[12.0]]
    q, r = self.sparql(world, """SELECT  (AVG(?y) AS ?nb)  { ?x onto:price ?y . }""")
    assert len(r) == 1
    assert r == [[11.0]]
    q, r = self.sparql(world, """SELECT  (SAMPLE(?y) AS ?nb)  { ?x onto:price ?y . }""")
    assert len(r) == 1
    assert (r == [[10.0]]) or (r == [[12.0]])
    q, r = self.sparql(world, """SELECT  (GROUP_CONCAT(?y; separator=";") AS ?nb)  { ?x onto:price ?y . }""")
    assert len(r) == 1
    assert r == [["10.0;12.0"]]
    
  def test_84(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x (COUNT(DISTINCT ?y) AS ?nb)  { ?x onto:rel ?y . }""")
    assert len(r) == 1
    assert r == [[onto.a1, 1]]
    assert q.column_types == ['objs', 'datas', 'datas']
    onto.b2.rel = [onto.b1, onto.b3]
    q, r = self.sparql(world, """SELECT  ?x (COUNT(DISTINCT ?y) AS ?nb)  { ?x onto:rel ?y . } GROUP BY ?x""")
    assert len(r) == 2
    assert { tuple(x) for x in r } == { (onto.a1, 1), (onto.b2, 2) }
    q, r = self.sparql(world, """SELECT  ?x (COUNT(?y) AS ?nb)  { ?x onto:rel ?y . } GROUP BY ?x HAVING(COUNT(?y) > 1)""")
    assert len(r) == 1
    assert { tuple(x) for x in r } == { (onto.b2, 2) }
    
  def test_85(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x ?l { ?x rdfs:label ?l . } ORDER BY ?l""")
    assert r == [[onto.A, 'Classe A'], [onto.A1, 'Classe A1'], [onto.a1, locstr('label_a', "en")], [onto.b1, locstr('label_b', "en")], [onto.b2, locstr('label_b', "en")], [onto.b3, locstr('label_b', "fr")], [onto.price, 'price'], [onto.rel, 'rel']]
    q, r = self.sparql(world, """SELECT  ?x ?l { ?x rdfs:label ?l . } ORDER BY DESC(?l)""")
    assert r == [[onto.rel, 'rel'], [onto.price, 'price'], [onto.b3, locstr('label_b', "fr")], [onto.b2, locstr('label_b', "en")], [onto.b1, locstr('label_b', "en")], [onto.a1, locstr('label_a', "en")], [onto.A1, 'Classe A1'], [onto.A, 'Classe A']]
    q, r = self.sparql(world, """SELECT  ?x ?l { ?x rdfs:label ?l . } ORDER BY DESC(?l) ?x""")
    assert r == [[onto.rel, 'rel'], [onto.price, 'price'], [onto.b1, locstr('label_b', "en")], [onto.b2, locstr('label_b', "en")], [onto.b3, locstr('label_b', "fr")], [onto.a1, locstr('label_a', "en")], [onto.A1, 'Classe A1'], [onto.A, 'Classe A']]
    
  def test_86(self):
    world, onto = self.prepare1()
    onto2 = world.get_ontology("http://test.org/insertions.owl")
    with onto2:
      q, r = self.sparql(world, """INSERT  { ?x a onto:B . }  WHERE  { ?x a onto:A . }""", compare_with_rdflib = False)
    assert r == [1]
    assert set(onto.a1.is_a) == { onto.A, onto.B }
    assert len(onto2.graph) == 2
    self.assert_triple(onto.a1.storid, rdf_type, onto.B.storid, world = world)
    
  def test_87(self):
    world, onto = self.prepare1()
    onto2 = world.get_ontology("http://test.org/insertions.owl")
    q, r = self.sparql(world, """WITH <%s>  INSERT  { ?x a onto:B . }  WHERE  { ?x a onto:A . }""" % onto2.base_iri, compare_with_rdflib = False)
    assert r == [1]
    assert set(onto.a1.is_a) == { onto.A, onto.B }
    assert len(onto2.graph) == 2
    self.assert_triple(onto.a1.storid, rdf_type, onto.B.storid, world = world)
    
  def test_88(self):
    world, onto = self.prepare1()
    onto2 = world.get_ontology("http://test.org/insertions.owl")
    with onto2:
      q, r = self.sparql(world, """INSERT  { ?x a onto:A . }  WHERE  { ?x a onto:B . }""", compare_with_rdflib = False)
    assert r == [3]
    assert set(onto.b1.is_a) == { onto.A, onto.B }
    assert set(onto.b2.is_a) == { onto.A, onto.B }
    assert set(onto.b3.is_a) == { onto.A, onto.B }
    assert len(onto2.graph) == 4
    self.assert_triple(onto.b1.storid, rdf_type, onto.A.storid, world = world)
    self.assert_triple(onto.b2.storid, rdf_type, onto.A.storid, world = world)
    self.assert_triple(onto.b3.storid, rdf_type, onto.A.storid, world = world)
    
  def test_89(self):
    world, onto = self.prepare1()
    onto2 = world.get_ontology("http://test.org/insertions.owl")
    with onto2:
      q, r = self.sparql(world, """INSERT  { ?b onto:rel ?a }  WHERE  { ?b a onto:B . BIND(NEWINSTANCEIRI(onto:A) AS ?a) }""", compare_with_rdflib = False)
    assert r == [3]
    assert len(onto2.graph) == 10
    assert onto2.a1.is_a == [onto.A]
    assert onto2.a1 in onto.b1.rel
    assert onto2.a2.is_a == [onto.A]
    assert onto2.a2 in onto.b2.rel
    assert onto2.a3.is_a == [onto.A]
    assert onto2.a3 in onto.b3.rel
    
  def test_90(self):
    world, onto = self.prepare1()
    onto2 = world.get_ontology("http://test.org/insertions.owl")
    with onto2:
      q, r = self.sparql(world, """INSERT  { ?b a owl:NamedIndividual . ?b a onto:B . ?a onto:rel ?b }  WHERE  { ?a a onto:A . BIND(UUID() AS ?b) }""", compare_with_rdflib = False)
    assert r == [1]
    assert len(onto2.graph) == 4
    i = list(onto2.individuals())[0]
    assert i.is_a == [onto.B]
    assert i in onto.a1.rel
    
  def test_91(self):
    world, onto = self.prepare1()
    onto2 = world.get_ontology("http://test.org/insertions.owl")
    with onto2:
      q, r = self.sparql(world, """INSERT  { ?b a owl:Restriction . ?b owl:onProperty onto:rel . ?b owl:someValuesFrom onto:B . ?a a ?b }  WHERE  { ?a a onto:A . BIND(BNODE() AS ?b) }""", compare_with_rdflib = False)
    assert r == [1]
    assert len(onto2.graph) == 5
    assert onto.rel.some(onto.B) in onto.a1.is_a
    
  def test_92(self):
    world, onto = self.prepare1()
    onto2 = world.get_ontology("http://test.org/insertions.owl")
    with onto2:
      q, r = self.sparql(world, """INSERT  { ?a onto:price "12"^^xsd:integer . }  WHERE  { ?a a onto:A }""", compare_with_rdflib = False)
    assert r == [1]
    assert len(onto2.graph) == 2
    assert onto.a1.price == [10.0, 12]
    assert onto.a1.price[-1].__class__ is int
    
  def test_93(self):
    world, onto = self.prepare1()
    onto2 = world.get_ontology("http://test.org/insertions.owl")
    with onto2:
      q, r = self.sparql(world, """INSERT  { ?a onto:price "12.0"^^xsd:decimal . }  WHERE  { ?a a onto:A }""", compare_with_rdflib = False)
    assert r == [1]
    assert len(onto2.graph) == 2
    assert onto.a1.price == [10.0, 12.0]
    assert onto.a1.price[-1].__class__ is float
    
  def test_94(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?a  { ?a onto:price 10.0 }""", compare_with_rdflib = False)
    assert r == [[onto.a1]]
    q, r = self.sparql(world, """SELECT  ?a  { ?a onto:price "10.0"^^xsd:decimal }""", compare_with_rdflib = False)
    assert r == [[onto.a1]]
    
  def test_95(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """DELETE  { ?a a onto:A }  WHERE  { ?a a onto:A }""", compare_with_rdflib = False)
    assert r == [1]
    assert onto.a1.is_a == [Thing]
    
  def test_96(self):
    world, onto = self.prepare1()
    onto2 = world.get_ontology("http://test.org/insertions.owl")
    with onto2:
      q, r = self.sparql(world, """DELETE  { ?a a onto:A }  INSERT  { ?a a onto:B }  WHERE  { ?a a onto:A }""", compare_with_rdflib = False)
    assert r == [1]
    assert len(onto2.graph) == 2
    assert not onto.A in onto.a1.is_a
    assert onto.B in onto.a1.is_a
    
  def test_97(self):
    world, onto = self.prepare1()
    onto.b2.label = []
    onto.b3.label.append("b3")
    q, r = self.sparql(world, """SELECT  ?b ?l  { ?b a onto:B . OPTIONAL { ?b rdfs:label ?l . } FILTER(BOUND(?l)) }""")
    assert len(r) == 3
    assert { tuple(x) for x in r } == { (onto.b1, locstr("label_b", "en")), (onto.b3, locstr("label_b", "fr")), (onto.b3, "b3") }
    
  def test_98(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x ?b  { ?x a owl:NamedIndividual . OPTIONAL { ?x a ?b . ?b rdfs:subClassOf* onto:B . } }""")
    assert len(r) == 4
    assert { tuple(x) for x in r } == { (onto.a1, None), (onto.b1, onto.B), (onto.b2, onto.B), (onto.b3, onto.B) }
    
  def test_99(self):
    world, onto = self.prepare1()
    onto2 = world.get_ontology("http://test.org/insertions.owl")
    with onto2:
      q, r = self.sparql(world, """INSERT  { ?a a [ a owl:Restriction ; owl:onProperty onto:rel ; owl:someValuesFrom onto:B ] . }  WHERE  { ?a a onto:A }""", compare_with_rdflib = False)
    assert r == [1]
    assert len(onto2.graph) == 5
    assert onto.rel.some(onto.B) in onto.a1.is_a
    
  def test_100(self):
    world, onto = self.prepare1()
    onto2 = world.get_ontology("http://test.org/insertions.owl")
    with onto2:
      q, r = self.sparql(world, """INSERT  { _:bn a owl:Restriction . _:bn owl:onProperty onto:rel . _:bn owl:someValuesFrom onto:B . ?a a _:bn }  WHERE  { ?a a onto:A }""", compare_with_rdflib = False)
    assert r == [1]
    assert len(onto2.graph) == 5
    assert onto.rel.some(onto.B) in onto.a1.is_a
    
  def test_101(self):
    world, onto = self.prepare1()
    onto2 = world.get_ontology("http://test.org/insertions.owl")
    with onto2:
      q, r = self.sparql(world, """INSERT  { ?b a ?? . ?b onto:price ?? . }  WHERE  { ?b a ?? }""", [onto.A, 13.0, onto.B], compare_with_rdflib = False)
    assert r == [3]
    assert len(onto2.graph) == 7
    assert onto.A in onto.b1.is_a
    assert onto.b1.price == [13.0]
    assert onto.A in onto.b2.is_a
    assert onto.b2.price == [13.0]
    assert onto.A in onto.b3.is_a
    assert onto.b3.price == [13.0]
    
  def test_102(self):
    world, onto = self.prepare1()
    onto2 = world.get_ontology("http://test.org/insertions.owl")
    with onto2:
      q, r = self.sparql(world, """INSERT  { ?b onto:annot ??1 . ?b onto:price ??2 . }  WHERE  { ?b a ??1 }""", [onto.B, 9], compare_with_rdflib = False)
    assert r == [3]
    assert len(onto2.graph) == 7
    assert onto.b1.annot == [onto.B]
    assert onto.b1.price == [9]
    assert onto.b2.annot == [onto.B]
    assert onto.b2.price == [9]
    assert onto.b3.annot == [onto.B]
    assert onto.b3.price == [9]
    
  def test_103(self):
    world, onto = self.prepare1()
    onto2 = world.get_ontology("http://test.org/insertions.owl")
    with onto2:
      q, r = self.sparql(world, """INSERT  { ?b onto:annot ??2 . ?b onto:price ??1 . }  WHERE  { ?b a ??2 }""", [9, onto.B], compare_with_rdflib = False)
    assert r == [3]
    assert len(onto2.graph) == 7
    assert onto.b1.annot == [onto.B]
    assert onto.b1.price == [9]
    assert onto.b2.annot == [onto.B]
    assert onto.b2.price == [9]
    assert onto.b3.annot == [onto.B]
    assert onto.b3.price == [9]
    
  def test_104(self):
    world, onto = self.prepare1()
    onto2 = world.get_ontology("http://test.org/insertions.owl")
    with onto2:
      q, r = self.sparql(world, """INSERT  { onto:a1 a onto:B . }  WHERE  {  }""", compare_with_rdflib = False)
    assert r == [1]
    assert len(onto2.graph) == 2
    assert onto.B in onto.a1.is_a
    
  def test_105(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """DELETE  { onto:a1 a onto:A . }  WHERE  {  }""", compare_with_rdflib = False)
    assert r == [1]
    assert onto.a1.is_a == [Thing]
    
  def test_106(self):
    world, onto = self.prepare1()
    onto.a1.annot = [locstr("Oignon", "fr")]
    q, r = self.sparql(world, """SELECT  (CONCAT(?x, "s") AS ?r)  { onto:a1 onto:annot ?x . }""", compare_with_rdflib = False)
    assert len(r) == 1
    assert r == [[locstr("Oignons", "fr")]]
    assert isinstance(r[0][0], locstr)
    assert r[0][0].lang == "fr"
    q, r = self.sparql(world, """SELECT  (CONCAT("Z", ?x) AS ?r)  { onto:a1 onto:annot ?x . }""", compare_with_rdflib = False)
    assert len(r) == 1
    assert r == [[locstr("ZOignon", "fr")]]
    assert isinstance(r[0][0], locstr)
    assert r[0][0].lang == "fr"
    
  def test_107(self):
    world, onto = self.prepare1()
    onto.b1.price = [9.0]
    onto.b2.price = [15.0]
    onto.b3.price = [18.0]
    q, r = self.sparql(world, """SELECT  ?y  {  ?y onto:price ?m . { SELECT  (MIN(?p) AS ?m)  { ?x onto:price ?p . } } }""", compare_with_rdflib = False)
    assert len(r) == 1
    assert r == [[onto.b1]]
    q, r = self.sparql(world, """SELECT  ?y  {  ?y onto:price ?m . { SELECT  (MAX(?p) AS ?m)  { ?x onto:price ?p . } } }""", compare_with_rdflib = False)
    assert len(r) == 1
    assert r == [[onto.b3]]
    
  def test_108(self):
    world, onto = self.prepare1()
    onto.b1.price = [9.0]
    onto.b2.price = [15.0]
    onto.b3.price = [18.0]
    q, r = self.sparql(world, """SELECT  ?y ?x  {  ?y onto:price ?p . { SELECT  ?x (MIN(?p) AS ?m)  { ?x onto:price ?p . } } FILTER(?p < ?m + 2.0) }""", compare_with_rdflib = False)
    assert len(r) == 2
    assert { tuple(x) for x in r } == { (onto.b1, onto.b1), (onto.a1, onto.b1) }
    
  def test_109(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x ?y  {  ?x rdfs:label "Classe A" . ?y a ?z . ?z rdfs:subClassOf* ?x }""", compare_with_rdflib = False)
    assert """AS (SELECT prelim1_objs_q1.s""" in q.sql # Fix o
    assert len(r) == 1
    assert { tuple(x) for x in r } == { (onto.A, onto.a1, ) }
    
  def test_110(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?y  {  ?x rdfs:label "Classe A" . ?y a ?z . ?z rdfs:subClassOf* ?x }""", compare_with_rdflib = False)
    assert """AS (SELECT prelim1_objs_q1.s""" in q.sql # Fix o
    assert len(r) == 1
    assert { tuple(x) for x in r } == { (onto.a1, ) }

  def test_111(self):
    world, onto = self.prepare1()
    onto2 = world.get_ontology("http://test.org/insertions.owl")
    with onto2:
      q, r = self.sparql(world, """INSERT { ?x rdfs:label "un A"@fr } WHERE  { ?x a onto:A . }""", compare_with_rdflib = False)
    assert len(onto.a1.label) == 2
    l = sorted(onto.a1.label)
    assert l[0] == locstr("label_a", "en")
    assert l[0].lang == "en"
    assert l[1] == locstr("un A", "fr")
    assert l[1].lang == "fr"
    del onto.a1.label
    assert len(onto.a1.label) == 2
    assert l[0] == locstr("label_a", "en")
    assert l[0].lang == "en"
    assert l[1] == locstr("un A", "fr")
    assert l[1].lang == "fr"

  def test_112(self):
    world, onto = self.prepare1()
    onto2 = world.get_ontology("http://test.org/insertions.owl")
    with onto2:
      q, r = self.sparql(world, """INSERT { ?x rdfs:label "un A" } WHERE  { ?x a onto:A . }""", compare_with_rdflib = False)
    assert len(onto.a1.label) == 2
    l = sorted(onto.a1.label)
    assert l[0] == locstr("label_a", "en")
    assert l[0].lang == "en"
    assert l[1] == "un A"
    del onto.a1.label
    assert len(onto.a1.label) == 2
    assert l[0] == locstr("label_a", "en")
    assert l[0].lang == "en"
    assert l[1] == "un A"

  def test_113(self):
    world, onto = self.prepare1()
    with onto:
      onto.A.is_a.append(onto.rel.some(onto.B))
    nb = len(onto.graph)
    q, r = self.sparql(world, """DELETE { ?r ?p ?o . } WHERE  { onto:A rdfs:subClassOf ?r . ?r a owl:Restriction . ?r ?p ?o . }""", compare_with_rdflib = False)
    assert len(onto.graph) == nb - 3
    
  def test_114(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x ?y  { ?x a onto:A.  ?x rdfs:label ?y. }""")
    assert len(r) == 1
    assert r == [[onto.a1, locstr("label_a", "en")]]
    assert q.column_names == ["?x", "?y"]
    
  def test_115(self):
    world, onto = self.prepare1()
    onto.a1.label = ['''test " ' ''']
    q, r = self.sparql(world, """SELECT  ?x ?y  { ?x rdfs:label ?y. } ORDER BY DESC(?y)""")
    
    csv = q.execute_csv()
    assert csv.replace("\r", "") == """x,y
http://test.org/onto.owl#a1,"test "" ' "
http://test.org/onto.owl#rel,rel
http://test.org/onto.owl#price,price
http://test.org/onto.owl#b3,label_b
http://test.org/onto.owl#b2,label_b
http://test.org/onto.owl#b1,label_b
http://test.org/onto.owl#A1,Classe A1
http://test.org/onto.owl#A,Classe A
""".replace("\r", "")
    
    tsv = q.execute_tsv()
    assert tsv.replace("\r", "") == """x\ty
http://test.org/onto.owl#a1\t"test "" ' "
http://test.org/onto.owl#rel\trel
http://test.org/onto.owl#price\tprice
http://test.org/onto.owl#b3\tlabel_b
http://test.org/onto.owl#b2\tlabel_b
http://test.org/onto.owl#b1\tlabel_b
http://test.org/onto.owl#A1\tClasse A1
http://test.org/onto.owl#A\tClasse A
""".replace("\r", "")

    json = q.execute_json()
    assert eval(json) == {'head': {'vars': ['x', 'y']}, 'results': {'bindings': [{'x': {'type': 'uri', 'value': 'http://test.org/onto.owl#a1'}, 'y': {'type': 'literal', 'value': 'test " \' ', 'datatype': 'http://www.w3.org/2001/XMLSchema#string'}}, {'x': {'type': 'uri', 'value': 'http://test.org/onto.owl#rel'}, 'y': {'type': 'literal', 'value': 'rel', 'datatype': 'http://www.w3.org/2001/XMLSchema#string'}}, {'x': {'type': 'uri', 'value': 'http://test.org/onto.owl#price'}, 'y': {'type': 'literal', 'value': 'price', 'datatype': 'http://www.w3.org/2001/XMLSchema#string'}}, {'x': {'type': 'uri', 'value': 'http://test.org/onto.owl#b3'}, 'y': {'type': 'literal', 'value': 'label_b', 'xml:lang': 'fr'}}, {'x': {'type': 'uri', 'value': 'http://test.org/onto.owl#b2'}, 'y': {'type': 'literal', 'value': 'label_b', 'xml:lang': 'en'}}, {'x': {'type': 'uri', 'value': 'http://test.org/onto.owl#b1'}, 'y': {'type': 'literal', 'value': 'label_b', 'xml:lang': 'en'}}, {'x': {'type': 'uri', 'value': 'http://test.org/onto.owl#A1'}, 'y': {'type': 'literal', 'value': 'Classe A1', 'datatype': 'http://www.w3.org/2001/XMLSchema#string'}}, {'x': {'type': 'uri', 'value': 'http://test.org/onto.owl#A'}, 'y': {'type': 'literal', 'value': 'Classe A', 'datatype': 'http://www.w3.org/2001/XMLSchema#string'}}]}}
    
    xml = q.execute_xml()
    assert xml.replace("\r", "") == '<?xml version="1.0"?>\n<sparql xmlns="http://www.w3.org/2005/sparql-results#">\n  <head>\n    <variable name="x"/>\n    <variable name="y"/>\n  </head>\n  <results>\n    <result>\n      <binding name="x">\n        <uri>http://test.org/onto.owl#a1</uri>\n      </binding>\n      <binding name="y">\n        <literal datatype="http://www.w3.org/2001/XMLSchema#string">test " \' </literal>\n      </binding>\n    </result>\n    <result>\n      <binding name="x">\n        <uri>http://test.org/onto.owl#rel</uri>\n      </binding>\n      <binding name="y">\n        <literal datatype="http://www.w3.org/2001/XMLSchema#string">rel</literal>\n      </binding>\n    </result>\n    <result>\n      <binding name="x">\n        <uri>http://test.org/onto.owl#price</uri>\n      </binding>\n      <binding name="y">\n        <literal datatype="http://www.w3.org/2001/XMLSchema#string">price</literal>\n      </binding>\n    </result>\n    <result>\n      <binding name="x">\n        <uri>http://test.org/onto.owl#b3</uri>\n      </binding>\n      <binding name="y">\n        <literal xml:lang="fr">label_b</literal>\n      </binding>\n    </result>\n    <result>\n      <binding name="x">\n        <uri>http://test.org/onto.owl#b2</uri>\n      </binding>\n      <binding name="y">\n        <literal xml:lang="en">label_b</literal>\n      </binding>\n    </result>\n    <result>\n      <binding name="x">\n        <uri>http://test.org/onto.owl#b1</uri>\n      </binding>\n      <binding name="y">\n        <literal xml:lang="en">label_b</literal>\n      </binding>\n    </result>\n    <result>\n      <binding name="x">\n        <uri>http://test.org/onto.owl#A1</uri>\n      </binding>\n      <binding name="y">\n        <literal datatype="http://www.w3.org/2001/XMLSchema#string">Classe A1</literal>\n      </binding>\n    </result>\n    <result>\n      <binding name="x">\n        <uri>http://test.org/onto.owl#A</uri>\n      </binding>\n      <binding name="y">\n        <literal datatype="http://www.w3.org/2001/XMLSchema#string">Classe A</literal>\n      </binding>\n    </result>\n  </results>\n</sparql>\n'.replace("\r", "")
    
  def test_116(self):
    import flask, werkzeug.serving, urllib.request, time
    from owlready2.sparql.endpoint import EndPoint
    world, onto = self.prepare1()
    
    app = flask.Flask("OwlreadyTest")
    endpoint = EndPoint(world)
    app.route("/sparql", methods = ["GET"])(endpoint)
    
    p = multiprocessing.Process(target = werkzeug.serving.run_simple, args = ("localhost", 5032, app))
    p.start()
    
    time.sleep(0.3)
    r = urllib.request.urlopen("http://localhost:5032/sparql?query=SELECT%20%20?x%20?y%20%20{%20?x%20rdfs:label%20?y.%20}%20ORDER%20BY%20DESC(?y)").read()
    assert r == b'x,y\r\nhttp://test.org/onto.owl#rel,rel\r\nhttp://test.org/onto.owl#price,price\r\nhttp://test.org/onto.owl#b3,label_b\r\nhttp://test.org/onto.owl#b2,label_b\r\nhttp://test.org/onto.owl#b1,label_b\r\nhttp://test.org/onto.owl#a1,label_a\r\nhttp://test.org/onto.owl#A1,Classe A1\r\nhttp://test.org/onto.owl#A,Classe A\r\n'
    
    r = urllib.request.urlopen(urllib.request.Request("http://localhost:5032/sparql?query=SELECT%20%20?x%20?y%20%20{%20?x%20rdfs:label%20?y.%20}%20ORDER%20BY%20DESC(?y)", headers = { "Accept" : "application/json" })).read()
    assert r == b"{'head': {'vars': ['x', 'y']}, 'results': {'bindings': [{'x': {'type': 'uri', 'value': 'http://test.org/onto.owl#rel'}, 'y': {'type': 'literal', 'value': 'rel', 'datatype': 'http://www.w3.org/2001/XMLSchema#string'}}, {'x': {'type': 'uri', 'value': 'http://test.org/onto.owl#price'}, 'y': {'type': 'literal', 'value': 'price', 'datatype': 'http://www.w3.org/2001/XMLSchema#string'}}, {'x': {'type': 'uri', 'value': 'http://test.org/onto.owl#b3'}, 'y': {'type': 'literal', 'value': 'label_b', 'xml:lang': 'fr'}}, {'x': {'type': 'uri', 'value': 'http://test.org/onto.owl#b2'}, 'y': {'type': 'literal', 'value': 'label_b', 'xml:lang': 'en'}}, {'x': {'type': 'uri', 'value': 'http://test.org/onto.owl#b1'}, 'y': {'type': 'literal', 'value': 'label_b', 'xml:lang': 'en'}}, {'x': {'type': 'uri', 'value': 'http://test.org/onto.owl#a1'}, 'y': {'type': 'literal', 'value': 'label_a', 'xml:lang': 'en'}}, {'x': {'type': 'uri', 'value': 'http://test.org/onto.owl#A1'}, 'y': {'type': 'literal', 'value': 'Classe A1', 'datatype': 'http://www.w3.org/2001/XMLSchema#string'}}, {'x': {'type': 'uri', 'value': 'http://test.org/onto.owl#A'}, 'y': {'type': 'literal', 'value': 'Classe A', 'datatype': 'http://www.w3.org/2001/XMLSchema#string'}}]}}"
    
    p.terminate()
    
  def test_117(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT DISTINCT ?x ?l  { { ?x rdfs:label ?l. } UNION { ?x rdfs:label ?l. } } ORDER BY ?l""")
    assert set(tuple(x) for x in r) == set(tuple(x) for x in [[onto.A, 'Classe A'], [onto.A1, 'Classe A1'], [onto.a1, locstr('label_a', "en")], [onto.b1, locstr('label_b', "en")], [onto.b2, locstr('label_b', "en")], [onto.b3, locstr('label_b', "fr")], [onto.price, 'price'], [onto.rel, 'rel']])
    
  def test_118(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT DISTINCT (xsd:integer(?p) as ?p2)  { ?x onto:price ?p. }""", compare_with_rdflib = False)
    assert r == [[10]]
    assert isinstance(r[0][0], int)
    
    onto.a1.price = [11]
    q, r = self.sparql(world, """SELECT DISTINCT (xsd:double(?p) as ?p2)  { ?x onto:price ?p. }""")
    assert r == [[11.0]]
    assert isinstance(r[0][0], float)
    
  def test_119(self):
    world, onto = self.prepare1()
    e = set(tuple(x) for x in [[None, 6, 11], [None, 9, Thing], [None, label, 'Classe A'], [onto.A1, 9, None], [onto.A2, 9, None], [onto.a1, 6, None]])
    
    q, r = self.sparql(world, """SELECT ?s ?p ?o { { ?s ?p onto:A } UNION { onto:A ?p ?o } }""")
    assert set(tuple(x) for x in r) == e
    
    q, r = self.sparql(world, """SELECT ?s ?p ?o { { onto:A ?p ?o } UNION { ?s ?p onto:A } }""")
    assert set(tuple(x) for x in r) == e
    
  def test_120(self):
    world, onto = self.prepare1()
    a2 = onto.A(label = "XXX")
    
    q, r = self.sparql(world, """SELECT ?x { ?x rdfs:label ?l. FILTER(CONTAINS(?l, "_a")) }""")
    assert r == [[onto.a1]]
    
    q, r = self.sparql(world, """SELECT ?x { ?x rdfs:label ?l. { FILTER(CONTAINS(?l, "_a")) } }""")
    assert r == [[onto.a1]]
    
    q, r = self.sparql(world, """SELECT ?x { ?x rdfs:label ?l. { FILTER(CONTAINS(?l, "_a")) } UNION { FILTER(CONTAINS(?l, "_b")) } }""")
    assert set(x[0] for x in r) == { onto.a1, onto.b1, onto.b2, onto.b3 }
    
  def test_121(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT ?x ?l { ?x rdfs:subClassOf* onto:A. ?x rdfs:label ?l. }""")
    assert set(tuple(x) for x in r) == { (onto.A, 'Classe A'), (onto.A1, 'Classe A1') }
    assert " IN " in q.sql
    
    q, r = self.sparql(world, """SELECT ?x { ?x a ?y. ?y rdfs:subClassOf* onto:A. }""")
    assert set(x[0] for x in r) == { onto.a1 }
    assert " IN " in q.sql
    
    q, r = self.sparql(world, """SELECT ?x { ?x a ?y. ?y rdfs:subClassOf* ?r. ?r rdfs:label "Classe A". }""")
    assert set(x[0] for x in r) == { onto.a1 }
    assert " IN " in q.sql
    
    q, r = self.sparql(world, """SELECT ?x { ?x rdfs:subClassOf* onto:A. }""")
    assert set(x[0] for x in r) == { onto.A, onto.A1, onto.A11, onto.A2 }
    assert not " IN " in q.sql
    
    q, r = self.sparql(world, """SELECT ?x { ?x rdfs:subClassOf* onto:A. FILTER(ISIRI(?x)) }""")
    assert set(x[0] for x in r) == { onto.A, onto.A1, onto.A11, onto.A2 }
    assert not " IN " in q.sql
    
    q, r = self.sparql(world, """SELECT ?x ?l { ?x rdfs:subClassOf* onto:A. ?x rdfs:label ?l. FILTER(ISIRI(?x)) }""")
    assert set(tuple(x) for x in r) == { (onto.A, 'Classe A'), (onto.A1, 'Classe A1') }
    assert " IN " in q.sql
    
    with onto:
      class A1B(onto.A1, onto.B): pass
      A1B.label = "A1B"
    q, r = self.sparql(world, """SELECT ?x ?l { ?x rdfs:subClassOf* onto:A. ?x rdfs:subClassOf* onto:B. ?x rdfs:label ?l. }""")
    assert r == [[A1B, "A1B"]]
    assert q.sql.count(" IN ") == 2
    
    q, r = self.sparql(world, """SELECT ?x { ?x rdfs:subClassOf* onto:A. ?x rdfs:subClassOf* onto:B. }""")
    assert r == [[A1B]]
    
  def test_122(self):
    world, onto = self.prepare1()
    onto.A11.comment.append("ok")
    q, r = self.sparql(world, """SELECT ?x { ?x rdfs:subClassOf* onto:A. { ?x rdfs:label "Classe A1". } UNION { ?x rdfs:comment "ok". } }""")
    assert set(x[0] for x in r) == { onto.A1, onto.A11 }

  def test_123(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT ?x { onto:a1 onto:rel|onto:subrel ?x }""")
    assert set(x[0] for x in r) == { onto.b2, onto.b3 }
    q, r = self.sparql(world, """SELECT ?x { ?x ^(onto:rel|onto:subrel) onto:a1 }""")
    assert set(x[0] for x in r) == { onto.b2, onto.b3 }
    
  def test_124(self):
    world, onto = self.prepare1()
    onto.A1.equivalent_to.append(onto.B)
    q, r = self.sparql(world, """SELECT ?i { ?i a ?c .  ?c (rdfs:subClassOf|owl:equivalentClass|^owl:equivalentClass)* onto:A . }""")
    assert set(x[0] for x in r) == { onto.a1, onto.b1, onto.b2, onto.b3 }
    
  def test_125(self):
    world, onto = self.prepare1()
    onto.A11.equivalent_to.append(onto.C)
    onto.B.equivalent_to.append(onto.C)
    q, r = self.sparql(world, """SELECT ?i { ?i a ?c .  ?c (rdfs:subClassOf|owl:equivalentClass|^owl:equivalentClass)* onto:A . }""")
    assert set(x[0] for x in r) == { onto.a1, onto.b1, onto.b2, onto.b3 }
    
  def test_126(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT ?i { { ?i rdfs:subClassOf* onto:A } UNION { ?i rdfs:subClassOf* onto:B } }""")
    assert q.sql.count("UNION") == 1
        
  def test_127(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT DISTINCT ?x ?r { ?x onto:price ?r . { ?x onto:rel onto:b2 } UNION { ?x onto:subrel onto:b3 } }""")
    assert r == [[onto.a1, 10.0]]
    
  def test_128(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT ?r { onto:a1 onto:price ?r . { onto:a1 onto:rel onto:b2 } UNION { onto:a1 onto:subrel onto:b3 } }""", compare_with_rdflib = False)
    assert r == [[10.0]]
    q, r = self.sparql(world, """SELECT ?r { onto:a1 onto:price ?r . { onto:a1 onto:rel onto:b1 } UNION { onto:a1 onto:subrel onto:b1 } }""", compare_with_rdflib = False)
    assert r == []
        
  def test_129(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT ?x { FILTER(STRSTARTS(STR(?x), "http://test.org/onto.owl#b")) }""", compare_with_rdflib = False)
    assert set(i[0] for i in r) == { onto.b1, onto.b2, onto.b3 }
    
  def test_130(self):
    world, onto = self.prepare1()
    onto.b1.label = ["b1"]
    onto.b2.label = ["b2"]
    onto.b3.label = ["b3"]
    q, r = self.sparql(world, """SELECT ?x { ?x rdfs:label ?l . VALUES ?l { "b1" "b2" } }""", compare_with_rdflib = False)
    assert set(i[0] for i in r) == { onto.b1, onto.b2 }

    q, r = self.sparql(world, """SELECT ?x { ?x ?p ?l . VALUES (?p ?l) { (rdfs:label "b1") (rdfs:label "b3") } }""", compare_with_rdflib = False)
    assert set(i[0] for i in r) == { onto.b1, onto.b3 }
    
  def test_131(self):
    world, onto = self.prepare1()
    a11 = onto.A11()
    q, r = self.sparql(world, """SELECT ?x { ?x a ?c . ?c rdfs:subClassOf* onto:A . }""", compare_with_rdflib = False)
    assert set(i[0] for i in r) == { onto.a1, a11 }
    
    q, r = self.sparql(world, """SELECT ?x { ?x a ?c . STATIC { ?c rdfs:subClassOf* onto:A . } }""", compare_with_rdflib = False)
    assert not "WITH" in q.sql
    assert set(i[0] for i in r) == { onto.a1, a11 }
    
  def test_132(self):
    world, onto = self.prepare1()
    a11 = onto.A11()
    q, r = self.sparql(world, """SELECT ?x { ?x a ?c . STATIC { ?c rdfs:subClassOf* ?a . ?a rdfs:label "Classe A" } }""", compare_with_rdflib = False)
    assert not "WITH" in q.sql
    assert set(i[0] for i in r) == { onto.a1, a11 }
    
  def test_133(self):
    world, onto = self.prepare1()
    a11 = onto.A11()
    a1  = onto.A1(label = ["Classe A1"])
    
    q, r = self.sparql(world, """SELECT ?x { ?x a ?c . ?x rdfs:label ?l . ?c rdfs:subClassOf* onto:A . ?c rdfs:label ?l }""", compare_with_rdflib = False)
    assert set(i[0] for i in r) == { a1 }
    
    q, r = self.sparql(world, """SELECT ?x { ?x a ?c . ?x rdfs:label ?l . STATIC { ?c rdfs:subClassOf* onto:A . ?c rdfs:label ?l } }""", compare_with_rdflib = False)
    assert not "RECURSIVE" in q.sql
    assert set(i[0] for i in r) == { a1 }
    
  def test_134(self):
    world, onto = self.prepare1()
    a11 = onto.A11()
    onto.A11.label = ["LLL"]
    q, r = self.sparql(world, """SELECT ?x ?l { ?x a ?c . STATIC { ?c rdfs:subClassOf* onto:A . ?c rdfs:label ?l } }""", compare_with_rdflib = False)
    assert set(tuple(i) for i in r) == { (onto.a1, "Classe A"), (a11, "LLL") }
    
  def test_135(self):
    world, onto = self.prepare1()
    a11 = onto.A11()
    q, r = self.sparql(world, """SELECT ?x { ?x a/rdfs:subClassOf*STATIC onto:A . }""", compare_with_rdflib = False)
    assert not "WITH" in q.sql
    assert set(i[0] for i in r) == { onto.a1, a11 }
    
    q, r = self.sparql(world, """SELECT ?x { ?x a/rdfs:subClassOf*STATIC/rdfs:label "Classe A" . }""", compare_with_rdflib = False)
    assert not "WITH" in q.sql
    assert set(i[0] for i in r) == { onto.a1, a11 }

  def test_136(self):
    world = self.new_world()
    onto = world.get_ontology("http://test.org/onto.owl")
    with onto:
      class C(Thing): pass
      class D(Thing): pass
      C.label = ["l1"]
      D.label = ["l1"]
      c = C()
      c.label = ["l3"]
      d = D()
      d.label = ["l4"]
      
      nb = world.sparql("""
INSERT {
  [
    rdf:type owl:Axiom ;
    owl:annotatedSource ?c ; 
    owl:annotatedProperty rdfs:label ; 
    owl:annotatedTarget ?l ; 
  ] rdfs:comment "Annotation sur une relation" .
}
WHERE {
  ?c rdfs:label ?l .
  ?c a owl:Class .
}
""")
      assert nb == 2
      
    assert comment[C, label, "l1"] == ['Annotation sur une relation']

  def test_137(self):
    world = self.new_world()
    onto = world.get_ontology("http://test.org/onto.owl")
    with onto:
      class C(Thing): pass
      class p(Thing >> Thing): pass
      
      c1 = C()
      c2 = C()
      c1.p = [c2]
      
      nb = world.sparql("""
INSERT {
  [
    rdf:type owl:Axiom ;
    owl:annotatedSource ?a ; 
    owl:annotatedProperty onto:p ; 
    owl:annotatedTarget ?b ; 
  ] rdfs:comment "Annotation sur une relation" .
}
WHERE {
  ?a onto:p ?b .
}
""")
      assert nb == 1
      
    assert comment[c1, p, c2] == ['Annotation sur une relation']

  def test_138(self):
    world, onto = self.prepare1()
    a11 = onto.A11()
    q, r = self.sparql(world, """SELECT ?x { { ?x a/rdfs:subClassOf*STATIC onto:A . } UNION { ?x a/rdfs:subClassOf*STATIC onto:B . } }""", compare_with_rdflib = False)
    assert not "WITH" in q.sql
    assert set(i[0] for i in r) == { onto.a1, a11, onto.b1, onto.b2, onto.b3 }
    
  def test_139(self):
    world, onto = self.prepare1()
    a11 = onto.A11()
    q, r = self.sparql(world, """SELECT ?x { { ?x rdfs:subClassOf* onto:A . } UNION { ?x rdfs:subClassOf*STATIC onto:B . } }""", compare_with_rdflib = False)
    assert set(i[0] for i in r) == { onto.A, onto.A1, onto.A11, onto.A2, onto.B }

    q, r = self.sparql(world, """SELECT ?x { { ?x rdfs:subClassOf*STATIC onto:A . } UNION { ?x rdfs:subClassOf*STATIC onto:B . } }""", compare_with_rdflib = False)
    assert not "WITH" in q.sql
    assert set(i[0] for i in r) == { onto.A, onto.A1, onto.A11, onto.A2, onto.B }
    
  def test_140(self):
    world, onto = self.prepare1()
    q1, r = self.sparql(world, """SELECT  (CONCAT(??, ?l) AS ?l2) { ?? rdfs:label ?l }""", [locstr("test_", "fr"), onto.a1], compare_with_rdflib = False)
    assert q1.nb_parameter == 2
    assert len(r) == 1
    assert { x[0] for x in r } == { locstr("test_label_a", "fr") }
    assert isinstance(r[0][0], locstr)
    assert r[0][0].lang == "fr"
    
  def test_141(self):
    world, onto = self.prepare1()
    a11 = onto.A1()
    q, r = self.sparql(world, """SELECT  ?x { ?x a ?c . { ?c rdfs:subClassOf* onto:A } UNION { ?c rdfs:subClassOf onto:B } }""", compare_with_rdflib = False)
    assert { i[0] for i in r } == { a11, onto.a1 }
    q, r = self.sparql(world, """SELECT  ?x { ?x a ?c . { ?c rdfs:subClassOf onto:A } UNION { ?c rdfs:subClassOf* onto:B } }""", compare_with_rdflib = False)
    assert { i[0] for i in r } == { a11, onto.b1, onto.b2, onto.b3 }
    
  def test_142(self):
    world, onto = self.prepare1()
    q, r = self.sparql(world, """SELECT  ?x { ?x a ?c . { ?c rdfs:subClassOf* onto:A } UNION { ?c rdfs:subClassOf* onto:B } }""", compare_with_rdflib = False)
    assert { i[0] for i in r } == { onto.a1, onto.b1, onto.b2, onto.b3 }
    
  def test_143(self):
    world, onto = self.prepare1()
    with onto:
      class C(Thing): pass
      C()
      a111 = onto.A11()
      
    q = world.prepare_sparql("""SELECT  ?x { ?x a ?c . { ?c rdfs:subClassOf*STATIC onto:A } UNION { ?c rdfs:subClassOf onto:B } }""")
    q, r = self.sparql(world, """SELECT  ?x { ?x a ?c . { ?c rdfs:subClassOf*STATIC onto:A } UNION { ?c rdfs:subClassOf onto:B } }""", compare_with_rdflib = False)
    assert { i[0] for i in r } == { onto.a1, a111 }
    q, r = self.sparql(world, """SELECT  ?x { ?x a ?c . { ?c rdfs:subClassOf* onto:A } UNION { ?c rdfs:subClassOf* onto:B } }""", compare_with_rdflib = False)
    assert { i[0] for i in r } == { onto.a1, a111, onto.b1, onto.b2, onto.b3 }
    q, r = self.sparql(world, """SELECT  ?x { ?x a ?c . { ?c rdfs:subClassOf* onto:A } UNION { ?c rdfs:subClassOf*STATIC onto:B } }""", compare_with_rdflib = False)
    assert { i[0] for i in r } == { onto.a1, a111, onto.b1, onto.b2, onto.b3 }
    q, r = self.sparql(world, """SELECT  ?x { ?x a ?c . { ?c rdfs:subClassOf*STATIC onto:A } UNION { ?c rdfs:subClassOf*STATIC onto:B } }""", compare_with_rdflib = False)
    assert { i[0] for i in r } == { onto.a1, a111, onto.b1, onto.b2, onto.b3 }
    
    #q, r = self.sparql(world, """SELECT  ?x { ?x a ?c . { ?c rdfs:subClassOf*STATIC onto:A } }""", compare_with_rdflib = False)
    #print(r)
    #print(q.sql)
    #assert { i[0] for i in r } == { onto.a1, a111 }
    
  def test_144(self):
    world, onto = self.prepare1()
    onto.A.label = ["xxx", onto.a1]

    import owlready2.sparql.parser
    save = owlready2.sparql.parser._DATA_PROPS
    owlready2.sparql.parser._DATA_PROPS = set()
    
    q, r = self.sparql(world, """SELECT  ?l { onto:A rdfs:label ?l . ?l a onto:A . }""", compare_with_rdflib = False)
    assert r == [[onto.a1]]
    
    q, r = self.sparql(world, """SELECT  ?l ?c { onto:A rdfs:label ?l . OPTIONAL { ?l a ?c . } }""", compare_with_rdflib = False)
    assert set(tuple(i) for i in r) == { ("xxx", None), (onto.a1, onto.A), (onto.a1, NamedIndividual) }
    
    owlready2.sparql.parser._DATA_PROPS = save
    
  def test_145(self):
    world, onto = self.prepare1()
    
    q, r = self.sparql(world, """
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT (DATETIME_SUB("2022-01-14T13:36:14.538042", "P1Y"^^xsd:duration) AS ?x)
WHERE {}
    """, compare_with_rdflib = False)
    assert r[0][0] == datetime.datetime(2021, 1, 14, 13, 36, 14, 538042)
    
    q, r = self.sparql(world, """
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT (DATETIME_ADD("2022-01-14T13:36:14.538042", "PT1S"^^xsd:duration) AS ?x)
WHERE {}
    """, compare_with_rdflib = False)
    assert r[0][0] == datetime.datetime(2022, 1, 14, 13, 36, 15, 538042)
    
    q, r = self.sparql(world, """
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT (DATE_SUB("2022-01-14", "P2D"^^xsd:duration) AS ?x)
WHERE {}
    """, compare_with_rdflib = False)
    assert r[0][0] == datetime.date(2022, 1, 12)
    
    q, r = self.sparql(world, """
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT (DATE_ADD("2022-01-14", "P1D"^^xsd:duration) AS ?x)
WHERE {}
    """, compare_with_rdflib = False)
    assert r[0][0] == datetime.date(2022, 1, 15)
    
    q, r = self.sparql(world, """
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT (DATE_DIFF("2022-01-14", "2022-01-28") AS ?x)
WHERE {}
    """, compare_with_rdflib = False)
    assert r[0][0] == datetime.timedelta(days = 14)
    
    q, r = self.sparql(world, """
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT (DATETIME_DIFF("2022-01-14T13:36:14"^^xsd:dateTime, "2022-01-14T13:36:24") AS ?x)
WHERE {}
    """, compare_with_rdflib = False)
    assert r[0][0] == datetime.timedelta(seconds = 10)

    
  def test_146(self):
    world, onto = self.prepare1()
    
    q, r = self.sparql(world, """
SELECT (<http://test.org/onto.owl#A> AS ?a)
WHERE { 
    <http://test.org/onto.owl#A> a ?class .
    <http://test.org/onto.owl#A> onto:rel ?x .
 }
    """, compare_with_rdflib = False)
    assert r == []

    q, r = self.sparql(world, """
SELECT (<http://test.org/onto.owl#A> AS ?a)
WHERE { 
    <http://test.org/onto.owl#A> a ?class .
          { <http://test.org/onto.owl#A> onto:rel ?x . }
    UNION { <http://test.org/onto.owl#A> onto:rel ?x . }
 }
    """, compare_with_rdflib = False)
    assert r == []
    
    q, r = self.sparql(world, """
SELECT (<http://test.org/onto.owl#A> AS ?a)
WHERE { 
    <http://test.org/onto.owl#A> a ?class .
          { <http://test.org/onto.owl#A> onto:rel ?x . }
    UNION { <http://test.org/onto.owl#A> onto:rel ?y . }
 }
    """, compare_with_rdflib = False)
    assert r == []

    q, r = self.sparql(world, """
SELECT (<http://test.org/onto.owl#A> AS ?a)
WHERE { 
    <http://test.org/onto.owl#A> a ?class .
    ?x a ?class .
          { <http://test.org/onto.owl#A> onto:rel ?x . }
    UNION { <http://test.org/onto.owl#A> onto:rel ?x . }
 }
    """, compare_with_rdflib = False)
    assert r == []
    assert " IN (SELECT" in q.sql
    
    q, r = self.sparql(world, """
SELECT ?a
WHERE { 
    ?a a onto:A .
          { ?a onto:rel ?x . }
    UNION { ?a onto:price ?y . }
 }
    """, compare_with_rdflib = False)
    assert r == [[onto.a1]]
    assert " IN (SELECT" in q.sql
    
  def test_147(self):
    world, onto = self.prepare1()
    onto.a1.price = [19]
    
    q, r = self.sparql(world, """
SELECT ?price WHERE {
  STATIC { onto:a1 onto:price ?price. }
}
""", compare_with_rdflib = False)
    assert r == [[19]]
    
    q, r = self.sparql(world, """
SELECT ?price ?x WHERE {
  STATIC { onto:a1 onto:price ?price. onto:a1 onto:rel ?x. }
}
""", compare_with_rdflib = False)
    assert r == [[19, onto.b2]]
    
  def test_148(self):
    world, onto = self.prepare1()
    
    q, r = self.sparql(world, """
SELECT ?x ?price WHERE {
VALUES ?x { <http://test.org/onto.owl#a1> } .
?x onto:price ?price .
}
""")
    assert r == [[onto.a1, 10.0]]
    
    q, r = self.sparql(world, """
SELECT ?x ?price WHERE {
VALUES ?x { <http://test.org/onto.owl#a1> } .
<http://test.org/onto.owl#a1> onto:price ?price .
}
""")
    assert r == [[onto.a1, 10.0]]

    q, r = self.sparql(world, """
SELECT ?a ?b ?price WHERE {
VALUES (?a ?b) { (<http://test.org/onto.owl#a1> <http://test.org/onto.owl#b1>) } .
?a onto:price ?price .
}
""")
    assert r == [[onto.a1, onto.b1, 10.0]]

    q, r = self.sparql(world, """
SELECT ?a ?b ?price WHERE {
VALUES (?a ?b) { (<http://test.org/onto.owl#a1> <http://test.org/onto.owl#b1>) } .
OPTIONAL { ?a onto:price ?price . }
}
""", compare_with_rdflib = False)
    assert r == [[onto.a1, onto.b1, 10.0]]

    q, r = self.sparql(world, """
SELECT ?a ?b ?price WHERE {
VALUES (?a ?b) { (<http://test.org/onto.owl#a1> <http://test.org/onto.owl#b1>) } .
OPTIONAL { ?b onto:price ?price . }
}
""", compare_with_rdflib = False)
    assert r == [[onto.a1, onto.b1, None]]

  def test_149(self):
    world, onto = self.prepare1()
    
    q, r = self.sparql(world, """
SELECT ?a ?b ?l WHERE {
VALUES (?a ?c) { (<http://test.org/onto.owl#a1> <http://test.org/onto.owl#b1>) } .
OPTIONAL { ?a onto:rel ?b . } OPTIONAL { ?b rdfs:label ?l . } .
}
""", compare_with_rdflib = False)
    
    assert "JOIN" in q.sql
    assert r == [[onto.a1, onto.b2, locstr("label_b", "en")]]

  def test_150(self):
    world, onto = self.prepare1()
    #a2 = onto.A(label = [locstr("label_a2", "en")], rel = [onto.a1])
    
    q, r = self.sparql(world, """
SELECT ?n WHERE {
    FILTER NOT EXISTS {
    onto:b1 a ?c .
    ?c rdfs:subClassOf* onto:A .
    }
    BIND(NEWINSTANCEIRI(onto:A) AS ?n).
}
""", compare_with_rdflib = False)

    assert len(r) == 1

    q, r = self.sparql(world, """
SELECT ?n WHERE {
    FILTER NOT EXISTS {
    onto:a1 a ?c .
    ?c rdfs:subClassOf* onto:A .
    }
    BIND(NEWINSTANCEIRI(onto:A) AS ?n).
}
""", compare_with_rdflib = False)

    assert len(r) == 0
    
    q, r = self.sparql(world, """
SELECT ?n WHERE {
    FILTER NOT EXISTS {
    onto:b1 a ?c .
    ?c rdfs:subClassOf*STATIC onto:A .
    }
    BIND(NEWINSTANCEIRI(onto:A) AS ?n).
}
""", compare_with_rdflib = False)

    assert len(r) == 1
    
    q, r = self.sparql(world, """
SELECT ?n WHERE {
    FILTER NOT EXISTS {
    onto:a1 a ?c .
    ?c rdfs:subClassOf*STATIC onto:A .
    }
    BIND(NEWINSTANCEIRI(onto:A) AS ?n).
}
""", compare_with_rdflib = False)

    assert len(r) == 0

  def test_151(self):
    world = self.new_world()
    
    onto = world.get_ontology("http://test.org/onto.owl#")
    
    with onto:
      class phone(DataProperty): pass
      class postcode(DataProperty): pass
      
      class C(Thing): pass
      c = C("obj_a", postcode = ["75019"], phone = ["06"])
      c = C("obj_b", postcode = ["75020"])
    
    q, r = self.sparql(world, """
SELECT * WHERE {
    VALUES ?name { onto:obj_a }.
    OPTIONAL { ?name onto:postcode ?postcode . }
    OPTIONAL { ?name onto:phone    ?phone . }
}""", compare_with_rdflib = False)
    assert r == [[onto.obj_a, "75019", "06"]]

    q, r = self.sparql(world, """
SELECT * WHERE {
    VALUES ?name { onto:obj_b }.
    OPTIONAL { ?name onto:postcode ?postcode . }
    OPTIONAL { ?name onto:phone    ?phone . }
}""", compare_with_rdflib = False)
    assert r == [[onto.obj_b, "75020", None]]
    
  def test_152(self):
    world, onto = self.prepare1()
    
    q, r = self.sparql(world, """
SELECT ?x WHERE { onto:a1 a ?x }
""", compare_with_rdflib = False)
    
  def test_153(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/onto.owl")
    with onto:
      class Cé(Thing): pass
      c = Cé()
      
    q, r = self.sparql(world, """
SELECT ?x WHERE { ?x a onto:Cé }
""", compare_with_rdflib = True)
    
  def test_154(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/onto.owl")
    with onto:
      class C(Thing): pass
      c1 = C(label = True)
      c2 = C(label = False)
      
    q, r = self.sparql(world, """SELECT ?x WHERE { ?x rdfs:label true }""", compare_with_rdflib = True)
    assert r == [[c1]]
    
    q, r = self.sparql(world, """SELECT ?x WHERE { ?x rdfs:label false }""", compare_with_rdflib = True)
    assert r == [[c2]]
    
  def test_155(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/onto.owl")
    with onto:
      class C(Thing): pass
      class D(Thing): pass
      class p(C >> D): pass
      class p1(C >> D): pass
      class p2(C >> D): pass
      class p3(C >> D): pass
      
      d1 = D()
      d2 = D()
      d3 = D()
      
      c1 = C(p = [d1, d2], p1 = [d1, d2], p2 = [d1, d2], p3 = [d1, d2])
      c2 = C(p = [d1, d3], p1 = [d1, d3], p2 = [d1, d3], p3 = [d1, d3])
      c3 = C(p = [d2, d3], p1 = [d2, d3], p2 = [d2, d3], p3 = [d2, d3])
      
    q, r = self.sparql(world, """SELECT DISTINCT ?x WHERE { { ?x onto:p onto:d1 } UNION { ?x onto:p onto:d2 } FILTER NOT EXISTS { ?x onto:p onto:d3 } }""", compare_with_rdflib = True)
    assert r == [[c1]]
    
    q = world.prepare_sparql("""INSERT { onto:D rdfs:label "ok2" } WHERE { { ?x onto:p1 onto:d1 } UNION { ?x onto:p2 onto:d2 } FILTER NOT EXISTS { ?x onto:p3 onto:d3 } }""")
    with onto: q.execute()
    assert D.label == ["ok2"]

  def test_156(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/onto.owl")
    with onto:
      class C(Thing): pass
      
      c1 = C()
      
    q, r = self.sparql(world, """SELECT (1 AS ?r) { FILTER NOT EXISTS { onto:c1 rdfs:label ?x } }""", compare_with_rdflib = True)
    assert r == [[1]]
    
    with onto:
      q, r = self.sparql(world, """INSERT { onto:C rdfs:label "ok" } WHERE { FILTER NOT EXISTS { onto:c1 rdfs:label ?x } }""", compare_with_rdflib = True)
    assert C.label == ["ok"]

  def test_157(self):
    world = self.new_world()
    onto1 = world.get_ontology("http://test.org/onto.owl")
    onto2 = world.get_ontology("http://test.org/onto2.owl")
    with onto1:
      class C(Thing): pass
      class p(C >> int): pass
      c1 = C()
      c1.p.append(1)
    with onto2:
      c1.p.append(2)
      c1.p.append(3)
      
    q, r = self.sparql(world, """SELECT ?i { onto:c1 onto:p ?i }""", compare_with_rdflib = True)
    assert set(i for i, in r) == { 1, 2, 3 }
    
    q = world.prepare_sparql("""SELECT ?i { GRAPH onto: { onto:c1 onto:p ?i } }""")
    
    q, r = self.sparql(world, """SELECT ?i { GRAPH onto: { onto:c1 onto:p ?i } }""", compare_with_rdflib = False)
    assert set(i for i, in r) == { 1 }
    
    q, r = self.sparql(world, """SELECT ?i { GRAPH <http://test.org/onto2.owl#> { onto:c1 onto:p ?i } }""", compare_with_rdflib = False)
    assert set(i for i, in r) == { 2, 3 }
    
    q, r = self.sparql(world, """SELECT ?i ?j { GRAPH ?o { onto:c1 onto:p ?i . onto:c1 onto:p ?j . FILTER(?i < ?j) } }""", compare_with_rdflib = False)
    assert r == [[2, 3]]
    
    q, r = self.sparql(world, """SELECT ?o ?i { GRAPH ?o { onto:c1 onto:p ?i } }""", compare_with_rdflib = False)
    assert set(tuple(i) for i in r) == { (onto1, 1), (onto2, 2), (onto2, 3) }
    
    q, r = self.sparql(world, """SELECT ?i { GRAPH ?? { onto:c1 onto:p ?i } }""", [onto2], compare_with_rdflib = False)
    assert set(i for i, in r) == { 2, 3 }
    
  def test_158(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/onto.owl")
    
    with onto:
      class Person(Thing): pass
      class address(Thing >> Thing): pass
      
      Person.is_a.append(address.max(1))
      
    q, r = self.sparql(world, """
SELECT ?restr {
  ??1 (rdfs:subClassOf | owl:equivalentClass)* ?restr .
  FILTER(?restr < 0) .
  ?restr owl:onProperty ??2 .
}""", [Person, address], compare_with_rdflib = False)
    
    assert r == [[address.max(1)]]
    
  def test_159(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/onto.owl")
    
    with onto:
      class Medicament(Thing): pass
      class Patient(Thing): pass
      class match(AnnotationProperty): pass
      
      class BetaBloquant(Medicament): pass
      class Verapamil(Medicament): pass
      class Metformine(Medicament): pass
      class Aspirin(Medicament): pass
      
      patient1 = Patient(match = [BetaBloquant, Verapamil])
      
    q, r = self.sparql(world, """
SELECT DISTINCT ?cond {
onto:patient1 onto:match ?x .
?x rdfs:subClassOf* ?cond .
}""")
    
    assert { i[0] for i in r } == { Thing, Medicament, BetaBloquant, Verapamil }

  def test_160(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/onto.owl")
    
    with onto:
      class Medicament(Thing): pass
      class Patient(Thing): pass
      class medicaments(Patient >> Medicament): pass
      
      class Regle(Thing): pass
      class nb_condition(Regle >> int, FunctionalProperty): pass
      class conditions(AnnotationProperty): pass
      class match(AnnotationProperty): pass
      
      class BetaBloquant(Medicament): pass
      class Verapamil(Medicament): pass
      class Metformine(Medicament): pass
      class Aspirin(Medicament): pass
      
      patient1 = Patient(medicaments = [BetaBloquant(), Verapamil()])
      regle1 = Regle(conditions = [BetaBloquant, Verapamil], nb_condition = 2)
      
      q, r = self.sparql(world, """
      INSERT { ??1 onto:match ?cond . }
      WHERE {
      ?regle onto:conditions ?cond .
      ??1 onto:medicaments/a/rdfs:subClassOf* ?cond.
      }
      """, [patient1])

      q, r = self.sparql(world, """
      INSERT { ??1 onto:match ?regle . }
      WHERE {
      ?regle onto:nb_condition ?nb_condition .
      ?regle onto:conditions ?cond .
      ??1 onto:match ?cond .
      }
      GROUP BY ?regle
      HAVING(COUNT(DISTINCT ?cond) = ?nb_condition)
      """, [patient1])
      
    assert r == [1]
    
  def test_161(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/onto.owl")
    with onto:
      class C(Thing): pass
      
    q, r = self.sparql(world, """INSERT { GRAPH <http://test.org/onto.owl> { ?c rdfs:comment "ok" } } WHERE { GRAPH ?g { ?c a owl:Class } }""", compare_with_rdflib = True)
    assert C.comment == ["ok"]
    
  def test_162(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/onto.owl")
    with onto:
      class C(Thing): pass
      
    q, r = self.sparql(world, """INSERT { GRAPH <http://test.org/onto.owl> { ?c rdfs:comment "ok" . ?c rdfs:label "lab", "lab2" ; rdfs:seeAlso 2 . } } WHERE { GRAPH ?g { ?c a owl:Class } }""", compare_with_rdflib = True)
    assert C.comment == ["ok"]
    assert C.label == ["lab", "lab2"]
    assert C.seeAlso == [2]
        
  def test_163(self):
    world = self.new_world()
    onto  = world.get_ontology("http://test.org/onto.owl")
    with onto:
      class C(Thing): pass
      c1 = C()
      
    assert c1.comment == []
    q, r = self.sparql(world, """INSERT { GRAPH <http://test.org/onto.owl> { onto:c1 rdfs:comment "ok" . } } WHERE {}""", compare_with_rdflib = True)
    assert c1.comment == ["ok"]
      
    assert C.comment == []
    q, r = self.sparql(world, """INSERT { GRAPH <http://test.org/onto.owl> { onto:C rdfs:comment "ok" . } } WHERE {}""", compare_with_rdflib = True)
    assert C.comment == ["ok"]
    
  def test_164(self):
    world = self.new_world()
    onto1 = world.get_ontology("http://test.org/onto1.owl")
    onto2 = world.get_ontology("http://test.org/onto2.owl")
    with onto1:
      class C(Thing): pass
    with onto2:
      class D(Thing): pass
      
    q, r = self.sparql(world, """INSERT { GRAPH ?g { ?c rdfs:comment "ok" } } WHERE { GRAPH ?g { ?c a owl:Class } }""", compare_with_rdflib = True)
    assert C.comment == ["ok"]
    assert D.comment == ["ok"]
    
    assert onto1.graph._get_data_triples_sp_od(C.storid, comment.storid) == [("ok", 60)]
    assert onto2.graph._get_data_triples_sp_od(C.storid, comment.storid) == []
    assert onto1.graph._get_data_triples_sp_od(D.storid, comment.storid) == []
    assert onto2.graph._get_data_triples_sp_od(D.storid, comment.storid) == [("ok", 60)]
    
    # q, r = self.sparql(world, """INSERT { GRAPH ??1 { ?c rdfs:label "lab" } } WHERE { ?c a owl:Class }""", [onto1], compare_with_rdflib = True)
    # assert C.label == ["lab"]
    # assert D.label == ["lab"]
    
    # assert onto1.graph._get_data_triples_sp_od(C.storid, label.storid) == [("lab", 60)]
    # assert onto2.graph._get_data_triples_sp_od(C.storid, label.storid) == []
    # assert onto1.graph._get_data_triples_sp_od(D.storid, label.storid) == [("lab", 60)]
    # assert onto2.graph._get_data_triples_sp_od(D.storid, label.storid) == []
    
  def test_165(self):
    world = self.new_world()
    onto = world.get_ontology("http://test.org/onto.owl")
    with onto:
      class C(Thing): pass
      class p(C >> int): pass
      c1 = C(p = [1, 2, 3])
      comment[c1, p, 1] = ["com"]
      
    q, r = self.sparql(world, """DELETE { ?x owl:annotatedTarget ??3 }  INSERT  { GRAPH ?g { ?x owl:annotatedTarget ??4 } }  WHERE  { ?x owl:annotatedSource ??1 ; owl:annotatedProperty ??2 . GRAPH ?g { ?x owl:annotatedTarget ??3 } }""", [c1, p, 1, 2], compare_with_rdflib = False)
    assert comment[c1, p, 1] == []
    assert comment[c1, p, 2] == ["com"]
    assert comment[c1, p, 3] == []
    
    q, r = self.sparql(world, """DELETE { ?x owl:annotatedTarget ??3 }  INSERT  { GRAPH ?g { ?x owl:annotatedTarget ??4 } }  WHERE  { GRAPH ?g { ?x owl:annotatedSource ??1 ; owl:annotatedProperty ??2 ; owl:annotatedTarget ??3 } }""", [c1, p, 2, 3], compare_with_rdflib = False)
    assert comment[c1, p, 1] == []
    assert comment[c1, p, 2] == []
    assert comment[c1, p, 3] == ["com"]
    
# Add test for Pellet

for Class in [Test, Paper]:
  if Class:
    for name, func in list(Class.__dict__.items()):
      if name.startswith("test_reasoning"):
        def test_pellet(self, func = func):
          global sync_reasoner
          sync_reasoner = sync_reasoner_pellet
          func(self)
          sync_reasoner = sync_reasoner_hermit
        setattr(Class, "%s_pellet" % name, test_pellet)

del Class # Else, it is considered as an additional test class!
        
if __name__ == '__main__': unittest.main()
  
