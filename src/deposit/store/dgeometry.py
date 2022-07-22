from deposit.store.abstract_dtype import AbstractDType
from deposit.utils.fnc_geometry import (coords_to_wkt, wkt_to_coords)

class DGeometry(AbstractDType):
	
	@property
	def geometry_type(self):
		
		return self.get_value()[0]
	
	@property
	def coords(self):
		
		return self.get_value()[1]
	
	@property
	def srid(self):
		
		return self.get_value()[2]
	
	@property
	def srid_vertical(self):
		
		return self.get_value()[3]
	
	@property
	def wkt(self):
		
		value = AbstractDType.get_value(self)
		if isinstance(value, tuple):
			return coords_to_wkt(*value)
		return value
	
	def get_value(self):
		
		value = AbstractDType.get_value(self)
		if value is None:
			AbstractDType.set_value(self, (None, None, None, None))
		elif isinstance(value, str):
			AbstractDType.set_value(self, wkt_to_coords(value))
		return AbstractDType.get_value(self)
	
	def set_value(self, value):
		# value = DGeometry or 
		#	WKT or 
		# 	(geometry_type, coords, srid, srid_vertical) or
		#	(geometry_type, coords, srid) or
		#	(geometry_type, coords)
		
		if isinstance(value, DGeometry):
			AbstractDType.set_value(self, value.value)
			return
		
		if (value is None) or isinstance(value, str):
			AbstractDType.set_value(self, value)
			return
		
		if (not (isinstance(value, tuple) or isinstance(value, list))) or (len(value) < 2):
			raise Exception("Invalid value specified: %s" % (str(value)))
		args = [None, None, -1, -1]
		args[:len(value)] = value
		value = tuple(args)
		AbstractDType.set_value(self, value)
	
	def to_dict(self):
		
		value = AbstractDType.get_value(self)
		if isinstance(value, tuple):
			value = coords_to_wkt(*value)
		
		return dict(
			dtype = self.__class__.__name__,
			value = value,
		)
	
	def __str__(self):
		
		return "%s(%s)" % (self.__class__.__name__, self.geometry_type)
