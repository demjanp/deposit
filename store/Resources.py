'''
	Deposit Store - Resources
	--------------------------
	
	Created on 10. 4. 2017
	
	@author: Peter Demjan <peter.demjan@gmail.com>
	
	accessible as store.resources
'''

from deposit.DLabel import (DResource)
from urllib.parse import urlparse
import os
import sys

class Resources(object):
	
	RESOURCE_STORED = 1
	RESOURCE_LOCAL = 2
	RESOURCE_ONLINE = 3
	RESOURCE_CONNECTED_LOCAL = 4
	RESOURCE_CONNECTED_ONLINE = 5
	
	def __init__(self, store):
		
		self.__store = store
	
	def __getattr__(self, key):
		
		return getattr(self.__store, key)
	
	def get_storage_type(self, uri):
		# return RESOURCE_STORED / _LOCAL / _ONLINE / _CONNECTED_LOCAL / _CONNECTED_ONLINE
		
		uri = str(uri).strip()
		parsed = urlparse(uri)
		if (parsed.scheme == "") and not (uri[0] in "\//"):
			if self._db.resources.size and (self._db.resources[:,0] == uri).any():
				return self.RESOURCE_STORED
		
		if os.path.isfile(uri) or ((parsed.scheme == "file") and os.path.isfile(os.path.normpath(parsed.path.strip("/").strip("\\")))):
			return self.RESOURCE_LOCAL
		
		connected_path = None
		for identifier in self._remote_files:
			if uri.startswith(identifier):
				connected_path = self._remote_files[identifier]
				break
		if connected_path:
			if urlparse(connected_path).scheme in ["http", "https"]:
				return self.RESOURCE_CONNECTED_ONLINE
			else:
				return self.RESOURCE_CONNECTED_LOCAL
		
		if parsed.scheme in ["http", "https", "ftp", "ftps"]:
			return self.RESOURCE_ONLINE
		
		return 0
	
	def get_path(self, uri, storage_type = None):
		# return path, filename, storage_type
		
		uri = str(uri).strip()
		if storage_type is None:
			storage_type = self.get_storage_type(uri)
		
		if storage_type == self.RESOURCE_ONLINE:
			return uri, self.file.extract_filename(uri), storage_type
		
		if storage_type == self.RESOURCE_LOCAL:
			parsed = urlparse(uri)
			if parsed.scheme == "file":
				uri = os.path.normpath(os.path.abspath(parsed.path.strip("/").strip("\\")))
			filename = os.path.split(uri)[-1]
			return uri, filename, storage_type
		
		if storage_type in [self.RESOURCE_STORED, self.RESOURCE_CONNECTED_LOCAL, self.RESOURCE_CONNECTED_ONLINE]:
			filename, path = self._db.resources[self._db.resources[:,0] == uri][0,1:]
			return path, filename, storage_type
		
		return None, None, None
	
	def get_uris(self, filename):
		# return uris of locally stored files specified by filename
		
		if self._db.resources.size:
			slice = self._db.resources[self._db.resources[:,1] == filename]
			if slice.size:
				return slice[:,0]
		return np.array([])
	
	def is_image(self, uri):
		
		return self._db.is_image(uri)
	
	def is_external_image(self, uri, storage_type = None):
		
		uri = str(uri).strip()
		if storage_type is None:
			storage_type = self.get_storage_type(uri)
		format = self.file.find_image_format(path, online = (storage_type == self.RESOURCE_ONLINE), connected_online = (storage_type == self.RESOURCE_CONNECTED_ONLINE))
		
		return not format is None
	
	def has_worldfile(self, uri, storage_type = None):
		
		uri = str(uri).strip()
		if (not storage_type is None) and (not storage_type in [self.RESOURCE_STORED, self.RESOURCE_CONNECTED_LOCAL, self.RESOURCE_CONNECTED_ONLINE]):
			return False
		return self._db.has_worldfile(uri)
	
	def is_3d(self, uri):
		
		uri = str(uri).strip()
		return uri.lower().endswith(".obj")
	
	def thumbnail(self, uri, size = 256, storage_type = None):
		# return path, filename, storage_type, thumbnail_path
		
		uri = str(uri).strip()
		if storage_type is None:
			storage_type = self.get_storage_type(uri)
		path, filename, _ = self.get_path(uri, storage_type)
		connected_online = (storage_type == self.RESOURCE_CONNECTED_ONLINE)
		return path, filename, storage_type, self.file.get_thumbnail(path, size, (storage_type == self.RESOURCE_ONLINE), (storage_type == self.RESOURCE_CONNECTED_ONLINE))
		
	def worldfile(self, uri):
		# return params [A, D, B, E, C, F], if uri has a worldfile associated
		
		uri = str(uri).strip()
		return self._db.get_worldfile(uri)
	
	def material_3d(self, uri, storage_type = None):
		# return path_material, path_texture
		
		uri = str(uri).strip()
		
		if storage_type is None:
			storage_type = self.get_storage_type(uri)
		path = self.get_path(uri, storage_type)[0]
		online = (storage_type in [self.RESOURCE_ONLINE, self.RESOURCE_CONNECTED_ONLINE])
		return self.file.obj.get_material(path, online)
	
	def add_local(self, uri, storage_type = None, orig_filename = None):
		# add resource as local
		# return new uri
		
		uri = str(uri).strip()
		if storage_type is None:
			storage_type = self.get_storage_type(uri)
		
		if not storage_type:
			return None
		
		if storage_type == self.RESOURCE_STORED:
			# no need to add new resource
			return uri
		
		online = (storage_type == self.RESOURCE_ONLINE)
		connected_online = (storage_type == self.RESOURCE_CONNECTED_ONLINE)
		
		# add to local store
		if online:
			src_path = uri
		else:
			src_path = self.get_path(uri, storage_type)[0]
		if orig_filename is None:
			orig_filename = self.file.extract_filename(src_path)
		uri, filename, tgt_path = self.file.add_to_store(src_path, self._db.get_unique_name(src_path), online = online)
		self._db.add_resource(uri, orig_filename, tgt_path)
		
		# check for worldfile
		path_worldfile = self.file.find_worldfile(src_path, online = online)
		if path_worldfile:
			params = self.file.load_worldfile(path_worldfile, online = online)
			if params:
				self._db.add_worldfile(uri, params)
		# check for material of 3d object
		elif self.is_3d(src_path):
			path_mtl, path_texture = self.file.obj.get_material(src_path)
			if path_mtl:
				self.file.add_material_3d(tgt_path, path_mtl, path_texture)
		# check if path is image
		format = self.file.find_image_format(tgt_path)
		if format:
			self._db.set_is_image(uri)
		return uri
		
	def add_remote(self, uri, storage_type = None):
		# add resource as remote
		# return uri
		
		uri = str(uri).strip()
		if storage_type is None:
			storage_type = self.get_storage_type(uri)
		
		if not storage_type:
			return None
		
		if storage_type in [self.RESOURCE_CONNECTED_LOCAL, self.RESOURCE_CONNECTED_ONLINE]:
			# no need to check resource
			return uri
		
		online = (storage_type == self.RESOURCE_ONLINE)
		
		# check if path is image
		if online:
			path = uri
		else:
			path = self.get_path(uri, storage_type)[0]
		format = self.file.find_image_format(path, online = online)
		if format:
			self._db.set_is_image(uri)
		
		return uri
		
	