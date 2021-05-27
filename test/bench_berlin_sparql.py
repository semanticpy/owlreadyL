
# Run with:
# gunicorn -b 127.0.0.1:5000 --preload -w 5 --worker-class=gevent owlready2.test.bench_berlin_sparql:app

# Or:
# uwsgi --http 127.0.0.1:5000 --plugin python -b 128000 -p 8 --module owlready2.test.bench_berlin_sparql:app > /dev/null 2>&1
# uwsgi --http 127.0.0.1:5000 -s /tmp/yourapplication.sock --plugin python -b 128000 -p 8 --manage-script-name --mount /=owlready2.test.bench_berlin_sparql:app > /dev/null 2>&1

# Then run Berlin SPARQL benchmark with:
# cd /home/jiba/telechargements/bsbmtools-0.2
# ./testdriver -w 1 -runs 10 -mt 5 http://localhost:5000/sparql

import sys, os, time, flask

from owlready2 import *
from owlready2.sparql.endpoint import *

QUADSTORE_ON_DISK = True

if QUADSTORE_ON_DISK:
  try: os.unlink("/tmp/t.sqlite3")
  except: pass
  try: os.unlink("/tmp/t.sqlite3-journal")
  except: pass
  world = World()
  world.set_backend(filename = "/tmp/t.sqlite3") #, exclusive = False) # Exclusive is not needed here, since it is read ontly
  
  class USD(float):
    def __new__(self, value): return float.__new__(self, value)
  def parser(s):   return USD(s)
  def unparser(x): return str(x)
  declare_datatype(USD, "http://www4.wiwiss.fu-berlin.de/bizer/bsbm/v01/vocabulary/USD", parser, unparser)
  
  onto = world.get_ontology("/home/jiba/telechargements/bsbmtools-0.2/dataset.nt").load()
  world.save()
  world.close()
  
  #default_world.set_backend(filename = "/tmp/t.sqlite3", read_only = True, exclusive = True)
  default_world.set_backend(filename = "/tmp/t.sqlite3", exclusive = True)
  
  
app = flask.Flask("OwlreadyBench")
endpoint = EndPoint(default_world)

#def endpoint():
  #for i in range(2000000): pass
  #time.sleep(0.05)
  #return """<?xml version="1.0"?><sparql xmlns="http://www.w3.org/2005/sparql-results#"></sparql>"""
  
app.route("/sparql", methods = ["GET"])(endpoint)


@app.route("/optimize", methods = ["GET"])
def optimize():
  default_world.graph.execute("""PRAGMA OPTIMIZE""")
  default_world.graph.execute("""PRAGMA VACUUM""")
  default_world.save()
  return "ok"
  
if __name__ == "__main__":
  import bjoern
  bjoern.run(app, "127.0.0.1", 5000)
