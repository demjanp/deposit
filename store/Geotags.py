'''
	Deposit Store - Geotags
	--------------------------
	
	Created on 10. 4. 2017
	
	@author: Peter Demjan <peter.demjan@gmail.com>
	
	accessible as store.geotags
'''

from deposit.DB import (RDF, DEP)
from deposit.DLabel import (value_to_wkt, wkt_to_wktLiteral)
from rdflib import (URIRef, Literal)
import numpy as np

class Geotags(object):
	
	def __init__(self, store):
		
		self.__store = store
	
	def __getattr__(self, key):
		
		return getattr(self.__store, key)
	
	def add(self, id_rel, value, srid = None):
		# set a geotag to a Descriptor the value of which is an image resource or geometry
		# value =  wkt or Literal or wktLiteral or [[x, y], ...]
		# srid = EPSG code (int)
		# return True if successful
		
		if self._db.add_geotag(id_rel, value, srid):
			return True
		return False
	
	def get(self, id_rel):
		# return geotag of a Relation as wktLiteral
		
		if not self._db.geotags.size:
			return None
		idx = np.where(self._db.geotags[:,0] == id_rel)[0]
		if idx.size:
			return wkt_to_wktLiteral(*value_to_wkt(self._db.geotags[idx[0],1], -1, -1))
		return None
	
	def get_uri(self, uri):
		# return all Descriptors which have the value uri specified by a geotag and their target Objects
		# return: [[geotag, id_obj, id_rel, id_cls], ...]; geotag = wktLiteral

		if not self._db.geotags.size:
			return np.array([])
		uri = str(uri)
		slice_rel = self._db.relations[(self._db.relations[:,3] == uri) & (self._db.relations[:,4] == "DResource")]
		if slice_rel.size:
			slice_tag = self._db.geotags[np.in1d(self._db.geotags[:,0], slice_rel[:,1])]
			if slice_tag.size:
				slice_rel = slice_rel[np.in1d(slice_rel[:,1], slice_tag[:,0])]
				if slice_rel.size:
					slice_tag = slice_tag[np.argsort(slice_tag[:,0])]
					slice_rel = slice_rel[np.argsort(slice_rel[:,1])]
					slice_tag = np.hstack((slice_tag[:,1].reshape((-1,1)), slice_rel[:,[2,1,0]])).astype(object) # [[geotag, id_obj, id_rel, id_cls], ...]
					for i in range(slice_tag.shape[0]):
						slice_tag[i,0] = wkt_to_wktLiteral(*value_to_wkt(slice_tag[i,0], -1, -1))
					return slice_tag
		return np.array([])
	
	def remove(self, id_rel):
		
		self._db.remove_geotag(id_rel)
	