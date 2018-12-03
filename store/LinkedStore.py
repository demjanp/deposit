from deposit.DModule import (DModule)

import os

class LinkedStore(DModule):
	
	def __init__(self, identifier, connstr = None, url = None):
		
		self.identifier = identifier
		self.prefix = os.path.split(self.identifier.strip("#"))[1]
		self.connstr = connstr
		self.url = url
		self.local_folder = None
		self.classes = [] # [name, ...]
		self.objects = {} # {local id: linked id, ...}
		self.object_lookup = {} # {linked id: local id, ...}
		self.local_resource_uris = []

		DModule.__init__(self)
	
	def merge(self):
		
		pass