Parallelism, multiprocessing and synchronization
================================================

Parallelism consist in executing several part of your program in parallel.
Three options are possible:

 * cooperative microthread (e.g. greenlets with GEvent): it allows running several "greenlet" in parallel,
   switching from one to others, but it does not actually run several commands in parallel and increase performances.
   Nevertheless, it is very interesting in a server setting: 
 * multi-thread parallelism: it allows sharing data and objects between threads, however,
   Python has poor multithreading supports (due to the global interpreter lock (GIL), only one thread at a time may execute Python commands).
 * multi-process parallelism: it allows executing Python commands in parallel,
   however, data sharing is more difficult and objects cannot be shared between processes. In addition, keep in mind that
   Owlready does not update the local Python objects from the quadstore if they are modified by other processes.
   
Owlready (>= 0.41) supports all options:

 * cooperative microthread can be used in a server setting, in order to let the server answer a simple/small request while a long request is running.
 * multi-thread parallelism can be used to parallelize long SPARQL queries (only the SQL query is parallelized, allowing to run Python commands meanwhile). There is no other interesting in multi-threading, due to Python's GIL.
 * multi-process parallelism can be used to run several process in parallel.

Two difficulties arise when using parallelism:

* Sharing data between processes is complex. When using Owlready, the easier solution is to put the quadstore
  with the ontology data on disk.
* Sensible parts of the code must be synchronized, e.g. one should avoid that severa processes write in the quadstore
  at the same time.

Several web application servers use multiple processes, and thus you will also encounter these difficulties when using them.


Parallelized file parsing
-------------------------

For huge OWL file (> 8 Mb), Owlready (>= 0.41) automatically uses a separate process for parsing the file
(the main process being in charge of inserting triples in the quadstore). This provide a 25% performance boost
on huge ontologies.


Thread-based parallel execution of SPARQLqueries
------------------------------------------------

This is the simplest options, and probably the best if you have long SPARQL queries.
Since version 0.41, Owlready supports some level of thread-based parallelization, for increasing performances
by executing several SPARQL queries in parallel. It does not require to care about synchronization or data sharing.

In order to use this feature, you first need to use a World stored in a local file,
to deactive exclusive mode and to activate thread parallelism support, as follows:

::
   
   >>> default_world.set_backend(filename = "my_quadstore.sqlite3", exclusive = False, enable_thread_parallelism = True)

When thread parallelism is activated, Owlready opens 3 additional connexions to the SQLite3 database storing the quadstore,
allowing 3 parallel threads.

Then, the quadstore must be saved on disk before running parallel queries, as follows:

::
   
   >>> default_world.save()
   

Executing many SPARQL queries in parallel
.........................................

The owlready2.sparql.execute_many() function can be used to execute several prepared SPARQL queries in parallel.
Both SELECT and INSERT/DELETE queries are supported.

execute_many() will start 3 threads for executing the queries in parallel, and returns a list of query results.

You may expect up to 100% performance boost, especially when the queries are long and complex
and the number of results is small (currently, Owlready only parallelize the SQL execution,
but not the loading of the resulting objects from the quadstore).

Here is a typical usage:

::

   >>> my_onto = get_ontology("XXX ontology IRI here")
   
   >>> queries = [
   ...     default_world.prepare_sparql("""XXX First SPARQL query here"""),
   ...     ...,
   ... ]
   
   >>> queries_params = [
   ...     [], # First SPARQL query parameters
   ...     ...,
   ... ]
   
   >>> import owlready2.sparql
   >>> results = [list(gen) for gen in owlready2.sparql.execute_many(my_onto, queries, queries_params)]

If you are also using Gevent (or another similar library), you may use the Gevent thread pool.
This can be done by providing a "spawn" function to execute_many(). The spawn function must accept a
callable with no argument, start a thread executing that callable, and return the thread object (which is expected to have
a .join() method). Here is an example for Gevent:

::

   >>> import gevent.hub
   >>> gevent_spawn = gevent.hub.get_hub().threadpool.apply_async
   >>> results = [list(gen) for gen in owlready2.sparql.execute_many(my_onto, queries, queries_params, gevent_spawn)]


Executing a single SPARQL query in parallel
...........................................

A single SPARQL query can be executed in parallel, in a separate thread. The query will not run faster (it will rather takes
a little more time), but the main thread will be let available for other tasks. This can be interesting e.g. on a server,
where a long query can be parallelized; meanwhile, the main thread may answer to other clients.

::
   
   >>> query = default_world.prepare_sparql("""XXX SPARQL query here""")
   >>> query.execute(spawn = True)


Similarly, you may want to use the Gevent thread pool, as follows:

