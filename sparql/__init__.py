# Owlready2
# Copyright (C) 2021 Jean-Baptiste LAMY
# LIMICS (Laboratoire d'informatique médicale et d'ingénierie des connaissances en santé), UMR_S 1142
# University Paris 13, Sorbonne paris-Cité, Bobigny, France

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

def _default_spawn(f):
  from threading import Thread
  thread = Thread(None, f)
  thread.start()
  return thread


def execute_many(onto, prepared_queries, paramss, spawn = True):
  if onto.world.graph.has_thread_parallelism:
    if onto.world.graph.has_changes():
      raise RuntimeError("Cannot execute parallelized queries on uncommited database. Please call World.save() before.")
    
    from gevent.hub import get_hub
    
    import _thread
    lock = _thread.allocate_lock()
    def f():
      try:
        with onto.world.graph.connexion_pool.get() as db:
          while True:
            with lock: i = args.pop()
            raws[i] = prepared_queries[i].execute_raw_with_db(paramss[i], db).fetchall()
      except IndexError: return
      
    args = list(range(len(prepared_queries)))
    raws = [None] * len(prepared_queries)
    
    if spawn is True: spawn = _default_spawn
    a = spawn(f)
    b = spawn(f)
    c = spawn(f)
    a.join()
    b.join()
    c.join()
    
    with onto:
      return [q.execute(params, raw) for raw, q, params in zip(raws, prepared_queries, paramss)]
    
  else:
    with onto:
      return [q.execute(params) for q, params in zip(prepared_queries, paramss)]

