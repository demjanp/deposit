from deposit.datasource.abstract_dbsource import AbstractDBSource

from deposit.utils.fnc_files import (is_local_url, url_to_path)
from deposit.utils.fnc_serialize import (GRAPH_ATTRS)

from collections import defaultdict
import time
import json

LEGACY_RESERVED_TABLES = ["#identifier", "#changed", "#local_folder", "#geotags", "#events", "#user_tools", "#queries", "#classless", "#version", "#order"]

class DBRel(AbstractDBSource):
	
	def __init__(self):
		
		AbstractDBSource.__init__(self)
		
		self._current_identifier = None
		self._identifiers = {}  # {identifier: [tablename, ...], ...}
	
	def connect(self):
		
		self._current_identifier = None
		self._identifiers.clear()
		
		return AbstractDBSource.connect(self)
	
	def disconnect(self):
		
		self._current_identifier = None
		self._identifiers.clear()
		
		return AbstractDBSource.disconnect(self)
	
	def is_deposit_db(self):
		
		tables = self.get_tables()
		for name in [
			"identifier", "db_meta", "classes", "subclasses", "relations",
			"user_tools", "queries", "locations",
		]:
			if name not in tables:
				return False
		return True
	
	def is_legacy_db(self):
		
		tables = self.get_tables()
		for name in [
			"#identifier", "#local_folder", "#user_tools",
			"#queries", "#classless", "#version", "#order",
		]:
			if name not in tables:
				return False
		return True
	
	def get_current_identifier(self):
		
		if self._current_identifier is None:
			was_connected = self.is_connected()
			cursor = self.get_cursor()
			schema = self.get_schema()
			identifier_name = "#identifier" if self.is_legacy_db() else "identifier"
			if identifier_name in self.get_tables():
				cursor.execute("SELECT * FROM %s.\"%s\";" % (schema, identifier_name,))
				for row in cursor.fetchall():
					self._current_identifier = json.loads(row[0])
					break
			if not was_connected:
				self.disconnect()
		
		return self._current_identifier
	
	def get_current_tables(self):
		
		return self.get_tables()
	
	def get_identifiers(self):
		
		if (not self._identifiers):
			was_connected = self.is_connected()
			if not was_connected:
				self.connect()
			if self.is_deposit_db() or self.is_legacy_db():
				identifier = self.get_current_identifier()
				if identifier is not None:
					self._identifiers[identifier] = self.get_tables()
			if not was_connected:
				self.disconnect()
		return self._identifiers
	
	def is_valid(self):
		
		was_connected = self.is_connected()
		cursor = self.get_cursor()
		
		ret = (cursor is not None) and (self.is_deposit_db() or self.is_legacy_db()) and \
			(self._identifier == self.get_current_identifier())
		
		if not was_connected:
			self.disconnect()
		return ret

	def delete(self):
		
		cursor = self.get_cursor()
		if cursor is None:
			return False
		for table in self.get_tables():
			cursor.execute("DROP TABLE \"%s\" CASCADE;" % (table))
		cursor.connection.commit()
		self.disconnect()
		self.set_identifier(None)
		
		return True
	
	def load_data(self, progress = None):
		# load data from postgres db
		
		if self.is_legacy_db():
			return self.load_legacy_data(progress)
		
		was_connected = self.is_connected()
		cursor = self.get_cursor()
		tables = self.get_tables()
		schema = self.get_schema()
		
		src_ = GRAPH_ATTRS["source"]
		tgt_ = GRAPH_ATTRS["target"]
		lbl_ = GRAPH_ATTRS["key"]
		id_ = GRAPH_ATTRS["name"]
		relations_ = GRAPH_ATTRS["link"]
		
		data = dict(
			object_relation_graph = dict(
				directed = True,
				multigraph = True,
				graph = {},
				nodes = [],			# [{id_: int, data: dict()}, ...]
				# relations_ = []	# [{src_: int, tgt_: int, lbl_: str, weight: float}, ...]
			),
			# node data = {
			#	(optional) descriptors: {descr_name: value or AbstractDType.to_dict(), ...}
			#	(optional) locations: {descr_name: DGeometry.to_dict(), ...}
			# }
			class_relation_graph = dict(
				directed = True,
				multigraph = True,
				graph = {},
				nodes = [],			# [{id_: str, data: dict()}, ...]
				# relations_ = []	# [{src_: str, tgt_: str, lbl_: str}, ...]
			),
			# node data = {
			#	order: int,
			#	(optional) descriptors = [descr_name, ...]
			# }
			class_membership_graph = dict(
				directed = True,
				multigraph = False,
				graph = {},
				nodes = [],			# [{id_: int/str}, ...]
				# relations_ = []	# [{src_: int/str, tgt_: int/str}, ...]
			),
			local_folder = None,
			max_order = None,
			user_tools = [],
			queries = {},
			deposit_version = None,
		)
		data["object_relation_graph"][relations_] = []
		data["class_relation_graph"][relations_] = []
		data["class_membership_graph"][relations_] = []
		
		table = "db_meta"
		cursor.execute("SELECT * FROM %s.\"%s\";" % (schema, table,))
		rows = cursor.fetchall()
		if rows:
			data_table = {}
			for row in rows:
				data_table[row[0]] = json.loads(row[1])
			data["deposit_version"] = data_table.get("deposit_version", None)
			data["local_folder"] = data_table.get("local_folder", None)
			data["max_order"] = data_table.get("max_order", None)
		
		classless_ = None
		pg_class_lookup = {}  # {name: pg_name, ...}
		class_node_lookup = {}  # {name: index in data["class_relation_graph"]["nodes"], ...}
		table = "classes"
		cursor.execute("SELECT * FROM %s.\"%s\";" % (schema, table,))
		rows = cursor.fetchall()
		for row in rows:
			pg_name, name, order = row
			if name is None:
				classless_ = pg_name[1:]
				pg_class_lookup[None] = pg_name
			else:
				pg_class_lookup[name] = pg_name
				class_node_lookup[name] = len(data["class_relation_graph"]["nodes"])
				data["class_relation_graph"]["nodes"].append(
					{id_: name, "data": {"order": order}}
				)
				data["class_membership_graph"]["nodes"].append({id_: name})
		
		table = "subclasses"
		cursor.execute("SELECT * FROM %s.\"%s\";" % (schema, table,))
		rows = cursor.fetchall()
		for row in rows:
			name, subclass = row
			data["class_membership_graph"][relations_].append({src_: name, tgt_: subclass})
		
		pg_relation_lookup = {}  # {(source, relation, target): pg_name, ...}
		table = "relations"
		cursor.execute("SELECT * FROM %s.\"%s\";" % (schema, table,))
		rows = cursor.fetchall()
		for row in rows:
			pg_name, source, relation, target = row
			pg_relation_lookup[(source, relation, target)] = pg_name
			if (source == target) or (source == classless_) or (target == classless_):
				continue
			data["class_relation_graph"][relations_].append(
				{src_: source, tgt_: target, lbl_: relation}
			)
			data["class_relation_graph"][relations_].append(
				{src_: target, tgt_: source, lbl_: "~" + relation}
			)
		
		for key in pg_relation_lookup:
			source, relation, target = key
			cursor.execute("SELECT * FROM %s.\"%s\";" % (schema, pg_relation_lookup[key],))
			rows = cursor.fetchall()
			for row in rows:
				_, source, target, weight = row
				data_row = {src_: source, tgt_: target, lbl_: relation}
				data_row_rev = {src_: target, tgt_: source, lbl_: "~" + relation}
				if weight is not None:
					data_row[weight] = weight
					data_row_rev[weight] = weight
				data["object_relation_graph"][relations_].append(data_row)
				data["object_relation_graph"][relations_].append(data_row_rev)
		
		obj_node_lookup = {}  # {obj_id: index in data["object_relation_graph"]["nodes"], ...}
		for class_name in pg_class_lookup:
			cursor.execute("SELECT * FROM %s.\"%s\";" % (schema, pg_class_lookup[class_name],))
			descr_names = [desc[0] for desc in cursor.description][1:]
			if class_name is not None:
				data["class_relation_graph"]["nodes"][class_node_lookup[class_name]]["data"]["descriptors"] = descr_names
			rows = cursor.fetchall()
			for row in rows:  # [obj_id, descr, ...]
				obj_id = row[0]
				if class_name is not None:
					data["class_membership_graph"]["nodes"].append({id_: obj_id})
					data["class_membership_graph"][relations_].append(
						{src_: class_name, tgt_: obj_id}
					)
				data_row = {id_: obj_id, "data": {}}
				if descr_names:
					data_row["data"]["descriptors"] = {}
					for i, descr_name in enumerate(descr_names):
						if row[i+1] is not None:
							data_row["data"]["descriptors"][descr_name] = json.loads(row[i+1])
				obj_node_lookup[obj_id] = len(data["object_relation_graph"]["nodes"])
				data["object_relation_graph"]["nodes"].append(data_row)
		
		table = "locations"
		cursor.execute("SELECT * FROM %s.\"%s\";" % (schema, table,))
		rows = cursor.fetchall()
		for row in rows:
			obj_id, descr_name, location = row
			obj_data = data["object_relation_graph"]["nodes"][obj_node_lookup[obj_id]]["data"]
			if "locations" not in obj_data:
				obj_data["locations"] = {}
			obj_data["locations"][descr_name] = json.loads(location)
		
		table = "user_tools"
		cursor.execute("SELECT * FROM %s.\"%s\";" % (schema, table,))
		rows = cursor.fetchall()
		for row in rows:
			data["user_tools"].append(json.loads(row[0]))
		
		table = "queries"
		cursor.execute("SELECT * FROM %s.\"%s\";" % (schema, table,))
		rows = cursor.fetchall()
		for row in rows:
			data["queries"][row[0]] = json.loads(row[1])
		
		if not was_connected:
			self.disconnect()
		
		return data
	
	def load_legacy_data(self, progress = None):
		# load data from postgres db (old format)
		
		def load_value(stored_value):
			
			if stored_value.startswith("\u0002"):
				return dict(
					dtype = "DString",
					value = stored_value.lstrip("\u0002"),
				)
			
			if stored_value.startswith('''{"dtype": '''):
				try:
					return json.loads(stored_value)
				except:
					pass
			
			return dict(
				dtype = "DString",
				value = stored_value,
			)
		
		was_connected = self.is_connected()
		cursor = self.get_cursor()
		tables = self.get_tables()
		schema = self.get_schema()
		
		data = dict(
			classes = {},
			objects = {},
			user_tools = [],
			queries = {},
			local_folder = None,
		)
		'''
		classes[class_name] = {
			order: int,
			objects: [int, ...],
			subclasses: [str, ...],
			descriptors: [str, ...],
			relations: {label_name: [class_name, ...], ...},
		}
		objects[obj_id] = {
			descriptors: {descr_name: {label: descriptor_dict}, ...},
			relations: {label_name: {objects: [int, ...], weights: {obj_id_tgt: weight, ...}, ...}, ...}
		}
		user_tools = [dict(), ...]
		queries[title] = querystr
		'''
		
		cursor.execute("SELECT * FROM %s.\"%s\";" % (schema, "#local_folder",))
		for row in cursor.fetchall():
			local_folder = json.loads(row[0])
			if is_local_url(local_folder):
				local_folder = url_to_path(local_folder)
			data["local_folder"] = local_folder
			break
		
		# load classes
		for table in tables:
			if not table.startswith("#"):
				data["classes"][table] = dict(
					order = None,
					objects = set(),
					subclasses = [],
					descriptors = [],
					relations = defaultdict(list),
				)
		
		# load objects and their classes & descriptors
		descriptor_names = set()
		for table in tables:
			if (not table.startswith("#")) or (table == "#classless"):
				cursor.execute("SELECT * FROM %s.\"%s\";" % (schema, table,))
				descr_names = [desc[0] for desc in cursor.description][1:]
				if table != "#classless":
					for name in descr_names:
						descriptor_names.add(name)
						if name not in data["classes"][table]["descriptors"]:
							data["classes"][table]["descriptors"].append(name)
				rows = cursor.fetchall()
				for row in rows:
					obj_id = row[0]
					if table != "#classless":
						data["classes"][table]["objects"].add(obj_id)
					data["objects"][obj_id] = dict(
						descriptors = {},
						relations = {},
					)
					for i in range(len(descr_names)):
						data["objects"][obj_id]["descriptors"][descr_names[i]] = {"label": load_value(row[i+1])}
		for table in data["classes"]:
			data["classes"][table]["objects"] = list(data["classes"][table]["objects"])
		for name in descriptor_names:
			if name in data["classes"]:
				continue
			data["classes"][name] = dict(
				order = None,
				objects = [],
				subclasses = [],
				descriptors = [],
				relations = [],
			)
		
		# load relations
		for table in tables:
			if table.startswith("#") and (table not in LEGACY_RESERVED_TABLES):
				if table.startswith("##classless#"):
					if table.endswith("##classless"): #  ##classless#rel##classless
						rel = table[12:].split("#")[0]
					else: #  ##classless#rel#cls
						rel, cls2 = table[12:].split("#")
				elif table.endswith("##classless"): #  #cls1#rel##classless
					_, cls1, rel = table[:-11].split("#")
					pass # don't keep class relations to classless
				else: #  #cls1#rel#cls2
					_, cls1, rel, cls2 = table.split("#")
					if cls2 not in data["classes"][cls1]["relations"][rel]:
						data["classes"][cls1]["relations"][rel].append(cls2)
				cursor.execute("SELECT * FROM %s.\"%s\";" % (schema, table,))
				rows = cursor.fetchall()
				for row in rows:
					source_id, target_id = row
					if rel not in data["objects"][source_id]["relations"]:
						data["objects"][source_id]["relations"][rel] = dict(\
							objects = [],
							weights = {},
						)
					if target_id not in data["objects"][source_id]["relations"][rel]["objects"]:
						data["objects"][source_id]["relations"][rel]["objects"].append(target_id)
		for table in data["classes"]:
			data["classes"][table]["relations"] = dict(data["classes"][table]["relations"])
		
		# load class order
		table = "#order"
		cursor.execute("SELECT * FROM %s.\"%s\";" % (schema, table,))
		rows = cursor.fetchall()
		for row in rows:
			data["classes"][row[0]]["order"] = row[1]
		
		# load user tools
		table = "#user_tools"
		cursor.execute("SELECT * FROM %s.\"%s\";" % (schema, table,))
		rows = cursor.fetchall()
		for row in rows:
			data["user_tools"].append(json.loads(row[0]))
		
		# load queries
		table = "#queries"
		cursor.execute("SELECT * FROM %s.\"%s\";" % (schema, table,))
		rows = cursor.fetchall()
		for row in rows:
			data["queries"][row[0]] = json.loads(row[1])
		
		if not was_connected:
			self.disconnect()
		
		return data
	
	def save_data(self, 
		db_meta,
		object_nodes, object_relations, 
		class_nodes, class_relations, 
		member_nodes, member_relations, 
		user_tools, queries, 
		progress = None
	):
		# store data in postgres db
		'''
		db_meta = dict(
			deposit_version,
			local_folder,
			max_order,
		)
		object_nodes = [{id: int, data: object_node_data}, ...]
			object_node_data = {
				(optional) descriptors: {descr_name: value or AbstractDType.to_dict(), ...}
				(optional) locations: {descr_name: DGeometry.to_dict(), ...}
			}
		object_relations = [{src: int, tgt: int, lbl: str, weight: float}, ...]
		class_nodes = [{id: str, data: class_node_data}, ...]
			class_node_data = {
				order: int,
				(optional) descriptors = [descr_name, ...]
			}
		class_relations = [{src: str, tgt: str, lbl: str}, ...]
		member_nodes = [{id: int/str}, ...]
		member_relations = [{src: int/str, tgt: int/str}, ...]
		user_tools = [dict(), ...]
		queries = {name: querystr, ...}
		'''
		
		def check_table(name, schema, cursor):
			
			cursor.execute(
				"SELECT table_name FROM information_schema.tables WHERE table_schema = '%s';" % (schema)
			)
			return name in [row[0] for row in cursor.fetchall()]
		
		def create_table(name, columns, schema, cursor, primary=None):
			
			if check_table(name, schema, cursor):
				cursor.execute("DROP TABLE IF EXISTS %s.\"%s\";" % (schema, name))
				deleted = False
				for i in range(20):
					time.sleep(0.5)
					if not check_table(name, schema, cursor):
						deleted = True
						break
				if not deleted:
					raise Exception("Could not delete table \"%s\"." % (name))
			if primary is not None:
				columns += f", PRIMARY KEY({primary})"
			cursor.execute("CREATE TABLE %s.\"%s\" (%s);" % (schema, name, columns))
			cursor.connection.commit()
			created = False
			for i in range(20):
				time.sleep(0.5)
				if check_table(name, schema, cursor):
					created = True
					break
			if not created:
				raise Exception("Could not create table \"%s\"." % (name))
		
		def save_class(class_name, object_nodes, obj_lookup, class_descriptors, class_order, schema, cursor):
			# object_nodes = {obj_id: data, ...}
			# obj_lookup = {class_name: set(obj_id, ...), ...}
			# class_descriptors = {class_name: set(descriptor_name, ...), ...}
			# class_order = {class_name: order, ...}
			#
			# returns locations = set([(obj_id, descriptor_name, json_data), ...])
			
			locations = set()
			descriptors = class_descriptors[class_name].copy()
			for obj_id in obj_lookup[class_name]:
				descriptors.update(object_nodes[obj_id].get("descriptors", set()))
			obj_column = "id"
			while obj_column in descriptors:
				obj_column += "_"
			descriptors = sorted(descriptors, key = lambda name: class_order[name])
			if descriptors:
				columns = "%s INTEGER, %s" % (obj_column, ", ".join([("\"%s\" TEXT" % name) for name in descriptors]))
			else:
				columns = "%s INTEGER" % (obj_column)
			column_names = ", ".join([("\"%s\"" % name) for name in [obj_column] + descriptors])
			table = "@%s" % (class_name)
			create_table(table, columns, schema, cursor, primary = obj_column)
			data = [] # [{obj_column: obj_id, [descr_name]: json(value), ...}, ...]
			for obj_id in sorted(obj_lookup[class_name]):
				row = {obj_column: obj_id}
				for name in descriptors:
					row[name] = None
					if ("descriptors" in object_nodes[obj_id]) and (name in object_nodes[obj_id]["descriptors"]):
						row[name] = json.dumps(object_nodes[obj_id]["descriptors"][name])
				if "locations" in object_nodes[obj_id]:
					for name in object_nodes[obj_id]["locations"]:
						locations.add((obj_id, name, json.dumps(object_nodes[obj_id]["locations"][name])))
				data.append(row)
			if data:
				cursor.execute("""
					DROP TYPE IF EXISTS item_;
					CREATE TYPE item_ as (%s);
					INSERT INTO %s.\"%s\" SELECT %s FROM json_populate_recordset(null::item_, %%s);
				""" % (columns, schema, table, column_names), (json.dumps(data),))
			
			return locations, obj_column
		
		identifier = self.get_identifier()
		tables = self.get_current_tables()
		was_connected = self.is_connected()
		cursor = self.get_cursor()
		schema = self.get_schema()
		
		src_ = GRAPH_ATTRS["source"]
		tgt_ = GRAPH_ATTRS["target"]
		lbl_ = GRAPH_ATTRS["key"]
		id_ = GRAPH_ATTRS["name"]
		
		object_nodes = dict([(row[id_], row["data"]) for row in object_nodes])
		# object_nodes = {obj_id: data, ...}
		
		for name in tables:
			cursor.execute("DROP TABLE IF EXISTS %s.\"%s\";" % (schema, name))
		
		table = "identifier"
		create_table(table, "name TEXT", schema, cursor)
		cursor.execute("INSERT INTO %s.\"%s\" VALUES ('%s');" % (schema, table, json.dumps(identifier)))
		
		table = "db_meta"
		columns = "variable TEXT, value TEXT"
		create_table(table, columns, schema, cursor)
		if db_meta:
			data = []
			for variable in db_meta:
				data.append({"variable": variable, "value": json.dumps(db_meta[variable])})
			cursor.execute("""
				DROP TYPE IF EXISTS item_;
				CREATE TYPE item_ as (%s);
				INSERT INTO %s.\"%s\" SELECT variable, value FROM json_populate_recordset(null::item_, %%s);
			""" % (columns, schema, table), (json.dumps(data),))
		
		class_names = set()
		class_descriptors = {}  # {class_name: set(descriptor_name, ...), ...}
		class_order = {}
		table = "classes"
		columns = "pg_name TEXT, name TEXT, order_ INTEGER"
		create_table(table, columns, schema, cursor, primary = 'pg_name')
		data = []
		for row in class_nodes:
			class_names.add(row[id_])
			if "descriptors" in row["data"]:
				class_descriptors[row[id_]] = set(row["data"]["descriptors"])
			else:
				class_descriptors[row[id_]] = set()
			class_order[row[id_]] = row["data"]["order"]
			data.append({"pg_name": "@%s" % (row[id_]), "name": row[id_], "order_": row["data"]["order"]})
		cursor.execute("""
			DROP TYPE IF EXISTS item_;
			CREATE TYPE item_ as (%s);
			INSERT INTO %s.\"%s\" SELECT pg_name, name, order_ FROM json_populate_recordset(null::item_, %%s);
		""" % (columns, schema, table), (json.dumps(data),))
		
		classless_ = "classless_"
		while classless_ in class_names:
			classless_ += "_"
		class_names.add(classless_)
		class_descriptors[classless_] = set()
		
		data = [{"pg_name": "@%s" % (classless_), "name": None, "order_": None}]
		cursor.execute("""
			DROP TYPE IF EXISTS item_;
			CREATE TYPE item_ as (%s);
			INSERT INTO %s.\"%s\" SELECT pg_name, name, order_ FROM json_populate_recordset(null::item_, %%s);
		""" % (columns, schema, table), (json.dumps(data),))
		
		subclasses = []  # [dict(name, subclass), ...]
		class_lookup = defaultdict(set)  # {obj_id: set(class_name, ...), ...}
		obj_lookup = defaultdict(set)  # {class_name: set(obj_id, ...), ...}
		for row in member_relations:
			if isinstance(row[src_], str) and isinstance(row[tgt_], int):
				class_lookup[row[tgt_]].add(row[src_])
				obj_lookup[row[src_]].add(row[tgt_])
			elif isinstance(row[src_], str) and isinstance(row[tgt_], str):
				subclasses.append({"name": row[src_], "subclass": row[tgt_]})
		for obj_id in object_nodes:
			if not class_lookup[obj_id]:
				class_lookup[obj_id].add(classless_)
				obj_lookup[classless_].add(obj_id)
		
		table = "subclasses"
		columns = "name TEXT, subclass TEXT"
		create_table(table, columns, schema, cursor)
		if subclasses:
			cursor.execute("""
				DROP TYPE IF EXISTS item_;
				CREATE TYPE item_ as (%s);
				INSERT INTO %s.\"%s\" SELECT name, subclass FROM json_populate_recordset(null::item_, %%s);
			""" % (columns, schema, table), (json.dumps(subclasses),))
		
		locations = set()  # [(obj_id, descriptor_name, json_data), ...]
		obj_columns = {}  # {class_name: obj_column, ...}
		for class_name in class_names:
			locations_, obj_column = save_class(class_name, object_nodes, obj_lookup, class_descriptors, class_order, schema, cursor)
			locations.update(locations_)
			obj_columns[class_name] = obj_column
		
		relations = {}  # {pg_name: [dict(source, target, weight), ...], ...}
		relation_classes = []  # [dict(pg_name, source, relation, target), ...]
		for row in class_relations:
			source = row[src_]
			target = row[tgt_]
			label = row[lbl_]
			if label.startswith("~"):
				continue
			pg_name = (source, label, target)
			relations[pg_name] = []
			relation_classes.append({"pg_name": "@%s_%s_%s" % pg_name, "source": source, "relation": label, "target": target})
		for row in object_relations:
			source = row[src_]
			target = row[tgt_]
			label = row[lbl_]
			if label.startswith("~"):
				continue
			weight = row["weight"] if "weight" in row else None
			classes_src = class_lookup[source]
			classes_tgt = class_lookup[target]
			for source_cls in classes_src:
				for target_cls in classes_tgt:
					pg_name = (source_cls, label, target_cls)
					if pg_name not in relations:
						relations[pg_name] = []
						relation_classes.append({"pg_name": "@%s_%s_%s" % pg_name, "source": source_cls, "relation": label, "target": target_cls})
					relations[pg_name].append({"source": source, "target": target, "weight": weight})
		for (source, label, target) in relations:
			table = "@%s_%s_%s" % (source, label, target)
			columns_table = f"rel_id SERIAL PRIMARY KEY, source INTEGER REFERENCES {schema}.\"@{source}\"({obj_columns[source]}), target INTEGER REFERENCES {schema}.\"@{target}\"({obj_columns[target]}), weight FLOAT"
			columns = f"source INTEGER, target INTEGER, weight FLOAT"
			create_table(table, columns_table, schema, cursor)
			cursor.execute("""
				DROP TYPE IF EXISTS item_;
				CREATE TYPE item_ as (%s);
				INSERT INTO %s.\"%s\" (source, target, weight) SELECT source, target, weight FROM json_populate_recordset(null::item_, %%s);
			""" % (columns, schema, table), (json.dumps(relations[(source, label, target)]),))
		
		table = "relations"
		columns = "pg_name TEXT, source TEXT, relation TEXT, target TEXT"
		create_table(table, columns, schema, cursor)
		cursor.execute("""
			DROP TYPE IF EXISTS item_;
			CREATE TYPE item_ as (%s);
			INSERT INTO %s.\"%s\" SELECT pg_name, source, relation, target FROM json_populate_recordset(null::item_, %%s);
		""" % (columns, schema, table), (json.dumps(relation_classes),))
		
		table = "locations"
		columns = "id INTEGER, descriptor TEXT, location TEXT"
		create_table(table, columns, schema, cursor)
		data = []
		for obj_id, descriptor_name, location in locations:
			data.append({"id": obj_id, "descriptor": descriptor_name, "location": location})
		if data:
			cursor.execute("""
				DROP TYPE IF EXISTS item_;
				CREATE TYPE item_ as (%s);
				INSERT INTO %s.\"%s\" SELECT id, descriptor, location FROM json_populate_recordset(null::item_, %%s);
			""" % (columns, schema, table), (json.dumps(data),))
		
		table = "user_tools"
		columns = "data TEXT"
		create_table(table, columns, schema, cursor)
		if user_tools:
			data = [dict(data = json.dumps(row)) for row in user_tools]
			cursor.execute("""
				DROP TYPE IF EXISTS item_;
				CREATE TYPE item_ as (%s);
				INSERT INTO %s.\"%s\" SELECT data FROM json_populate_recordset(null::item_, %%s);
			""" % (columns, schema, table), (json.dumps(data),))
		
		table = "queries"
		columns = "title TEXT, querystr TEXT"
		create_table(table, columns, schema, cursor)
		if queries:
			data = []
			for title in queries:
				data.append(dict(title = title, querystr = json.dumps(queries[title])))
			cursor.execute("""
				DROP TYPE IF EXISTS item_;
				CREATE TYPE item_ as (%s);
				INSERT INTO %s.\"%s\" SELECT title, querystr FROM json_populate_recordset(null::item_, %%s);
			""" % (columns, schema, table), (json.dumps(data),))
		
		cursor.connection.commit()
		
		if not was_connected:
			self.disconnect()
		
		return True
	
	def __str__(self):
		
		return "PostgreSQL Relational"