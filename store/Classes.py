'''
	Deposit Store - Classes
	--------------------------
	
	Created on 10. 4. 2017
	
	@author: Peter Demjan <peter.demjan@gmail.com>
	
	accessible as store.classes
'''

from deposit.DB import (RDF, DEP)
from rdflib import (Literal)
import numpy as np

class Classes(object):
	
	def __init__(self, store):
		
		self.__store = store
	
	def __getattr__(self, key):
		
		return getattr(self.__store, key)
	
	def add(self, label):
		# create or look up a Class specified by label
		# return id_cls
		
		if not isinstance(label, Literal):
			label = Literal(label)
		id_cls = self._db.add_class(label)
		return id_cls
	
	def get(self):
		# return ids of all Classes
		
		if self._db.classes.size:
			return self._db.classes[:,0]
		return self._db.classes
	
	def is_descriptor(self, id_cls):
		# return True if Class is a Descriptor
		
		if self._db.relations.size:
			return (self._db.relations[:,0] == id_cls).any()
		return False
	
	def get_descriptors(self, id_cls):
		# return all Classes which are Descriptors of the specified Class and its Subclasses
		
		if not (self._db.members.size and self._db.objects.size and self._db.relations.size and self._db.classes.size):
			return np.array([])
		class_ids = np.hstack((self.members.get_all_subclasses(id_cls), [id_cls]))
		slice = self._db.members[np.in1d(self._db.members[:,0], class_ids)]
		if slice.size:
			slice = slice[slice[:,2].astype("<U3") == self._db.get_dep_class_prefix("Object")]
			if slice.size:
				slice = self._db.relations[np.in1d(self._db.relations[:,2], slice[:,2])]
				if slice.size:
					slice = slice[slice[:,0].astype("<U3") == self._db.get_dep_class_prefix("Class")]
					if slice.size:
						return np.unique(slice[:,0])
		return np.array([])
	
	def set_label(self, id_cls, label):
		# update label of Class specified by id (if another class with the same label does not exist)
		# return True if succeeded
		
		if not isinstance(label, Literal):
			label = Literal(label)
		if self._db.set_class(id_cls, label):
			return True
		return False
	
	def remove(self, id_cls):
		# remove Class and all associated Edges
		
		self._db.remove_class(id_cls)
		