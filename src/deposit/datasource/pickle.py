from deposit import __version__
from deposit.datasource.abstract_filesource import AbstractFileSource
from deposit.utils.fnc_serialize import update_local_folder
from deposit.utils.fnc_files import as_url

import pickle
import shutil

class Pickle(AbstractFileSource):
	
	EXTENSION = "pickle"
	
	def save_data(self, store, resources, path):
		
		for obj in store.G.iter_objects_data():
			obj._store = None
		for cls in store.G.iter_classes_data():
			cls._store = None
		
		self.update_progress(1, 10, text = "Saving data")
		
		path_save = path + ".part"
		with open(path_save, "wb") as f:
			pickle.dump(dict(
				object_relation_graph = store.G.objects_to_pickle(),
				class_relation_graph = store.G.classes_to_pickle(),
				class_membership_graph = store.G.members_to_pickle(),
				resources = resources,
				local_folder = store._local_folder,
				max_order = store._max_order,
				user_tools = store._user_tools,
				queries = store._queries,
				deposit_version = __version__,
			), f, pickle.HIGHEST_PROTOCOL, fix_imports = False)
		
		shutil.move(path_save, path)
		
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
	
	def data_to_store(self, data, store, path):
		
		update_local_folder(data)
		store.clear()
		store.G.objects_from_pickle(data["object_relation_graph"])
		store.G.classes_from_pickle(data["class_relation_graph"])
		store.G.members_from_pickle(data["class_membership_graph"])
		store._resources = dict([(as_url(url), data["resources"][url]) for url in data["resources"] if (url and data["resources"][url])])
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

