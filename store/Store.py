from deposit import Broadcasts
from deposit.DModule import (DModule)
from deposit.store.DElements.DObjects import (DObjects)
from deposit.store.DElements.DClasses import (DClasses)
from deposit.store.DElements.DRelations import (DRelation)
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
		self.pickle = None
		
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

		self.data_source = None # DB / DBRel / JSON / Pickle / RDFGraph / None

		DModule.__init__(self)
		
		self.objects = DObjects(self)
		self.classes = DClasses(self)
		
		self.json = self.datasources.JSON()
		self.pickle = self.datasources.Pickle()
		
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
			
#			dsources = {"json": store.datasources.JSON, "rdf": store.datasources.RDF, "pickle": store.datasources.Pickle}
			dsources = {"json": store.datasources.JSON, "pickle": store.datasources.Pickle}  # TODO implement RDF
			if identifier[-1] == "#":
				for ext in dsources:
					ds = dsources[ext](url = "%s.%s" % (identifier[:-1], ext))
					if (ds is not None) and ds.load():
						return ds
			
			ds = None
			ext = identifier.split(".")[-1].lower().strip()
			if ext in dsources:
				ds = dsources[ext](url = identifier)
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
	
	def add_objects(self, identifier_ds, connstr = None, selected_ids = None, localise = False):
		# add objects from a different store, specified by identifier and connstr
		# identifier_ds = identifier or DataSource
		# if selected_ids == None: import all objects
		
		def set_data(data):
			# data = {local_folder, changed, classes, objects, events, user_tools, queries}
			
			resource_uris = []
			for id in data["objects"]:
				for name in data["objects"][id]["descriptors"]:
					if (data["objects"][id]["descriptors"][name]["label"]["dtype"] == "DResource") and (not data["objects"][id]["descriptors"][name]["label"]["path"] is None):
						if not data["objects"][id]["descriptors"][name]["label"]["value"] in resource_uris:
							resource_uris.append(data["objects"][id]["descriptors"][name]["label"]["value"])
			local_folder = self.local_folder
			self.clear()
			self.local_folder = local_folder
			self.classes.from_dict(data["classes"])
			self.objects.from_dict(data["objects"])
			self.set_local_resource_uris(resource_uris)
			self.changed = data["changed"]
			self.events.from_list(data["events"])
			self.user_tools.from_list(data["user_tools"])
			self.queries.from_dict(data["queries"])
			self.localise_resources(True)
			self.images.load_thumbnails()
		
		def add_data(data): # TODO implement
			
			resource_uris = []
			for id in data["objects"]:
				for name in data["objects"][id]["descriptors"]:
					if (data["objects"][id]["descriptors"][name]["label"]["dtype"] == "DResource") and (not data["objects"][id]["descriptors"][name]["label"]["path"] is None):
						if not data["objects"][id]["descriptors"][name]["label"]["value"] in resource_uris:
							resource_uris.append(data["objects"][id]["descriptors"][name]["label"]["value"])
			# TODO
			# add data["classes"] = {name: class data, ...}
			#	name, objects, subclasses, descriptors, relations
			# add data["objects"] = {id: object data, ...}
			# set_local_resource_uris
			# add data["user_tools"]
			# add data["queries"]
			# localise_resources(True, ids)
			self.images.load_thumbnails()
		
		def collect_ids(id, selected_ids, selected_classes, store, found):
			
			queue = set([id])
			while queue:
				print("\r%d            " % (len(queue)), end = "")
				id1 = queue.pop()
				if id1 in found:
					continue
				obj = store.objects[id1]
				if obj is None:
					return
				found.add(id1)
				for rel in obj.relations:
					if rel.startswith("~") and (id1 not in selected_ids):
						continue
					for id2 in obj.relations[rel]:
						if id2 is None:
							continue
						if id2 in found:
							continue
						if (id2 not in selected_ids) and selected_classes.intersection(store.objects[id2].classes.keys()):
							continue
						queue.add(id2)
		
		if isinstance(identifier_ds, dict):
			self.stop_broadcasts()
			if (not len(self.objects)) and (not len(self.classes)):
				set_data(identifier_ds)
				self.resume_broadcasts()
				return
			# TODO else use add_data
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
		
		if selected_ids is None:
			found_ids = set(list(store.objects.keys()))
			selected_ids = found_ids
			selected_classes = set(list(store.classes.keys()))
		
		else:
			selected_ids = set(selected_ids)
			selected_classes = set([])
			found_ids = set([])
			for id in selected_ids:
				selected_classes.update(store.objects[id].classes.keys())
			for id in selected_ids:
				collect_ids(id, selected_ids, selected_classes, store, found_ids)
		
		id_lookup = {} # {orig_id: new_id, ...}
		for id_orig in found_ids:
			id_lookup[id_orig] = self.objects.add().id
		cmax = len(found_ids)
		cnt = 1
		rel_collect = {}  # {rel: [[cls_name, ...], [cls_name, ...]], ...}
		for id_orig in found_ids:
			print("\rImporting %d/%d            " % (cnt, cmax), end = "")
			cnt += 1
			obj_orig = store.objects[id_orig]
			obj_new = self.objects[id_lookup[id_orig]]
			for cls in obj_orig.classes:
				obj_new.classes.add(cls)
			for rel in obj_orig.relations:
				if rel not in rel_collect:
					rel_collect[rel] = [set([]), set([])]
				rel_collect[rel][0].update(obj_orig.classes.keys())
				relation = obj_orig.relations[rel]
				obj_new.relations[rel] = DRelation(obj_new.relations, rel)
				for id2 in relation:
					if id2 is None:
						continue
					if id2 not in id_lookup:
						continue
					if (id2 not in selected_ids) and selected_classes.intersection(store.objects[id2].classes.keys()):
						continue
					weight = None
					if id2 in relation._weights:
						weight = relation._weights[id2]
					obj2 = store.objects[id2]
					rel_collect[rel][1].update(obj2.classes.keys())
					obj_new.relations[rel][id_lookup[id2]] = obj2
					if weight is not None:
						obj_new.relations[rel]._weights[id_lookup[id2]] = weight
			for descr in obj_orig.descriptors:
				label = obj_orig.descriptors[descr].label
				if label.__class__.__name__ == "DResource":
					if label.is_stored():
						label._value = as_url(label._path)
						label._path = None
				descr = obj_new.descriptors.add(descr, label)
				descr.geotag = obj_orig.descriptors[descr].geotag
		for rel in rel_collect:
			if rel.startswith("~"):
				continue
			classes1, classes2 = rel_collect[rel]
			if not classes1:
				continue
			else:
				for name1 in classes1:
					if not classes2:
						self.classes[name1].add_relation(rel, "!*")
					else:
						for name2 in classes2:
							self.classes[name1].add_relation(rel, name2)
		
		self.populate_descriptor_names()
		self.populate_relation_names()
		if localise:
			ids = [id_lookup[id_orig] for id_orig in id_lookup]
			self.localise_resources(True, ids)
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

