from deposit import Broadcasts
from deposit.DModule import (DModule)
from deposit.store.DElements.DObjects import (DObjects)
from deposit.store.DElements.DClasses import (DClasses)
from deposit.store.DElements.DDescriptors import (DDescriptor)
from deposit.store.DLabel.DNone import (DNone)
from deposit.store.Files import (Files)
from deposit.store.Images import (Images)
from deposit.store.Events import (Events)
from deposit.store.UserTools import (UserTools)
from deposit.store.Queries import (Queries)
from deposit.store.Query.Query import (Query)
from deposit.store.datasources._DataSources import (DataSources)
from deposit.store.datasources._DataSource import (DataSource)
from deposit.store.externalsources._ExternalSources import (ExternalSources)
from deposit.store.Conversions import (as_url, to_unique)

import time
import os

class Store(DModule):

	def __init__(self, *args, parent = None):
		
		self.parent = parent

		self.objects = None
		self.classes = None

		self.json = None
		
		self.datasources = DataSources(self)
		self.externalsources = ExternalSources(self)
		
		self.files = None
		self.images = None
		self.events = None
		self.user_tools = None
		self.queries = None

		self.local_folder = None
		self.changed = None
		self.linked = {} # {identifier: LinkedStore(), ...}
		self._local_resource_uris = []
		self.save_events = False

		self.data_source = None # DB / DBRel / JSON / RDFGraph / None

		DModule.__init__(self)
		
		self.objects = DObjects(self)
		self.classes = DClasses(self)
		
		self.json = self.datasources.JSON()
		
		self.files = Files(self)
		self.images = Images(self)
		self.events = Events(self)
		self.user_tools = UserTools(self)
		self.queries = Queries(self)
		
		from deposit.store.DElements.DClasses import (DClass)
		from deposit.store.DElements.DObjects import (DObject)
		from deposit.store.DElements.DRelations import (DRelations)
		from deposit.store.DElements.DDescriptors import (DDescriptors)
		
		self.DCLASS = DClass
		self.DCLASSES = DClasses
		self.DOBJECT = DObject
		self.DOBJECTS = DObjects
		self.DRELATIONS = DRelations
		self.DDESCRIPTORS = DDescriptors
		
		self.connect_broadcast(Broadcasts.ELEMENT_ADDED, self.on_data_changed)
		self.connect_broadcast(Broadcasts.ELEMENT_CHANGED, self.on_data_changed)
		self.connect_broadcast(Broadcasts.ELEMENT_DELETED, self.on_data_changed)
		self.connect_broadcast(Broadcasts.STORE_LOCAL_FOLDER_CHANGED, self.on_data_changed)
		
		if len(args) > 0:
			if len(args[0]) == 2:
				self.load(*args)
			elif len(args[0]) == 1:
				self.load(args[0][0])

	@property
	def identifier(self):

		if self.data_source is None:
			return None
		return self.data_source.identifier
	
	@property
	def connstr(self):
		
		if self.data_source is None:
			return None
		return self.data_source.connstr

	def clear(self):

		self.objects = DObjects(self)
		self.classes = DClasses(self)
		self.local_folder = None
		self.changed = None
		self.linked = {}
		self._local_resource_uris = []
		self.events.clear()
		self.user_tools.clear()
		self.queries.clear()

		self.broadcast(Broadcasts.STORE_LOADED)

	def set_datasource(self, data_source):
		
		if not ((data_source is None) or isinstance(data_source, DataSource)):
			raise Exception("Invalid data source specified:", data_source)
		self.data_source = data_source
		self.broadcast(Broadcasts.STORE_DATA_SOURCE_CHANGED)

	def set_local_folder(self, path, silent = False):
		
		if not os.path.isdir(path):
			os.mkdir(path)
		self.local_folder = path
		if not silent:
			self.broadcast(Broadcasts.STORE_LOCAL_FOLDER_CHANGED)
	
	def localise_resources(self, force = False, ids = None):
		
		if self.local_folder is None:
			return
		if ids is None:
			ids = self.objects.keys()
		cmax = len(ids)
		cnt = 1
		for id in ids:
			print("\rCopying files %d/%d         " % (cnt, cmax), end = "")
			cnt += 1
			for descr in self.objects[id].descriptors:
				descr = self.objects[id].descriptors[descr]
				if descr.linked:
					continue
				if descr.label.__class__.__name__ != "DResource":
					continue
				if (not force) and descr.label.is_stored():
					continue
				if descr.label.is_stored():
					path = descr.label._path
					self.del_local_resource_uri(descr.label.value)
				else:
					path = descr.label.value
				descr.label = self.files.store_local(path)
			self.broadcast(Broadcasts.ELEMENT_CHANGED, self.objects[id])
	
	@property
	def class_names(self):

		return self.classes.keys()

	@property
	def relation_names(self):

		return sorted(list(set(sum((list(self.classes[name].relations.keys()) for name in self.classes), []))))

	@property
	def descriptor_names(self):

		ret = list(set(sum((self.classes[name].descriptors for name in self.classes), [])))
		return sorted(ret, key = lambda name: self.classes[name].order)
	
	@property
	def local_resource_uris(self):
		
		return self._local_resource_uris

	def add_local_resource_uri(self, uri):

		if not uri in self._local_resource_uris:
			self._local_resource_uris.append(uri)

	def del_local_resource_uri(self, uri):

		if uri in self._local_resource_uris:
			self._local_resource_uris = [uri2 for uri2 in self._local_resource_uris if uri2 != uri]

	def set_local_resource_uris(self, uris):

		self._local_resource_uris = uris
	
	def set_save_events(self, state):
		
		self.save_events = state
	
	def null_descriptor(self, obj, cls):
		
		return DDescriptor(obj, cls, DNone())
	
	def reverse_relation(self, name):

		if name == "*":
			return name
		if name.startswith("~"):
			return name[1:]
		return "~" + name

	def query(self, querystr):

		return Query(self, querystr)
	
	def get_datasource(self, identifier, connstr, store = None):
		
		if store is None:
			store = self
		
		if identifier:
			identifier = as_url(identifier)
		
		if not connstr is None:
			
			ds = store.datasources.DBRel()
			if ds.set_connstr(connstr) and ds.is_valid() and ds.load():
				return ds
			
			if not identifier is None:
				ds = store.datasources.DB(identifier = identifier, connstr = connstr)
				if ds.load():
					return ds
			
		elif not identifier is None:
			
			if identifier[-1] == "#":
				ds = store.datasources.JSON(url = "%s.json" % (identifier[:-1]))
				if (ds is not None) and ds.load():
					return ds
				ds = store.datasources.RDFGraph(url = "%s.rdf" % (identifier[:-1]))
				if (ds is not None) and ds.load():
					return ds
			
			ext = identifier.split(".")[-1].lower().strip()
			if ext == "json":
				ds = store.datasources.JSON(url = identifier)
			elif ext == "rdf":
				ds = store.datasources.RDFGraph(url = identifier)
			if (ds is not None) and ds.load():
				return ds
		
		return None

	def load(self, identifier = None, connstr = None):
		# convenience function & used by MRUD
		
		ds = self.get_datasource(identifier, connstr)
		if ds is None:
			return False
		self.set_datasource(ds)
		return True
	
	def save(self):
		# convenience function
		
		result = False
		if self.data_source is not None:
			result = self.data_source.save()
		return result
	
	def add_objects(self, identifier_ds, connstr = None, ids = None, localise = False):
		# add objects from a different store, specified by identifier and connstr
		# identifier_ds = identifier or DataSource
		# if ids == None: import all objects
		
		def collect_ids(id, store, found = []):
			
			if id in found:
				return
			obj = store.objects[id]
			if obj is None:
				return
			found.append(id)
			for rel in obj.relations:
				for id2 in obj.relations[rel]:
					if id2 is None:
						continue
					if id2 in found:
						return
					collect_ids(id2, store, found)
		
		if isinstance(identifier_ds, dict):
			self.stop_broadcasts()
			store = Store()
			ds = DataSource(store)
			ds.from_dict(identifier_ds)
			store.set_datasource(ds)
		else:
			if (identifier_ds == self.identifier) and (connstr == self.connstr):
				return
			store = Store()
			ds = self.get_datasource(identifier_ds, connstr, store)
			if ds is None:
				return
			self.stop_broadcasts()
			store.set_datasource(ds)
		
		found_ids = []
		if ids is None:
			ids = store.objects.keys()
		for id in ids:
			collect_ids(id, store, found_ids)
		id_lookup = {} # {orig_id: new_id, ...}
		for id_orig in found_ids:
			id_lookup[id_orig] = self.objects.add().id
		cmax = len(found_ids)
		cnt = 1
		for id_orig in found_ids:
			print("\rImporting %d/%d            " % (cnt, cmax), end = "")
			cnt += 1
			obj_orig = store.objects[id_orig]
			obj_new = self.objects[id_lookup[id_orig]]
			for cls in obj_orig.classes:
				obj_new.classes.add(cls)
			for rel in obj_orig.relations:
				if rel.startswith("~"):
					continue
				for id2 in obj_orig.relations[rel]:
					if id2 is None:
						continue
					if id2 not in id_lookup:
						continue
					weight = obj_orig.relations[rel].weight(id2)
					obj_new.relations.add(rel, id_lookup[id2], weight)
			for descr in obj_orig.descriptors:
				label = obj_orig.descriptors[descr].label
				if label.__class__.__name__ == "DResource":
					if label.is_stored():
						label._value = as_url(label._path)
						label._path = None
				descr = obj_new.descriptors.add(descr, label)
				descr.geotag = obj_orig.descriptors[descr].geotag
		if localise:
			ids = [id_lookup[id_orig] for id_orig in id_lookup]
			self.localise_resources(True, ids)
		self.populate_descriptor_names()
		self.populate_relation_names()
		self.resume_broadcasts()
	
	def populate_descriptor_names(self):

		for class_name in self.classes:
			for id in self.classes[class_name].objects:
				for descr in self.objects[id].descriptors:
					self.classes[class_name].add_descriptor(descr)

	def populate_relation_names(self):

		for class_name1 in self.classes:
			for id1 in self.classes[class_name1].objects:
				for rel in self.objects[id1].relations:
					for id2 in self.objects[id1].relations[rel]:
						if len(self.objects[id2].classes):
							for class_name2 in self.objects[id2].classes:
								self.classes[class_name1].add_relation(rel, class_name2)
						else:
							self.classes[class_name1].add_relation(rel, "!*")
	
	def on_data_changed(self, *args):
		
		self.changed = time.time()
		self.broadcast(Broadcasts.STORE_DATA_CHANGED)

