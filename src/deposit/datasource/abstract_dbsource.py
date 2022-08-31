from deposit import __version__
from deposit.datasource.abstract_datasource import AbstractDatasource
from deposit.store.abstract_delement import AbstractDElement

from deposit.utils.fnc_serialize import (
	parse_connstr, legacy_data_to_store, json_data_to_store, GRAPH_ATTRS
)
from deposit.utils.fnc_files import (sanitize_filename)

from collections import defaultdict
from natsort import natsorted
import datetime, time
import psycopg2
import sys
import os

class AbstractDBSource(AbstractDatasource):
	
	def __init__(self):
		
		AbstractDatasource.__init__(self)
		
		self._username = None
		self._password = None
		self._host = None
		self._database = None
		self._schema = None
		self._identifier = None
		self._local_folder = None
		
		self._cursor = None
		self._tables = []  # [tablename, ...]
		self._schemas = []  # [schemaname, ...]
	
	def get_name(self):
		
		if self._identifier is not None:
			return self._identifier
		return "data"
	
	def to_dict(self):
		
		data = AbstractDatasource.to_dict(self)
		data["identifier"] = self.get_identifier()
		data["connstr"] = self.get_connstr()
		
		return data
	
	def get_username(self):
		
		return self._username
	
	def get_password(self):
		
		return self._password
	
	def get_host(self):
		
		return self._host
	
	def get_database(self):
		
		return self._database
	
	def get_schema(self):
		
		return self._schema
	
	def get_identifier(self):
		
		return self._identifier
	
	def get_connstr(self):
		
		username = self.get_username()
		password = self.get_password()
		host = self.get_host()
		database = self.get_database()
		schema = self.get_schema()
		if None in [username, password, host, database, schema]:
			return None
		
		return "postgres://%s:%s@%s/%s?currentSchema=%s" % (username, password, host, database, schema)
	
	def get_folder(self):
		
		return None
	
	def get_local_folder(self):
		
		return self._local_folder

	def get_cursor(self):
		
		if self._cursor is None:
			self.connect()
		return self._cursor
	
	def get_schemas(self):
		
		return self._schemas
	
	def get_tables(self):
		
		was_connected = self.is_connected()
		cursor = self.get_cursor()
		
		if (not self._tables) and (cursor):
			schema = self.get_schema()
			if schema in self._schemas:
				cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = '%s';" % (schema))
				self._tables = natsorted([row[0] for row in cursor.fetchall()])
		if not was_connected:
			self.disconnect()
		return self._tables
	
	def set_username(self, value):
		
		self._username = value
	
	def set_password(self, value):
		
		self._password = value
	
	def set_host(self, value):
		
		self._host = value
	
	def set_database(self, value):
		
		self._database = value
	
	def set_schema(self, value):
		
		self._schema = value
	
	def set_identifier(self, value):
		
		self._identifier = value
	
	def set_connstr(self, value):
		
		parsed = parse_connstr(value)
		if not parsed:
			return
		self.set_username(parsed["username"])
		self.set_password(parsed["password"])
		self.set_host(parsed["host"])
		self.set_database(parsed["dbname"])
		self.set_schema(parsed["schema"])
	
	def connect(self):
		
		if self._cursor is not None:
			self._cursor.connection.close()
		self._cursor = None
		self._tables = []
		self._schemas = []
		
		dbname = self.get_database()
		user = self.get_username()
		password = self.get_password()
		host = self.get_host()
		port = 5432
		if None in [dbname, user, password, host]:
			return False
		if ":" in host:
			host, port = host.split(":")
			if not port.isdigit():
				return False
			port = int(port)
		
		try:
			conn = psycopg2.connect(
				dbname = dbname,
				user = user,
				password = password,
				host = host,
				port = port,
			)
		except:
			_, exc_value, _ = sys.exc_info()
			print("Connection Error: %s" % (str(exc_value)))
			return False
		self._cursor = conn.cursor()
		if self._cursor is not None:
			self._cursor.execute("SELECT schema_name FROM information_schema.schemata")
			self._schemas = natsorted([row[0] for row in self._cursor.fetchall()])
		
		return True
	
	def disconnect(self):
		
		if self._cursor is not None:
			conn = self._cursor.connection
			self._cursor.close()
			conn.close()
			self._cursor = None
	
	def is_connected(self):
		
		if (self._cursor is None) or self._cursor.closed:
			return False
		return True
	
	def is_valid(self):
		
		return False
	
	def can_create(self):
		
		was_connected = self.is_connected()
		cursor = self.get_cursor()
		
		ret = (cursor is not None)
		
		if not was_connected:
			self.disconnect()
		return ret
	
	def create(self):
		
		was_connected = self.is_connected()
		cursor = self.get_cursor()
		
		schema = self.get_schema()
		if schema:
			cursor.execute("CREATE SCHEMA IF NOT EXISTS %s" % (schema))
			cursor.connection.commit()
			ret = True
		else:
			ret = False
		
		if not was_connected:
			self.disconnect()
		
		return ret
	
	def delete(self):
		
		return False
	
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
		
		pass
	
	def backup(self, store, folder):
		
		name = sanitize_filename(self.get_name())
		tgt_file = "%s_%s" % (
			name,
			datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d'),
		)
		ext = ".pickle"
		n = 1
		while True:
			tgt_path = os.path.join(folder, "%s_%d%s" % (tgt_file, n, ext))
			if not os.path.isfile(tgt_path):
				break
			n += 1
		do_backup = store._do_backup
		store._do_backup = False
		store.save(path = tgt_path)
		store._do_backup = do_backup
	
	def save(self, store, progress = None, identifier = None, connstr = None, *args, **kwargs):
		
		def delements_to_dict(data):
			
			for node_data in data["nodes"]:
				if isinstance(node_data["data"], AbstractDElement):
					node_data["data"] = node_data["data"].to_dict()
		
		self.set_progress(progress)
		
		if not store.has_local_folder():
			return False
		
		if identifier is not None:
			self.set_identifier(identifier)
		if connstr is not None:
			self.set_connstr(connstr)
		if not self.can_create():
			return False
		self.create()
		
		self._local_folder = store._local_folder
		
		db_meta = dict(
			deposit_version = __version__,
			local_folder = store._local_folder,
			max_order = store._max_order,
		)
		
		data = store.G.objects_to_json(GRAPH_ATTRS)
		delements_to_dict(data)
		object_nodes = data["nodes"]  # [{id: int, data: dict()}, ...]
		object_relations = data[GRAPH_ATTRS["link"]]  # [{src: int, tgt: int, lbl: str}, ...]
		
		data = store.G.classes_to_json(GRAPH_ATTRS)
		delements_to_dict(data)
		class_nodes = data["nodes"]  # [{id: str, data: dict()}, ...]
		class_relations = data[GRAPH_ATTRS["link"]]  # [{src: str, tgt: str, lbl: str}, ...]
		
		data = store.G.members_to_json(GRAPH_ATTRS)
		member_nodes = data["nodes"]  # [{id: int/str}, ...]
		member_relations = data[GRAPH_ATTRS["link"]]  # [{src: int/str, tgt: int/str}, ...]
		
		user_tools = store._user_tools  # [dict(), ...]
		
		queries = store._queries  # {name: querystr, ...}
		
		return self.save_data(
			db_meta,
			object_nodes, object_relations, 
			class_nodes, class_relations, 
			member_nodes, member_relations, 
			user_tools, queries, 
			progress
		)
	
	def load_data(self, progress = None):
		# returns data or legacy_data
		# data = dict(
		#	object_relation_graph = nx.node_link_data
		#	class_relation_graph = nx.node_link_data
		#	class_membership_graph = nx.node_link_data
		#	local_folder = str
		#	max_order = int
		#	user_tools = list
		#	queries = dict()
		#	deposit_version = str
		# )
		#
		# legacy_data = dict(
		#	classes = dict()
		#	objects = dict()
		#	user_tools = list
		#	queries = dict()
		#	local_folder = str
		# )
		
		return {}
		
	def load(self, store, progress = None, identifier = None, connstr = None, *args, **kwargs):
		
		self.set_progress(progress)
		
		if identifier is not None:
			self.set_identifier(identifier)
		if connstr is not None:
			self.set_connstr(connstr)
		if not self.is_valid():
			return False
		
		data = self.load_data(progress)  # DEBUG
#		try:
#			data = self.load_data(progress)
#		except:
#			print("LOAD ERROR: %s" % (str(sys.exc_info())))  # DEBUG
#			return False
		
		if "classes" in data:
			local_folder = data["local_folder"]
			if not legacy_data_to_store(data, store, local_folder, progress = self._progress):
				print("LOAD ERROR: Invalid legacy file format")  # DEBUG
				return False
		else:	
			if not json_data_to_store(data, store, self._progress):
				print("LOAD ERROR: Loading data")  # DEBUG
				return False
		
		store.set_datasource(self)
		
		return True
	
	def __str__(self):
		
		return "%s (%s)" % (self.__class__.__name__, str(self.get_identifier()))

