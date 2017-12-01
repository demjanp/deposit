'''
	Deposit Store
	--------------------------
	
	Created on 10. 4. 2017
	
	@author: Peter Demjan <peter.demjan@gmail.com>
	
	Interface to a Deposit database, file store and client
	
	Initialize using a DB and File (optional) objects
	e.g.: Store(DB("http://mygraph#", "sqlite://"), File("data/"))
	
	sub-objects:
		.objects = Objects()
		.classes = Classes()
		.members = Members()
		.relations = Relations()
		.geotags = Geotags()
		.projections = Projections()
		.resources = Resources()
		.geometry = Geometry()
		.queryfnc = Queryfnc()
		.observer = Observer

'''

from deposit.store.Objects import Objects
from deposit.store.Classes import Classes
from deposit.store.Members import Members
from deposit.store.Relations import Relations
from deposit.store.Geotags import Geotags
from deposit.store.Projections import Projections
from deposit.store.Resources import Resources
from deposit.store.Geometry import Geometry
from deposit.store.Queryfnc import Queryfnc
from deposit.store.Observer import Observer

from deposit.DB import (DB, OGC)
from deposit.File import file_from_db
from deposit.DLabel import (DLabel, DString, DResource, DGeometry, DNone)
from rdflib import (URIRef, Literal)
from urllib.parse import urlparse
import numpy as np
import os
import shutil
import copy

