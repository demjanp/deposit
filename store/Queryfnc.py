'''
	Deposit Store - Queryfnc (optimized query functions)
	--------------------------
	
	Created on 10. 4. 2017
	
	@author: Peter Demjan <peter.demjan@gmail.com>
	
	accessible as store.queryfnc
'''

from deposit.DB import (DEP)
from rdflib import (URIRef, Literal)
from deposit.DLabel import (DLabel, DString, DResource, DGeometry, DNone)
import numpy as np

class Queryfnc(object):
	
	def __init__(self, store):
		
		self.__store = store
	
	def __getattr__(self, key):
		
		return getattr(self.__store, key)
	
	def class_exists(self, label):
		# return True if a Class named label exists
		
		return (self._db.classes.shape[0] > 0) and (self._db.classes[:,1] == str(label)).any()
	
	def get_class_by_label(self, label):
		# return id of Class specified by label
		
		if self._db.classes.size:
			slice = self._db.classes[self._db.classes[:,1] == str(label)]
			if slice.size:
				return slice[0,0]
		return None
	
	def is_related(self, objects1, label, objects2, rev, neg_rel):
		# return objects filtered if Relation with the specified label exists between objects1 and objects2
		# if label is None: any Relation
		# rev: if True find reverse relations
		# neg_rel: if True find objects not connected by the specified Relation		
		
		if self._db.relations.size:
			i1, i2 = (2, 0) if rev else (0, 2)
			slice = self._db.relations[np.in1d(self._db.relations[:,i1], objects1)]
			if not slice.size:
				return np.array([])
			slice = slice[np.in1d(slice[:,i2], objects2)]
			if not slice.size:
				return np.array([])
			if label is None:
				return slice[:,[i1, i2]]
			else:
				slice = slice[slice[:,3] == str(label)]
				if neg_rel:
					slice = objects1[~np.in1d(objects1, slice[:,i1])]
					if not slice.size:
						return np.array([])
					return np.vstack((slice, slice)).T
				elif slice.size:
					return slice[:,[i1, i2]]
		return np.array([])
		
	def get_related(self, id_obj, label, classes, rev, neg_rel, neg_cls):
		# return Objects of the specified Classes connected to Object id_obj by a Relation specified by label
		# classes: [id_cls, ...]
		# if label is None: any Relation
		# if classes is None: any Class
		# rev: if True find reverse relations
		# neg_rel: if True find objects not connected by the specified Relation
		# neg_cls: if True find objects not of the specified Class
		# return [id_obj, ...] if id_obj is string, else [[id_obj1, id_obj2], ...]
		
		out = []
		if self._db.relations.size:
			if isinstance(id_obj, list) or (isinstance(id_obj, np.ndarray) and (not id_obj.dtype == str)):
				id_obj = np.array(id_obj, dtype = str)
			if classes is None:
				objects = self._db.objects.copy()
			else:
				slice = self._db.members[np.in1d(self._db.members[:,0], classes), 2]
				if not slice.size:
					return np.array([])
				if neg_cls:
					objects = self._db.objects[~np.in1d(self._db.objects, slice)]
				else:
					objects = self._db.objects[np.in1d(self._db.objects, slice)]
				if not objects.size:
					return np.array([])
			if isinstance(id_obj, str):
				slice = self.is_related(np.array([id_obj]), label, objects, rev, neg_rel) # [[id_obj, id_obj2], ...]
			else:
				if not id_obj.size:
					return np.array([])
				slice = self.is_related(id_obj, label, objects, rev, neg_rel) # [[id_obj, id_obj2], ...]
			if slice.size:
				if isinstance(id_obj, str):
					return slice[:,1].tolist()
				return slice
		if isinstance(id_obj, str):
			return []
		return np.array([])
	
	def get_related_classless(self, id_obj, label, rev, neg_rel):
		# return classless Objects connected to Object id_obj by a Relation specified by label
		# if label is None: any Relation
		# rev: if True find reverse relations
		# neg_rel: if True find objects not connected by the specified Relation
		# return [id_obj, ...]

		out = []
		if self._db.relations.size:
			if isinstance(id_obj, list) or (isinstance(id_obj, np.ndarray) and (not id_obj.dtype == str)):
				id_obj = np.array(id_obj, dtype = str)
			objects = self._db.objects[~np.in1d(self._db.objects, self._db.members[:,2])]
			if not objects.size:
				return np.array([])
			if isinstance(id_obj, str):
				slice = self.is_related(np.array([id_obj]), label, objects, rev, neg_rel) # [[id_obj, id_obj2], ...]
			else:
				if not id_obj.size:
					return np.array([])
				slice = self.is_related(id_obj, label, objects, rev, neg_rel) # [[id_obj, id_obj2], ...]
			if slice.size:
				if isinstance(id_obj, str):
					return slice[:,1].tolist()
				return slice
		if isinstance(id_obj, str):
			return []
		return np.array([])
	
	def get_related_by_label(self, id_obj1, label, id_obj2, rev):
		# return id_rel of a Relation between two Objects specified by label
		# rev: if True find reverse relations
		
		if self._db.relations.size:
			i1, i2 = (2, 0) if rev else (0, 2)
			slice = self._db.relations[(self._db.relations[:,i1] == id_obj1) & (self._db.relations[:,i2] == id_obj2) & (self._db.relations[:,3] == str(label))]
			if slice.size:
				return slice[0,1]
		return None
	
	def get_object_descriptors(self, objects, classes, neg_cls):
		# return Relations and Classes which are Descriptors to Objects where Classes belong to classes
		# objects: [id_obj, ...]
		# classes: [id_cls, ...]
		# if classes is None: any Class
		# neg_cls: if True find Classes not belonging to classes
		# return [[id_obj, id_rel, id_cls], ...]
		
		if isinstance(objects, list):
			objects = np.array(objects, dtype = object)
		if self._db.relations.size and self._db.classes.size and objects.size:
			slice = self._db.relations[np.in1d(self._db.relations[:,2], objects)]
			if slice.size:
				slice = slice[:,[2,1,0]] # [[id_obj, id_rel, id_cls], ...]
				if classes is None:
					slice = slice[slice[:,2].astype("<U3") == self._db.get_dep_class_prefix("Class")]
				elif neg_cls:
					obj_neg = slice[np.in1d(slice[:,2], classes)]
					if obj_neg.size:
						slice = slice[~np.in1d(slice[:,0], obj_neg[:,0])]
				else:
					slice = slice[np.in1d(slice[:,2], classes)]
				if slice.size:
					slice = slice.astype(str)
					return np.unique(np.ascontiguousarray(slice).view(np.dtype((np.void, slice.dtype.itemsize * 3)))).view(slice.dtype).reshape(-1, 3)
		return np.array([])
	
	def get_descriptor_by_cls(self, obj_id, cls_id):
		# return DLabel
		# TODO obsolete (unused)
		
		if self._db.relations.size:
			slice = self._db.relations[(self._db.relations[:,0] == cls_id) & (self._db.relations[:,2] == obj_id)]
			if slice.size:
				_, rel_id, _, label, dtype = slice[0]
				return globals()[dtype](label, relation = rel_id)
		return DNone()
