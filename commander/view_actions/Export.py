from deposit.DLabel import (DString, DResource, DGeometry, DNone)
from PyQt5 import (QtCore, QtWidgets)


FORMATS = {
	"xlsx": "Excel 2007+ Workbook (*.xlsx)",
	"shp": "ESRI Shapefile (*.shp)",
}

def get_state(model, view):
	
	active = view.active()
	return (not active is None) and hasattr(active, "grid_data"), False

def triggered(model, view, checked):
	
	def _has_geometry(grid):
		
		for row in grid:
			for value in row:
				if isinstance(value, DGeometry):
					return True
		return False
	
	active = view.active()
	has_selected = (len(active.selected()) > 0)
	grid = active.grid_data(selected = has_selected)
	if grid:
		if _has_geometry(grid):
			filter = ";;".join([FORMATS["xlsx"], FORMATS["shp"]])
		else:
			filter = FORMATS["xlsx"]
		path, format = QtWidgets.QFileDialog.getSaveFileName(view, caption = "Export Selected Cells As" if has_selected else "Export Query As", filter = filter)
		if path:
			for key in FORMATS:
				if FORMATS[key] == format:
					break
			format = key
			if format == "shp":
				geometries = []
				srid = -1
				fields = []
				data = [] # [{field: value, ...}, ...]; in order of geometries
				orig_fields = [field.value for field in grid[0]]
				for row in grid[1:]:
					collect_geo = []
					collect_data = {} # {field: value, ...}
					for i, item in enumerate(row):
						if isinstance(item, DGeometry):
							collect_geo.append(item)
						elif orig_fields[i] != "":
							collect_data[orig_fields[i]] = item
					if collect_geo:
						for field in collect_data:
							if not field in fields:
								fields.append(field)
					for geo in collect_geo:
						if srid == -1:
							srid = geo.srid
						geometries.append(geo.value)
						data.append({})
						for field in collect_data:
							data[-1][field] = str(collect_data[field])
				if geometries:
					fields = sorted(fields, key = lambda field: orig_fields.index(field))
					model.store.file.shapefiles.write(path, geometries, srid, fields, data)
				return
			
			if format == "xlsx":
				fields = [str(field) for field in grid[0]]
				data = [dict([(fields[i], str(grid[j + 1][i])) for i in range(len(fields)) if (fields[i] != "")]) for j in range(len(grid) - 1)]
				model.store.file.xlsx.write(path, [field for field in fields if field != ""], data)
				return
			
			