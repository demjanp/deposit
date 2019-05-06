from deposit.store.DLabel.DLabel import (DLabel)

from deposit.store.Conversions import (as_path)
from urllib.parse import urlparse
from urllib.request import urlopen
import json
import os

class DResource(DLabel):
	# constructor attributes:
	#	value: url in str compatible type
	# public properties:
	#	value = url in string format
	#	filename = [filename].[ext]
	#	projection = wkt format
	#	worldfile = [A, D, B, E, C, F]
	# public methods:
	#	open() returns opened resource
	#	is_stored()	returns True if resource is stored locally
	#	is_image() returns True if resource is an image
	# setters:
	#	set_projection(wkt)
	#	set_worldfile([A, D, B, E, C, F])
	#	set_stored(filename, path)
	#	set_image(True/False)

	def __init__(self, value):
		
		self._filename = None
		self._path = None
		self._projection = None
		self._worldfile = None
		self._image = None
		
		super(DResource, self).__init__(str(value))
	
	@property
	def query_value(self):
		# value to use when evaluating query

		return json.dumps(self._value)

	@property
	def filename(self):

		if not self._filename is None:
			return self._filename
		filename = os.path.split(self._value)[1]
		if filename:
			return filename
		return self._value
	
	@property
	def time_modified(self):
		
		path = self._path
		if path is None:
			path = as_path(self._value)
		if not path is None:
			return os.stat(path).st_mtime
		return -1
	
	@property
	def projection(self):

		return self._projection

	def set_projection(self, wkt):

		self._projection = wkt

	@property
	def worldfile(self):

		return self._worldfile

	def set_worldfile(self, values):
		# values = [A, D, B, E, C, F]
		
		if isinstance(values, list) and (len(values) == 6):
			self._worldfile = values.copy()

	def open(self):
		
		if self._path is not None:
			return open(self._path, "rb")
		parsed = urlparse(self._value)
		if parsed.scheme == "file":
			path = os.path.normpath(parsed.path.strip("/").strip("\\"))
			if os.path.isfile(path):
				return open(path, "rb")
			return None
		if parsed.scheme in ["http", "https", "ftp", "ftps"]:
			return urlopen(self._value)
		return None

	def is_stored(self):

		return (not self._path is None)

	def set_stored(self, filename, path):

		self._filename, self._path = filename, path

	def is_image(self):

		return (self._image == True)

	def set_image(self, state):

		self._image = state

	def to_dict(self):

		return dict(
			dtype = "DResource",
			value = self._value,
			filename = self._filename,
			path = self._path,
			projection = self._projection,
			worldfile = self._worldfile,
			image = self._image,
		)

	def from_dict(self, data):

		self._value = data["value"]
		self._filename = data["filename"]
		self._path = data["path"]
		self._projection = data["projection"]
		self._worldfile = data["worldfile"]
		self._image = data["image"]
		
		return self