class Store(object):
	
	def __init__(self, db = None, file = None):
		# db = a Deposit DB object
		# file = a Deposit File object
		
		if db is None:
			db = DB()
		if file is None:
			file = file_from_db(db)
		self._params = [db.params, None if (file is None) else file.path()] # [[identifier, connstr], path]; db and file parameters used to initialize store
		self._db = db
		self.file = file
		self._on_changed_fnc = None
		self._on_message_fnc = None
		self._changing = 0
		self._remote_files = {} # {identifier: file path, ...}
		self._srid = [None, None] # [horizontal SRID, vertical SRID]
		
		super(Store, self).__init__()
		
		self.objects = Objects(self)
		self.classes = Classes(self)
		self.members = Members(self)
		self.relations = Relations(self)
		self.geotags = Geotags(self)
		self.projections = Projections(self)
		self.resources = Resources(self)
		self.geometry = Geometry(self)
		self.queryfnc = Queryfnc(self)
		self.observer = Observer(self)
		
		self._db.set_on_changed(self._on_changed)
		self._populate_db_paths()
	
	def _on_changed(self):
		
		if (not self._on_changed_fnc is None) and (not self._changing):
			self._on_changed_fnc(self._db.changed, self._db.changed_ids)
			self._db.reset_changed_ids()
	
	def _populate_db_paths(self, db = None, file = None):
		# add paths to db._resources
		
		if db is None:
			db = self._db
		if file is None:
			file = self.file
		
		if db._resources.size:
			path = file.path()
			if urlparse(path).scheme in ["http", "https"]:
				for i in range(db._resources.shape[0]):
					db._resources[i,2] = db._resources[i,0].replace("#","/")
			else:
				paths = file.get_stored_paths()
				if paths:
					for i in range(db._resources.shape[0]):
						if db._resources[i,0] in paths:
							db._resources[i,2] = paths[db._resources[i,0]]
		
	def _copy_data(self, path):
		
		if not os.path.exists(path):
			os.makedirs(os.path.abspath(path))
		if path and self.file.path() and (os.path.normpath(os.path.abspath(path)) != os.path.normpath(os.path.abspath(self.file.path()))):
			for uri, filename, src_path in self._db.resources:
				if src_path and (not "#" in uri):
					tgt_path = os.path.join(self.file.get_new_dir(path), os.path.split(src_path)[1])
					if not os.path.isfile(tgt_path):
						shutil.copyfile(src_path, tgt_path)
	
	# common functions
	
	def params(self):
		# returns [[identifier, connstr], path]; db and file parameters used to initialize store
		
		return self._params
	
	def identifier(self):
		
		return self._db.identifier
	
	def server_url(self):
		
		return self._db.server_url
	
	def has_database(self):
		
		return self._db.has_database()
	
	def checked_out(self):
		
		return self._db.checked_out
	
	def check_out_source(self):
		
		return self._db.check_out_source
	
	def connect_remote(self, db, file):
		# connect a remote store
		
		ident = db.identifier
		parsed = urlparse(file.path())
		online = (parsed.scheme in ["http", "https"])
		self.begin_change()
		if self._db.merge_remote(db, online = online):
			if not ident in self._remote_files:
				self._remote_files[ident] = file.path()
			if not online:
				self.file.merge_thumbnails(file.thumbnails())
				if db._resources.size:
					i0 = self._db._resources.shape[0] - db._resources.shape[0]
					paths = file.get_stored_paths()
					if paths:
						for i in range(db._resources.shape[0]):
							if db._resources[i,0] in paths:
								self._db._resources[i0 + i,2] = paths[db._resources[i,0]]
		
		self.end_change()
	
	def remote_identifiers(self):
		# return [identifier, ...]
		
		return sorted(self._remote_files.keys())
	
	def save_to_file(self, path):
		
		path = os.path.normpath(path)
		self._db.serialize(path)
		self._copy_data(os.path.split(path)[0])
	
	def store_in_database(self, identifier, connstr, path):
		
		self._db.store_in_db(identifier, connstr)
		self._copy_data(path)
	
	def check_out(self, path, objects = None):
		
		store_check = copy.copy(self)
		store_check._db = copy.copy(self._db)
		store_check.set_on_changed(None)
		store_check.set_on_message(None)
		store_check._db.set_checked_out(self._db.identifier, objects)
		store_check.save_to_file(path)
		store_check = None
	
	def check_in(self, ident, overwrite = False):
		# overwrite: True if colliding Descriptors during check-in should be overwritten in the source database, False if they should be added under a new name
		# return state, missing_members, missing_relations, duplicate_descriptors
		# state = True if check-in was successfull else error message
		# missing_members = [[id_src, id_tgt], ...]; Members not checked in due to deletion in source database
		# missing_relations = [[id_src, id_tgt, label], ...]; Relations not checked in due to deletion in source database
		# duplicate_descriptors = {name: cls_id, ...}; Descriptors created due to colisions (Descriptor -> label -> Object combination exists in source database with a different label)
		
		def _node_exists(id):
			
			if self._db.is_class(id, "Class"):
				return (self._db.classes[:,0] == id).any()
			if self._db.is_class(id, "Object"):
				return (self._db.objects == id).any()
			return
		
		ident_source = ident.strip("#").split("/")[-1]
		ident_self = self._db.identifier.strip("#").split("/")[-1]
		if ident_source == ident_self:
			return "Error: Cannot check in database with the same identifier as current.", [], [], {}
		
		db_check = DB(ident)
		file_check = file_from_db(db_check)
		self._populate_db_paths(db_check, file_check)
		
		if db_check.check_out_source != self._db.identifier:
			return "Error: Check-out source of the specified database is different than current.", [], [], {}
		
		missing_members = [] # [[id_src, id_tgt], ...]; Members not checked in due to deletion in current database
		missing_relations = [] # [[id_src, id_tgt, label], ...]; Relations not checked in due to deletion in current database
		duplicate_descriptors = {} # {name: cls_id, ...}; Descriptors created due to colisions (Descriptor -> label -> Object combination exists in current database with a different label)
		
		id_lookup = {}
		# check in Objects
		for id_obj in db_check.objects[~np.in1d(db_check.objects, db_check.checked_out)]:
			id_lookup[id_obj] = self._db.add_object()
		# check in created Classes
		for cls_id, label in db_check.classes[~np.in1d(db_check.classes[:,0], db_check.checked_out)]:
			id_lookup[cls_id] = self._db.add_class(Literal(label))
		# check in renamed Classes
		for cls_id, label in db_check.classes[np.in1d(db_check.classes[:,0], db_check.checked_out_updated)]:
			if overwrite:
				self._db.set_class(cls_id, Literal(label))
				id_lookup[cls_id] = cls_id
			else:
				id_lookup[cls_id] = self._db.add_class(Literal(label))
		# check in Members
		for id_src, _, id_tgt in db_check.members:
			checked = False
			if id_src in id_lookup:
				id_src = id_lookup[id_src]
				checked = True
			elif not _node_exists(id_src): # check if id_src still exists in current database
				missing_members.append([id_src, id_tgt])
				continue
			if id_tgt in id_lookup:
				id_tgt = id_lookup[id_tgt]
				checked = True
			elif not _node_exists(id_tgt): # check if id_tgt still exists in current database
				missing_members.append([id_src, id_tgt])
				continue
			if checked:
				self._db.add_member(id_src, id_tgt)
		# check in Relations
		for id_src, rel_id, id_tgt, label, dtype in db_check.relations:
			
			# check if id_src still exists in current database
			if id_src in id_lookup:
				id_src = id_lookup[id_src]
			elif not _node_exists(id_src):
				missing_relations.append([id_src, id_tgt, label])
				continue
			
			# check if id_tgt still exists in current database
			if id_tgt in id_lookup:
				id_tgt = id_lookup[id_tgt]
			elif not _node_exists(id_tgt):
				missing_relations.append([id_src, id_tgt, label])
				continue
			
			# Relation is a Descriptor (cls_id -> rel -> id_obj)
			if self._db.is_class(id_src, "Class"):
				
				exists = False
				
				# check if descriptor id_src -> id_tgt already exists in current database
				if self._db.relations.size:
					slice = self._db.relations[(self._db.relations[:,0] == id_src) & (self._db.relations[:,2] == id_tgt)]
					if slice.size:
						# if it has different label or dtype and was created or updated in checked out db, create or update descriptor
						label2, dtype2 = slice[0,3:]
						if ((label2 != label) or (dtype2 != dtype)) and (db_check.checked_out_updated == rel_id).any():
							if overwrite:
								exists = False
							else:
								name = self._db.classes[self._db.classes[:,0] == id_src][0,1]
								n = 0
								while (not name in duplicate_descriptors) and (self._db.classes[:,1] == name).any():
									n += 1
									name = "%s_%d" % (name, n)
								if name in duplicate_descriptors:
									id_src = duplicate_descriptors[name]
								else:
									id_src = self._db.add_class(Literal(name))
									duplicate_descriptors[name] = id_src
						else:
							exists = True
					
				if not exists:
					
					tag = None
					
					if dtype == "DResource":
						label = DResource(label)
						if db_check.resources.size:
							slice = db_check.resources[db_check.resources[:,0] == label.value]
							if slice.size: # resource is local
								filename, path = slice[0,1:]
								uri, _, path = self.file.add_to_store(path, filename)
								self._db.add_resource(URIRef(uri), filename, path)
								label = DResource(uri)
						
						if db_check.worldfiles.size:
							slice = db_check.worldfiles[db_check.worldfiles[:,0] == label.value]
							if slice.size: # resource has a worldfile
								self._db.add_worldfile(label.value, slice[0,1:])
						
					elif dtype == "DGeometry":
						tag = db_check.geotags.get(rel_id)
					
					else: # DString / DDateTime
						label = globals()[dtype](label)
					
					rel_id = self._db.add_descriptor(id_src, id_tgt, label)
					if not tag is None: # relation has geotag
						self._db.add_geotag(rel_id, tag)
			
			# Relation is between Objects (id_obj -> rel -> id_obj)
			else: # id_obj -> rel -> id_obj
				self._db.add_relation(id_src, id_tgt, Literal(label))
		
		# delete entities deleted in checked out database
		for id in db_check.checked_out_deleted:
			cls = self._db.get_dep_class_by_id(id)
			if cls == "Object":
				self.objects.remove(id)
			elif cls == "Class":
				self.classes.remove(id)
			elif cls == "Member":
				self._db.remove_member_id(id)
			elif cls == "Relation":
				self.relations.remove(id)
		
		return True, missing_members, missing_relations, duplicate_descriptors
	
	def get_schema(self):
		# return path to RDF schema of current database in RDF/XML format
		
		ident = self._db.identifier.split("/")[-1].strip("#")
		path = os.path.join(self.file.get_temp_path(), "%s_%s.rdf" % (ident, self._db.changed))
		if not os.path.isfile(path):
			self._db.serialize(path)
		return os.path.abspath(path)
	
	def get_label(self, id, read_only = None, as_string = False):
		# id = str or array
		# read_only = True/False or [True, False, ...] in order of id
		# return label (or [label, ...]) of a graph element as an instance of DLabel
		
		if isinstance(id, str) and ("#" in id):
			read_only = True
		if isinstance(id, list):
			id = np.array(id, dtype = object)
		if isinstance(read_only, list):
			read_only = np.array(read_only)
		if isinstance(id, np.ndarray):
			if isinstance(read_only, np.ndarray):
				if read_only.dtype != bool:
					read_only_conv = np.zeros(read_only.shape[0], dtype = bool)
					read_only_conv[read_only == "True"] = True
					read_only = read_only_conv
			elif not read_only is None:
				if (read_only == True) or (read_only == "True") or (read_only == 1):
					read_only = np.ones(id.shape[0], dtype = bool)
				else:
					read_only = np.zeros(id.shape[0], dtype = bool)
			
			if not read_only is None:
				if (not isinstance(read_only, np.ndarray)) or (id.shape[0] != len(read_only)):
					return []
			if self._db.classes.size:
				slice = self._db.classes[np.in1d(self._db.classes[:,0], id)] # [[id_cls, label], ...]
				if slice.size:
					slice = slice[np.argsort(slice[:,0])]
					ids = slice[:,0]
					slice = slice[np.searchsorted(slice[:,0], id)][:,1]
					if as_string:
						return slice.tolist()
					if read_only is None:
						return [DString(slice[i], read_only = ("#" in ids[i])) for i in range(slice.shape[0])]
					else:
						return [DString(slice[i], read_only = (read_only[i] or ("#" in ids[i]))) for i in range(slice.shape[0])]
			if self._db.relations.size:
				slice = self._db.relations[np.in1d(self._db.relations[:,1], id)]
				if slice.size:
					slice = slice[:,[1,3,4]]
					slice = slice[np.argsort(slice[:,0])]
					slice = slice[np.searchsorted(slice[:,0], id)]
					if as_string:
						return slice[:,1].tolist()
					if read_only is None:
						return [globals()[dtype](label, relation = rel_id, read_only = ("#" in rel_id)) for rel_id, label, dtype in slice]
					else:
						return [globals()[slice[i,2]](slice[i,1], read_only = read_only[i] or ("#" in slice[i,0]), relation = slice[i,0]) for i in range(slice.shape[0])]
			return []
		else:
			read_only = ((read_only == True) or (read_only == "True") or (read_only == 1))
			if self._db.classes.size:
				slice = self._db.classes[self._db.classes[:,0] == id]
				if slice.size:
					if as_string:
						return slice[0,1]
					return DString(slice[0,1], read_only = read_only or ("#" in id))
			if self._db.relations.size:
				slice = self._db.relations[self._db.relations[:,1] == id]
				if slice.size:
					label, dtype = slice[0, 3:]
					if as_string:
						return label
					return globals()[dtype](label, read_only = read_only or ("#" in id), relation = id)
			if as_string:
				return None
			return DNone(read_only = read_only)
	
	def get_description(self, id):
		# return description of a graph element
		# TODO
		
		raise NotImplementedError
	
	def get_dep_class_by_id(self, id):
		# return Deposit class name
		
		return self._db.get_dep_class_by_id(id)
	
	def get_dep_class_prefix(self, dep_class):
		
		return self._db.get_dep_class_prefix(dep_class)
	
	def swap_order(self, id_cls1, id_cls2):
		# swap order of two Classes based on ids, return their new orders or None, None if ordering was not possible
		
		return self._db.swap_order(id_cls1, id_cls2)
	
	def get_order(self, id_cls):
		# return order of a Class
		
		idx = np.where(self._db.classes[:,0] == id_cls)[0]
		if idx.size:
			if not self._db.order.ndim:
				return int(self._db.order.flatten())
			return self._db.order[int(idx[0])]
		return None
	
	def get_changed(self):
		# return timestamp of last change of the connected graph
		
		return self._db.changed
	
	def get_changed_ids(self):
		# return {created: [id, ...], updated: [id, ...], deleted: [id, ...], ordered: [id, ...]}
		
		return self._db.changed_ids
	
	def set_on_changed(self, func):
		# call func() when the connected graph changes
		
		self._on_changed_fnc = func
	
	def begin_change(self):
		# call before executing multiple writes to supress calling the "on changed" function
		
		self._changing += 1
	
	def end_change(self):
		# call after executing multiple writes
		
		if self._changing:
			self._changing -= 1
		if not self._changing:
			if not self._on_changed is None:
				self._on_changed()
	
	def set_on_message(self, func):
		
		self._on_message_fnc = func
	
	def message(self, text):
		
		if not self._on_message_fnc is None:
			self._on_message_fnc(text)
	
	def set_srid(self, srid, vertical_srid = None):
		
		self._srid = [srid, vertical_srid]
	
	def srid(self):
		# return [horizontal SRID, vertical SRID]
		
		return self._srid
	
	# convenience functions
	
	def add_object_by_name(self, names = []):
		# create an Object and make it Member of Classes specified by names
		# names: [name, ...]
		# return id_obj
		
		self.begin_change()
		id_obj = self._db.add_object()
		for name in names:
			id_cls = self._db.add_class(Literal(name))
			self._db.add_member(id_cls, id_obj)
		self.end_change()
		return id_obj
	
	def add_unique_object(self, classes, descriptors):
		# classes = [name, ...]
		# descriptors = {name: value, ...}
		# return id_obj
		
		id_obj = None
		self.begin_change()
		class_ids = [self._db.add_class(Literal(name)) for name in classes]
		descr_ids = dict([(self._db.add_class(Literal(name)), descriptors[name]) for name in descriptors]) # {id_descr: value, ...}
		
		slice = self._db.objects
		if slice.size:
			for id_cls in class_ids:
				slice = slice[np.in1d(slice, self._db.members[self._db.members[:,0] == id_cls, 2])]
				if not slice.size:
					break
		if slice.size:
			for id_descr in descr_ids:
				slice = slice[np.in1d(slice, self._db.relations[(self._db.relations[:,0] == id_descr) & (self._db.relations[:,3] == descr_ids[id_descr]), 2])]
				if not slice.size:
					break
		if slice.size:
			slice.sort()
			id_obj = slice[0]
		else:
			id_obj = self._db.add_object()
			for id_cls in class_ids:
				self._db.add_member(id_cls, id_obj)
			for id_descr in descr_ids:
				self.relations.add_descriptor(id_descr, id_obj, descr_ids[id_descr])
		self.end_change()
		return id_obj
	
	def add_member_by_name(self, name1, name2):
		# make name2 a Member (Subclass) of name1
		# return id_cls1, id_cls2
		
		self.begin_change()
		id_cls1 = self._db.add_class(Literal(name1))
		id_cls2 = self._db.add_class(Literal(name2))
		self._db.add_member(id_cls1, id_cls2)
		self.end_change()
		return id_cls1, id_cls2
	
	def add_descriptor_by_name(self, id_obj, name, value):
		# create or look up a Descriptor Class specified by name and create a Relation to the Object specified by value
		# return rel_id, cls_id (id of the Descriptor Relation and Class)
		
		self.begin_change()
		cls_id = self._db.add_class(Literal(name))
		rel_id = self.relations.add_descriptor(cls_id, id_obj, value)
		self.end_change()
		return rel_id, cls_id
	