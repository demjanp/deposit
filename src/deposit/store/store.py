from deposit.store.dgraph import DGraph
from deposit.store.dobject import DObject
from deposit.store.dclass import DClass
from deposit.store.dresource import DResource
from deposit import datasource as Datasource
from deposit.query.query import Query

from deposit.utils.fnc_files import (
	as_url, url_to_path, extract_filename, get_image_format, delete_stored, 
	store_locally, update_image_filename, get_updated_local_url, open_url, 
	clear_temp_dir, get_named_path, get_free_subfolder, get_unique_path, 
	prune_local_files,
)
from deposit.utils.fnc_serialize import (value_to_str)
from deposit.utils.fnc_get_linked_objects import (get_linked_objects)

from collections import defaultdict
from natsort import natsorted
import shutil
import os


class Store(object):
	
	def __init__(self, keep_temp = False, *args, **kwargs):
		
		self.G = DGraph()
		
		self._datasource = Datasource.Memory()
		self._resources = {}			# {url: DResource, ...}
		self._added = set()				# set(path, ...)
		self._deleted = set()			# set((filename, path), ...)
		self._user_tools = []
		self._queries = {}
		self._local_folder = None		# folder to store DResource files flagged as is_stored
		self._keep_temp = keep_temp
		self._do_backup = True
		self._saved = True
		
		self._min_free_id = None
		self._max_order = 0
		self._descriptors = None
		self._relation_labels = None
		
		self._callbacks_paused = False
		self._callback_added = set()
		self._callback_deleted = set()
		self._callback_changed = set()
		self._callback_saved = set()
		self._callback_loaded = set()
		self._callback_local_folder_changed = set()
		self._callback_user_tools_changed = set()
		self._callback_queries_changed = set()
		self._callback_settings_changed = set()
		self._callback_error = set()
		
	def _init_min_free_id(self) -> None:
		
		if self._min_free_id is None:
			self._min_free_id = 1
			while self.G.has_object(self._min_free_id):
				self._min_free_id += 1
	
	def _check_inverse_rel(self, src, tgt, label: str) -> tuple:
		
		if label.startswith("~"):
			label = label.strip("~")
			return tgt, src, label
		
		return src, tgt, label
	
	def _on_descriptor_set(self, descr):
		
		if self._descriptors is not None:
			self._descriptors.add(descr)
	
	def _on_descriptor_deleted(self):
		
		self._descriptors = None
	
	def _on_relation_added(self, label):
		
		if self._relation_labels is not None:
			self._relation_labels.add(label)
	
	def _on_relation_deleted(self):
		
		self._relation_labels = None
	
	def _on_resource_deleted(self, resource):
		
		if not resource.object_ids:
			self.del_resource(resource)
	
	
	# ---- Callbacks
	# ------------------------------------------------------------------------
	def set_callbacks_paused(self, state):
		
		self._callbacks_paused = state
	
	def set_callback_added(self, func):
		# func(elements: list); elements = [DObject, DClass, ...]
		
		self._callback_added.add(func)
	
	def callback_added(self, elements):
		
		self._saved = False
		if self._callbacks_paused:
			return
		for func in self._callback_added:
			func(elements)
	
	def set_callback_deleted(self, func):
		# func(elements: list); elements = [obj_id, name, ...]
		
		if self._callbacks_paused:
			return
		self._callback_deleted.add(func)
	
	def callback_deleted(self, elements):
		
		self._saved = False
		if self._callbacks_paused:
			return
		for func in self._callback_deleted:
			func(elements)
	
	def set_callback_changed(self, func):
		# func(elements: list); elements = [DObject, DClass, ...]
		
		if self._callbacks_paused:
			return
		self._callback_changed.add(func)
	
	def callback_changed(self, elements):
		
		self._saved = False
		if self._callbacks_paused:
			return
		for func in self._callback_changed:
			func(elements)
	
	def set_callback_saved(self, func):
		# func(datasource)
		
		self._callback_saved.add(func)
	
	def callback_saved(self, datasource):
		
		self._saved = True
		if self._callbacks_paused:
			return
		for func in self._callback_saved:
			func(datasource)
	
	def set_callback_loaded(self, func):
		# func()
		
		self._callback_loaded.add(func)
	
	def callback_loaded(self):
		
		self._saved = True
		if self._callbacks_paused:
			return
		for func in self._callback_loaded:
			func()
	
	def set_callback_local_folder_changed(self, func):
		# func()
		
		self._callback_local_folder_changed.add(func)
	
	def callback_local_folder_changed(self):
		
		self._saved = False
		if self._callbacks_paused:
			return
		for func in self._callback_local_folder_changed:
			func()
	
	def set_callback_queries_changed(self, func):
		# func()
		
		self._callback_queries_changed.add(func)
	
	def callback_queries_changed(self):
		
		self._saved = False
		if self._callbacks_paused:
			return
		for func in self._callback_queries_changed:
			func()
	
	def set_callback_user_tools_changed(self, func):
		# func()
		
		self._callback_user_tools_changed.add(func)
	
	def callback_user_tools_changed(self):
		
		self._saved = False
		if self._callbacks_paused:
			return
		for func in self._callback_user_tools_changed:
			func()
	
	def set_callback_settings_changed(self, func):
		# func()
		
		self._callback_settings_changed.add(func)
	
	def callback_settings_changed(self):
		
		if self._callbacks_paused:
			return
		for func in self._callback_settings_changed:
			func()
	
	def set_callback_error(self, func):
		
		self._callback_error.add(func)
	
	def callback_error(self, message):
		
		print(message)
		for func in self._callback_error:
			func(message)
	
	
	# ---- General
	# ------------------------------------------------------------------------
	def clear(self) -> None:
		
		self.G.clear()
		self.flush_added_deleted()
		
		self._resources = {}
		self._user_tools = []
		self._queries = {}
		self._local_folder = None
		self._saved = False
		
		self._min_free_id = None
		self._max_order = 0
		self._descriptors = None
		self._relation_labels = None
	
	def flush_added_deleted(self):
		
		for path in self._added:
			if not os.path.isfile(path):
				continue
			filename = os.path.basename(path)
			tgt_path = os.path.join(get_named_path("_deleted", self.get_folder()), filename)
			shutil.move(path, tgt_path)
		
		for filename, path in self._deleted:
			if not os.path.isfile(path):
				continue
			filename = os.path.basename(path)
			tgt_path = get_unique_path(filename, get_free_subfolder(self.get_folder()))
			shutil.move(path, tgt_path)
		
		self._added = set()
		self._deleted = set()
	
	def get_updated_url(self, resource, store = None):
		
		if store is None:
			store = self
		if not resource.is_stored:
			return resource.url
		url_new = get_updated_local_url(resource.url, store.get_folder())
		if url_new != resource.url:
			if resource.url in self._resources:
				del self._resources[resource.url]
			if url_new is not None:
				resource.value = (url_new, resource.filename, resource.is_stored, resource.is_image)
				self._resources[url_new] = resource
		return url_new
	
	def update_resource_urls(self):
		
		for obj in self.get_objects():
			for descr in obj.get_descriptors():
				value = obj.get_descriptor(descr)
				if isinstance(value, DResource):
					if self.get_updated_url(value) is None:
						obj.del_descriptor(descr)
	
	def set_local_folder(self, path, progress = None):
		
		if path is None:
			self._local_folder = None
			self.callback_local_folder_changed()
			return
		if not os.path.isdir(path):
			os.makedirs(path, exist_ok = True)
		prev_local_folder = self._local_folder
		self._local_folder = os.path.normpath(os.path.abspath(path))
		
		cmax = len(self.get_objects())
		cnt = 1
		to_del = set()
		added_urls = set()
		for obj in self.get_objects():
			if progress is not None:
				if progress.cancel_pressed():
					self._local_folder = prev_local_folder
					for url_new in added_urls:
						del self._resources[url_new]
					progress.stop()
					return
				progress.update_state(text = "Copying Resources", value = cnt, maximum = cmax)
				cnt += 1
			for descr in obj.get_descriptors():
				resource = obj.get_descriptor(descr)
				if isinstance(resource, DResource):
					url, filename, is_stored, is_image = resource.value
					if is_stored:
						url_new = get_updated_local_url(url, self.get_folder())
						if url_new is None:
							url_new, is_stored = self.store_resource(url, filename)
						resource.value = (url_new, filename, is_stored, is_image)
						self._resources[url_new] = resource
						to_del.add(url)
						added_urls.add(url_new)
		for url in to_del:
			if url in self._resources:
				del self._resources[url]
		if progress is not None:
			progress.stop()
		
		self.callback_local_folder_changed()
	
	def has_local_folder(self):
		
		return (self._local_folder is not None)
	
	def get_folder(self):
		
		if self._local_folder is None:
			if self._datasource is None:
				return None
			return self._datasource.get_folder()
		return self._local_folder
	
	def get_resource_urls(self):
		
		return set([key for key in self._resources.keys() if key is not None])
	
	def store_resource(self, url: str, filename: str) -> tuple[str, bool]:
		# if possible, store resource locally
		#
		# returns (url, is_stored); url = new url if stored locally; is_stored = True/False
		
		folder = self.get_folder()
		if folder is None:
			return (url, False)
		
		path = store_locally(url, filename, folder, self.get_resource_urls())
		if path is None:
			return (url, False)
		self._added.add(path)
		return (as_url(path), True)
	
	def prune_resources(self):
		
		paths = set()
		for url in self._resources:
			url = get_updated_local_url(url, self.get_folder())
			if url is not None:
				paths.add(url_to_path(url))
		prune_local_files(paths, self.get_folder())
	
	def open_resource(self, resource):
		# resource = DResource
		
		url, filename, is_stored, is_image = resource.value
		if is_stored:
			url_new = get_updated_local_url(url, self.get_folder())
			if url_new is None:
				raise Exception("File %s not found" % (url))
			if url_new != url:
				resource.value = (url_new, filename, is_stored, is_image)
				url = url_new
		
		return open_url(url)
	
	
	# ---- Create
	# ------------------------------------------------------------------------
	def add_object(self) -> DObject:
		
		self._init_min_free_id()
		obj_id = self._min_free_id
		
		obj = DObject(self, obj_id)
		self.G.add_object(obj_id, obj)
		
		while self.G.has_object(self._min_free_id):
			self._min_free_id += 1
		
		self.callback_added([obj])
		
		return obj
	
	def add_class(self, name) -> DClass:
		
		if isinstance(name, DClass):
			name = name.name
		if not self.G.has_class(name):
			cls = DClass(self, name, self._max_order)
			self.G.add_class(name, cls)
			self._max_order += 1
			
			self.callback_added([cls])
		
		return self.G.get_class_data(name)
	
	def add_resource(self, 
		url: str, 
		filename: str = None, 
		is_stored: bool = None, 
		is_image: bool = None
	) -> DResource:
		# filename = "name.ext"; if None, determine automatically
		# is_stored = True if resource is stored in local folder
		#	= False, not stored locally
		#	= None, attempt to store it locally if possible & set is_stored flag
		# is_image = True if resource is an image; if None, determine automatically
		
		url = as_url(url)
		
		format = None
		if is_image is None:
			format = get_image_format(url)
			is_image = (format is not None)
		
		if filename is None:
			filename = extract_filename(url)
			if is_image:
				filename = update_image_filename(filename, format)
		
		if is_stored is None:
			is_stored = False
			if self.get_folder():
				url, is_stored = self.store_resource(url, filename)
		
		if url not in self._resources:
			self._resources[url] = DResource((url, filename, is_stored, is_image))
		
		return self._resources[url]
	
	def add_user_tool(self, user_tool):
		
		self._user_tools.append(user_tool)
		self.callback_user_tools_changed()
	
	def add_saved_query(self, title, querystr):
		
		if not (title and querystr):
			return
		self._queries[title] = querystr
		self.callback_queries_changed()

	def _is_equal(self, value1, value2):
		
		if isinstance(value1, DResource) and isinstance(value2, DResource) and value1.is_stored and value2.is_stored:
			return value1.filename == value2.filename
		return value_to_str(value1) == value_to_str(value2)
	
	def _check_related(self, obj, related_data, match_empty=True, checked_objects=None, matches=None):
		
		if not related_data:
			return 0
		
		if matches is None:
			matches = set()
		
		if checked_objects is None:
			checked_objects = set()
	
		if obj in checked_objects:
			return -1
		
		for (class_name_1, label, class_name_2, descriptor_name), expected_value in related_data.items():
			key = (class_name_1, label, class_name_2, descriptor_name)
			related_objects = [
				rel_obj for rel_obj, rel_label in obj.get_relations() if rel_label == label
			]
			found_one = False
			for rel_obj in related_objects:
				if class_name_2 in rel_obj.get_class_names():
					if descriptor_name in rel_obj.get_descriptor_names():
						found_one = True
						value = rel_obj.get_descriptor(descriptor_name)
						if not self._is_equal(value, expected_value):
							continue
						matches.add(key)
						# Check for nested related data specific to the found object
						nested_related_data = {
							k: v for k, v in related_data.items() if k[0] == class_name_2
						}
						if nested_related_data:
							if self._check_related(rel_obj, nested_related_data, match_empty, checked_objects.copy(), matches) == -1:
								return -1
			if (match_empty or found_one) and (key not in matches):
				return -1
		checked_objects.add(obj)
		return len(matches)
	
	def _check_descriptors_and_locations(self, obj, data, locations, match_empty=True):
		
		matches = set()	
		# Check descriptor values
		for descriptor_name in data:
			value = obj.get_descriptor(descriptor_name)
			if self._is_equal(value, data[descriptor_name]):
				matches.add(descriptor_name)
			
			if (not self._is_equal(value, data[descriptor_name])) and (match_empty or ((value is not None) and (data[descriptor_name] is not None))):
				return -1
			
			# Check descriptor location
			if not self._check_location(obj, descriptor_name, locations, match_empty):
				return -1
		
		return len(matches)
	
	def _check_location(self, obj, descriptor_name, locations, match_empty=True):
		# Helper function for find_object_with_descriptors
		if descriptor_name not in locations:
			return True
		location = obj.get_location(descriptor_name)
		if (location is None) and (not match_empty):
			return True
		if location == locations[descriptor_name]:
			return True
		return False
	
	def find_object_with_descriptors(self, classes, data, locations={}, related_data={}, match_empty=True):
		"""
		Finds an object that meets specified criteria within given classes, descriptors,
		locations, and related objects.

		Parameters:
		-----------
		classes : [DClass, None, ...]
			A list of class objects to search within. Use `None` to include all objects
			with any class.
		data : {descriptor_name: value, ...}
			A dictionary mapping descriptor names to their required values for the search.
		locations : {descriptor_name: location, ...}, optional
			A dictionary specifying the locations for each descriptor.
		related_data : {(class_name_1, label, class_name_2, descriptor_name): value, ...}, optional
			A dictionary defining the relationships to other objects that must be checked.
			Specifies which class, descriptor, and label are required in the related objects.
		match_empty : bool, optional
			If True, check missing descriptors, locations and relations. If False, add missing locations and descriptors

		Returns:
		--------
		object or None
			The first object that meets all specified criteria. Returns `None` if no such
			object is found.
		"""

		def _get_class_members(cls):
			if cls is None:
				return set([obj for obj in self.get_objects() if obj.get_classes()])
			return cls.get_members(direct_only=True)
		
		def _check_object(obj, data, locations, related_data, match_empty):
			matches_descr = self._check_descriptors_and_locations(obj, data, locations, match_empty)
			if matches_descr < 0:
				return 0
		
			# Check related objects
			matches_rel = self._check_related(obj, related_data, match_empty)
			if matches_rel < 0:
				return 0
			
			return matches_descr + matches_rel
		
		found = []
		if not classes:
			classes = [None]
		for obj in set.union(*[_get_class_members(cls) for cls in classes]):
			matches = _check_object(obj, data, locations, related_data, match_empty)
			if matches > 0:
				found.append((obj, matches))
		if not found:
			return None
		
		# Select match with the most matches
		obj, _ = sorted(found, key = lambda item: item[1], reverse=True)[0]
		
		return obj
	
	def add_external_descriptor(self, obj, name, value, store = None):
		# localize descriptor if it is a DResource
		
		if store is None:
			store = self
		if isinstance(value, DResource):
			is_stored = value.is_stored
			url = self.get_updated_url(value, store = store)
			if is_stored == True:
				is_stored = None
			obj.set_resource_descriptor(name, value.url, value.filename, is_stored, value.is_image)
		else:
			obj.set_descriptor(name, value)
	
	def set_object_descriptors(self, obj, data, locations = {}, match_empty=True, store = None):
		if store is None:
			store = self
		for descriptor_name in data:
			value = data[descriptor_name]
			if (not match_empty) and (value is None) and obj.has_descriptor(descriptor_name):
				continue
			self.add_external_descriptor(obj, descriptor_name, value, store = store)
			if descriptor_name in locations:
				obj.set_location(descriptor_name, locations[descriptor_name])
	
	def add_object_with_descriptors(self, cls, data, locations = {}, obj = None, store = None):
		# cls = DClass or None
		# data = {descriptor_name: value, ...}
		# locations = {descriptor_name: location, ...}
		
		if store is None:
			store = self
		if obj is None:
			obj = self.add_object()
		if cls is not None:
			cls.add_member(obj.id)
		self.set_object_descriptors(obj, data, locations=locations, match_empty=True, store=store)
		
		return obj
	
	def add_data_row(self, data, relations=set(), unique=set(), existing={}, return_added=False, match_empty=False):
		"""
		Adds objects to the store with specified classes, descriptors, and relations.
		
		Parameters:
		-----------
		data : {(Class name, Descriptor name): value, ...}
			A dictionary where the keys are tuples of (Class name, Descriptor name) and the values 
			are the corresponding descriptor values to be set for the objects.
		relations : set([(Class name 1, label, Class name 2), ...]), optional
			A set of tuples defining the relationships between classes. Each tuple specifies a 
			relationship in the form (Class name 1, Label, Class name 2).
		unique : set([Class name, ...]), optional
			A set of class names where new objects should always be added, rather than reusing 
			existing objects with identical descriptors. This ensures unique objects for these classes.
		existing : {Class name: Object, ...}, optional
			A dictionary mapping class names to existing objects that should be updated rather than 
			creating new ones. 
		match_empty : bool, optional
			If True, check missing locations and descriptors. If False, add missing locations and descriptors
		
		return_added : bool, optional
			If `True`, the function returns a tuple containing the number of added objects and a 
			dictionary mapping class names to the added objects. Otherwise, it only returns the 
			number of added objects.
		
		Returns:
		--------
		int or tuple
			Returns the number of objects added. If `return_added` is `True`, it returns a tuple 
			(n_added, added) where `n_added` is the number of objects added, and `added` is a 
			dictionary mapping class names to the added objects.
		"""
		
		collect = defaultdict(dict)
		for key in data:
			class_name, descriptor_name = key
			if (class_name is None) or (descriptor_name is None):
				continue
			cls = self.add_class(class_name)
			collect[cls][descriptor_name] = data[key]
		data = collect	# {cls: {descriptor_name: value, ...}, ...}
		
		collect = defaultdict(set)
		for class_name1, label, class_name2 in relations:
			cls1 = self.get_class(class_name1)
			cls2 = self.get_class(class_name2)
			if (cls1 is None) or (cls2 is None) or (label is None):
				continue
			if cls1 in data:
				collect[cls1].add((label, cls2))
			if cls2 in data:
				if label.startswith("~"):
					label = label[1:]
				else:
					label = "~" + label
				collect[cls2].add((label, cls1))
		for cls1 in data:
			for cls2, label in cls1.get_relations():
				if cls2 in data:
					collect[cls1].add((label, cls2))
		relations_all = collect	 # {cls1: [(label, cls2), ...], ...}
		
		relations_one_way = set()
		for cls1 in relations_all:
			for label, cls2 in relations_all[cls1]:
				if label.startswith("~"):
					continue
				if cls1 == cls2:
					continue
				relations_one_way.add((cls1, label, cls2))
		relation_tiers = []
		done = set()
		classes_done = set()
		while True:
			todo = relations_one_way.difference(done)
			if not todo:
				break
			tier_relations = set()
			tier_classes = set()
			on_right = set([row[2] for row in todo])
			for row in todo:
				if row[0] not in on_right:
					tier_classes.add(row[0])
					for row2 in relations_one_way:
						if row2[2] == row[0]:
							tier_relations.add(row2)
					done.add(row)
			if tier_classes:
				relation_tiers.append((tier_relations, tier_classes))
				classes_done.update(tier_classes)
			else:
				break
		
		for cls in data:
			if cls in classes_done:
				continue
			tier_relations = set()
			tier_classes = {cls}
			classes_done.add(cls)
			for row in relations_one_way:
				if row[2] == cls:
					tier_relations.add(row)
			relation_tiers.append((tier_relations, tier_classes))
		
		n_added = 0
		added = {}	# {cls: obj, ...}
		for i, (tier_relations, tier_classes) in enumerate(relation_tiers):
			for cls in tier_classes:
				added[cls] = None
				if cls.name in existing:
					added[cls] = self.add_object_with_descriptors(
						cls, data[cls], obj=existing[cls.name]
					)
				elif cls.name not in unique:
					related_data = {}  # {(class_name_1, label, class_name_2, descriptor_name): value, ...}
					cls_done = set()
					for cls1, label, cls2 in tier_relations:
						if cls2 != cls:
							continue
						if cls1 in data:
							for descriptor_name in data[cls1]:
								related_data[(cls2.name, "~" + label, cls1.name, descriptor_name)] = data[cls1][descriptor_name]
								cls_done.add(cls1)
					for tier_relations_prev, tier_classes_prev in relation_tiers[:i]:
						for cls1, label, cls2 in tier_relations_prev:
							if cls2 not in cls_done:
								continue
							if cls1 in data:
								for descriptor_name in data[cls1]:
									related_data[(cls2.name, "~" + label, cls1.name, descriptor_name)] = data[cls1][descriptor_name]
					added[cls] = self.find_object_with_descriptors([cls], data[cls], related_data=related_data, match_empty=match_empty)
				if added[cls] is None:
					added[cls] = self.add_object_with_descriptors(cls, data[cls])
					n_added += 1
				else:
					self.set_object_descriptors(added[cls], data[cls], match_empty=match_empty)
		
		for cls1 in relations_all:
			if cls1 not in added:
				continue
			for label, cls2 in relations_all[cls1]:
				if cls2 not in added:
					continue
				added[cls1].add_relation(added[cls2], label)
		
		if return_added:
			return n_added, dict([(cls.name, added[cls]) for cls in added])
		return n_added
	
	def import_store(self, store, unique: set=set(), match_empty: bool=False, progress=None) -> None:
		"""
		Imports objects from another store instance recursively and tiered by dependency.
		
		Parameters:
		-----------
		store : Store
			The store instance to import objects from.
		unique : set, optional
			A set of class names for which new objects should always be added rather than reusing existing ones.
		match_empty : bool, optional
			If True, check missing locations and descriptors. If False, add missing locations and descriptors
		progress : DProgress, optional
			Progress indicator.
		"""
		def _should_cancel():
			if progress and progress.cancel_pressed():
				return True
			return False
		
		def _get_related_data(obj, tier_relations, store):
			# get data from ancestors of obj where (cls2, label, cls1) is in tier_relations
			related_data = {}  # {(cls1, ~label, cls2, descriptor_name): value, ...}
			queue = {obj.id}
			done = set()
			while queue:
				orig_id = queue.pop()
				orig = store.get_object(orig_id)
				classes1 = set(orig.get_class_names())
				for orig2, label in orig.get_relations():
					if not label.startswith('~'):
						continue
					classes2 = set(orig2.get_class_names())
					if classes2.intersection(classes1):
						continue
					if orig2.id in done:
						continue
					cls_combos = set()
					for cls1 in classes1:
						for cls2 in classes2:
							if (cls2, label[1:], cls1) in tier_relations:
								cls_combos.add((cls1, cls2))
					if not cls_combos:
						continue
					for descr in orig2.get_descriptor_names():
						for cls1, cls2 in cls_combos:
							related_data[(cls1, label, cls2, descr)] = orig2.get_descriptor(descr)
					queue.add(orig2.id)
					done.add(orig2.id)
			return related_data
		
		def _get_object_data(obj):
			classes = [self.get_class(cls.name) for cls in obj.get_classes()]
			data = {descr.name: obj.get_descriptor(descr) for descr in obj.get_descriptors()}
			locations = {descr.name: obj.get_location(descr) for descr in obj.get_descriptors() if obj.get_location(descr) is not None}
			return classes, data, locations
		
		def _add_object(classes):
			obj = self.add_object()
			for cls in classes:
				self.G.add_class_child(cls.name, obj.id)
			return obj
		
		# Step 1: Import classes and descriptors
		for cls in store.get_classes(ordered=True):
			self.add_class(cls.name)
		for cls in store.get_classes():
			cls_ = self.get_class(cls.name)
			for descr in cls.get_descriptors(ordered=True):
				cls_.set_descriptor(descr.name)
			for subcls in cls.get_subclasses():
				cls_.add_subclass(subcls)
			for cls2, label in cls.get_relations():
				cls_.add_relation(cls2.name, label)
		
		# Step 2: Prepare for tiered import
		relations = set()
		for cls1 in store.get_classes():
			for cls2, label in cls1.get_object_relations(direct_only = True):
				if label.startswith("~"):
					continue
				if cls1 == cls2:
					continue
				relations.add((cls1.name, label, cls2.name))
		relation_tiers = []
		done = set()
		classes_done = set()
		while True:
			todo = relations.difference(done)
			if not todo:
				break
			tier_relations = set()
			tier_classes = set()
			on_right = set([row[2] for row in todo])
			for row in todo:
				if row[0] not in on_right:
					tier_classes.add(row[0])
					for row2 in relations:
						if row2[2] == row[0]:
							tier_relations.add(row2)
					done.add(row)
			if tier_classes:
				relation_tiers.append((tier_relations, tier_classes))
				classes_done.update(tier_classes)
			else:
				break
		
		for cls in store.get_classes():
			if cls in classes_done:
				continue
			tier_relations = set()
			tier_classes = {cls.name}
			classes_done.add(cls.name)
			for row in relations:
				if row[2] == cls:
					tier_relations.add(row)
			relation_tiers.append((tier_relations, tier_classes))
		
		# Find or add objects based on their classes, descriptors, locations and related data
		tier_relations = set()
		obj_lookup = {}
		objects_done = set()
		cnt = 0
		cmax = len(relation_tiers)
		for tier_relations_, tier_classes in relation_tiers:
			tier_relations.update(tier_relations_)
			# tier_relations = {(cls1, label, cls2), ...}
			# tier_classes = {cls, ...}
			if _should_cancel():
				return
			if progress:
				progress.update_state(text="Importing", value=cnt, maximum=cmax)
			cnt += 1
			for cls in tier_classes:
				if cls in unique:
					continue
				for obj_src in store.get_class(cls).get_members(direct_only=True):
					if obj_src.id in obj_lookup:
						continue
					related_data = _get_related_data(obj_src, tier_relations, store)  # {(cls1, ~label, cls2, descriptor_name): value, ...}
					classes, data, locations = _get_object_data(obj_src)
					obj = self.find_object_with_descriptors(classes, data, locations, related_data, match_empty=match_empty)
					if obj is None:
						obj = _add_object(classes)
					if obj.id not in objects_done:
						self.set_object_descriptors(obj, data, locations=locations, match_empty=match_empty, store=store)
						objects_done.add(obj.id)
					obj_lookup[obj_src.id] = obj
		
		# Add any remaining objects
		for obj_src in store.get_objects():
			if obj_src.id not in obj_lookup:
				classes, data, locations = _get_object_data(obj_src)
				obj = _add_object(classes)
				obj_lookup[obj_src.id] = obj
				self.set_object_descriptors(obj, data, locations=locations, match_empty=match_empty, store=store)
				objects_done.add(obj.id)
		for obj_src_id in obj_lookup:
			obj = obj_lookup[obj_src_id]
			if obj.id not in objects_done:
				classes, data, locations = _get_object_data(store.get_object(obj_src_id))
				self.set_object_descriptors(obj, data, locations=locations, match_empty=match_empty, store=store)
		
		# Add relations between objects
		for obj_src1 in store.get_objects():
			for obj_src2, label in obj_src1.get_relations():
				if label.startswith('~'):
					continue
				weight = obj_src1.get_relation_weight(obj_src2.id, label)
				obj_lookup[obj_src1.id].add_relation(obj_lookup[obj_src2.id], label, weight)
		
		if progress:
			progress.update_state(text="Importing Complete", value=cmax, maximum=cmax)
	
	
	# ---- Read
	# ------------------------------------------------------------------------
	def get_object(self, obj_id) -> DObject:
		
		if isinstance(obj_id, DObject):
			obj_id = obj_id.id
		if self.G.has_object(obj_id):
			return self.G.get_object_data(obj_id)
		return None
	
	def get_objects(self) -> set:
		# return {DObject, ...}
		
		return set(obj for obj in self.G.iter_objects_data())
	
	def get_object_ids(self) -> set:
		
		return set(self.G.iter_objects())
	
	def check_obj_id(self, obj_id) -> None:
		
		if isinstance(obj_id, DObject):
			obj_id = obj_id.id
		if not self.G.has_object(obj_id):
			raise Exception("Specified object %s does not exist." % (str(obj_id)))
	
	
	def get_class(self, name) -> DClass:
		
		if isinstance(name, DClass):
			name = name.name
		if self.G.has_class(name):
			return self.G.get_class_data(name)
		return None
	
	def get_classes(self, ordered = False) -> list:
		# return [DClass, ...]
		
		classes = []
		for cls in self.G.iter_classes_data():
			classes.append(cls)
		if ordered:
			return sorted(classes, key = lambda cls: cls.order)
		return classes
	
	def get_class_names(self, ordered = False) -> list:
		# return [name, ...]
		
		if ordered:
			return [cls.name for cls in self.get_classes(ordered = True)]
		return list(self.G.iter_classes())
	
	def has_class(self, name) -> bool:
		
		if isinstance(name, DClass):
			name = name.name
		return self.G.has_class(name)
	
	
	def get_descriptors(self, ordered = False) -> list:
		# returns [DClass, ...]
		
		if self._descriptors is None:
			self._descriptors = set()
			for obj in self.get_objects():
				for name in obj.get_descriptor_names():
					self._descriptors.add(self.G.get_class_data(name))
			for cls in self.get_classes():
				for name in cls.get_descriptor_names():
					self._descriptors.add(self.G.get_class_data(name))
		
		if ordered:
			return sorted(list(self._descriptors), key = lambda cls: cls.order)
		return list(self._descriptors)
	
	def get_descriptor_names(self, ordered = False) -> list:
		# returns [name, ...]
		
		return [cls.name for cls in self.get_descriptors(ordered)]
	
	def get_descriptor_values(self, class_name, descriptor_name, direct_only = True) -> list:
		# direct_only = if True, don't return members of subclasses
		#
		# returns [value, ...]
		
		cls = self.get_class(class_name)
		descr = self.get_class(descriptor_name)
		if (cls is None) or (descr is None):
			return []
		for obj in cls.get_members(direct_only):
			value = obj.get_descriptor(descr)
			if value is not None:
				yield value
	
	
	def get_user_tools(self):
		
		return self._user_tools.copy()
	
	
	def get_saved_query(self, title):
		
		if title in self._queries:
			return self._queries[title]
		return ""
	
	def get_saved_queries(self):
		
		return natsorted(self._queries.keys())
	
	
	def get_relation_labels(self) -> set:
		
		if self._relation_labels is None:
			self._relation_labels = set()
			for _, _, label in self.G.iter_object_relations():
				if not label.startswith("~"):
					self._relation_labels.add(label)
			for _, _, label in self.G.iter_class_relations():
				if not label.startswith("~"):
					self._relation_labels.add(label)
		
		return self._relation_labels
	
	def reverse_relation(self, label):
		
		if label.startswith("~"):
			return label[1:]
		return "~" + label
	
	def get_linked_objects(self, classes, relations, progress=None):
		# classes = [class_name, ...]
		# relations = [(class1, label, class2), ...]
		
		return get_linked_objects(self, classes, relations, progress)
	
	def get_query(self, querystr: str, **kwargs) -> object:
		
		return Query(self, querystr, **kwargs)
	
	def get_subgraph(self, objects: list, progress = None):
		# returns store which contains specified objects with their descriptors
		# and objects related to them, except objects from the same class as the
		# specified objects
		
		def _get_or_add_object(store, obj, obj_lookup):
			
			if obj.id in obj_lookup:
				return obj_lookup[obj.id]
			obj2 = store.add_object()
			obj_lookup[obj.id] = obj2
			return obj2
		
		def _get_object_data(obj):
			data = {descr.name: obj.get_descriptor(descr) for descr in obj.get_descriptors()}
			locations = {descr.name: obj.get_location(descr) for descr in obj.get_descriptors() if obj.get_location(descr) is not None}
			return data, locations
		
		store = Store(keep_temp = True)
		
		# add objects
		obj_lookup = {}	 # {orig_id: DObject in store, ...}
		classes0 = set()
		for obj in objects:
			obj_id = _get_or_add_object(store, obj, obj_lookup)
			for cls in obj.get_classes():
				classes0.add(cls.name)
		
		# add object relations
		queue = set(obj_lookup.keys())
		done = set()
		classes_all = classes0.copy()
		while queue:
			orig_id = queue.pop()
			orig = self.get_object(orig_id)
			classes1 = set(orig.get_class_names())
			for orig2, label in orig.get_relations():
				classes2 = set(orig2.get_class_names())
				if classes2.intersection(classes0 | classes1):
					continue
				classes_all.update(classes2)
				weight = orig.get_relation_weight(orig2, label)
				obj2 = _get_or_add_object(store, orig2, obj_lookup)
				if orig2.id in done:
					continue
				queue.add(orig2.id)
				done.add(orig2.id)
		
		# add relations between objects
		for orig_id_1 in obj_lookup:
			orig1 = self.get_object(orig_id_1)
			for orig2, label in orig1.get_relations():
				if label.startswith('~'):
					continue
				if orig2.id not in obj_lookup:
					continue
				weight = orig1.get_relation_weight(orig2.id, label)
				obj_lookup[orig_id_1].add_relation(obj_lookup[orig2.id], label, weight)
		
		# collect descriptor names
		for orig_id in obj_lookup:
			for descr in self.get_object(orig_id).get_descriptors():
				classes_all.add(descr.name)
		for class_name in classes_all.copy():
			for descr in self.get_class(class_name).get_descriptors():
				classes_all.add(descr.name)
		
		# add classes & members
		for cls in self.get_classes(ordered = True):
			if cls.name not in classes_all:
				continue
			cls_ = store.add_class(cls.name)
			for obj in cls.get_members():
				if obj.id not in obj_lookup:
					continue
				cls_.add_member(obj_lookup[obj.id].id)
		
		# add subclasses, descriptors & relations
		for class_name in classes_all:
			cls_orig = self.get_class(class_name)
			cls = store.get_class(class_name)
			for cls2 in cls_orig.get_subclasses():
				if cls2.name in classes_all:
					cls.add_subclass(cls2.name)
			for descr in cls_orig.get_descriptors():
				if descr.name in classes_all:
					cls.set_descriptor(descr.name)
			for cls2_orig, label in cls_orig.get_relations():
				if cls2_orig.name in classes_all:
					cls.add_relation(cls2_orig.name, label)
		
		# add descriptors & locations
		for orig_id in obj_lookup:
			orig = self.get_object(orig_id)
			data, locations = _get_object_data(orig)
			self.set_object_descriptors(obj_lookup[orig_id], data, locations=locations, match_empty=True, store=self)
			
		return store
	
	
	# ---- Update
	# ------------------------------------------------------------------------
	def switch_order(self, cls1, cls2) -> None:
		
		if isinstance(cls1, str):
			cls1 = self.get_class(cls1)
		if isinstance(cls2, str):
			cls2 = self.get_class(cls2)
		if (cls1 is None) or (cls2 is None):
			raise Exception("Invalid classes specified")
		
		cls1.order, cls2.order = cls2.order, cls1.order
		
		self.callback_changed([cls1, cls2])
	
	
	# ---- Delete
	# ------------------------------------------------------------------------
	def del_object(self, obj_id) -> None:
		
		if isinstance(obj_id, DObject):
			obj_id = obj_id.id
		if not self.G.has_object(obj_id):
			return
		obj = self.get_object(obj_id)
		if obj.has_descriptors():
			for descr in obj.get_descriptors():
				obj.del_descriptor(descr)
			self._descriptors = None
		self.G.del_object(obj_id)
		self._init_min_free_id()
		if obj_id < self._min_free_id:
			self._min_free_id = obj_id
		self.callback_deleted([obj_id])
	
	def del_class(self, name) -> None:
		
		if isinstance(name, DClass):
			name = name.name
		if not self.G.has_class(name):
			return
		# check and remove if class is descriptor for objects / classes
		descr = self.G.get_class_data(name)
		deleted = False
		for obj in self.G.iter_objects_data():
			if obj._on_class_deleted(descr):
				deleted = True
		for cls in self.G.iter_classes_data():
			if cls._on_class_deleted(descr):
				deleted = True
		if deleted:
			self._descriptors = None
		self.G.del_class(name)
		self._max_order = 0
		classes = self.get_classes()
		if classes:
			self._max_order = max([cls.order for cls in classes]) + 1
		self.callback_deleted([name])
	
	def del_resource(self, resource: DResource) -> None:
		
		if resource.is_stored:
			filename, path = delete_stored(resource.url, self.get_folder())
			if path is not None:
				self._deleted.add((filename, path))
		url = resource.url
		if url in self._resources:
			del self._resources[url]
	
	def del_user_tool(self, label):
		
		if isinstance(label, list):
			label = label[0]
		self._user_tools = [user_tool for user_tool in self._user_tools if user_tool["label"] != label]
		self.callback_user_tools_changed()
	
	def del_saved_query(self, title):
		
		if title in self._queries:
			del self._queries[title]
			self.callback_queries_changed()
	
	
	# ---- Persistence
	# ------------------------------------------------------------------------
	def init_datasource(self, format, kwargs):
		# format = Datasource or format
		
		ext_to_format = {
			".json": "JSON",
			".pickle": "Pickle",
		}
		
		if format is None:
			ext = None
			for key in ["path", "url"]:
				if kwargs.get(key, None) is not None:
					ext = os.path.splitext(kwargs[key])[-1]
					break
			if ext is not None:
				ext = ext.lower()
				if ext in ext_to_format:
					format = ext_to_format[ext]
		if format is None:
			if ("identifier" in kwargs) and ("connstr" in kwargs):
				for datasource in [Datasource.DB, Datasource.DBRel]:
					ds = datasource()
					ds.set_connstr(kwargs["connstr"])
					ds.set_identifier(kwargs["identifier"])
					if ds.is_valid():
						return ds
					ds = None
				ds = None
			
		if format is None:
			format = self._datasource
		
		if format is None:
			raise Exception("Format not specified")
		
		if isinstance(format, Datasource.AbstractDatasource):
			return format
		if not hasattr(Datasource, format):
			raise Exception("Invalid format specified: %s" % (format))
		return getattr(Datasource, format)()
	
	def get_datasource(self):
		
		return self._datasource
	
	def set_datasource(self, datasource):
		
		self._datasource = datasource
	
	def has_auto_backup(self):
		
		return self._do_backup
	
	def set_auto_backup(self, state):
		
		self._do_backup = state
		self.callback_settings_changed()
	
	def save(self, datasource = None, *args, **kwargs):
		
		if self._do_backup and (self._datasource is not None):
			folder = self._datasource.get_folder()
			if folder is None:
				folder = self.get_folder()
			folder = get_named_path("_backup", folder)
			self._datasource.backup(self, folder)
		
		# datasource = Datasource or format
		datasource = self.init_datasource(datasource, kwargs)
		if datasource.save(self, datasource = datasource, *args, **kwargs):
			self._added = set()
			self._deleted = set()
			self.callback_saved(datasource)
			return True
		return False
	
	def load(self, datasource = None, *args, **kwargs):
		# datasource = Datasource or format
		
		datasource = self.init_datasource(datasource, kwargs)
		self.set_callbacks_paused(True)
		if datasource.load(self, datasource = datasource, *args, **kwargs):
			self.set_callbacks_paused(False)
			self.callback_loaded()
			return True
		self.set_callbacks_paused(False)
		return False
	
	def is_saved(self):
		
		return self._saved
	
	def __del__(self):
		
		if self._keep_temp:
			return
		try:
			clear_temp_dir()
		except:
			pass

