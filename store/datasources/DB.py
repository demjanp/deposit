'''
	
	Save Deposit database in a PostgreSQL database
	
	Schema:
		
		Classes:
			table = [identifier]#classes
			columns:
				name (text)
				data (text)
		
		Objects:
			table = [identifier]#objects
			columns:
				id (integer)
				data (text)
		
		Queries:
			table = [identifier]#queries
			columns:
				title (text)
				querystr (text)
		
		User tools:
			table = [identifier]#user_tools
			columns:
				data (text)
		
		Events:
			table = [identifier]#events
			columns:
				time (text)
				user_ (text)
				delement (text)
				key (text)
				function (text)
				args (text)
		
		Local folder:
			table = [identifier]#local_folder
			columns:
				path (text)
		
		Changed:
			table = [identifier]#changed
			columns:
				timestamp (text)
		
		Deposit version:
			table = [identifier]#deposit_version
			columns:
				version (text)
	
'''


from deposit import Broadcasts, __version__
from deposit.store.datasources._DataSource import (DataSource)
from deposit.store.LinkedStore import (LinkedStore)

from collections import defaultdict
import psycopg2
import json
import sys

class DB(DataSource):
	
	def __init__(self, store, identifier = None, connstr = None):

		DataSource.__init__(self, store)
		
		if isinstance(identifier, str) and (not identifier.endswith("#")):
			identifier = identifier + "#"
		
		self.identifier = identifier
		self.connstr = connstr
		self.schema = self.get_schema(self.connstr)
	
	def get_schema(self, connstr):
		
		schema = "public"
		if connstr is None:
			return schema
		if "?" in connstr:
			schema = connstr.split("?")[-1].split("%3D")[-1]
		return schema
	
	def set_connstr(self, connstr):

		self.connstr = connstr
		self.schema = self.get_schema(self.connstr)
		cursor, tables = self.connect()
		if cursor is None:
			self.connstr = None
			ret = False
		else:
			cursor.connection.close()
			ret = True
		if self.store.data_source == self:
			self.broadcast(Broadcasts.STORE_DATA_SOURCE_CHANGED)
		return ret
	
	def connect(self, create_schema = False):
		
		try:
			conn = psycopg2.connect(self.connstr)
		except:
			_, exc_value, _ = sys.exc_info()
			print("Connection Error in %s: %s" % (self.connstr, str(exc_value)))
			return None, []
		cursor = conn.cursor()
		
		if create_schema:
			cursor.execute("CREATE SCHEMA IF NOT EXISTS %s" % (self.schema))
			cursor.connection.commit()
		
		cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = '%s';" % (self.schema))
		tables = [row[0] for row in cursor.fetchall()]
		return cursor, tables
	
	def get_identifiers(self):

		def is_deposit_db(names):
			
			for name in ["classes", "objects", "changed", "local_folder"]:
				if not name in names:
					return False
			return True
		
		cursor, tables = self.connect()
		if cursor is None:
			return []
		
		cursor.connection.close()
		
		collect = defaultdict(list) # {identifier: [name, ...], ...}
		for table in tables:
			ident = table.split("#")
			if len(ident) == 2:
				ident, name = ident
				collect[ident].append(name)
		
		return [ident + "#" for ident in collect if is_deposit_db(collect[ident])]
	
	def is_valid(self):
		
		if self.get_identifiers():
			return True
		return False
	
	def get_local_folder(self, identifier):
		
		cursor, tables = self.connect()
		if cursor is None:
			return ""
		if (identifier + "local_folder") not in tables:
			return ""
		cursor.execute("SELECT * FROM \"%s\";" % (identifier + "local_folder",))
		local_folder = ""
		for row in cursor.fetchall():
			local_folder = json.loads(row[0])
			break
		cursor.connection.close()
		return local_folder
	
	def save(self):
	
		def create_table(name, columns, tables, cursor):

			if name in tables:
				cursor.execute("DROP TABLE \"%s\";" % (name))
			cursor.execute("CREATE TABLE %s.\"%s\" (%s);" % (self.schema, name, columns))
		
		if self.identifier is None:
			return False
		
		cursor, tables = self.connect()
		if cursor is None:
			return False
		
		if not self.wait_if_busy():
			return False
		self.is_busy = True
		
		data_class = self.store.classes.to_dict() # {name: class data, ...}
		data_object = self.store.objects.to_dict() # {id: object data, ...}
		
		table = self.identifier + "classes"
		class_type = "name TEXT, data TEXT"
		create_table(table, class_type, tables, cursor)
		if data_class:
			data = []
			for name in data_class:
				data.append(dict(name = name, data = json.dumps(data_class[name])))
			cursor.execute("""
				DROP TYPE IF EXISTS class_;
				CREATE TYPE class_ as (%s);
				INSERT INTO \"%s\" SELECT name, data FROM json_populate_recordset(null::class_, %%s);
			""" % (class_type, table), (json.dumps(data),))
		
		table = self.identifier + "objects"
		object_type = "id INTEGER, data TEXT"
		create_table(table, object_type, tables, cursor)
		if data_object:
			data = []
			for id in data_object:
				data.append(dict(id = id, data = json.dumps(data_object[id])))
			cursor.execute("""
				DROP TYPE IF EXISTS object_;
				CREATE TYPE object_ as (%s);
				INSERT INTO \"%s\" SELECT id, data FROM json_populate_recordset(null::object_, %%s);
			""" % (object_type, table), (json.dumps(data),))
		
		table = self.identifier + "changed"
		create_table(table, "timestamp TEXT", tables, cursor)
		cursor.execute("INSERT INTO \"%s\" VALUES ('%s');" % (table, json.dumps(self.store.changed)))

		table = self.identifier + "deposit_version"
		create_table(table, "version TEXT", tables, cursor)
		cursor.execute("INSERT INTO \"%s\" VALUES ('%s');" % (table, __version__))

		table = self.identifier + "local_folder"
		create_table(table, "path TEXT", tables, cursor)
		if not self.store.local_folder is None:
			cursor.execute("INSERT INTO \"%s\" VALUES ('%s');" % (table, json.dumps(self.store.local_folder)))
		
		table = self.identifier + "events"
		event_type = "time TEXT, user_ TEXT, delement TEXT, key TEXT, function TEXT, args TEXT"
		create_table(table, event_type, tables, cursor)
		if self.store.save_events:
			events = self.store.events.to_list()
			if events:
				data = []
				for t, user, delement, key, function, args in events:
					t, user, delement, key, function, args = [json.dumps(val) for val in [t, user, delement, key, function, args]]
					data.append(dict(time = t, user_ = user, delement = delement, key = key, function = function, args = args))
				cursor.execute("""
					DROP TYPE IF EXISTS event_;
					CREATE TYPE event_ as (%s);
					INSERT INTO \"%s\" SELECT time, user_, delement, key, function, args FROM json_populate_recordset(null::event_, %%s);
				""" % (event_type, table), (json.dumps(data),))
		
		table = self.identifier + "user_tools"
		user_tool_type = "data TEXT"
		create_table(table, user_tool_type, tables, cursor)
		data_user_tools = self.store.user_tools.to_list()
		if data_user_tools:
			data = []
			for row in data_user_tools:
				data.append(dict(data = json.dumps(row)))
			cursor.execute("""
				DROP TYPE IF EXISTS user_tool_;
				CREATE TYPE user_tool_ as (%s);
				INSERT INTO \"%s\" SELECT data FROM json_populate_recordset(null::user_tool_, %%s);
			""" % (user_tool_type, table), (json.dumps(data),))
		
		table = self.identifier + "queries"
		queries_type = "title TEXT, querystr TEXT"
		create_table(table, queries_type, tables, cursor)
		data_queries = self.store.queries.to_dict()
		if data_queries:
			data = []
			for title in data_queries:
				data.append(dict(title = title, querystr = json.dumps(data_queries[title])))
			cursor.execute("""
				DROP TYPE IF EXISTS queries_;
				CREATE TYPE queries_ as (%s);
				INSERT INTO \"%s\" SELECT title, querystr FROM json_populate_recordset(null::queries_, %%s);
			""" % (queries_type, table), (json.dumps(data),))
		
		cursor.connection.commit()
		cursor.connection.close()
		
		self.is_busy = False
		return True
	
	def load(self):
		
		if self.identifier is None:
			return False
		
		if not self.wait_if_busy():
			return False
		self.is_busy = True
		
		cursor, tables = self.connect()
		if cursor is None:
			self.is_busy = False
			return False
		
		if not self.identifier in self.get_identifiers():
			self.is_busy = False
			return False
		
		self.stop_broadcasts()
		self.store.events.stop_recording()
		self.store.clear()

		has_class_descriptors = False  # TODO will be obsolete for new databases
		data = {}
		table = self.identifier + "classes"
		cursor.execute("SELECT * FROM \"%s\";" % (table,))
		rows = cursor.fetchall()
		if rows:
			data = {} # {name: class data, ...}
			for row in rows:
				data[row[0]] = json.loads(row[1])
			self.store.classes.from_dict(data)
			for name in data:  # TODO will be obsolete for new databases
				has_class_descriptors = ("descriptors" in data[name])
				break
			data = None
		
		resource_uris = []
		
		table = self.identifier + "objects"
		cursor.execute("SELECT * FROM \"%s\";" % (table,))
		rows = cursor.fetchall()
		if rows:
			data = {} # {id: object data, ...}
			for row in rows:
				data[row[0]] = json.loads(row[1])
			self.store.objects.from_dict(data)
		
			for id in data:
				for name in data[id]["descriptors"]:
					if (data[id]["descriptors"][name]["label"]["dtype"] == "DResource") and (not data[id]["descriptors"][name]["label"]["path"] is None):
						if not data[id]["descriptors"][name]["label"]["value"] in resource_uris:
							resource_uris.append(data[id]["descriptors"][name]["label"]["value"])
		
		self.store.set_local_resource_uris(resource_uris)
		
		if not has_class_descriptors:  # TODO will be obsolete for new databases
			self.store.populate_descriptor_names()  # TODO will be obsolete for new databases
			self.store.populate_relation_names()  # TODO will be obsolete for new databases
		
		cursor.execute("SELECT * FROM \"%s\";" % (self.identifier + "changed",))
		for row in cursor.fetchall():
			self.store.changed = json.loads(row[0])
			break

		cursor.execute("SELECT * FROM \"%s\";" % (self.identifier + "local_folder",))
		for row in cursor.fetchall():
			self.store.local_folder = json.loads(row[0])
			break
		
		table = self.identifier + "events"
		if table in tables: # TODO will be obsolete for new databases
			cursor.execute("SELECT * FROM \"%s\";" % (table,))
			rows = cursor.fetchall()
			if rows:
				data = []  # [[t, user, class_name, key, func_name, args], ...]
				for row in rows:
					data.append([json.loads(val) for val in row])
				self.store.events.from_list(data)
		
		table = self.identifier + "user_tools"
		if table in tables: # TODO will be obsolete for new databases
			cursor.execute("SELECT * FROM \"%s\";" % (table,))
			rows = cursor.fetchall()
			if rows:
				data = []
				for row in rows:
					data.append(json.loads(row[0]))
				self.store.user_tools.from_list(data)
		
		table = self.identifier + "queries"
		if table in tables: # TODO will be obsolete for new databases
			cursor.execute("SELECT * FROM \"%s\";" % (table,))
			rows = cursor.fetchall()
			if rows:
				data = {}  # {title: querystr, ...}
				for row in rows:
					data[row[0]] = json.loads(row[1])
				self.store.queries.from_dict(data)
		
		self.store.images.load_thumbnails()
		
		self.store.set_datasource(self)
		
		self.is_busy = False
		
		self.store.events.resume_recording()
		self.resume_broadcasts()
		self.broadcast(Broadcasts.STORE_LOADED)
		
		cursor.connection.close()
		
		return True
	
	def link(self):
		
		if self.identifier is None:
			return False

		cursor, tables = self.connect()
		if cursor is None:
			return False
		
		if not self.identifier in self.get_identifiers():
			return False
		
		if not self.wait_if_busy():
			return False
		self.is_busy = True
		
		self.stop_broadcasts()
		self.store.events.stop_recording()
		
		if not self.identifier in self.store.linked:
			self.store.linked[self.identifier] = LinkedStore(self.identifier)

		has_class_descriptors = False  # TODO will be obsolete for new databases
		table = self.identifier + "classes"
		cursor.execute("SELECT * FROM \"%s\";" % (table,))
		data = {}
		rows = cursor.fetchall()
		if rows:
			data = {} # {name: class data, ...}
			for row in rows:
				data[row[0]] = json.loads(row[1])
			self.store.classes.from_dict_linked(data, self.identifier)
			for name in data:  # TODO will be obsolete for new databases
				has_class_descriptors = ("descriptors" in data[name])
				break
			data = None
		
		table = self.identifier + "objects"
		cursor.execute("SELECT * FROM \"%s\";" % (table,))
		rows = cursor.fetchall()
		if rows:
			data = {} # {id: object data, ...}
			for row in rows:
				data[row[0]] = json.loads(row[1])
			self.store.objects.from_dict_linked(data, self.identifier)
		
		# replace ids of objects in classes with the new ids
		for name in self.store.linked[self.identifier].classes:
			self.store.classes[name]._objects = [self.store.linked[self.identifier].object_lookup[id] for id in self.store.classes[name]._objects]
		
		resource_uris = self.store.local_resource_uris
		
		for id in data:
			for name in data[id]["descriptors"]:
				if (data[id]["descriptors"][name]["label"]["dtype"] == "DResource") and (not data[id]["descriptors"][name]["label"]["path"] is None):
					if not data[id]["descriptors"][name]["label"]["value"] in resource_uris:
						resource_uris.append(data[id]["descriptors"][name]["label"]["value"])
					if not data[id]["descriptors"][name]["label"]["value"] in self.store.linked[self.identifier].local_resource_uris:
						self.store.linked[self.identifier].local_resource_uris.append(data[id]["descriptors"][name]["label"]["value"])
		self.store.set_local_resource_uris(resource_uris)
		if not has_class_descriptors:  # TODO will be obsolete for new databases
			self.store.populate_descriptor_names()  # TODO will be obsolete for new databases
			self.store.populate_relation_names()  # TODO will be obsolete for new databases

		cursor.execute("SELECT * FROM \"%s\";" % (self.identifier + "local_folder",))
		for row in cursor.fetchall():
			self.store.linked[self.identifier].local_folder = json.loads(row[0])
			break
		
		self.store.images.load_thumbnails(root_folder = self.store.linked[self.identifier].local_folder)
		
		self.is_busy = False
		
		self.store.events.resume_recording()
		self.resume_broadcasts()
		self.broadcast(Broadcasts.STORE_LOADED)
		
		cursor.connection.close()
		
		return True

