Parallelism, multiprocessing and synchronization
================================================

Parallelism consist in executing several part of your program in parallel.
With Owlready (and Python in general), it is recommended to use multi-process parallelism, rather than multithreading,
because Python has poor multithreading supports (due to its global interpreter lock).

Two difficulties arise when using parallelism:

* Sharing data between processes is complex. When using Owlready, the easier solution is to put the quadstore
  with the ontology data on disk.
* Sensible parts of the code must be synchronized, e.g. one should avoid that severa processes write in the quadstore
  at the same time.

Several web application servers use multiple processes, and thus you will also encounter these difficulties when using them.


Synchronization
---------------

For using Owlready with multiple processes, and sharing the quadstore between processes, you need to:

* Store the quadstore on disk.
* Open the quadstore in non-exclusive mode (exclusive = False in set_backend()).
* Perform each modification to an ontology inside a "with ontology:" block. Owlready maintain a lock for each
  quadstore, which prevents multiple writes at the same time.
  Thus, for improving performances, you should also avoid long computation inside "with ontology:" blocks.
* Call World.save() at the end of each "with ontology:" block, in order to commit the changes to the quadstore database.
  

Multiprocessing with Gunicorn
-----------------------------

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



Multiprocessing with uWSGI
--------------------------

The previous server example can be run with `uWSGI <https://uwsgi-docs.readthedocs.io/en/latest/>`_ as follows:

::

   uwsgi --http 127.0.0.1:5000 --plugin python -p 5 --module test:app

