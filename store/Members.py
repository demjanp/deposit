'''
	Deposit Store - Members
	--------------------------
	
	Created on 10. 4. 2017
	
	@author: Peter Demjan <peter.demjan@gmail.com>
	
	accessible as store.members
'''

from deposit.DB import (DEP)
import numpy as np

class Members(object):
	
	def __init__(self, store):
		
		self.__store = store
	
	def __getattr__(self, key):
		
		return getattr(self.__store, key)

	def _get_member_chain(self, id_cls, role, start = True):
		# recursively collect ids of all Classes which are Members of the Class specified by id_cls and their Members etc.
		# role = "children" or "parents"
		out = [id_cls]
		for id_cls2 in (self.members.get_parents if (role == "parents") else self.members.get_subclasses)(id_cls):
			out += self._get_member_chain(id_cls2, role, start = False)
		if start:
			return out[1:]
		return out
	
	def add(self, id_src, id_tgt):
		# set id_tgt to be a Member of id_src
		# return id_mem
		
		id_mem = self._db.add_member(id_src, id_tgt)
		return id_mem
	
	def is_member(self, id_tgt, cls_id):
		# return True if id_tgt is a member of cls_id
		
		if self._db.members.size:
			return ((self._db.members[:,0] == cls_id) & (self._db.members[:,2] == id_tgt)).any()
		return False
		
	
	def get(self, id_cls, subclasses = False):
		# if subclasses = True, return also Members of Subclasses
		# return Objects which are Members of Class id_cls
		# return [id_obj, ...]
		
		if not self._db.members.size:
			return np.array([])
		if subclasses:
			class_ids = np.hstack((self.members.get_all_subclasses(id_cls), [id_cls]))
			slice = self._db.members[np.in1d(self._db.members[:,0], class_ids)]
			if slice.size:
				return np.unique(slice[:,2])
		else:
			slice = self._db.members[self._db.members[:,0] == id_cls]
			if slice.size:
				return slice[:,2]
		return np.array([])
	
	def get_parents(self, id):
		# return Classes which the Node specified by id (Object or Class) is a Member of
		# return [id_cls, ...]
		
		if not self._db.members.size:
			return np.array([])
		slice = self._db.members[self._db.members[:,2] == id]
		if slice.size:
			return slice[:,0]
		return np.array([])
	
	def get_all_parents(self, id_cls):
		# recursively collect ids of all Classes of which the specified Class is a Member of and their parents etc.
		
		return np.array(self._get_member_chain(id_cls, "parents"))
	
	def get_subclasses(self, id_cls):
		# return Classes which are subclasses of Class id_cls
		# return [id_cls, ...]
		
		if not self._db.members.size:
			return np.array([])
		slice = self._db.members[self._db.members[:,0] == id_cls]
		if slice.size:
			slice = slice[slice[:,2].astype("<U3") == self._db.get_dep_class_prefix("Class")]
			if slice.size:
				return slice[:,2]
		return np.array([])
	
	def get_all_subclasses(self, id_cls):
		# recursively collect ids of all Classes which are Members of the Class specified by id_cls and their Members etc.
		
		return np.array(self._get_member_chain(id_cls, "children"))
	
	def remove(self, id_src, id_tgt):
		# remove id_tgt from Members of id_src
		
		self._db.remove_member(id_src, id_tgt)

