from deposit.externalsource.abstract_externalsource import AbstractExternalsource
from deposit.store.dgeometry import DGeometry
from deposit.utils.fnc_geometry import (add_srid_to_wkt, split_srid_from_wkt)
from deposit.utils.fnc_serialize import (try_numeric)

from shapefile import (Reader, Writer)
from shapely.geometry import shape as shapely_shape
from shapely import wkt as shapely_wkt

class SHP(AbstractExternalsource):
	
	def __init__(self):
		
		AbstractExternalsource.__init__(self)
		
		self._columns = {} # {column_idx: name, ...}
		self._data = [] # [{column_idx: value, ...}, ...]
	
	def sheets(self):
		
		return ["0"]
	
	def column_count(self, sheet):
		
		return len(self._columns)
	
	def row_count(self, sheet):
		
		return len(self._data)
	
	def column_name(self, sheet, column_idx):
		
		if column_idx not in self._columns:
			return None
		return self._columns[column_idx]
	
	def data(self, sheet, row_idx, column_idx):
		
		if row_idx > len(self._data) - 1:
			return None
		if column_idx not in self._data[row_idx]:
			return None
		return self._data[row_idx][column_idx]
	
	def save(self, get_header, get_item, n_rows, n_cols, path = None, url = None, *args, **kwargs):
		# get_header(col, user_role = False) = column_name or (class_name, descriptor_name) if user_role = True
		# get_item(row, col) = deposit_gui.QueryItem
		
		def abbrev_to(name, chars, columns_abbrev):
			
			if len(name) > chars:
				n = 1
				while True:
					name_new = name[:chars - len(str(n))] + str(n)
					if not name_new in columns_abbrev.values():
						return name_new
					n += 1
			return name
		
		self.set_path(path, url)
		path = self.get_path()
		if path is None:
			return False
		
		geometries = []  # [(Shapely geometry, geometry type), ...]
		row_idxs = [] # [row, ...]
		for row in range(n_rows):
			for col in range(n_cols):
				item = get_item(row, col)
				if item.is_geometry():
					wkt, srid, srid_vertical = split_srid_from_wkt(item.value.wkt)
					# TODO implement saving srid, srid_vertical
					geometries.append((shapely_wkt.loads(wkt), item.value.geometry_type))
					row_idxs.append(row)
					break
		
		if not row_idxs:
			return False
		
		column_names = self.get_header_data(get_header, n_cols)
		columns_abbrev = {} # {col: column_abbrev, ...}; abbreviated column names
		for col in range(n_cols):
			column_abbrev = column_names[col]
			if len(column_abbrev) > 10:
				class_name, descriptor_name = get_header(col, user_role = True)
				names = [name for name in [class_name, descriptor_name] if isinstance(name, str)]
				if len(names) == 2:
					column_abbrev = "_".join([abbrev_to(names[0], 4, columns_abbrev), abbrev_to(names[1], 5, columns_abbrev)])
				elif len(names) == 1:
					column_abbrev = abbrev_to(names[0], 10, columns_abbrev)
				else:
					column_abbrev = abbrev_to("no class", 10, columns_abbrev)
			column_abbrev = column_abbrev.replace(".", "_")
			columns_abbrev[col] = column_abbrev
		
		shapeType = -1
		shape_types = {
			"POINT": 1,
			"LINESTRING": 3,
			"POLYGON": 5,
			"MULTIPOINT": 8,
			"POINTZ": 11,
			"LINESTRINGZ": 13,
			"POLYGONZ": 15,
			"MULTIPOINTZ": 18,
			"POINTM": 21,
			"LINESTRINGM": 23,
			"POLYGONM": 25,
			"MULTIPOINTM": 28,
		}
		for _, geometry_type in geometries:
			geometry_type = geometry_type.upper()
			if geometry_type not in shape_types:
				raise Exception("Unknown geometry type")
			if shapeType > -1:
				if shape_types[geometry_type] != shapeType:
					raise Exception("Geometries must be of the same type")
			else:
				shapeType = shape_types[geometry_type]
		
		sf = Writer(path, shapeType = shapeType)
		types = {} # {col: type, ...}
		shp_types = {bool: "C", int: "N", float: "N", str: "C"}
		conv_order = ["N", "C"]
		data = {}
		has_data = False
		for i, row in enumerate(row_idxs):
			data[i] = {}
			for col in range(n_cols):
				item = get_item(row, col)
				if item.is_geometry():
					continue
				data[i][col] = try_numeric(item.get_display_data())
				has_data = True
				typ = type(data[i][col])
				typ = shp_types[typ] if typ in shp_types else "C"
				if (not col in types) or (
					(typ != types[col]) and \
					(conv_order.index(typ) > conv_order.index(types[col]))
				):
					types[col] = typ
		if not has_data:
			types[0] = "N"
			columns_abbrev[0] = "ID"
			for i in range(len(geometries)):
				data[i][0] = i + 1
		for col in range(n_cols):
			if col in types:
				sf.field(columns_abbrev[col], fieldType = types[col], size = "128")
		for i in range(len(geometries)):
			sf.shape(geometries[i][0].__geo_interface__)
			if types:
				sf.record(*[data[i].get(col,None) for col in range(n_cols) if col in types])
		sf.close()
		
		return True
	
	def load(self, path = None, url = None, *args, **kwargs):
		
		self.set_path(path, url)
		path = self.get_path()
		if path is None:
			return False
		
		self._columns.clear()
		self._data.clear()
		
		# get SRID
		srid = -1
		srid_vertical = -1
		# TODO try to discover SRID from .prj file
		
		# get geometries & data
		geo_column = "Geometry"
		sf = Reader(path)
		names = []
		for idx, name in enumerate(sf.fields[1:]):
			self._columns[idx + 1] = name[0]
			names.append(name[0])
		while geo_column in names:
			geo_column = geo_column + "_"
		
		geometries = [add_srid_to_wkt(shapely_shape(shape.__geo_interface__).wkt, srid, srid_vertical) for shape in sf.shapes()]
		# geometries = [wkt definition, ...] in order of records
		for i, record in enumerate(sf.records()):
			self._data.append(dict([(idx, str(record[idx - 1]).strip()) for idx in self._columns]))
			self._data[-1][0] = DGeometry((geometries[i]))
		self._columns[0] = geo_column
		
		return True

