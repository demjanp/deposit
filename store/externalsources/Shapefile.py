from deposit.store.externalsources._ExternalSource import (ExternalSource)
from deposit.store.DLabel.DGeometry import (DGeometry)
from deposit.store.DLabel.DString import (DString)
from deposit.store.Conversions import (as_path)

from shapefile import (Reader, Writer)

class Shapefile(ExternalSource):

	def __init__(self, store, url):

		self._columns = {} # {column_idx: name, ...}
		self._data = {} # [{column_idx: value, ...}, ...]
		
		ExternalSource.__init__(self, store, url)
	
	def load(self):
		
		def _get_points(shape):
			
			points = shape.points
			if hasattr(shape, "z"):
				x, y = zip(*points)
				return list(zip(x, y, shape.z))
			return points
		
		self._columns = {}
		self._data = []
		
		path = as_path(self.url)
		if path is None:
			return False
		
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
		
		shp_type = sf.shape(0).shapeType
		shapes_wkt = { # WKT formatting for geometric shapes
			1: "POINT(%s)",
			3: "LINESTRING(%s)",
			5: "POLYGON((%s))",
			8: "MULTIPOINT(%s)",
			11: "POINTZ(%s)",
			13: "LINESTRINGZ(%s)",
			15: "POLYGONZ((%s))",
			18: "MULTIPOINTZ(%s)",
			21: "POINTM(%s)",
			23: "LINESTRINGM(%s)",
			25: "POLYGONM((%s))",
			28: "MULTIPOINTM(%s)",
		}
		if not shp_type in shapes_wkt:
			raise Exception("Unrecognized shapefile type")
		
		geometries = [shapes_wkt[shp_type] % ", ".join([" ".join([str(p) for p in point]) for point in _get_points(shape)]) for shape in sf.shapes()]
		# geometries = [wkt definition, ...] in order of records
		for i, record in enumerate(sf.records()):
			self._data.append(dict([(idx, DString(str(record[idx - 1]).strip())) for idx in self._columns]))
			self._data[-1][0] = DGeometry(geometries[i], srid = srid, srid_vertical = srid_vertical)
		self._columns[0] = geo_column
		
		return True
	
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
	
	def export_data(self, query):
		
		def get_label(item):
			
			label = item.descriptor
			if label is None:
				return None
			return label.label
		
		def abbrev_to(name, chars, columns_abbrev):
			
			if len(name) > chars:
				n = 1
				while True:
					name_new = name[:chars - len(str(n))] + str(n)
					if not name_new in columns_abbrev.values():
						return name_new
					n += 1
			return name
		
		path = as_path(self.url, check_if_exists = False)
		if path is None:
			return
		
		geometries = []  # [[coords, geometry_type], ...]
		row_idxs = [] # [row_idx, ...]
		for row_idx, row in enumerate(query):
			for column in row:
				label = get_label(row[column])
				if label.__class__.__name__ == "DGeometry":
					geometries.append(label.coords)
					row_idxs.append(row_idx)
					break
		
		if not row_idxs:
			return
		
		columns_abbrev = {} # {column: column_abbrev, ...}; abbreviated column names
		for column in query.columns:
			column_abbrev = column
			if len(column_abbrev) > 10:
				if "." in column_abbrev:
					column_abbrev = column_abbrev.split(".")
					column_abbrev = "_".join([abbrev_to(column_abbrev[0], 4, columns_abbrev), abbrev_to(column_abbrev[1], 5, columns_abbrev)])
				else:
					column_abbrev = abbrev_to(column_abbrev, 10, columns_abbrev)
			column_abbrev = column_abbrev.replace(".", "_")
			columns_abbrev[column] = column_abbrev
		
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
			if geometry_type not in shape_types:
				raise Exception("Unknown geometry type")
			if shapeType > -1:
				if shape_types[geometry_type] != shapeType:
					raise Exception("Geometries must be of the same type")
			else:
				shapeType = shape_types[geometry_type]
		
		sf = Writer(shapeType = shapeType)
		types = {} # {column: type, ...}
		shp_types = {bool: "C", int: "N", float: "N", str: "C"}
		conv_order = ["N", "C"]
		for row in query:
			for column in row:
				label = get_label(row[column])
				if label.__class__.__name__ != "DString":
					continue
				value = label.try_numeric
				typ = type(value)
				typ = shp_types[typ] if typ in shp_types else "C"
				if (not column in types) or ((typ != types[column]) and (conv_order.index(typ) > conv_order.index(types[column]))):
					types[column] = typ
		for column in types:
			sf.field(columns_abbrev[column], fieldType = types[column], size = "128")
		for i in range(len(geometries)):
			row = query[row_idxs[i]]
			coords = geometries[i][0]
			if shapeType in [1, 11, 21]: # point types
				sf.point(*coords[0], shapeType = shapeType)
			else:
				sf.poly(shapeType = shapeType, parts = [coords])
			if types:
				record = []
				for column in types:
					label = get_label(row[column])
					if label is not None:
						label = label.value
					record.append(label)
				sf.record(*record)
		sf.save(path)

