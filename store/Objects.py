'''
	Deposit Store - Objects
	--------------------------
	
	Created on 10. 4. 2017
	
	@author: Peter Demjan <peter.demjan@gmail.com>
	
	accessible as store.objects
'''

from deposit.DB import (RDF, DEP)
import numpy as np

class Objects(object):
	
	def __init__(self, store):
		
		self.__store = store
	
	def __getattr__(self, key):
		
		return getattr(self.__store, key)
	
	def add(self):
		# create a new Object
		# return id_obj
		
		id_obj = self._db.add_object()
		return id_obj
	
	def get(self):
		# return ids of all Objects
		
		return self._db.objects.copy()
	
	def get_classless(self):
		# return ids of all Objects which are not Members of a Class
		
		if (not self._db.objects.size) or (not self._db.members.size):
			return self._db.objects
		return self._db.objects[~np.in1d(self._db.objects, self._db.members[:,2])]
	
	def get_descriptors(self, id_obj):
		# return all Classes which are Descriptors of the specified Object and the corresponding Relations
		# return [[id_rel, id_cls], ...]
		
		slice = self._db.relations[self._db.relations[:,2] == id_obj]
		if slice.size:
			slice = slice[:,[1,0]] # [[id_rel, id_cls], ...]
			return slice[slice[:,1].astype("<U3") == self._db.get_dep_class_prefix("Class")]
		return np.array([])
	
	def merge(self, id_obj1, id_obj2):
		# merge Objects into one (id_obj1) and return it
		# in case of conflict, keep Descriptors of id_obj1
		
		self.begin_change()
		
		# replicate Classes
		for id_cls in self.members.get_parents(id_obj2):
			self.members.add(id_cls, id_obj1)
		
		# replicate Relations
		for role in ["source", "target"]:
			for id_rel, id_obj3 in self.relations.get(id_obj2, role):
				if role == "source":
					self.relations.add(id_obj1, id_obj3, self.get_label(id_rel))
				else:
					self.relations.add(id_obj3, id_obj1, self.get_label(id_rel))
		
		# replicate Descriptors
		descriptors1 = self.objects.get_descriptors(id_obj1)
		if descriptors1.size:
			descriptors1 = descriptors1[:,1]
		descriptors1 = descriptors1.tolist()
		for id_rel, id_cls in self.objects.get_descriptors(id_obj2):
			if not id_cls in descriptors1:
				self.relations.add_descriptor(id_cls, id_obj1, self.get_label(id_rel))
		
		self.objects.remove(id_obj2)
		
		self.end_change()
		
		return id_obj1
	
	def duplicate(self, id_obj):
		# duplicate Object and return id of the new Object
		
		self.begin_change()
		
		id_obj2 = self.objects.add()
		
		# replicate Classes
		for id_cls in self.members.get_parents(id_obj):
			self.members.add(id_cls, id_obj2)
		
		# replicate Relations
		for role in ["source", "target"]:
			for id_rel, id_obj3 in self.relations.get(id_obj, role):
				if role == "source":
					self.relations.add(id_obj2, id_obj3, self.get_label(id_rel))
				else:
					self.relations.add(id_obj3, id_obj2, self.get_label(id_rel))
		
		# replicate Descriptors
		for id_rel, id_cls in self.objects.get_descriptors(id_obj):
			self.relations.add_descriptor(id_cls, id_obj2, self.get_label(id_rel))
		
		self.end_change()
		
		return id_obj2
	
	def remove(self, id_obj):
		# remove Object and all associated Edges
		
		self._db.remove_object(id_obj)
	