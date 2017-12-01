'''
	Deposit file store
	--------------------------
	
	Created on 10. 4. 2017
	
	@author: Peter Demjan <peter.demjan@gmail.com>
	
	Initialize as File(path) where path = directory containing the files
	Files are stored in subdirectories dynamically created when the number of files in one directory reaches a limit set by set_files_per_dir()
'''

from deposit.file.Images import (Images)
from deposit.file.Shapefiles import Shapefiles
from deposit.file.XLSX import XLSX
from deposit.file.CSV import CSV
from deposit.file.OBJ import OBJ

import os
import sys
import shutil
import hashlib
import tempfile
import numpy as np
from urllib.parse import urlparse
from urllib.request import urlopen

def file_from_db(db):
	# return a File object based on db.server_url and db.identifier, or None if not possible
	
	file = None
	if db.server_url is None:
		file = File()
	else:
		scheme = urlparse(db.server_url).scheme
		if scheme == "file":
			file = File(db.server_url)
		elif scheme in ["http", "https"]:
			file = File(db.identifier.strip("#"))
	return file

class File(object):
	
	FILES_PER_DIR = 5000
	
	def __init__(self, path = None):
		
		self.images = Images(self)
		self.shapefiles = Shapefiles(self)
		self.xlsx = XLSX(self)
		self.csv = CSV(self)
		self.obj = OBJ(self)
		
		self._permanent_path = (not path is None)
		
		self._thumbnails = np.array([], dtype = object) # [[hashed_filename, path], ...]
		
		# set self._path
		parsed = urlparse(path)
		if self._permanent_path:
			if parsed.scheme == "file":
				# extract from uri
				path = parsed.path.strip("/").strip("\\")
			self._path = os.path.normpath(path)
		else:
			# make temporary
			self._path = os.path.normpath(os.path.join(tempfile.gettempdir(), "deposit"))
		if ((not path is None) and (not parsed.scheme in ["http", "https"])) and (not os.path.exists(self._path)):
			os.makedirs(self._path)
		
		self._populate_thumbnails()
	
	def _populate_thumbnails(self):
		# iterate through all thumbnails and store them in lookup array
		
		self._thumbnails = []
		thumb_path = os.path.join(self._path, "_thumbnails")
		if os.path.exists(thumb_path):
			for dirname in os.listdir(thumb_path):
				dirname = os.path.join(thumb_path, dirname)
				if os.path.isdir(dirname):
					for filename in os.listdir(dirname):
						self._thumbnails.append([filename, os.path.abspath(os.path.join(dirname, filename))])
		self._thumbnails = np.array(self._thumbnails, dtype = object)
	
	def thumbnails(self):
		# return [[hashed_filename, path], ...]
		
		return self._thumbnails
	
	def merge_thumbnails(self, connected_thumbnails):
		# merge local and remote thumbnails after connecting a database
		
		if connected_thumbnails.size:
			if self._thumbnails.size:
				self._thumbnails = np.vstack((self._thumbnails, connected_thumbnails))
			else:
				self._thumbnails = connected_thumbnails
	
	# paths
	
	def has_permanent_path(self):
		# returns True if a permanent data storage path is specified
		
		return self._permanent_path
	
	def is_valid_filename(self, filename):
		# return True if filename is valid
		
		tmp_path = os.path.join(self.get_temp_path(), filename)
		try:
			f = open(tmp_path, "w")
		except:
			return False
		f.close()
		os.remove(tmp_path)
		return True
	
	def extract_filename(self, path, default = "file"):
		# return filename extracted from path
		
		filename = os.path.split(path)[-1].strip()
		if not self.is_valid_filename(filename):
			return default
		return filename
	
	def path(self):
		
		return self._path
	
	def get_temp_path(self):
		# return temporary path
		
		tempdir = os.path.join(tempfile.gettempdir(), "deposit", "temp")
		if not os.path.exists(tempdir):
			os.makedirs(os.path.abspath(tempdir))
		return os.path.normpath(tempdir)
	
	def get_stored_path(self, filename, root = None):
		# return full path to stored file
		
		if root is None:
			root = self._path
		for dirname in os.listdir(root):
			if os.path.isdir(os.path.join(root, dirname)):
				path = os.path.join(root, dirname, filename)
				if os.path.exists(path):
					return os.path.abspath(path)
		return None
	
	def get_stored_paths(self):
		# return paths of all stored files
		# {filename: path, ...}
		
		if self._path is None:
			return {}
		ret = {}
		for dirname in os.listdir(self._path):
			dirname = os.path.join(self._path, dirname)
			if os.path.isdir(dirname):
				for filename in os.listdir(dirname):
					path = os.path.normpath(os.path.join(dirname, filename))
					ret[filename] = path
		return ret
	
	def open(self, path, filename = None, online = False):
		# open path with the system's standard application
		# if filename is specified and differs from the original, return a local copy of the resource with the specified filename
		# if online, open a local copy
		
		if online or (not filename is None):
			if filename is None:
				filename = self.extract_filename(path)
			path = self.make_temp_copy(path, filename, online)
		
		if sys.platform in ["linux", "linux2", "darwin"]:
			return # TODO
		
		elif sys.platform.startswith("win"):
			os.startfile(path)
	
	
	# storing
	
	def get_new_dir(self, root = None):
		# return a path in local file storage to store a new file
		
		def _get_dirs():
			
			dirs = []
			for dirname in os.listdir(root):
				curdir = os.path.join(root, dirname)
				if os.path.isdir(curdir):
					try:
						int(dirname)
						dirs.append([dirname, len(os.listdir(curdir))])
					except:
						pass
			return dirs
		
		def _make_dirname(n):
			
			return ("%%0%dd" % (max(4, len(str(int(self.FILES_PER_DIR)))))) % (n)
		
		if root is None:
			root = self._path
		
		dirs = _get_dirs()
		min_files = 0
		if dirs:
			dirs = sorted(dirs, key = lambda row: row[1]) # [[dir, no. of files], ...]; sorted by least files first
			min_files = dirs[0][1]
		if (not dirs) or (min_files >= self.FILES_PER_DIR):
			# make new directory
			used = [int(d[0]) for d in dirs]
			unused = sorted([d for d in range(len(dirs)) if not d in used])
			if unused:
				tgt_dir = _make_dirname(unused[0])
			elif dirs:
				tgt_dir = _make_dirname(len(dirs))
			else:
				tgt_dir = _make_dirname(0)
			try:
				os.makedirs(os.path.abspath(os.path.join(root, tgt_dir)))
			except:
				print("File.get_new_dir", sys.exc_info())
				return None
		else:
			tgt_dir = dirs[0][0]
		return os.path.abspath(os.path.join(root, tgt_dir))
	
	def make_temp_copy(self, uri, filename = None, online = False):
		# return a temporary local copy of the file specified in uri named filename
		# if filename is None: take file name from uri
		# online: specifies whether file is an online resource
		
		uri = str(uri).strip()
		
		if filename is None:
			filename = self.extract_filename(uri)
		tgt_path = os.path.abspath(os.path.join(self.get_temp_path(), filename))
		if online:
			with urlopen(uri) as f_src, open(tgt_path, "wb") as f_tgt:
				shutil.copyfileobj(f_src, f_tgt)
			f_src.close()
			f_tgt.close()
		else:
			shutil.copyfile(uri, tgt_path)
		return tgt_path
	
	def add_to_store(self, uri, filename = None, online = False):
		# add file to local store
		# filename: if specified, the new name under which to store the file
		# return [new uri, filename, path]
		
		uri = str(uri).strip()
		
		if filename is None:
			filename = self.extract_filename(uri)
		
		# if filename already exists in store, add number
		n = 0
		new_uri, ext = os.path.splitext(filename.lower())
		modified_uri = new_uri
		while self.get_stored_path(modified_uri + ext):
			n += 1
			modified_uri = "%s_%d" % (new_uri, n)
		if n:
			new_uri = modified_uri
		new_uri = new_uri + ext
		
		tgt_path = os.path.join(self.get_new_dir(), new_uri)
		if online:
			with urlopen(uri) as f_src, open(tgt_path, "wb") as f_tgt:
				shutil.copyfileobj(f_src, f_tgt)
			f_src.close()
			f_tgt.close()
		else:
			shutil.copyfile(uri, tgt_path)
		return [new_uri, filename, tgt_path]
	
	# images
	
	def find_image_format(self, uri, online = False, connected_online = False):
		
		uri = str(uri).strip()
		
		# retrieve from connected online database
		if connected_online:
			f_resp = urlopen("%s/format/%s" % os.path.split(uri))
			format = json.loads(f_resp.read().decode("utf-8"))["format"]
			f_resp.close()
			return format
		
		# try to get format from thumbnail
		if self._thumbnails.size:
			file_hash = hashlib.md5(uri.encode("utf-8")).hexdigest()
			for filename, path in self._thumbnails:
				if filename.startswith(file_hash):
					f = open(path, "rb")
					data = f.read()
					f.close()
					i = data.find(b"\xff\xfe")
					if i > -1:
						return data[i + 2:].decode("ascii")
					break
		
		# get format from online file
		if online:
			f = urlopen(uri)
			info = f.info()["Content-type"]
			f.close()
			for ext in self.images.IMAGE_EXTENSIONS:
				if info.endswith(ext):
					return ext
			return None
			
		# get format from local file
		else:
			return self.images.get_format(uri)
		
		return None
	
	def get_thumbnail(self, uri, size = 256, online = False, connected_online = False):
		# find or make thumbnail from image specified by uri
		# return path
		
		uri = str(uri).strip()
		
		# thumbnail filename
		filename = "%s_%s.jpg" % (hashlib.md5(uri.encode("utf-8")).hexdigest(), size)
		
		if self._thumbnails.size:
			slice = self._thumbnails[self._thumbnails[:,0] == filename]
			if slice.size:
				return slice[0,1]
		
		# get thumbnails dir
		root = self._path
		scheme = urlparse(root).scheme
		if scheme in ["http", "https"]:
			root = os.path.join(tempfile.gettempdir(), "deposit")
		root = os.path.join(root, "_thumbnails")
		if not os.path.exists(root):
			os.makedirs(root)
		tgt_path = os.path.join(self.get_new_dir(root), filename)
		
		# retrieve from connected online database
		if connected_online:
			src_path = "%s/thumb/%s" % os.path.split(uri)
			with urlopen(src_path) as f_src, open(tgt_path, "wb") as f_tgt:
				shutil.copyfileobj(f_src, f_tgt)
			f_src.close()
			f_tgt.close()
			return tgt_path
		
		# make local copy of online resource
		if online:
			src_path = self.make_temp_copy(uri, "thumb_temp", online = True)
		else:
			src_path = uri
		
		# generate new thumbnail
		self.images.make_thumbnail(src_path, tgt_path, size)
		if self._thumbnails.size:
			self._thumbnails = np.vstack((self._thumbnails, [[filename, tgt_path]]))
		else:
			self._thumbnails = np.array([[filename, tgt_path]], dtype = object)
		return tgt_path
	
	
	# worldfiles
	
	def find_worldfile(self, uri, online = False):
		# try to find and return path to worldfile associated with image uri
		
		uri = str(uri).strip()
		
		path, ext = os.path.splitext(uri)
		if not ext:
			return None
		ext = ext.strip(".").lower()
		path_worldfile = None
		for extw in ["%sw" % ext, "%swx" % ext, "%s%sw" % (ext[0], ext[-1]), "%s%swx" % (ext[0], ext[-1])]:
			path_worldfile = ".".join([path, extw])
			if online:
				try:
					urlopen(path_worldfile)
					break
				except:
					path_worldfile = None
			elif os.path.isfile(path_worldfile):
				break
			path_worldfile = None
		return path_worldfile
	
	def load_worldfile(self, uri, online = False):
		# load ESRI worldfile parameters from file
		# return A, D, B, E, C, F
		
		uri = str(uri).strip()
		
		if online:
			f = urlopen(uri)
		try:
			f = open(uri, "r")
		except:
			return None
		lines = f.readlines()
		f.close()
		if len(lines) == 6:
			try:
				lines = [float(line.replace(",",".")) for line in lines]
			except:
				return None
			return lines
		return None
	
	def save_worldfile(self, params, path):
		# save worldfile to path
		# params = [A, D, B, E, C, F]
		
		f = open(path, "w")
		for value in params:
			f.write("%s\n" % (str(value).replace(".",",")))
		f.close()
	
	
	# 3d
	
	def add_material_3d(self, path, path_mtl = None, path_texture = None, online = False):
		# TODO support for online store (http)
		
		if online:
			return
		if not (path_mtl or path_texture):
			return
		tgt_path, filename = os.path.split(path)
		filename = os.path.splitext(filename)[0]
		if path_mtl:
			shutil.copyfile(path_mtl, os.path.join(tgt_path, filename + ".mtl"))
		if path_texture:
			shutil.copyfile(path_texture, os.path.join(tgt_path, filename + os.path.splitext(path_texture)[1]))
		
	