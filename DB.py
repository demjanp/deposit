'''
	Deposit database
	--------------------------
	
	Created on 10. 4. 2017
	
	@author: Peter Demjan <peter.demjan@gmail.com>
		
'''

from rdflib import (Namespace, Graph, Literal, URIRef)

# RDF Namespaces
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
OGC = Namespace("http://www.opengis.net/ont/geosparql#")
DEP = Namespace("http://future_url/2017/04/deposit-schema#")

import psycopg2
from urllib.parse import urlparse
from deposit.DLabel import (value_to_wkt, wkt_to_wktLiteral, id_to_int)
import numpy as np
import time
import datetime
import os
import json
import tempfile
import unicodedata
from sys import platform

# valid Deposit class names and prefixes used for graph element ids
ID_PREFIX = {
	"Object": "obj",
	"Class": "cls",
	"Member": "mem",
	"Relation": "rel",
}

CHANGED_IDS_EMPTY = dict(created = [], updated = [], deleted = [], ordered = [])

class DB(object):
	
	def __init__(self, identifier = None, connstr = None):
		# identifier = Deposit graph RDF source IRI or Graph
		# connstr = database connection string, e.g.: postgres://archeoforum:1111@127.0.0.1:5432/deposit
		
		self._params = [identifier, connstr]
		self._is_server = False
		self._server_url = None
		scheme = None
		if identifier is None:
			self._identifier = "temp#"
			self._server_url = None
		else:
			self._identifier = identifier.strip().strip("#").strip("/") + "#"
			scheme = urlparse(identifier).scheme
			self._server_url = urlparse(self._identifier)
			if scheme == "file":
				self._server_url = "file:///" + os.path.split(self._server_url.path.strip("/\\"))[0]
			elif scheme in ["http", "https"]:
				self._server_url = "%s://%s" % (scheme, self.server_url.netloc)
		
		self._connstr = connstr
		self._on_changed_fnc = None
		
		self._objects = np.array([], dtype = object)
		self._classes = np.array([], dtype = object)
		self._order = np.array([], dtype = int)
		self._checked_out = np.array([], dtype = object)
		self._checked_out_updated = np.array([], dtype = object)
		self._checked_out_deleted = np.array([], dtype = object)
		self._check_out_source = None
		self._members = np.array([], dtype = object)
		self._relations = np.array([], dtype = object)
		self._resources = np.array([], dtype = object)
		self._geotags = np.array([], dtype = object)
		self._worldfiles = np.array([], dtype = object)
		self._images = np.array([], dtype = object)
		self._changed = None
		self._changed_ids = None
		
		self._connected_remote = [] # [identifier, ...]; idents of connected remote databases
		
		self._last_new_id = {} # {prefix: id, ...}; store last id created
		
		self.reset_changed_ids()
		
		if connstr:
			self._load_database(self._identifier, connstr)
		elif self._server_url:
			self._parse(self._identifier, scheme)
		
	def _connect_database(self, connstr):
		
		try:
			conn = psycopg2.connect(connstr)
		except:
			return None, []
		cursor = conn.cursor()
		cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
		tables = [row[0] for row in cursor.fetchall()]
		return cursor, tables
	
	def _populate_remote_objects(self):
		# add referenced remote objects to self._objects
		
		if self._members.size:
				for id_tgt in self._members[:,2]:
					if ("#" in id_tgt) and (id_tgt[:3] == ID_PREFIX["Object"]):
						self._objects = np.union1d(self._objects, [id_tgt])
		if self._relations.size:
			for id_src, _, id_tgt in self._relations[:,:3]:
				if ("#" in id_src) and (id_src[:3] == ID_PREFIX["Object"]):
					self._objects = np.union1d(self._objects, [id_src])
				if ("#" in id_tgt) and (id_tgt[:3] == ID_PREFIX["Object"]):
					self._objects = np.union1d(self._objects, [id_tgt])
	
	def _load_database(self, identifier, connstr):
		
		cursor, tables = self._connect_database(connstr)
		if cursor is None:
			return
		for name in ["objects", "classes", "order", "members", "relations", "resources", "geotags", "worldfiles", "images", "checked_out"]:
			table = identifier + name
			cursor.execute("SELECT * FROM \"%s\";" % (table,))
			rows = cursor.fetchall()
			if rows:
				if name == "order":
					self._order = np.array([int(row[1]) for row in rows], dtype = int)
				elif name == "resources":
					self.__dict__["_" + name] = np.array([list(row) + [""] for row in rows], dtype = object)
				elif len(rows[0]) == 1:
					self.__dict__["_" + name] = np.array([row[0] for row in rows], dtype = object)
				else:
					self.__dict__["_" + name] = np.array([row for row in rows], dtype = object)
		self._populate_remote_objects()
		cursor.execute("SELECT * FROM \"%s\";" % (identifier + "check_out_source",))
		for row in cursor.fetchall():
			self._check_out_source = str(row[0])
			break
		cursor.execute("SELECT * FROM \"%s\";" % (identifier + "changed",))
		for row in cursor.fetchall():
			self._changed = row[0]
			break
		cursor.connection.close()
	
	def _parse(self, identifier, scheme):
		
		def to_id(uri):
			
			return "#".join(uri.split("#")[1:])
		
		GRA = Namespace(identifier)
		graph = Graph()
		if scheme == "file":
			path = identifier[7:].strip("/\\#") + ".rdf"
			if platform in ["linux", "linux2", "darwin"]:
				os.chdir("/")
			graph.parse(path, publicID = identifier.strip("#"))
		elif scheme in ["http", "https"]:
			graph.parse(identifier.strip("#"), format = "xml", publicID = identifier.strip("#"))
		
		self._objects = np.array([], dtype = object)
		self._classes = np.array([], dtype = object)
		self._order = np.array([], dtype = int)
		self._checked_out = np.array([], dtype = object)
		self._checked_out_updated = np.array([], dtype = object)
		self._checked_out_deleted = np.array([], dtype = object)
		self._check_out_source = None
		self._members = np.array([], dtype = object)
		self._relations = np.array([], dtype = object)
		self._resources = np.array([], dtype = object)
		self._geotags = np.array([], dtype = object)
		self._worldfiles = np.array([], dtype = object)
		self._images = np.array([], dtype = object)
		
		self._objects = [to_id(s) for s in graph[ : RDF["type"] : DEP["Object"]]]
		self._objects = np.array(sorted(self._objects, key = lambda obj_id: id_to_int(obj_id)), dtype = object)
		
		self._classes = [[to_id(s), graph.value(s, DEP["label"], None).value] for s in graph[ : RDF["type"] : DEP["Class"]]]
		if self._classes:
			self._classes = np.array(sorted(self._classes, key = lambda row: id_to_int(row[0])), dtype = object)
			self._order = []
			for p, o in graph[GRA["order"] : : ]:
				cls_id = to_id(o)
				if self.is_class(cls_id, "Class"):
					self._order.append([cls_id, int(p.split("_")[-1])])
			self._order = np.genfromtxt(np.array(sorted(self._order, key = lambda row: id_to_int(row[0])))[:,1].astype("|S"))
			if not self._order.shape:
				self._order = np.array([int(self._order)], dtype = int)
		else:
			self._classes = np.array([], dtype = object)
		
		self._checked_out = np.array([to_id(o) for _, o in graph[GRA["checked_out"] : : ] if not o.endswith("CheckedOut")], dtype = object)
		self._checked_out_updated = np.array([to_id(o) for _, o in graph[GRA["checked_out_updated"] : : ] if not o.endswith("CheckedOutUpdated")], dtype = object)
		self._checked_out_deleted = np.array([to_id(o) for _, o in graph[GRA["checked_out_deleted"] : : ] if not o.endswith("CheckedOutDeleted")], dtype = object)
		self._check_out_source = graph.value(None, RDF["type"], DEP["CheckOutSource"])
		if not self._check_out_source is None:
			self._check_out_source = str(self._check_out_source)
		
		self._images = np.array([os.path.split(uri)[-1] if uri.startswith(self._server_url) else str(uri) for _, uri in graph[GRA["images"] : : ] if not uri.endswith("Images")], dtype = object)
		
		self._resources = np.array([[os.path.split(str(uri))[-1], filename.value, ""] for uri, filename in graph[ : RDFS["label"] : ] if isinstance(uri, URIRef) and isinstance(filename, Literal)], dtype = object)
		
		sources = []
		for s, o in graph[ : DEP["source"] : ]:
			id_edge, id_node = to_id(s), to_id(o)
			sources.append([id_node, id_edge, id_edge[:3]])
		if sources:
			sources = np.array(sorted(sources, key = lambda row: [row[2], id_to_int(row[1])]), dtype = object) # [[id_src, mem_id / rel_id, typ], ...]
			targets = []
			for s, o in graph[ : DEP["target"] : ]:
				id_edge, id_node = to_id(s), to_id(o)
				targets.append([id_node, id_edge, id_edge[:3]])
			targets = np.array(sorted(targets, key = lambda row: [row[2], id_to_int(row[1])]), dtype = object) # [[id_tgt, mem_id / rel_id, typ], ...]
			sources_mem = sources[sources[:,2] == ID_PREFIX["Member"],:2] # [[id_src, mem_id], ...]
			targets_mem = targets[targets[:,2] == ID_PREFIX["Member"],:2] # [[id_tgt, mem_id], ...]
			
			if sources_mem.shape[0]:
				self._members = np.hstack((sources_mem, targets_mem[:,0].reshape((-1,1))))
			sources_mem = None
			targets_mem = None
			
			sources_rel = sources[sources[:,2] == ID_PREFIX["Relation"],:2] # [[id_src, rel_id], ...]
			targets_rel = targets[targets[:,2] == ID_PREFIX["Relation"],:2] # [[id_tgt, rel_id], ...]
			if sources_rel.shape[0]:
				labels = [] # [[rel_id, label, dtype], ...]
				for s, label in graph[ : DEP["label"] : ]:
					rel_id = to_id(s)
					if self.is_class(rel_id, "Relation"):
						if isinstance(label, Literal) and (label.datatype == OGC.wktLiteral):
							dtype = "DGeometry"
							label = str(label)
						elif isinstance(label, URIRef):
							dtype = "DResource"
							label = str(label)
							if label.startswith(self._server_url):
								label = os.path.split(label)[-1]
						else:
							dtype = "DString"
							label = label.value
						labels.append([rel_id, label, dtype])
				labels = np.array(sorted(labels, key = lambda row: id_to_int(row[0])), dtype = object)
				self._relations = np.hstack((sources_rel, targets_rel[:,0].reshape((-1,1)), labels[:,1:]))
			sources_rel = None
			targets_rel = None
		
		self._geotags = np.array([[to_id(s), str(o)] for s, o in graph[ : DEP["geotag"] : ]], dtype = object)
		
		for i, letter in enumerate("ADBECF"):
			for s, o in graph[ : DEP["worldfile_%s" % letter] : ]:
				uri = str(s)
				if uri.startswith(self._server_url):
					uri = os.path.split(uri)[-1]
				if not self._worldfiles.size:
					self._worldfiles = np.array([[uri, 0, 0, 0, 0, 0, 0]], dtype = object)
				idxs = np.where(self._worldfiles[:,0] == uri)[0]
				if idxs.size:
					self._worldfiles[idxs[0], i + 1] = o.value
				else:
					self._worldfiles = np.vstack((self._worldfiles, [[uri, 0, 0, 0, 0, 0, 0]]))
					self._worldfiles[-1, i + 1] = o.value
		
		self._populate_remote_objects()
		
		self._changed = graph.value(GRA["changed"], RDF.value, None)
		if not self._changed is None:
			self._changed = self._changed.value
		
	def _upd_changed(self, created = [], updated = [], deleted = [], ordered = []):
		# update timestamp of last change of the connected graph to current time
		# created / updated / deleted / ordered = [id, ...]; ids of changed elements
		
		timestamp = time.time()
		self._changed = timestamp
		self._changed_ids["created"] += [str(val) for val in created]
		self._changed_ids["updated"] += [str(val) for val in updated]
		self._changed_ids["deleted"] += [str(val) for val in deleted]
		self._changed_ids["ordered"] += [str(val) for val in ordered]
		if not self._on_changed_fnc is None:
			self._on_changed_fnc()
	
	def _get_new_id(self, ids, prefix, index = None):
		
		n = 0
		if prefix in self._last_new_id:
			n = int(self._last_new_id[prefix][4:]) + 1
		elif ids.size:
			if self._connected_remote:
				n = np.array([id[4:] for id in (ids if index is None else ids[:,index]) if not "#" in id], dtype = int).max()
			else:
				n = np.array([id[4:] for id in (ids if index is None else ids[:,index])], dtype = int).max()
			n += 1
		self._last_new_id[prefix] = "%s_%d" % (prefix, n)
		return self._last_new_id[prefix]
	
	@property
	def server_url(self):
		# "[scheme]://[Deposit server url]" or "file:///[path/to/data]"
		
		return self._server_url
	
	@property
	def identifier(self):
		# "[scheme]://[Deposit server url]/deposit/[identifier]#" or "file:///[path/to/data]/[identifier]#"
		
		return self._identifier
	
	@property
	def params(self):
		# [identifier, connstr]; original parameters used to initialize database
		
		return self._params
	
	@property
	def objects(self):
		# [obj_id, ...]; sorted by obj_id
		
		return self._objects

	@property
	def classes(self):
		# [[cls_id, label], ...]; sorted by cls_id
		
		return self._classes

	@property
	def order(self):
		# [order, ...]; in order of classes
		
		return self._order
	
	@property
	def members(self):
		# [[id_src, mem_id, id_tgt], ...]; sorted by mem_id
		
		return self._members
	
	@property
	def relations(self):
		# [[id_src, rel_id, id_tgt, label, dtype], ...]; sorted by rel_id; dtype = "DString" / "DResource" / "DGeometry"
		
		return self._relations
	
	@property
	def resources(self):
		# [[uri, filename, path], ...]
		
		return self._resources
	
	@property
	def geotags(self):
		# [[rel_id, tag], ...]
		
		return self._geotags
	
	@property
	def worldfiles(self):
		# [[uri, A, D, B, E, C, F], ...]
		
		return self._worldfiles
	
	@property
	def images(self):
		# [uri, ...]; list of image resources
		
		return self._images
	
	@property
	def checked_out(self):
		# [id, ...]; ids of objects, classes and relations
		
		return self._checked_out
	
	@property
	def checked_out_updated(self):
		# [id, ...]; ids of classes and relations that have been updated whilst checked out
		
		return self._checked_out_updated
	
	@property
	def checked_out_deleted(self):
		# [id, ...]; ids of objects, classes and relations that have been deleted whilst checked out
		
		return self._checked_out_deleted
	
	@property
	def check_out_source(self):
		# URIRef or None; identifier of the source database if current database is checked out
		
		return self._check_out_source
	
	@property
	def changed(self):
		# timestamp
		
		return -1 if self._changed is None else self._changed
	
	@property
	def changed_ids(self):
		# {created: [id, uri, ...], updated: [id, uri, ...], deleted: [id, uri, ...], ordered: [id, uri, ...]}
		
		return self._changed_ids
	
	def reset_changed_ids(self):
		
		self._changed_ids = {}
		for key in CHANGED_IDS_EMPTY:
			self._changed_ids[key] = CHANGED_IDS_EMPTY[key].copy()
	
	def has_database(self):
		
		return (not self._connstr is None)
	
	def is_server(self):
		# return True if database is a remote Deposit Server
		
		return self._is_server
	
	def get_dep_class_prefix(self, dep_class):
		
		return ID_PREFIX[dep_class]
	
	def get_dep_class_by_id(self, id):
		# return Deposit class name
		
		if "#" in id:
			id = id.split("#")[0]
		prefix = id.split("_")[0]
		for dep_class in ID_PREFIX:
			if ID_PREFIX[dep_class] == prefix:
				return dep_class
		return None
	
	def is_class(self, id, dep_class):
		# return True if id belongs to dep_class
		
		if "#" in id:
			id = id.split("#")[0]
		return isinstance(id, str) and id.startswith(ID_PREFIX[dep_class])

	def set_on_changed(self, func):
		# call func() when the connected graph changes
		
		self._on_changed_fnc = func
	
	def serialize(self, path):
		
		if os.path.isfile(path):
			path_bak = "%s.bak" % (path)
			if os.path.isfile(path_bak):
				os.remove(path_bak)
			os.rename(path, path_bak)
		
		f = open(path, "w", encoding = "utf-8")
		
		# header
		f.write('''<?xml version="1.0" encoding="UTF-8"?>\n''')
		f.write('''<!--\n''')
		f.write('''\tRDF Schema of a Deposit database\n''')
		f.write('''\tCreated: %s\n''' % (datetime.date.today().isoformat()))
		f.write('''-->\n''')
		f.write('''<rdf:RDF\n''')
		f.write('''\txmlns:rdf="%s"\n''' % RDF)
		f.write('''\txmlns:rdfs="%s"\n''' % RDFS)
		f.write('''\txmlns:ogc="%s"\n''' % OGC)
		f.write('''\txmlns:dep="%s"\n''' % DEP)
		f.write('''>\n''')
		
		# objects
		for obj_id in self._objects:
			if not "#" in obj_id:
				f.write('''\t<dep:Object rdf:about="#%s"/>\n''' % (obj_id))
		
		# classes
		for cls_id, label in self._classes:
			if not "#" in cls_id:
				f.write('''\t<dep:Class rdf:about="#%s">\n''' % (cls_id))
				f.write('''\t\t<dep:label>%s</dep:label>\n''' % (label))
				f.write('''\t</dep:Class>\n''')
		
		# order
		f.write('''\t<dep:Order rdf:about="#order">\n''')
		for i, order in enumerate(self._order):
			if not "#" in self._classes[i,0]:
				f.write('''\t\t<rdf:_%d rdf:resource = "#%s"/>\n''' % (order, self._classes[i,0]))
		f.write('''\t</dep:Order>\n''')
		
		# checked out
		f.write('''\t<dep:CheckedOut rdf:about="#checked_out">\n''')
		for i, id in enumerate(self._checked_out):
			if not "#" in id:
				f.write('''\t\t<rdf:_%d rdf:resource = "#%s"/>\n''' % (i, id))
		f.write('''\t</dep:CheckedOut>\n''')
		
		# checked out updated
		f.write('''\t<dep:CheckedOutUpdated rdf:about="#checked_out_updated">\n''')
		for i, id in enumerate(self._checked_out_updated):
			if not "#" in id:
				f.write('''\t\t<rdf:_%d rdf:resource = "#%s"/>\n''' % (i, id))
		f.write('''\t</dep:CheckedOutUpdated>\n''')
		
		# checked out deleted
		f.write('''\t<dep:CheckedOutDeleted rdf:about="#checked_out_deleted">\n''')
		for i, id in enumerate(self._checked_out_deleted):
			if not "#" in id:
				f.write('''\t\t<rdf:_%d rdf:resource = "#%s"/>\n''' % (i, id))
		f.write('''\t</dep:CheckedOutDeleted>\n''')
		
		# check out source
		if not self._check_out_source is None:
			f.write('''\t<dep:CheckOutSource rdf:about="%s"/>\n''' % (self._check_out_source))
		
		# members
		for id_src, mem_id, id_tgt in self._members:
			if not "#" in mem_id:
				f.write('''\t<dep:Member rdf:about="#%s">\n''' % (mem_id))
				f.write('''\t\t<dep:source rdf:resource="#%s"/>\n''' % (id_src))
				f.write('''\t\t<dep:target rdf:resource="#%s"/>\n''' % (id_tgt))
				f.write('''\t</dep:Member>\n''')
		
		# relations
		for id_src, rel_id, id_tgt, label, dtype in self._relations:
			if not "#" in rel_id:
				f.write('''\t<dep:Relation rdf:about="#%s">\n''' % (rel_id))
				if dtype == "DGeometry":
					f.write('''\t\t<dep:label rdf:datatype="%swktLiteral">%s</dep:label>\n''' % (OGC, label.replace("<", "&lt;").replace(">", "&gt;")))
				elif dtype == "DResource":
					f.write('''\t\t<dep:label rdf:resource="%s"/>\n''' % (label))
				else:
					f.write('''\t\t<dep:label>%s</dep:label>\n''' % (label))
				# TODO projection
				
				if self._geotags.size:
					slice = self._geotags[self._geotags[:,0] == rel_id]
					if slice.size:
						geotag = slice[0,1]
						f.write('''\t\t<dep:geotag rdf:datatype="%swktLiteral">%s</dep:geotag>\n''' % (OGC, geotag.replace("<", "&lt;").replace(">", "&gt;")))
				f.write('''\t\t<dep:source rdf:resource="#%s"/>\n''' % (id_src))
				f.write('''\t\t<dep:target rdf:resource="#%s"/>\n''' % (id_tgt))
				f.write('''\t</dep:Relation>\n''')
		
		# worldfiles
		for row in self._worldfiles:
			f.write('''\t<rdfs:Resource rdf:about="%s">\n''' % (row[0]))
			for i, letter in enumerate("ADBECF"):
				f.write('''\t\t<dep:worldfile_%s rdf:datatype="http://www.w3.org/2001/XMLSchema#decimal">%s</dep:worldfile_%s>\n''' % (letter, row[i + 1], letter))
			f.write('''\t</rdfs:Resource>\n''')
		
		# resources
		for uri, filename, _ in self._resources:
			if not (("#" in uri) and (uri.split("#")[0] in self._connected_remote)):
				f.write('''\t<rdfs:Resource rdf:about="%s">\n''' % (os.path.split(uri)[1]))
				f.write('''\t\t<rdfs:label>%s</rdfs:label>\n''' % (filename))
				f.write('''\t</rdfs:Resource>\n''')
		
		# descriptions
		# TODO
		
		# images
		f.write('''\t<dep:Images rdf:about="#images">\n''')
		for i, uri in enumerate(self._images):
			if not (("#" in uri) and (uri.split("#")[0] in self._connected_remote)):
				f.write('''\t\t<rdf:_%d rdf:resource = "%s"/>\n''' % (i, uri))
		f.write('''\t</dep:Images>\n''')		
		
		# changed
		f.write('''\t<dep:Changed rdf:about="#changed">\n''')
		f.write('''\t\t<rdf:value rdf:datatype="http://www.w3.org/2001/XMLSchema#double">%s</rdf:value>\n''' % (self._changed))
		f.write('''\t</dep:Changed>\n''')
		
		f.write('''</rdf:RDF>\n''')
		f.close()
	
	def store_in_db(self, identifier, connstr):
		
		def _create_table(name, columns, tables, cursor):
			
			if name in tables:
				cursor.execute("DROP TABLE \"%s\";" % (name))
			cursor.execute("CREATE TABLE \"%s\" (%s);" % (name, columns))
		
		def _jsonify(data):
			for i, row in enumerate(data):
				for key in row:
					if isinstance(row[key], np.generic):
						data[i][key] = np.asscalar(row[key])
			return json.dumps(data)
		
		cursor, tables = self._connect_database(connstr)
		if cursor is None:
			return
		
		table = identifier + "objects"
		object_type = "obj_id VARCHAR(512)"
		_create_table(table, object_type, tables, cursor)
		if self._objects.size:
			data = []
			for obj_id in self._objects:
				if not "#" in obj_id:
					data.append(dict(obj_id = obj_id))
			cursor.execute("""
				DROP TYPE IF EXISTS object_;
				CREATE TYPE object_ as (%s);
				INSERT INTO \"%s\" (obj_id) SELECT obj_id FROM json_populate_recordset(null::object_, %%s);
			""" % (object_type, table), (_jsonify(data),))
		
		table = identifier + "classes"
		class_type = "cls_id VARCHAR(512), label TEXT"
		_create_table(table, class_type, tables, cursor)
		if self._classes.size:
			data = []
			for cls_id, label in self._classes:
				if not "#" in cls_id:
					data.append(dict(cls_id = cls_id, label = label))
			cursor.execute("""
				DROP TYPE IF EXISTS class_;
				CREATE TYPE class_ as (%s);
				INSERT INTO \"%s\" SELECT cls_id, label FROM json_populate_recordset(null::class_, %%s);
			""" % (class_type, table), (_jsonify(data),))
		
		table = identifier + "order"
		order_type = "cls_id VARCHAR(512), ord INTEGER"
		_create_table(table, order_type, tables, cursor)
		if self._order.size:
			data = []
			for i in range(self._order.shape[0]):
				if not "#" in self._classes[i,0]:
					data.append(dict(cls_id = self._classes[i,0], ord = int(self._order[i])))
			cursor.execute("""
				DROP TYPE IF EXISTS order_;
				CREATE TYPE order_ as (%s);
				INSERT INTO \"%s\" SELECT cls_id, ord FROM json_populate_recordset(null::order_, %%s);
			""" % (order_type, table), (_jsonify(data),))
		
		table = identifier + "members"
		member_type = "id_src VARCHAR(512), mem_id VARCHAR(512), id_tgt VARCHAR(512)"
		_create_table(table, member_type, tables, cursor)
		if self._members.size:
			data = []
			for id_src, mem_id, id_tgt in self._members:
				if not "#" in mem_id:
					data.append(dict(id_src = id_src, mem_id = mem_id, id_tgt = id_tgt))
			cursor.execute("""
				DROP TYPE IF EXISTS member_;
				CREATE TYPE member_ as (%s);
				INSERT INTO \"%s\" SELECT id_src, mem_id, id_tgt FROM json_populate_recordset(null::member_, %%s);
			""" % (member_type, table), (_jsonify(data),))
		
		table = identifier + "relations"
		relation_type = "id_src VARCHAR(512), rel_id VARCHAR(512), id_tgt VARCHAR(512), label TEXT, dtype VARCHAR(16)"
		_create_table(table, relation_type, tables, cursor)
		if self._relations.size:
			data = []
			for id_src, rel_id, id_tgt, label, dtype in self._relations:
				if not "#" in rel_id:
					data.append(dict(id_src = id_src, rel_id = rel_id, id_tgt = id_tgt, label = label, dtype = dtype))
			cursor.execute("""
				DROP TYPE IF EXISTS relation_;
				CREATE TYPE relation_ as (%s);
				INSERT INTO \"%s\" SELECT id_src, rel_id, id_tgt, label, dtype FROM json_populate_recordset(null::relation_, %%s);
			""" % (relation_type, table), (_jsonify(data),))
		
		table = identifier + "resources"
		resource_type = "uri TEXT, filename TEXT"
		_create_table(table, resource_type, tables, cursor)
		if self._resources.size:
			data = []
			for uri, filename, _ in self._resources:
				if not "#" in uri:
					data.append(dict(uri = uri, filename = filename))
			cursor.execute("""
				DROP TYPE IF EXISTS resource_;
				CREATE TYPE resource_ as (%s);
				INSERT INTO \"%s\" SELECT uri, filename FROM json_populate_recordset(null::resource_, %%s);
			""" % (resource_type, table), (_jsonify(data),))
		
		table = identifier + "geotags"
		geotag_type = "rel_id VARCHAR(512), tag TEXT"
		_create_table(table, geotag_type, tables, cursor)
		if self._geotags.size:
			data = []
			for rel_id, tag in self._geotags:
				if not "#" in rel_id:
					data.append(dict(rel_id = rel_id, tag = tag))
			cursor.execute("""
				DROP TYPE IF EXISTS geotag_;
				CREATE TYPE geotag_ as (%s);
				INSERT INTO \"%s\" SELECT rel_id, tag FROM json_populate_recordset(null::geotag_, %%s);
			""" % (geotag_type, table), (_jsonify(data),))
		
		table = identifier + "worldfiles"
		worldfile_type = "uri TEXT, A NUMERIC, D NUMERIC, B NUMERIC, E NUMERIC, C NUMERIC, F NUMERIC"
		_create_table(table, worldfile_type, tables, cursor)
		if self._worldfiles.size:
			data = []
			for uri, A, D, B, E, C, F in self._worldfiles:
				data.append(dict(uri = uri, A = A, D = D, B = B, E = E, C = C, F = F))
			cursor.execute("""
				DROP TYPE IF EXISTS worldfile_;
				CREATE TYPE worldfile_ as (%s);
				INSERT INTO \"%s\" SELECT uri, A, D, B, E, C, F FROM json_populate_recordset(null::worldfile_, %%s);
			""" % (worldfile_type, table), (_jsonify(data),))
		
		table = identifier + "images"
		image_type = "uri TEXT"
		_create_table(table, image_type, tables, cursor)
		if self._images.size:
			data = []
			for uri in self._images:
				if not (("#" in uri) and (uri.split("#")[0] in self._connected_remote)):
					data.append(dict(uri = uri))
			cursor.execute("""
				DROP TYPE IF EXISTS image_;
				CREATE TYPE image_ as (%s);
				INSERT INTO \"%s\" SELECT uri FROM json_populate_recordset(null::image_, %%s);
			""" % (image_type, table), (_jsonify(data),))
		
		table = identifier + "checked_out"
		checkout_type = "id VARCHAR(512)"
		_create_table(table, checkout_type, tables, cursor)
		if self._checked_out.size:
			data = []
			for id in self._checked_out:
				data.append(dict(id = id))
			cursor.execute("""
				DROP TYPE IF EXISTS checkout_;
				CREATE TYPE checkout_ as (%s);
				INSERT INTO \"%s\" SELECT id FROM json_populate_recordset(null::checkout_, %%s);
			""" % (checkout_type, table), (_jsonify(data),))
		
		table = identifier + "checked_out_updated"
		_create_table(table, checkout_type, tables, cursor)
		if self._checked_out_updated.size:
			data = []
			for id in self._checked_out_updated:
				data.append(dict(id = id))
			cursor.execute("""
				DROP TYPE IF EXISTS checkout_;
				CREATE TYPE checkout_ as (%s);
				INSERT INTO \"%s\" SELECT id FROM json_populate_recordset(null::checkout_, %%s);
			""" % (checkout_type, table), (_jsonify(data),))
		
		table = identifier + "checked_out_deleted"
		_create_table(table, checkout_type, tables, cursor)
		if self._checked_out_deleted.size:
			data = []
			for id in self._checked_out_deleted:
				data.append(dict(id = id))
			cursor.execute("""
				DROP TYPE IF EXISTS checkout_;
				CREATE TYPE checkout_ as (%s);
				INSERT INTO \"%s\" SELECT id FROM json_populate_recordset(null::checkout_, %%s);
			""" % (checkout_type, table), (_jsonify(data),))
		
		table = identifier + "check_out_source"
		_create_table(table, "uri TEXT", tables, cursor)
		if self._check_out_source:
			cursor.execute("INSERT INTO \"%s\" VALUES (%s);" % (table, repr(self._check_out_source)))
		
		table = identifier + "changed"
		_create_table(table, "timestamp NUMERIC", tables, cursor)
		cursor.execute("INSERT INTO \"%s\" VALUES (%f);" % (table, self.changed))
		
		cursor.connection.commit()
		cursor.connection.close()
	
	def merge_remote(self, db, online = False):
		
		def _to_images_item(uri, identifier):
			
			if urlparse(uri).scheme:
				return uri
			return identifier + uri
		
		self._connected_remote.append(db.identifier)
		ident = db.identifier.strip("#").split("/")[-1]
		ident_suffix = "#" + db.identifier.strip("#")
		ident_self = self.identifier.strip("#").split("/")[-1]
		if ident == ident_self:
			print("Error: Cannot merge database with the same identifier as current.")
			return False
		
		objects = np.array([obj_id + ident_suffix for obj_id in db.objects], dtype = object)
		if objects.size:
			if self._objects.size:
				objects = objects[~np.in1d(objects, self._objects)]
				self._objects = np.hstack((self._objects, objects))
			else:
				self._objects = objects
		classes = np.array([[cls_id + ident_suffix, "%s:%s" % (ident, label)] for cls_id, label in db.classes], dtype = object)
		if classes.size:
			if self._classes.size:
				self._classes = np.vstack((self._classes, classes))
			else:
				self._classes = classes
		order_max = self._order.max() if self._order.size else 0
		if db.order.size:
			if self._order.size:
				self._order = np.hstack((self._order, db.order + order_max))
			else:
				self._order = db.order
		members = np.array([[id_src + ident_suffix, mem_id + ident_suffix, id_tgt + ident_suffix] for id_src, mem_id, id_tgt in db.members], dtype = object)
		if members.size:
			if self._members.size:
				self._members = np.vstack((self._members, members))
			else:
				self._members = members
		relations = np.array([[id_src + ident_suffix, rel_id + ident_suffix, id_tgt + ident_suffix, (db.identifier + label) if ((dtype == "DResource") and (not "/" in label) and (not "\\" in label)) else label, dtype] for id_src, rel_id, id_tgt, label, dtype in db.relations], dtype = object)
		if relations.size:
			if self._relations.size:
				self._relations = np.vstack((self._relations, relations))
			else:
				self._relations = relations
		resources = np.array([[db.identifier + uri, filename, path] for uri, filename, path in db.resources], dtype = object)
		if resources.size:
			if online:
				collect = []
				for uri, filename, path in resources:
					collect.append([uri, filename, uri.replace("#","/")])
				resources = np.array(collect, dtype = object)
			if self._resources.size:
				self._resources = np.vstack((self._resources, resources))
			else:
				self._resources = resources.copy()
		
		geotags = np.array([[rel_id + ident_suffix, tag] for rel_id, tag in db.geotags], dtype = object)
		if geotags.size:
			if self._geotags.size:
				self._geotags = np.vstack((self._geotags, geotags))
			else:
				self._geotags = geotags
		worldfiles = np.array([[db.identifier + uri, A, D, B, E, C, F] for uri, A, D, B, E, C, F in db.worldfiles], dtype = object)
		if worldfiles.size:
			if self._worldfiles.size:
				self._worldfiles = np.vstack((self._worldfiles, worldfiles))
			else:
				self._worldfiles = worldfiles
		images = np.array([_to_images_item(uri, db.identifier) for uri in db.images], dtype = object)
		if images.size:
			if self._images.size:
				self._images = np.hstack((self._images, images))
			else:
				self._images = images
		self._upd_changed()
		
		return True
	
	# Object
	
	def add_object(self):
		# return obj_id
		
		obj_id = self._get_new_id(self._objects, ID_PREFIX["Object"])
		self._objects = np.hstack((self._objects, [obj_id]))
		self._upd_changed(created = [obj_id])
		return obj_id
	
	def remove_object(self, obj_id):
		
		if "#" in obj_id:
			return # do not delete objects from connected remote databases
		
		idx = np.where(self._checked_out == obj_id)[0]
		if idx.size:
			self.set_checked_out_deleted(obj_id)
			self._checked_out = np.delete(self._checked_out, idx[0])
		self._objects = self._objects[self._objects != obj_id]
		if self._members.size:
			self._members = self._members[(self._members[:,0] != obj_id) & (self._members[:,2] != obj_id)]
		rel_ids = []
		if self._relations.size:
			slice = self._relations[(self._relations[:,0] == obj_id) | (self._relations[:,2] == obj_id)]
			if slice.size:
				rel_ids = slice[:,1]
				self._relations = self._relations[~np.in1d(self._relations[:,1], rel_ids)]
				rel_ids = rel_ids.tolist()
		self._upd_changed(deleted = [obj_id] + rel_ids)
	
	# Class
	
	def add_class(self, label):
		# label = Literal
		# return cls_id
		
		# check if a Class with this label already exists
		if self._classes.size:
			slice = self._classes[self._classes[:,1] == label.value]
			if slice.size:
				return slice[0,0]
		cls_id = self._get_new_id(self._classes, ID_PREFIX["Class"], 0)
		max_order = 0
		if self._classes.size:
			max_order = self._order.max()
			self._classes = np.vstack((self._classes, [[cls_id, label.value]]))
		else:
			self._classes = np.array([[cls_id, label.value]], dtype = object)
		self._order = np.hstack((self._order, [max_order + 1]))
		self._upd_changed(created = [cls_id])
		return cls_id
	
	def set_class(self, cls_id, label):
		# label = Literal
		# return True if succeeded
		
		if "#" in cls_id:
			return # do not modify classes from connected remote databases

		# check if a Class with this label already exists
		slice = self._classes[self._classes[:,1] == label.value]
		if slice.size:
			return False
		idx = np.where(self._classes[:,0] == cls_id)[0]
		if idx.size:
			if (self._checked_out == cls_id).any():
				self.set_checked_out_updated(cls_id)
			self._classes[idx[0],1] = label.value
			self._upd_changed(updated = [cls_id])
			return True
		return False
	
	def remove_class(self, cls_id):
		
		if "#" in cls_id:
			return # do not delete classes from connected remote databases
		
		idx = np.where(self._classes[:,0] == cls_id)[0]
		if idx.size:
			idx2 = np.where(self._checked_out == cls_id)[0]
			if idx2.size:
				self.set_checked_out_deleted(cls_id)
				self._checked_out = np.delete(self._checked_out, idx2[0])
			idx = idx[0]
			self._classes = np.delete(self._classes, idx, axis = 0)
			obj_ids = np.array([], dtype = object)
			if self._members.size:
				slice = self._members[(self._members[:,0] == cls_id) | (self._members[:,2] == cls_id)]
				if slice.size:
					self._members = self._members[~np.in1d(self._members[:,1], slice[:,1])]
					slice = [id for id in slice[:,2] if id.startswith(ID_PREFIX["Object"])]
					if slice:
						obj_ids = np.union1d(obj_ids, slice)
			rel_ids = []
			if self._relations.size:
				slice = self._relations[self._relations[:,0] == cls_id]
				if slice.size:
					rel_ids = slice[:,1]
					obj_ids = np.union1d(obj_ids, slice[:,2])
					self._relations = self._relations[~np.in1d(self._relations[:,1], rel_ids)]
					rel_ids = rel_ids.tolist()
			self._order = np.delete(self._order, idx, axis = 0)
			self._order[self._order > idx] -= 1
			self._upd_changed(deleted = [cls_id] + rel_ids, updated = obj_ids.tolist())
	
	# Member
	
	def add_member(self, id_src, id_tgt):
		# set id_tgt to be a Member of id_src
		# return mem_id
		
		if "#" in id_src:
			return # do not modify classes from connected remote databases

		# check if id_tgt already is a Member of id_src
		if self._members.size:
			slice = self._members[(self._members[:,0] == id_src) & (self._members[:,2] == id_tgt)]
			if slice.size:
				return slice[0,1]
		mem_id = self._get_new_id(self._members, ID_PREFIX["Member"], 1)
		if self._members.size:
			self._members = np.vstack((self._members, [[id_src, mem_id, id_tgt]]))
		else:
			self._members = np.array([[id_src, mem_id, id_tgt]], dtype = object)
		self._upd_changed(updated = [id_src, id_tgt])
		return mem_id
	
	def remove_member(self, id_src, id_tgt):
		# remove id_tgt from Members of id_src
		
		if "#" in id_src:
			return # do not modify classes from connected remote databases
		
		idx = np.where((self._members[:,0] == id_src) & (self._members[:,2] == id_tgt))[0]
		if idx.size:
			idx = idx[0]
			mem_id = self._members[idx, 1]
			idx2 = np.where(self._checked_out == mem_id)[0]
			if idx2.size:
				self.set_checked_out_deleted(mem_id)
				self._checked_out = np.delete(self._checked_out, idx2[0])
			self._members = np.delete(self._members, idx, axis = 0)
			self._upd_changed(updated = [id_src, id_tgt])
	
	def remove_member_id(self, mem_id):
		
		idx = np.where(self._checked_out == mem_id)[0]
		if idx.size:
			self.set_checked_out_deleted(mem_id)
			self._checked_out = np.delete(self._checked_out, idx[0])
		idx = np.where(self._members == mem_id)[0]
		id_src, id_tgt = self._members[idx,0], self._members[idx,2]
		self._members = np.delete(self._members, idx, axis = 0)
		self._upd_changed(updated = [id_src, id_tgt])
		
	
	# Relation
	
	def add_relation(self, id_src, id_tgt, label):
		# create a Relation connecting Objects id_src and id_tgt with the specified label
		# label = Literal
		# return rel_id
		
		if not (self.is_class(id_src, "Object") and self.is_class(id_tgt, "Object")):
			return
		# check if Relation already exists
		if self._relations.size:
			slice = self._relations[(self._relations[:,0] == id_src) & (self._relations[:,2] == id_tgt) & (self._relations[:,3] == label.value)]
			if slice.size:
				return slice[0,1]
		# create new Edge
		rel_id = self._get_new_id(self._relations, ID_PREFIX["Relation"], 1)
		if self._relations.size:
			self._relations = np.vstack((self._relations, [[id_src, rel_id, id_tgt, label.value, "DString"]]))
		else:
			self._relations = np.array([[id_src, rel_id, id_tgt, label.value, "DString"]], dtype = object)
		self._upd_changed(created = [rel_id], updated = [id_src, id_tgt])
		return rel_id
	
	def add_descriptor(self, id_src, id_tgt, label):
		# create a Relation connecting id_src (the Descriptor Class) and id_tgt (Object) with the specified label
		# label = DLabel
		# return rel_id
		
		if not (self.is_class(id_src, "Class") and self.is_class(id_tgt, "Object")):
			return
		dtype = label.__class__.__name__
		label = label.label
		# check if Descriptor already exists
		if self._relations.size:
			idx = np.where((self._relations[:,0] == id_src) & (self._relations[:,2] == id_tgt))[0]
			if idx.size:
				idx = idx[0]
				rel_id = self._relations[idx, 1]
				if self._relations[idx, 3] == str(label):
					return rel_id
				# only one specific Descriptor for a specific Object can exist
				self._relations[idx, 3] = str(label)
				self._relations[idx, 4] = dtype
				if (self._checked_out == rel_id).any():
					self.set_checked_out_updated(rel_id)
				self._upd_changed(updated = [rel_id, id_src, id_tgt])
				return rel_id
		# create new Edge
		rel_id = self._get_new_id(self._relations, ID_PREFIX["Relation"], 1)
		if self._relations.size:
			self._relations = np.vstack((self._relations, [[id_src, rel_id, id_tgt, str(label), dtype]]))
		else:
			self._relations = np.array([[id_src, rel_id, id_tgt, str(label), dtype]], dtype = object)
		self.set_checked_out_updated(rel_id)
		self._upd_changed(created = [rel_id], updated = [id_src, id_tgt])
		return rel_id
	
	def remove_relation(self, rel_id):
		
		if "#" in rel_id:
			return # do not delete relations from connected remote databases
		
		idx = np.where(self._checked_out == rel_id)[0]
		if idx.size:
			self.set_checked_out_deleted(rel_id)
			self._checked_out = np.delete(self._checked_out, idx[0])
		
		idx = np.where(self._relations[:,1] == rel_id)[0]
		if idx.size:
			idx = idx[0]
			id_src, _, id_tgt, label, dtype = self._relations[idx]
			self._relations = np.delete(self._relations, idx, axis = 0)
			updated = [id_src, id_tgt]
			if dtype == "DResource":
				updated.append(URIRef(label))
			self._upd_changed(deleted = [rel_id], updated = updated)
	
	# Resource
	
	def get_unique_name(self, origname):
		
		origname = unicodedata.normalize("NFKD", str(origname).lower()).encode("ascii", "ignore").decode("ascii")
		origname, ext = os.path.splitext(os.path.split(origname)[-1])
		origname = origname.replace(".", "_").replace(" ", "_")
		filename = origname + ext
		if self._resources.size:
			slice = self._resources[self._resources[:,0] == filename]
			if slice.size:
				ext = ext.strip(".")
				suffix = 0
				filename = "%s_%d.%s" % (origname, suffix, ext)
				try:
					suffix = int(os.path.splitext(slice[0,0])[0].split("_")[-1]) + 1
				except:
					pass
				while True:
					filename = "%s_%d.%s" % (origname, suffix, ext)
					if not (self._resources[:,0] == filename).any():
						return filename
					suffix += 1
		return filename
	
	def add_resource(self, uri, filename, path):
		# uri = URIRef
		
		if not isinstance(uri, URIRef):
			uri = URIRef(str(uri))
		if self._resources.size and (self._resources[:,0] == str(uri)).any():
			return
		if not self._resources.size:
			self._resources = np.array([[str(uri), filename, path]], dtype = object)
		else:
			self._resources = np.vstack((self._resources, [[str(uri), filename, path]]))
		self._upd_changed(created = [uri])
	
	def is_image(self, uri):
		# return True if resource is marked as an image
		
		if self._images.size:
			return (self._images == str(uri)).any()
		return False
	
	def set_is_image(self, uri):
		# mark resource as image
		# uri = URIRef
		
		if self._images.size and (self._images == str(uri)).any():
			return
		if not self._images.size:
			self._images = np.array([str(uri)], dtype = object)
		else:
			self._images = np.hstack((self._images, [str(uri)]))
	
	def remove_resource(self, uri):
		# uri = URIRef
		
		if not isinstance(uri, URIRef):
			uri = URIRef(str(uri))
		if self._resources.size:
			self._resources = self._resources[self._resources[:,0] != str(uri)]
			self._upd_changed(deleted = [uri])
	
	# Geotag
	
	def add_geotag(self, rel_id, value, srid = None, srid_vertical = None):
		# set a geotag to a Descriptor the value of which is an image resource or geometry
		# value = wktLiteral
		# return True if successful
		
		if "#" in rel_id:
			return False # do not modify relations from connected remote databases
		
		if not self._relations.size:
			return False
		slice = self._relations[self._relations[:,1] == rel_id]
		if slice.size:
			label, dtype = slice[0][3:]
			if dtype in ["DResource", "DGeometry"]:
				value = wkt_to_wktLiteral(*value_to_wkt(value, srid, srid_vertical))
				found = False
				if self._geotags.size:
					idx = np.where(self._geotags[:,0] == rel_id)[0]
					if idx.size:
						self._geotags[idx[0],1] = str(value)
						found = True
				if not found:
					if not self._geotags.size:
						self._geotags = np.array([[rel_id, str(value)]], dtype = object)
					else:
						self._geotags = np.vstack((self._geotags, [[rel_id, str(value)]]))
				self._upd_changed(updated = [rel_id, label])
				return True
		return False
	
	def remove_geotag(self, rel_id):
		
		if "#" in rel_id:
			return # do not modify relations from connected remote databases
		
		if self._geotags.size:
			self._geotags = self._geotags[self._geotags[:,0] != rel_id]
			slice = self._relations[self._relations[:,1] == rel_id]
			self._upd_changed(updated = [rel_id, slice[0][3]])
	
	# Worldfile
	
	def has_worldfile(self, uri):
		
		if self._worldfiles.size:
			return (self._worldfiles[:,0] == str(uri)).any()
		return False
	
	def get_worldfile(self, uri):
		# return params [A, D, B, E, C, F], if uri has a worldfile associated
		
		if self._worldfiles.size:
			slice = self._worldfiles[self._worldfiles[:,0] == str(uri)]
			if slice.size:
				return [float(val) for val in slice[0,1:]]
		return None
	
	def add_worldfile(self, uri, params):
		# set worldfile parameters to an uri
		# params = [A, D, B, E, C, F]
		
		uri = str(uri)
		if self._worldfiles.size:
			self._worldfiles = self._worldfiles[self._worldfiles[:,0] != uri]
		if isinstance(params, np.ndarray):
			params = params.tolist()
		if self._worldfiles.size:
			self._worldfiles = np.vstack((self._worldfiles, [[uri] + params]))
		else:
			self._worldfiles = np.array([[uri] + params], dtype = object)
	
	# Order
	
	def swap_order(self, id_cls1, id_cls2):
		# swap order of two objects based on ids
		# return their new orders or None, None if ordering was not possible
		
		if ("#" in id_cls1) or ("#" in id_cls2):
			return None, None # do not modify classes from connected remote databases
		
		idx1 = np.where(self._classes[:,0] == id_cls1)[0]
		idx2 = np.where(self._classes[:,0] == id_cls2)[0]
		if idx1.size and idx2.size:
			self._order[idx1[0]], self._order[idx2[0]] = self._order[idx2[0]], self._order[idx1[0]]
			self._upd_changed(ordered = [id_cls1, id_cls2])
			return self._order[idx1[0]], self._order[idx2[0]]
		return None, None
	
	# Check Out
	
	def set_checked_out(self, uri, objects = None):
		# set all ids as checked out
		# uri = URIRef or str
		# objects = [obj_id, ...]; if specified, check out only elements related to these objects
		
		if not objects is None:
			# prune all elements to only objects, related objects, their classes, parent classes and descriptors
			if isinstance(objects, list):
				objects = np.array(objects, dtype = object)
			# objects and related objects
			related_objects = np.array([], dtype = object)
			if self._relations.size:
				slice = self._relations[np.in1d(self._relations[:,0], objects) | np.in1d(self._relations[:,2], objects)]
				if slice.size:
					slice = np.union1d(slice[:,0], slice[:,2])
					related_objects = np.union1d(related_objects, slice[slice.astype("<U3") == self.get_dep_class_prefix("Object")])
					related_objects = np.setdiff1d(related_objects, objects)
			self._objects = np.hstack((objects, related_objects))
			# classes, descriptors and their parent classes
			classes_keep = np.array([], dtype = object)
			if self._relations.size:
				classes_keep = np.unique(self._relations[np.in1d(self._relations[:,2], self._objects), 0])
				if classes_keep.size:
					classes_keep = classes_keep[classes_keep.astype("<U3") == self.get_dep_class_prefix("Class")]
			if self._members.size:
				classes_keep = np.union1d(classes_keep, self._members[np.in1d(self._members[:,2], self._objects), 0])
				if classes_keep.size:
					parent_classes = self._members[np.in1d(self._members[:,2], classes_keep), 0]
					while parent_classes.size:
						classes_keep = np.union1d(classes_keep, parent_classes)
						parent_classes = self._members[np.in1d(self._members[:,2], parent_classes), 0]
			ids_keep = self._objects
			if classes_keep.size:
				mask = np.in1d(self._classes[:,0], classes_keep)
				self._classes = self._classes[mask]
				self._order = self._order[mask]
				ids_keep = np.hstack((ids_keep, classes_keep))
			else:
				self._classes = classes_keep.copy()
				self._members = classes_keep.copy()
			# keep only members with source & target in kept objects or classes
			if self._members.size:
				self._members = self._members[np.in1d(self._members[:,0], ids_keep) & np.in1d(self._members[:,2], ids_keep)]
			# keep only relations with source & target in kept objects or classes
			if self._relations.size:
				self._relations = self._relations[np.in1d(self._relations[:,0], ids_keep) & np.in1d(self._relations[:,2], ids_keep)]
			# keep only resources, worldfiles, geotags and image information used in relations
			if self._relations.size:
				labels_keep = np.unique(self._relations[~np.in1d(self._relations[:,2], related_objects),3])
				if self._resources.size:
					self._resources = self._resources[np.in1d(self._resources[:,0], labels_keep)]
				if self._worldfiles.size:
					self._worldfiles = self._worldfiles[np.in1d(self._worldfiles[:,0], labels_keep)]
				if self._images.size:
					self._images = self._images[np.in1d(self._images, labels_keep)]
				if self._geotags.size:
					self._geotags = self._geotags[np.in1d(self._geotags[:,0], self._relations[:,1])]
			else:
				self._resources = np.array([], dtype = object)
				self._geotags = np.array([], dtype = object)
				self._worldfiles = np.array([], dtype = object)
				self._images = np.array([], dtype = object)
		
		self._checked_out = np.array([], dtype = object)
		if self._objects.size:
			self._checked_out = np.hstack((self._checked_out, self._objects))
		if self._classes.size:
			self._checked_out = np.hstack((self._checked_out, self._classes[:,0]))
		if self._relations.size:
			self._checked_out = np.hstack((self._checked_out, self._relations[:,1]))
		self._check_out_source = str(uri)
	
	def set_checked_out_updated(self, id):
		
		self._checked_out_updated = np.hstack((self._checked_out_updated, [id]))
	
	def set_checked_out_deleted(self, id):
		
		self._checked_out_deleted = np.hstack((self._checked_out_deleted, [id]))
	