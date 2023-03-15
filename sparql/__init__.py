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


def execute_many(onto, prepared_queries, paramss):
  if onto.world.graph.has_gevent:
    from gevent.hub import get_hub
    raws = get_hub().threadpool.apply(_execute_many_gevent, (onto, prepared_queries, paramss))
    r = []
    with onto:
      for raw, q, params in zip(raws, prepared_queries, paramss):
        r.append(q.execute(params, raw))
    return r
  else:
    with onto:
      r = [q.execute(params) for q, params in zip(prepared_queries, paramss)]
    return r
    
def _execute_many_gevent(onto, prepared_queries, paramss):
  #r = []
  #for q, params in zip(prepared_queries, paramss):
  #  r.append(q.execute_raw(params))
  return [q.execute_raw(params).fetchall() for q, params in zip(prepared_queries, paramss)]  
