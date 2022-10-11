from deposit.datasource.abstract_dbsource import AbstractDBSource

from deposit.utils.fnc_files import (is_local_url, url_to_path)
from deposit.utils.fnc_serialize import (GRAPH_ATTRS)

from collections import defaultdict
import json

class DB(AbstractDBSource):
	
	def __init__(self):
		
		AbstractDBSource.__init__(self)	
		
		self._identifiers = {}  # {identifier: [tablename, ...], ...}
	
	def connect(self):
		
		self._identifiers.clear()
		
		return AbstractDBSource.connect(self)
	
	def disconnect(self):
		
		self._identifiers.clear()
		
		return AbstractDBSource.disconnect(self)
	
	def get_current_tables(self):
		
		identifiers = self.get_identifiers()
		ident = self.get_identifier()
		if ident not in identifiers:
			return []
		return identifiers[ident]
	
	def is_deposit_db(self, tables = None):
		
		if tables is None:
			tables = self.get_current_tables()
		for name in [
			"db_meta", "user_tools", "queries", 
			"object_nodes", "object_relations", 
			"class_nodes", "class_relations", 
			"member_nodes", "member_relations",
			]:
			if name not in tables:
				return False
		return True
	
	def is_legacy_db(self, tables = None):
		
		if tables is None:
			tables = self.get_current_tables()
		for name in ["classes", "objects", "local_folder"]:
			if name not in tables:
				return False
		return True
	
	def get_identifiers(self):
		
		if (not self._identifiers):
			collect = defaultdict(list)
			for table in self.get_tables():
				ident = table.split("#")
				if len(ident) == 2:
					ident, name = ident
					collect[ident].append(name)
			self._identifiers = {}
			for ident in collect:
				if self.is_deposit_db(collect[ident]) or self.is_legacy_db(collect[ident]):
					self._identifiers[ident] = collect[ident].copy()
		
		return self._identifiers
	
	def is_valid(self):
		
		was_connected = self.is_connected()
		cursor = self.get_cursor()
		
		ret = (cursor is not None) and (self._identifier in self.get_identifiers())
		
		if not was_connected:
			self.disconnect()
		
		return ret
	
	def delete(self):
		
		identifier = self.get_identifier()
		cursor = self.get_cursor()
		if (identifier is None) or (cursor is None):
			return False
		for table in self.get_current_tables():
			table = "%s#%s" % (identifier, table)
			cursor.execute("DROP TABLE IF EXISTS \"%s\";" % (table))
		cursor.connection.commit()
		self.disconnect()
		self.set_identifier(None)
		
		return True
	
	def load_data(self, progress = None):
		
		if self.is_legacy_db():
			return self.load_legacy_data(progress)
		
		identifier = self.get_identifier()
		
		was_connected = self.is_connected()
		cursor = self.get_cursor()
		
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
				nodes = [],
			),
			class_relation_graph = dict(
				directed = True,
				multigraph = True,
				graph = {},
				nodes = [],
			),
			class_membership_graph = dict(
				directed = True,
				multigraph = False,
				graph = {},
				nodes = [],
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
		
		table = identifier + "#db_meta"
		cursor.execute("SELECT * FROM \"%s\";" % (table,))
		rows = cursor.fetchall()
		if rows:
			data_table = {}
			for row in rows:
				data_table[row[0]] = json.loads(row[1])
			data["deposit_version"] = data_table.get("deposit_version", None)
			data["local_folder"] = data_table.get("local_folder", None)
			data["max_order"] = data_table.get("max_order", None)
		
		table = identifier + "#object_nodes"
		cursor.execute("SELECT * FROM \"%s\";" % (table,))
		rows = cursor.fetchall()
		for row in rows:
			data["object_relation_graph"]["nodes"].append(
				{id_: row[0], "data": json.loads(row[1])}
			)
		
		table = identifier + "#object_relations"
		cursor.execute("SELECT * FROM \"%s\";" % (table,))
		rows = cursor.fetchall()
		for row in rows:
			data["object_relation_graph"][relations_].append({
				src_: row[0],
				tgt_: row[1],
				lbl_: row[2],
				"weight": row[3],
			})
		
		table = identifier + "#class_nodes"
		cursor.execute("SELECT * FROM \"%s\";" % (table,))
		rows = cursor.fetchall()
		for row in rows:
			data["class_relation_graph"]["nodes"].append(
				{id_: row[0], "data": json.loads(row[1])}
			)
		
		table = identifier + "#class_relations"
		cursor.execute("SELECT * FROM \"%s\";" % (table,))
		rows = cursor.fetchall()
		for row in rows:
			data["class_relation_graph"][relations_].append({
				src_: row[0],
				tgt_: row[1],
				lbl_: row[2],
			})
		
		table = identifier + "#member_nodes"
		cursor.execute("SELECT * FROM \"%s\";" % (table,))
		rows = cursor.fetchall()
		for row in rows:
			data["class_membership_graph"]["nodes"].append(
				{id_: json.loads(row[0])}
			)
		
		table = identifier + "#member_relations"
		cursor.execute("SELECT * FROM \"%s\";" % (table,))
		rows = cursor.fetchall()
		for row in rows:
			data["class_membership_graph"][relations_].append({
				src_: json.loads(row[0]),
				tgt_: json.loads(row[1]),
			})
		
		table = identifier + "#user_tools"
		cursor.execute("SELECT * FROM \"%s\";" % (table,))
		rows = cursor.fetchall()
		for row in rows:
			data["user_tools"].append(json.loads(row[0]))
		
		table = identifier + "#queries"
		cursor.execute("SELECT * FROM \"%s\";" % (table,))
		rows = cursor.fetchall()
		for row in rows:
			data["queries"][row[0]] = json.loads(row[1])
		
		if not was_connected:
			self.disconnect()
		
		return data
	
	def load_legacy_data(self, progress = None):
		# load data from postgres db (old format)
				
		identifier = self.get_identifier()
		tables = self.get_current_tables()
		
		was_connected = self.is_connected()
		cursor = self.get_cursor()
		
		data = dict(
			classes = {},
			objects = {},
			user_tools = [],
			queries = {},
			local_folder = None,
		)
		
		cursor.execute("SELECT * FROM \"%s\";" % (identifier + "#local_folder",))
		for row in cursor.fetchall():
			local_folder = json.loads(row[0])
			if is_local_url(local_folder):
				local_folder = url_to_path(local_folder)
			data["local_folder"] = local_folder
			break
		
		table = identifier + "#classes"
		cursor.execute("SELECT * FROM \"%s\";" % (table,))
		rows = cursor.fetchall()
		if rows:
			for row in rows:
				data["classes"][row[0]] = json.loads(row[1])
		
		table = identifier + "#objects"
		cursor.execute("SELECT * FROM \"%s\";" % (table,))
		rows = cursor.fetchall()
		if rows:
			for row in rows:
				data["objects"][row[0]] = json.loads(row[1])
		
		table = identifier + "#user_tools"
		if table in tables:
			cursor.execute("SELECT * FROM \"%s\";" % (table,))
			rows = cursor.fetchall()
			if rows:
				for row in rows:
					data["user_tools"].append(json.loads(row[0]))
		
		table = identifier + "#queries"
		if table in tables:
			cursor.execute("SELECT * FROM \"%s\";" % (table,))
			rows = cursor.fetchall()
			if rows:
				for row in rows:
					data["queries"][row[0]] = json.loads(row[1])
		
		if was_connected:
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
		
		def create_table(name, columns, tables, cursor):

			if name.split("#")[-1] in tables:
				cursor.execute("DROP TABLE \"%s\";" % (name))
			cursor.execute("CREATE TABLE %s.\"%s\" (%s);" % (self.get_schema(), name, columns))
		
		identifier = self.get_identifier()
		tables = self.get_current_tables()
		was_connected = self.is_connected()
		cursor = self.get_cursor()
		
		src_ = GRAPH_ATTRS["source"]
		tgt_ = GRAPH_ATTRS["target"]
		lbl_ = GRAPH_ATTRS["key"]
		id_ = GRAPH_ATTRS["name"]
		
		table = identifier + "#db_meta"
		columns = "variable TEXT, value TEXT"
		create_table(table, columns, tables, cursor)
		if db_meta:
			data = []
			for variable in db_meta:
				data.append({"variable": variable, "value": json.dumps(db_meta[variable])})
			cursor.execute("""
				DROP TYPE IF EXISTS node_;
				CREATE TYPE node_ as (%s);
				INSERT INTO \"%s\" SELECT variable, value FROM json_populate_recordset(null::node_, %%s);
			""" % (columns, table), (json.dumps(data),))
		
		table = identifier + "#object_nodes"
		columns = "id INTEGER, data TEXT"
		create_table(table, columns, tables, cursor)
		if object_nodes:
			data = []
			for node in object_nodes:
				data.append({"id": node[id_], "data": json.dumps(node["data"])})
			cursor.execute("""
				DROP TYPE IF EXISTS node_;
				CREATE TYPE node_ as (%s);
				INSERT INTO \"%s\" SELECT id, data FROM json_populate_recordset(null::node_, %%s);
			""" % (columns, table), (json.dumps(data),))
		
		table = identifier + "#object_relations"
		columns = "src INTEGER, tgt INTEGER, label TEXT, weight FLOAT"
		create_table(table, columns, tables, cursor)
		if object_relations:
			data = []
			for rel in object_relations:
				data.append({"src": rel[src_], "tgt": rel[tgt_], "label": rel[lbl_], "weight": rel["weight"] if "weight" in rel else None})
			cursor.execute("""
				DROP TYPE IF EXISTS rel_;
				CREATE TYPE rel_ as (%s);
				INSERT INTO \"%s\" SELECT src, tgt, label, weight FROM json_populate_recordset(null::rel_, %%s);
			""" % (columns, table), (json.dumps(data),))
		
		table = identifier + "#class_nodes"
		columns = "id TEXT, data TEXT"
		create_table(table, columns, tables, cursor)
		if class_nodes:
			data = []
			for node in class_nodes:
				data.append({"id": node[id_], "data": json.dumps(node["data"])})
			cursor.execute("""
				DROP TYPE IF EXISTS node_;
				CREATE TYPE node_ as (%s);
				INSERT INTO \"%s\" SELECT id, data FROM json_populate_recordset(null::node_, %%s);
			""" % (columns, table), (json.dumps(data),))
		
		table = identifier + "#class_relations"
		columns = "src TEXT, tgt TEXT, label TEXT"
		create_table(table, columns, tables, cursor)
		if class_relations:
			data = []
			for rel in class_relations:
				data.append({"src": rel[src_], "tgt": rel[tgt_], "label": rel[lbl_]})
			cursor.execute("""
				DROP TYPE IF EXISTS rel_;
				CREATE TYPE rel_ as (%s);
				INSERT INTO \"%s\" SELECT src, tgt, label FROM json_populate_recordset(null::rel_, %%s);
			""" % (columns, table), (json.dumps(data),))
		
		table = identifier + "#member_nodes"
		columns = "id TEXT"
		create_table(table, columns, tables, cursor)
		if member_nodes:
			data = []
			for node in member_nodes:
				data.append({"id": json.dumps(node[id_])})
			cursor.execute("""
				DROP TYPE IF EXISTS node_;
				CREATE TYPE node_ as (%s);
				INSERT INTO \"%s\" SELECT id FROM json_populate_recordset(null::node_, %%s);
			""" % (columns, table), (json.dumps(data),))
		
		table = identifier + "#member_relations"
		columns = "src TEXT, tgt TEXT"
		create_table(table, columns, tables, cursor)
		if member_relations:
			data = []
			for rel in member_relations:
				data.append({"src": json.dumps(rel[src_]), "tgt": json.dumps(rel[tgt_])})
			cursor.execute("""
				DROP TYPE IF EXISTS rel_;
				CREATE TYPE rel_ as (%s);
				INSERT INTO \"%s\" SELECT src, tgt FROM json_populate_recordset(null::rel_, %%s);
			""" % (columns, table), (json.dumps(data),))		
		
		table = identifier + "#user_tools"
		columns = "data TEXT"
		create_table(table, columns, tables, cursor)
		if user_tools:
			data = []
			for row in user_tools:
				data.append({"data": json.dumps(row)})
			cursor.execute("""
				DROP TYPE IF EXISTS user_tool_;
				CREATE TYPE user_tool_ as (%s);
				INSERT INTO \"%s\" SELECT data FROM json_populate_recordset(null::user_tool_, %%s);
			""" % (columns, table), (json.dumps(data),))
		
		table = identifier + "#queries"
		columns = "title TEXT, querystr TEXT"
		create_table(table, columns, tables, cursor)
		if queries:
			data = []
			for title in queries:
				data.append({"title": title, "data": json.dumps(queries[title])})
			cursor.execute("""
				DROP TYPE IF EXISTS node_;
				CREATE TYPE node_ as (%s);
				INSERT INTO \"%s\" SELECT title, querystr FROM json_populate_recordset(null::node_, %%s);
			""" % (columns, table), (json.dumps(data),))
		
		cursor.connection.commit()
		
		if not was_connected:
			self.disconnect()
		
		return True

