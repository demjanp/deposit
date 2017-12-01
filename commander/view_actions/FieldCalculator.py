'''
	Field Calculator
	--------------------------
	
	syntax:
	
	$([Descriptor]) inserts Descriptor value e.g. $(Descr 1) + 2
	ROW() inserts current row number
	POINT(x y) inserts a point e.g. POINT(10 20) or POINT($(X) $(Y))
	POLYGON(x1 y1, x2 y2, ...) inserts a polygon e.g. POLYGON($(X1) $(Y1), $(X2) $(Y2), $(X3) $(Y3), $(X1) $(Y1))
	X([Descriptor]), Y([Descriptor]) returns the X/Y coordinate of a geometric Descriptor e.g. X($(Point))
	RES(uri) inserts a Resource e.g. RES("file:///C:/path/to/file.jpg") or RES($(Uri))
	
'''

from deposit.commander.QueryLstView import QueryLstView
from deposit.DLabel import (DLabel, DString, DResource, DGeometry, DNone, try_numeric)
from deposit.file.Shapefiles import WKT_PREFIXES
from PyQt5 import (QtCore, QtWidgets)

def get_state(model, view):
	
	active = view.active()
	if isinstance(active, QueryLstView):
		selected = active.selected()
		return (len(selected) > 0) and isinstance(active, QueryLstView) and ("cls_id" in selected[0]["data"]) and (not "obj_id2" in selected[0]["data"]), False
	return False, False

def triggered(model, view, checked):
	# TODO handle multipoints and multipolygons
	# TODO handle extracting coordinates from geometry: X([Descriptor]), Y([Descriptor]) returns the X/Y coordinate of a geometric Descriptor e.g. X($(Point))
	
	active = view.active()
	selected = active.selected()
	
	names = [name for _, name in active._model.column_headers()]
	obj_ids = {} # {row: obj_id, ...}
	rows = []
	for data in selected:
		data = data["data"]
		if not data["row"] in rows:
			rows.append(data["row"])
			obj_ids[data["row"]] = data["obj_id"]
	
	sources_rel = {} # {row: {name: rel_id, ...}, ...}
	sources_quan = {} # {row: {name: value, ...}, ...}
	for row in rows:
		sources_rel[row] = {}
		sources_quan[row] = {}
		for column in range(active._model.column_count()):
			data = active._model.table_data(row, column)["data"]
			if "rel_id" in data:
				sources_rel[row][names[column]] = data["rel_id"]
			elif "value" in data:
				sources_quan[row][names[column]] = data["value"]
	
	cls_id = selected[0]["data"]["cls_id"]
	cls_label = model.store.get_label(cls_id).value
	values = view.get_values("Field Calculator", ("expr", [cls_label + " =", ""]))
	
	if values and values["expr"]:
		expr = values["expr"]
		descrs = [] # [descriptor name, ...]
		geometry = False
		resource = False
		# replace $(...) with %(...)s
		i = 0
		while (i > -1):
			i = expr.find("$(", i)
			if i > -1:
				j = i + 2
				brackets = 1
				while brackets and (j < len(expr)):
					if expr[j] == "(":
						brackets += 1
					elif expr[j] == ")":
						brackets -= 1
					j += 1
				if not brackets:
					descrs.append(expr[i + 2:j - 1])
					expr = expr[:i] + "%(" + descrs[-1] + ")s" + expr[j:]
					i = i + len(descrs[-1]) + 4
		# replace ROW() with %(.ROW)s
		expr = expr.replace("ROW()", "%(.ROW)s")
		
		# handle GEOMETRY_TYPE(wkt), e.g. POINT($(x) $(y)) or POINT($(wkt)) or POINT($(x) 123) or POLYGON($(x1) $(y1), $(x2) $(y2))
		for prefix in WKT_PREFIXES:
			if expr.startswith(prefix):
				expr = expr[len(prefix):-1]
				geometry = True
				break
		if geometry:
			# strip outside brackets for simple points, polygons and linestrings
			if expr.startswith("(") and expr.endswith(")") and (not prefix.startswith("MULTI")):
				expr = expr[1:-1]
			# multiple spaces -> single space
			prev_len = 0
			while prev_len < len(expr):
				prev_len = len(expr)
				expr = expr.replace("  ", " ")
			# get coordinates
			geometry = [] # [[expr x, expr y], ...]
			brackets = 0
			i = 0
			for j in range(len(expr)):
				if expr[j] == "(":
					brackets += 1
				elif expr[j] == ")":
					brackets -= 1
				if not brackets:
					if expr[j] == ",":
						geometry.append(expr[i:j].strip())
						i = j + 1
			geometry.append(expr[i:j + 1].strip())
			for i, element in enumerate(geometry):
				if element.startswith("("):
					brackets = 1
					j = 1
					while brackets and (j < len(element)):
						if element[j] == "(":
							brackets += 1
						elif element[j] == ")":
							brackets -= 1
						j += 1
					geometry[i] = [element[:j], element[j:].strip()]
				elif element.endswith(")"):
					j = element.find("(")
					geometry[i] = [element[:j].strip(), element[j:].strip()]
				else:
					geometry[i] = element.split(" ")
		
		# handle RES(uri), e.g. RES(file:///C:/images/img_1.png)
		elif expr.startswith("RES("):
			expr = expr.strip("")[4:-1]
			resource = True
		
		# calculate values and set descriptors
		model.store.begin_change()
		
		for row in rows:
			values = {".ROW": row} # {class name: value, ...}; class name = Descriptor or Class.Descriptor
			for name in descrs:
				if name in sources_rel[row]:
					label = model.store.get_label(sources_rel[row][name])
				elif name in sources_quan[row]:
					label = DString(sources_quan[row][name])
				else:
					label = DString("")
				value = label.value
				if isinstance(label, DString):
					value = try_numeric(value)
				if isinstance(value, str):
					value = "\"%s\"" % (value)
				values[name] = value
			
			if geometry:
				coords = []
				for coord in geometry:
					coords.append([])
					for expr_coord in coord:
						try:
							coords[-1].append(eval(expr_coord % values))
						except:
							coords = None
							break
					if coords is None:
						break
				if coords:
					coords = [(coord[0] if len(coord) == 1 else coord) for coord in coords]
					
					model.store.relations.add_descriptor(cls_id, obj_ids[row], DGeometry(coords))
			else:
				try:
					value = eval(expr % values)
				except:
					if expr.startswith("local:"):
						value = expr
					else:
						value = None
				if not value is None:
					if resource:
						if value.startswith("local:"):
							uris = model.store.resources.get_uris(value[6:])
							if uris.size:
								value = DResource(uris[0])
							else:
								value = None
						else:
							value = DResource(value)
					if not value is None:
						model.store.relations.add_descriptor(cls_id, obj_ids[row], value)
		model.store.end_change()
	
	