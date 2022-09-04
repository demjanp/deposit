from deposit import __version__
from deposit.datasource.abstract_filesource import AbstractFileSource

from deposit.utils.fnc_serialize import (GRAPH_ATTRS)

import pickle
import copy
import sys
import os

class Pickle(AbstractFileSource):
	
	EXTENSION = "pickle"
	
	def save_data(self, store, resources, path):
		
		for obj in store.G.iter_objects_data():
			obj._store = None
		for cls in store.G.iter_classes_data():
			cls._store = None
		
		self.update_progress(1, 10, text = "Saving data")
		
		with open(path, "wb") as f:
			pickle.dump(dict(
				object_relation_graph = store.G.objects_to_json(GRAPH_ATTRS),
				class_relation_graph = store.G.classes_to_json(GRAPH_ATTRS),
				class_membership_graph = store.G.members_to_json(GRAPH_ATTRS),
				resources = resources,
				local_folder = store._local_folder,
				max_order = store._max_order,
				user_tools = store._user_tools,
				queries = store._queries,
				deposit_version = __version__,
			), f, pickle.HIGHEST_PROTOCOL, fix_imports = False)
		
		for obj in store.G.iter_objects_data():
			obj._store = store
		for cls in store.G.iter_classes_data():
			cls._store = store
		
		self.update_progress(10)
		
		return True
	
	def load_data(self, path):
		
		self.update_progress(1, 10)
		with open(path, "rb") as f:
			data = pickle.load(f, fix_imports = False)
		return data
	
	def data_to_store(self, data, store):
		
		store.clear()
		'''
		store.G.objects_from_pickle(data["object_relation_graph"])
		store.G.classes_from_pickle(data["class_relation_graph"])
		store.G.members_from_pickle(data["class_membership_graph"])
		'''  # TODO obsolete (only kept to load data saved in previous format)
		store.G.objects_from_json(data["object_relation_graph"], GRAPH_ATTRS)
		store.G.classes_from_json(data["class_relation_graph"], GRAPH_ATTRS)
		store.G.members_from_json(data["class_membership_graph"], GRAPH_ATTRS)
		store._resources = data["resources"]
		store._local_folder = data["local_folder"]
		store._max_order = data["max_order"]
		store._user_tools = data["user_tools"]
		store._queries = data["queries"]
		
		for obj in store.G.iter_objects_data():
			obj._store = store
		for cls in store.G.iter_classes_data():
			cls._store = store
		
		self.update_progress(10)
		
		return True

