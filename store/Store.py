from deposit import Broadcasts
from deposit.DModule import (DModule)
from deposit.store.DElements.DObjects import (DObjects)
from deposit.store.DElements.DClasses import (DClasses)
from deposit.store.DElements.DDescriptors import (DDescriptor)
from deposit.store.DLabel.DNone import (DNone)
from deposit.store.Files import (Files)
from deposit.store.Images import (Images)
from deposit.store.Query.Query import (Query)
from deposit.store.datasources._DataSources import (DataSources)
from deposit.store.datasources._DataSource import (DataSource)
from deposit.store.externalsources._ExternalSources import (ExternalSources)
from deposit.store.Conversions import (as_url, to_unique)

from importlib import import_module
import time

class Store(DModule):

	def __init__(self, parent = None):

		self.parent = parent

		self.objects = None
		self.classes = None

		self.json = None
		
		self.datasources = DataSources(self)
		self.externalsources = ExternalSources(self)
		
		self.files = None
		self.images = None

		self.local_folder = None
		self.changed = None
		self.linked = {} # {identifier: LinkedStore(), ...}
		self._local_resource_uris = []

		self.data_source = None # DB / DBRel / JSON / RDFGraph / None

		DModule.__init__(self)

		self.objects = DObjects(self)
		self.classes = DClasses(self)
		
		self.json = self.datasources.JSON()
		
		self.files = Files(self)
		self.images = Images(self)
		
		self.DCLASS = getattr(import_module("deposit.store.DElements.DClasses"), "DClass")
		self.DCLASSES = getattr(import_module("deposit.store.DElements.DClasses"), "DClasses")
		self.DOBJECT = getattr(import_module("deposit.store.DElements.DObjects"), "DObject")
		self.DOBJECTS = getattr(import_module("deposit.store.DElements.DObjects"), "DObjects")
		self.DRELATIONS = getattr(import_module("deposit.store.DElements.DRelations"), "DRelations")
		self.DDESCRIPTORS = getattr(import_module("deposit.store.DElements.DDescriptors"), "DDescriptors")

		self.connect_broadcast(Broadcasts.ELEMENT_ADDED, self.on_data_changed)
		self.connect_broadcast(Broadcasts.ELEMENT_CHANGED, self.on_data_changed)
		self.connect_broadcast(Broadcasts.ELEMENT_DELETED, self.on_data_changed)

	@property
	def identifier(self):

		if self.data_source is None:
			return None
		return self.data_source.identifier

	def clear(self):

		self.objects = DObjects(self)
		self.classes = DClasses(self)
		self.local_folder = None
		self.changed = None
		self.linked = {}
		self._local_resource_uris = []

		self.broadcast(Broadcasts.STORE_LOADED)

	def set_datasource(self, data_source):
		
		if not ((data_source is None) or isinstance(data_source, DataSource)):
			raise Exception("Invalid data source specified:", data_source)
		self.data_source = data_source
		self.broadcast(Broadcasts.STORE_DATA_SOURCE_CHANGED)

	def set_local_folder(self, path):

		self.local_folder = path
		self.broadcast(Broadcasts.STORE_LOCAL_FOLDER_CHANGED)

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
	
	def load(self, identifier = None, connstr = None):
		# convenience function & used by MRUD
		
		if identifier:
			identifier = as_url(identifier)
		
		if not connstr is None:
			
			ds = self.datasources.DBRel()
			if ds.set_connstr(connstr) and ds.is_valid() and ds.load():
				self.set_datasource(ds)
				return True
			
			if not identifier is None:
				ds = self.datasources.DB(identifier = identifier, connstr = connstr)
				if ds.load():
					self.set_datasource(ds)
					return True
			
		elif not identifier is None:
			ds = None
			if identifier[-1] == "#":
				# TODO no extension given - find .json or .rdf file
				return True # DEBUG
			else:
				ext = identifier.split(".")[-1].lower().strip()
				if ext == "json":
					ds = self.datasources.JSON(url = identifier)
				elif ext == "rdf":
					ds = self.datasources.RDFGraph(url = identifier)
			if (not ds is None) and ds.load():
				self.set_datasource(ds)
				return True
		
		return False

	def populate_descriptor_names(self):  # TODO will be obsolete for new databases

		for class_name in self.classes:
			for id in self.classes[class_name].objects:
				for descr in self.objects[id].descriptors:
					self.classes[class_name].add_descriptor(descr)

	def populate_relation_names(self):  # TODO will be obsolete for new databases

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