from collections import OrderedDict
from importlib import import_module
import os

class CmdDict(OrderedDict):
	
	def __init__(self, *args):
		
		self.classes = {} # {name: class, ...}
		
		OrderedDict.__init__(self)
		
		self._load_classes()
	
	def _load_classes(self):
		# helper function to load classes from a folder
		# return {name: class, ...}

		self.classes = {}
		folder = self.__class__.__name__.lower()
		path_classes = os.path.join(os.path.dirname(__file__), folder)
		for file in os.listdir(path_classes):
			if file.startswith("_") or (not file.endswith(".py")) or os.path.isdir(os.path.join(path_classes, file)):
				continue
			file = file.split(".")[0]
			self.classes[file] = getattr(import_module("deposit.commander.%s.%s" % (folder, file)), file)

