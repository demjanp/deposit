'''
	Deposit Store - Geometry
	--------------------------
	
	Created on 10. 4. 2017
	
	@author: Peter Demjan <peter.demjan@gmail.com>
	
	accessible as store.geometry
'''

from deposit.DLabel import (value_to_wkt, wkt_to_coords, wkt_to_wktLiteral)
import numpy as np

class Geometry(object):
	
	def __init__(self, store):
		
		self.__store = store
	
	def __getattr__(self, key):
		
		return getattr(self.__store, key)
	
	def to_wkt(self, value, srid = None, srid_vertical = None):
		# convert supplied geometric value & srid to wkt, srid
		# value = wkt or Literal or wktLiteral or [[x, y], ...]
		# srid, srid_vertical = EPSG code (int)
		# return wkt, srid, srid_vertical
		
		return value_to_wkt(value, srid, srid_vertical)
	
	def to_wktLiteral(self, value, srid = None, srid_vertical = None):
		# convert supplied geometric value & srid to wktLiteral
		# value = wkt or Literal or wktLiteral or [[x, y], ...]
		# srid, srid_vertical = EPSG code (int)
		# return wktLiteral
		
		return wkt_to_wktLiteral(*value_to_wkt(value, srid, srid_vertical))
	
	def to_coords(self, value, srid = None, srid_vertical = None):
		# convert supplied geometric value & srid to a list of coordinates, geometry type and srid
		# value = wkt or Literal or wktLiteral or [[x, y], ...]
		# srid, srid_vertical = EPSG code (int)
		# return [[x, y, ...], ...], type, srid, srid_vertical; type = geometry type (POINT, POLYGON, etc.)
		
		wkt, srid, srid_vertical = value_to_wkt(value, srid, srid_vertical)
		coords, typ = wkt_to_coords(wkt)
		return np.array(coords), typ, srid, srid_vertical
	

	