from deposit.datasource.abstract_datasource import AbstractDatasource
from deposit.store.dresource import DResource

from deposit.utils.fnc_files import (as_url, url_to_path, copy_resources)
from deposit.utils.fnc_serialize import (legacy_data_to_store)

import datetime, time
import shutil
import sys
import os

class AbstractFileSource(AbstractDatasource):
	
	EXTENSION = "file"
	
	def __init__(self):
		
		AbstractDatasource.__init__(self)
		
		self._path = None
		self._progress = None
	
	def to_dict(self):
		
		data = AbstractDatasource.to_dict(self)
		data["url"] = self.get_url()
		
		return data
	
	def get_name(self):
		
		name = self.get_url()
		if name is not None:
			name = os.path.basename(name)
			if name:
				return os.path.splitext(name)[0]
		return "file"
	
	def is_valid(self):
		
		return os.path.isfile(self._path)
	
	def can_create(self):
		# return error / warning code
		
		path = self.get_path()
		if path is None:
			return False
		
		return True
	
	def get_folder(self):
		
		if self._path is not None:
			return os.path.dirname(self._path)
		return None
	
	def get_url(self):
		
		if self._path is not None:
			return as_url(self._path)
		return None
	
	def get_path(self):
		
		return self._path
	
	def set_path(self, path):
		
		self._path = os.path.normpath(os.path.abspath(path))
	
	def create(self):
		
		folder = self.get_folder()
		if folder is None:
			return False
		
		if not os.path.isdir(folder):
			try:
				os.makedirs(folder, exist_ok = True)
			except:
				return False
		
		return True
	
	def save_data(self, store, resources, path):
		# re-implement
		
		return {}
	
	def backup(self, store, folder):
		
		tgt_file, ext = os.path.splitext(os.path.split(self._path)[-1])
		tgt_file = "%s_%s" % (
			tgt_file, 
			datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d'),
		)
		n = 1
		while True:
			tgt_path = os.path.join(folder, "%s_%d%s" % (tgt_file, n, ext))
			if not os.path.isfile(tgt_path):
				break
			n += 1
		shutil.copy2(self._path, tgt_path)
	
	def save(self, store, progress = None, path = None, url = None, *args, **kwargs):
		
		self.set_progress(progress)
		
		if (path is None) and (url is not None):
			path = url_to_path(url)
		
		if path == self.get_path():
			path = None
		
		if path is not None:
			self.set_path(path)
			if not self.create():
				return False
		
		path = self.get_path()
		path, ext = os.path.splitext(path)
		if ext.lower() != ".%s" % (self.EXTENSION):
			ext = ".%s" % (self.EXTENSION)
		path = path + ext
		
		# copy all is_stored resources to new folder (if not already there)
		src_folder = store.get_folder()
		if store.has_local_folder():
			dst_folder = src_folder
		else:
			dst_folder = os.path.normpath(os.path.abspath(os.path.dirname(path)))
		
		resources = {}
		if dst_folder == src_folder:
			resources = store._resources
		
		elif store._resources:
			cmax = len(store._resources)
			cnt = 1
			self.update_progress(cnt, cmax, text = "Copying files")
			resources = copy_resources(
				store._resources, src_folder, dst_folder, progress = self._progress
			)
			if not resources:
				return False
		
		return self.save_data(store, resources, path)
	
	def load_data(self, path):
		# re-implement
		
		return {}
	
	def load(self, store, progress = None, path = None, url = None, *args, **kwargs):
		
		self.set_progress(progress)
		
		if (path is None) and (url is not None):
			path = url_to_path(url)
		
		if path == self.get_path():
			path = None
		
		if path is not None:
			self.set_path(path)
			if not self.is_valid():
				return False
		
		path = self.get_path()
		if path is None:
			store.callback_error("LOAD ERROR: Path not specified")
			return False
		
		try:
			data = self.load_data(path)
		except:
			_, exc_value, _ = sys.exc_info()
			store.callback_error("LOAD ERROR: %s" % (str(exc_value)))
			return False
		
		if "classes" in data:
			if not legacy_data_to_store(data, store, path, progress = self._progress):
				store.callback_error("LOAD ERROR: Invalid legacy file format")
				return False
		
		else:
			for name in ["object_relation_graph", "class_relation_graph", "class_membership_graph", 
				"local_folder", "max_order", "deposit_version", "user_tools", "queries",
			]:
				if name not in data:
					store.callback_error("LOAD ERROR: Invalid file format")
					return False
			
			if not self.data_to_store(data, store):
				store.callback_error("LOAD ERROR: Loading data")
				return False
		
		store.set_datasource(self)
		store.update_resource_urls()
		
		return True
	
	def data_to_store(self, data, store):
		# re-implement
		
		return False
