from deposit.DModule import (DModule)

from importlib import import_module
import os

class ExternalSources(DModule):
	
	def __init__(self, store):
		
		self.store = store
		self._classes = {} # {name: ExternalSource, ...}

		DModule.__init__(self)

		self.set_up()
	
	def set_up(self):
		
		self._classes = {}
		path_classes = os.path.join(os.path.dirname(__file__))
		for file in os.listdir(path_classes):
			if file.startswith("_") or (not file.endswith(".py")) or os.path.isdir(os.path.join(path_classes, file)):
				continue
			file = file.split(".")[0]
			self._classes[file] = getattr(import_module("deposit.store.externalsources.%s" % (file)), file)
	
	def __contains__(self, key):
		
		return key in self._classes
	
	def __getitem__(self, key):
		
		if key in self._classes:
			return self._classes[key](self.store)
		raise IndexError()
	