::

   >>> import gevent.hub
   >>> gevent_spawn = gevent.hub.get_hub().threadpool.apply_async
   >>> query.execute(spawn = gevent_spawn)


Cooperative microthreads (e.g. GEvent)
--------------------------------------

Microthreads will not improve the performances of Owlready, however, they will allow running several tasks in parallel,
which is interesting if you need to perform small tasks during long tasks (e.g. in a server), or if some part of your
program is waiting on an external, non-Python, task (e.g. a network call, including the use of a server database like Postgresql).

Synchronization
...............

For using Owlready with cooperative microthreads, you need to:

* Use a custom lock for the quadstore. By default, Owlready use the internal SQLite3 database as a lock; this does not
  work with microthreads because all microthreads share the same SQLite3 connexion. The solution is to use a custom lock,
  for example with GEvent :
  
  ::
     
     >>> gevent.lock
     >>> default_world.set_backend(filename = "your_quadstore.sqlite3",
     ...                           lock     = gevent.lock.RLock())
     
* Perform each modification to an ontology inside a "with ontology:" block.
  This prevents multiple writes at the same time.
  For improving performances, you should also avoid long computation inside "with ontology:" blocks.
  
* Switch to other microthreads when desired (e.g. by calling gevent.sleep(0)).
  To let other microthreads write in the quadstore, you should do that outside "with ontology:" blocks.
  
Other synchronization tasks (listed below, for multiprocessing) are not needed for microthreads.


Multiprocessing
---------------

Multiprocessing requires synchronization, which can be very complex (and may have a significant performance cost).

Multiprocessing is recommended mostly when using a read-only quadstore, because Owlready does not update the local
Python objects from the quadstore if they are modified by another process.


Synchronization
...............

For using Owlready with multiple processes, and sharing the quadstore between processes, you need to:

* Store the quadstore on disk.
* Open the quadstore in non-exclusive mode (exclusive = False in set_backend()).
* Perform each modification to an ontology inside a "with ontology:" block. Owlready maintain a lock for each
  quadstore, which prevents multiple writes at the same time.
  Thus, for improving performances, you should also avoid long computation inside "with ontology:" blocks.
* Call World.save() at the end of each "with ontology:" block, in order to commit the changes to the quadstore database.


Server example
..............

This section gives a small example of a multi-process server using a shared Owlready quadstore.

The example uses `Flask <https://flask.palletsprojects.com/>`_ and `Gunicorn <https://gunicorn.org/>`_.
It provides 2 URL: the first one (/gen) creates 5 new instances of the C class. The second (/test) returns the ID
of the current process and the number of instances in the quadstore.

::

   import sys, os, flask, time
   from owlready2 import *
   
   default_world.set_backend(filename = "/tmp/t.sqlite3", exclusive = False)
   
   onto = get_ontology("http://test.org/onto.owl")
   
   with onto:
     class C(Thing): pass
     default_world.save()
     
   
   app = flask.Flask("OwlreadyBench")
   
   @app.route("/gen")
   def gen():
     with onto:
       for i in range(5):
         c = C()
         c.label = [os.getpid()]
         print(c, c.storid)
       default_world.save()
     return ""
   
   @app.route("/test")
   def test():
     time.sleep(0.02)
     nb = len(list(C.instances()))
     return "%s %s" % (os.getpid(), nb)

You can run this server in multiprocessor mode with Gunicorn as follows:

::

   gunicorn -b 127.0.0.1:5000 --preload -w 5 --worker-class=gevent test:app

where "test" is the previous file's name (without ".py"),
and 5 in "-w 5" is recommended to be the number of CPU plus 1 (here, my computer has 4 CPU, thus -w 5).

Then, after running the server, you can use the following script to make 100 concurrent calls to /gen, and then
10 concurrent calls to /test:

::
   
   from urllib.request import *
   
   import eventlet, eventlet.green.urllib.request
   def fetch(url): return eventlet.green.urllib.request.urlopen(url).read()
   
   urls = ["http://localhost:5000/gen"] * 100
   pool = eventlet.GreenPool()
   for body in pool.imap(fetch, urls): pass
   
   urls = ["http://localhost:5000/test"] * 10
   pool = eventlet.GreenPool()
   for body in pool.imap(fetch, urls): print(body)

As the 10 calls to /test are executed by different processes, this allows to verify that the various processes have access
to all the created instances (normally, 500 instances).

The previous server example can also be run with `uWSGI <https://uwsgi-docs.readthedocs.io/en/latest/>`_ as follows:

::

   uwsgi --http 127.0.0.1:5000 --plugin python -p 5 --module test:app

