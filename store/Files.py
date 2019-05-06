from deposit.DModule import (DModule)
from deposit.store.Projections import (get_raster_projection, get_esri_prj)
from deposit.store.Worldfiles import (get_worldfile)
from deposit.store.DLabel.DResource import (DResource)
from urllib.parse import urlparse
from urllib.request import urlopen
from unidecode import unidecode
import tempfile
import shutil
import sys
import os

class Files(DModule):
	
	FILES_PER_DIR = 5000
	
	def __init__(self, store):
		
		self.store = store

		DModule.__init__(self)
	
	def get_stored_paths(self, local_folder = None):
		
		if local_folder is None:
			local_folder = self.store.local_folder
		if not local_folder:
			return {}
		stored_paths = {} # {filename: path, ...}
		for dirname in os.listdir(local_folder):
			dirname = os.path.join(local_folder, dirname)
			if os.path.isdir(dirname):
				for filename in os.listdir(dirname):
					path = os.path.normpath(os.path.join(dirname, filename))
					stored_paths[filename] = path
		return stored_paths

	def get_new_dir(self, local_folder = None):
		# return a path in local file storage to store a new file
		
		if local_folder is None:
			local_folder = self.store.local_folder
		if not local_folder:
			return None
		
		def _get_dirs():
			
			dirs = []
			for dirname in os.listdir(local_folder):
				curdir = os.path.join(local_folder, dirname)
				if os.path.isdir(curdir):
					try:
						int(dirname)
						dirs.append([dirname, len(os.listdir(curdir))])
					except:
						pass
			return dirs
		
		def _make_dirname(n):
			
			return ("%%0%dd" % (max(4, len(str(int(self.FILES_PER_DIR)))))) % (n)
		
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
			
			new_dir = os.path.abspath(os.path.join(local_folder, tgt_dir))
			if not os.path.isdir(new_dir):
				try:
					os.makedirs(new_dir)
				except:
					print("Dir not created: %s" % new_dir)
		else:
			tgt_dir = dirs[0][0]
		
		return os.path.abspath(os.path.join(local_folder, tgt_dir))
	
	def get_temp_path(self, subdir = "temp"):
		# return temporary path
		
		tempdir = os.path.normpath(os.path.abspath(os.path.join(tempfile.gettempdir(), "deposit", subdir)))
		if not os.path.isdir(tempdir):
			try:
				os.makedirs(tempdir)
			except:
				print("Dir not created: %s" % tempdir)
		return tempdir
	
	def get_deleted_path(self, name = "_deleted"):
		
		if self.store.local_folder is None:
			return self.get_temp_path(name)
		path = os.path.normpath(os.path.abspath(os.path.join(self.store.local_folder, name)))
		if not os.path.exists(path):
			os.makedirs(path)
		return path
	
	def get_backup_path(self, name = "_backup"):
		
		return self.get_deleted_path(name)
	
	def get_local_path(self, uri, local_folder = None):
		
		if local_folder is None:
			local_folder = self.store.local_folder
		if not local_folder:
			return None
		
		if not uri:
			return None
		if local_folder is None:
			return None
		for dirname in os.listdir(local_folder):
			if dirname.startswith("_") or (not dirname.isnumeric()):
				continue
			if os.path.isdir(os.path.join(local_folder, dirname)):
				path = os.path.join(local_folder, dirname, uri)
				if os.path.exists(path):
					return os.path.abspath(path)
		return None
	
	def extract_filename(self, url, default = "file"):
		# return filename extracted from path
		
		def is_valid_filename(filename):
			# return True if filename is valid
			
			tmp_path = os.path.join(self.get_temp_path("is_valid_filename"), filename)
			try:
				f = open(tmp_path, "w")
			except:
				return False
			f.close()
			os.remove(tmp_path)
			return True
		
		_, filename = os.path.split(url)
		if not filename:
			return default
		filename = unidecode(filename.strip())
		for i in range(len(filename)):
			if not (filename[i].isalnum() or (filename[i] in "._-")):
				filename = filename[:i] + "_" + filename[i+1:]
		if not is_valid_filename(filename):
			return default
		return filename
	
	def store_local(self, url):
		# store resource locally, return DResource
		
		filename = self.extract_filename(url)
		
		# get unique uri
		uri = filename
		if uri in self.store.local_resource_uris:
			uri, ext = os.path.splitext(uri)
			n = 1
			while True:
				new_uri = "%s_%d%s" % (uri, n, ext)
				if not new_uri in self.store.local_resource_uris:
					break
			uri = new_uri
			
		# get local path based on uri
		tgt_path = self.get_local_path(uri)
		if tgt_path is None:
			tgt_path = os.path.join(self.get_new_dir(), uri)
		
		# check if resource is image (by extension)
		format = self.store.images.get_format(url)
		
		def open_url(url):
			
			if os.path.isfile(url):
				return open(url, "rb")
			parsed = urlparse(url)
			if parsed.scheme == "file":
				url_path = os.path.normpath(parsed.path.strip("/").strip("\\"))
				if os.path.isfile(url_path):
					return open(url_path, "rb")
				return None
			if parsed.scheme in ["http", "https", "ftp", "ftps"]:
				try:
					return urlopen(url)
				except:
					return None
			return None
		
		# store resource locally
		f_src = open_url(url)
		if not f_src is None:
			ext = None
			if format is None:
				# check if resource is image (by examining file)
				ext = os.path.splitext(url)[1]
				if not ext:
					format = self.store.images.get_format(f_src)
					uri = "%s.%s" % (uri, format)
					tgt_path = "%s.%s" % (tgt_path, format)
					filename = "%s.%s" % (filename, format)
			
			# store resource
			f_tgt = open(tgt_path, "wb")
			shutil.copyfileobj(f_src, f_tgt)
			f_src.close()
			f_tgt.close()
		else:
			return None
		
		proj_wkt = None
		wf_params = None
		if not format is None:
			# get projection wkt of image if applicable
			proj_wkt = get_raster_projection(url)
			
			# get worldfile of image if applicable
			wf_params = get_worldfile(url)
		
		# populate & return DResource
		label = DResource(uri)
		label.set_projection(proj_wkt)
		label.set_worldfile(wf_params)
		label.set_image((not format is None))
		label.set_stored(filename, tgt_path)
		
		self.store.add_local_resource_uri(uri)
		
		return label
	
	def delete_local(self, uri):
		
		if not uri in self.store.local_resource_uris:
			return False
		
		self.store.del_local_resource_uri(uri)
		
		src_path = self.get_local_path(uri)
		if not src_path is None:
			filename = os.path.split(src_path)[1]
			tgt_path0 = os.path.join(self.get_deleted_path(), filename)
			path, filename = os.path.split(tgt_path0)
			name, ext = os.path.splitext(filename)
			tgt_path = tgt_path0
			n = 1
			while os.path.isfile(tgt_path):
				tgt_path = os.path.join(path, "%s_%d%s" % (name, n, ext))
				n += 1
			shutil.move(src_path, tgt_path)
			
			return True
		
		return False
	
	def open(self, label):
		
		filename = self.extract_filename(label.filename)
		f_src = label.open()
		if not f_src is None:
			tgt_path = os.path.join(self.store.files.get_temp_path(), filename)
			f_tgt = open(tgt_path, "wb")
			shutil.copyfileobj(f_src, f_tgt)
			f_src.close()
			f_tgt.close()
			if sys.platform in ["linux", "linux2", "darwin"]:
				return # TODO
			if sys.platform.startswith("win"):
				os.startfile(tgt_path)

