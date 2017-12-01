'''
	Deposit Store - Relations
	--------------------------
	
	Created on 10. 4. 2017
	
	@author: Peter Demjan <peter.demjan@gmail.com>
	
	accessible as store.relations
'''

from deposit.DLabel import (DLabel, DString, DResource, DGeometry)
from rdflib import (URIRef, Literal)
from urllib.parse import urlparse
import numpy as np
import os

class Relations(object):
	
	def __init__(self, store):
		
		self.__store = store
	
	def __getattr__(self, key):
		
		return getattr(self.__store, key)
	
	def add(self, id_src, id_tgt, label):
		# create a Relation connecting Objects id_src and id_tgt with the specified label
		# label can be a DLabel object
		# return id_rel
		
		# format label
		if not isinstance(label, Literal):
			label = Literal(str(label))
		id_rel = self._db.add_relation(id_src, id_tgt, label)
		return id_rel
	
	def add_descriptor(self, id_src, id_tgt, label, convert_geometry = False):
		# create a Relation connecting id_src (the Descriptor Class) and id_tgt (Object) with the specified label
		# label can be a DLabel object
		# if convert_geometry is True: convert strings to wktLiteral where applicable
		# if label is a locally stored image with a worldfile, set also worldfile
		# return rel_id
		
		# format label
		if not isinstance(label, DLabel):
			if isinstance(label, str) and convert_geometry and label.startswith("<http://www.opengis.net/def/crs/"):
				label = DGeometry(label)
			elif isinstance(label, URIRef):
				label = DResource(label)
			else:
				label = DString(label)
		if isinstance(label, DGeometry):
			srid_horiz, srid_vert = self.srid()
			do_set = False
			if (not srid_horiz is None) and (label.srid == -1):
				do_set = True
			else:
				srid_horiz = label.srid
			if (not srid_vert is None) and (label.srid_vertical == -1):
				do_set = True
			else:
				srid_vert = label.srid_vertical
			if do_set:
				label = DGeometry(label.label, srid_horiz, srid_vert, label.read_only, label.relation)
		rel_id = self._db.add_descriptor(id_src, id_tgt, label)
		return rel_id
	
	def get(self, id, role, label = None):
		# return all Objects connected to the Node specified by id by a Relation with the label where id is the source or target (specified by role)
		# if label is None, return all Objects connected by the Relation
		# return [[rel_id, id_obj], ...]
		
		if (not self._db.relations.size) or (not self._db.objects.size):
			return np.array([])
		if label is None:
			slice = self._db.relations[self._db.relations[:,(0 if (role == "source") else 2)] == id]
		else:
			slice = self._db.relations[(self._db.relations[:,(0 if (role == "source") else 2)] == id) & (self._db.relations[:,3] == str(label))]
		if slice.size:
			slice = slice[slice[:,2 if (role == "source") else 0].astype("<U3") == self._db.get_dep_class_prefix("Object")]
			if slice.size:
				return slice[:,[1,2 if (role == "source") else 0]]
		return np.array([])
	
	def get_labels(self):
		# return all labels used for Relations
		
		if (not self._db.relations.size) or (not self._db.objects.size):
			return np.array([])
		slice = self._db.relations[self._db.relations[:,0].astype("<U3") == self._db.get_dep_class_prefix("Object")]
		if slice.size:
			return np.unique(slice[:,3])
		return np.array([])
	
	def get_source_target(self, id_rel):
		# return id_src, id_tgt
		
		if self._db.relations.size:
			slice = self._db.relations[self._db.relations[:,1] == id_rel]
			if slice.size:
				return slice[0,[0,2]].tolist()
		return None, None
	
	def get_multi(self, obj_ids):
		# get all relations for all obj_ids
		# return [[relation label, class label, cls_id, reversed], ...]
		
		def _collect_relations(obj_ids, reversed):
			
			ret = [] # [[relation label, class label, cls_id, reversed], ...]
			rel_found = self._db.relations[np.in1d(self._db.relations[:,2 if reversed else 0], obj_ids)]
			if rel_found.size:
				rel_found = rel_found[rel_found[:,0 if reversed else 2].astype("<U3") == self._db.get_dep_class_prefix("Object")]
			if rel_found.size:
				if reversed:
					rel_found = rel_found[:,[0,3]]
				else:
					rel_found = rel_found[:,[2,3]]
				rel_found = rel_found.astype(str)
				rel_found = np.unique(np.ascontiguousarray(rel_found).view(np.dtype((np.void, rel_found.dtype.itemsize * 2)))).view(rel_found.dtype).reshape(-1, 2)
				rel_found = rel_found.astype(object)
				# rel_found = [[obj_id2, relation label], ...]
				if self._db.members.size:
					classless = np.unique(rel_found[~np.in1d(rel_found[:,0], self._db.members[:,2]), 1])
					for obj_id2, rel_label in rel_found:
						cls_ids = self._db.members[self._db.members[:,2] == obj_id2, 0]
						if cls_ids.size:
							for cls_id, cls_label in self._db.classes[np.in1d(self._db.classes[:,0], cls_ids)]:
								row = [rel_label, cls_label, cls_id, reversed]
								if not row in ret:
									ret.append(row)
				else:
					classless = rel_found
				for rel_label in classless:
					row = [rel_label, "!*", None, reversed]
					if not row in ret:
						ret.append(row)
			return ret
		
		if not self._db.relations.size:
			return np.array([])
		if isinstance(obj_ids, list):
			obj_ids = np.array(obj_ids, dtype = object)
		if not obj_ids.size:
			return np.array([])
		ret = []
		for reversed in [False, True]:
			ret += _collect_relations(obj_ids, reversed)
		return ret
	
	def remove(self, id_rel):
		
		self._db.remove_relation(id_rel)

