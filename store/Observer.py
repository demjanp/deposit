'''
	Deposit Store - Observer
	--------------------------
	
	Created on 14. 11. 2017
	
	@author: Peter Demjan <peter.demjan@gmail.com>
	
	accessible as store.observer
'''

from deposit.Query import (Query)
from deposit.DLabel import (DLabel, DString, DResource, DGeometry)
import os
import sys
import shutil
import hashlib
import psycopg2
import unicodedata

def get_dirs(path):
	# recursively get all subdirectories of path
	
	dirs = []
	for name in os.listdir(path):
		name = os.path.join(path, name)
		if os.path.isdir(name):
			dirs.append(os.path.abspath(name))
			dirs += get_dirs(name)
	return dirs

def hash_name(name):
	
	return hashlib.md5(str(name).encode("utf-8")).hexdigest()

def normalize_name(name):
	
	return unicodedata.normalize("NFKD", str(name).lower()).encode("ascii", "ignore").decode("ascii").replace(".", "_").replace(" ", "_")

def command(name):
	def register(func):
		func._command = name
		return func
	return register

class Observer(object):
	
	PARSABLE_EXTENSIONS = [".htm", ".html", ".php"]
	
	def __init__(self, store):
		
		self.__store = store
		
		super(Observer, self).__init__()
		
		self._commands = {} # {name: function, ...}
		self._path_resources = None
		self._cursor = None
		self._queries = {} # {query hash: table, ...}
		self._resources = {} # {filename: path, ...}
		self._existing_resources = {} # {filename: path, ...}
		
		for name in dir(self):
			func = getattr(self, name)
			if hasattr(func, "_command"):
				self._commands[func._command] = func
	
	def __getattr__(self, key):
		
		return getattr(self.__store, key)
	
	def _connect_database(self, connstr):
		
		try:
			conn = psycopg2.connect(connstr)
		except:
			print("\nObserver Error: Could not connect to database.", sys.exc_info())
			return False
		self._cursor = conn.cursor()
		return True
	
	def _commit_database(self):
		
		self._cursor.connection.commit()
	
	def _disconnect_database(self):
		
		if self._cursor:
			self._cursor.connection.close()
	
	def _clear_database(self):
		# drop all tables with name beginning with identifier of this database
		
		self._cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
		for row in self._cursor.fetchall():
			table = row[0]
			if table.startswith(self.identifier()):
				self._cursor.execute("DROP TABLE \"%s\";" % (table))
		self._cursor.connection.commit()
	
	def _load_existing_resources(self):
		
		if not os.path.isdir(self._path_resources):
			os.makedirs(self._path_resources)
		paths = get_dirs(self._path_resources)
		for path in paths:
			for filename in os.listdir(path):
				tgt_path = os.path.join(path, filename)
				self._existing_resources[filename] = tgt_path
	
	def _add_resource(self, path):
		# add resource to database
		
		filename = os.path.split(path)[1]
		if filename in self._resources:
			return self._resources[filename]
		if filename in self._existing_resources:
			self._resources[filename] = self._existing_resources[filename]
			tgt_path = self._resources[filename]
		else:
			tgt_path = os.path.join(self.file.get_new_dir(self._path_resources), filename)
			shutil.copyfile(path, tgt_path)
			self._resources[filename] = tgt_path
		return tgt_path
	
	def _remove_orphan_resources(self):
		# remove files and subdirectories not used in the Observer database from self._path_resources
		
		used = self._resources.values()
		paths = get_dirs(self._path_resources)
		for path in paths:
			for path_file in os.listdir(path):
				path_file = os.path.join(path, path_file)
				if not path_file in used:
					os.remove(path_file)
		for path in paths:
			if not len(os.listdir(path)):
				os.rmdir(path)
	
	def _parse(self, path_src, path_tgt, connstr):
		# parse the template file path_src and store it in path_tgt
		
		if not os.path.splitext(path_src)[1].lower() in self.PARSABLE_EXTENSIONS:
			shutil.copyfile(path_src, path_tgt)
			return
		
		# add database connect command to beginning of each file
		source_out = "<?php\n$db = pg_connect(\"%s\");\n?>\n" % (connstr)
		f_src = open(path_src, "r")
		source_in = f_src.read()
		f_src.close()
		
		# find and evaluate commands in format $[command]([argument], [argument])
		i = 0
		while True:
			i_last = i
			i = source_in.find("$", i)
			if i == -1:
				break
			j = source_in.find("(", i)
			found_command = False
			if (j > -1) and (not "$" in source_in[i+1:j]) and (j > i + 1):
				command = source_in[i+1:j]
				j += 1
				found_brackets = 1
				k = j
				while found_brackets and (k < len(source_in)):
					if source_in[k] == "(":
						found_brackets += 1
					elif source_in[k] == ")":
						found_brackets -= 1
					k += 1
				if found_brackets:
					k = -1
				else:
					k -= 1
				if k > -1:
					args = [arg.strip() for arg in source_in[j:k].split(",") if arg.strip() != ""]
					if command in self._commands:
						inject_str = None
						try:
							inject_str = self._commands[command](*args)
						except:
							print("Observer._parse command: %s args: %s" % (command, str(args).encode("ascii", "ignore")), sys.exc_info())
						if inject_str:
							source_out += source_in[i_last:i] + inject_str
							i_last = k + 1
							j = k + 1
				i = j
			if not found_command:
				source_out += source_in[i_last:i+1]
				i += 1
		if i_last < len(source_in):
			source_out += source_in[i_last:]
		
		# store parsed file in path_tgt
		f_tgt = open(path_tgt, "w")
		f_tgt.write(source_out)
		f_tgt.close()
	
	def _get_query_values(self, query):
		# helper functiom for query and foreach
		# return columns, values
		# columns = [column_name, ...]
		# values = [{column_name: value, ...}, ...]
		
		def _get_values(row, columns):
			
			values = {} # {column_name: value, ...}
			paths = {} # {column_name: path, ...}
			thumbnails = {} # {column_name: thumbnail_path, ...}
			objects3d = {} # {column_name: [path_material, path_texture], ...}
			for name, id in columns:
				if isinstance(row[id], DResource):
					path, filename, storage_type = self.resources.get_path(row[id].label)
					if self.resources.is_image(row[id].label):
						thumbnails[name] = self._add_resource(self.resources.thumbnail(row[id].label, 256, storage_type)[3])
					elif self.resources.is_3d(row[id].label):
						objects3d[name] = self.resources.material_3d(row[id].label)
						for path2 in objects3d[name]:
							if not path2 is None:
								self._add_resource(path2)
					paths[name] = self._add_resource(path)
					values[name] = filename
				else:
					values[name] = row[id].value
			return values, paths, thumbnails, objects3d
		
		columns = [] # [[column_name, cls_descr_id], ...]
		values = [] # [{column_name: value, ...}, ...]
		qry = Query(self.__store, query)
		if qry.columns:
			for cls_descr_id, label in qry.columns:
				columns.append([label.value, cls_descr_id])
			parent_dir = os.path.split(os.path.split(self._path_resources)[0])[0]
			columns_new = []
			cmax = len(qry.objects)
			c = 1
			for obj_id in qry:
				print("\rQuery: %s, %d/%d              " % (query, c, cmax), end = "")
				c += 1
				values.append({})
				values[-1], paths, thumbnails, objects3d = _get_values(qry[obj_id], columns)
				if paths:
					for column_name in paths:
						name_path = "%s.path" % (column_name)
						if not name_path in columns_new:
							columns_new.append(name_path)
						values[-1][name_path] = paths[column_name][len(parent_dir):].replace("\\","/")
				if thumbnails:
					for column_name in thumbnails:
						name_path = "%s.thumbnail" % (column_name)
						if not name_path in columns_new:
							columns_new.append(name_path)
						values[-1][name_path] = thumbnails[column_name][len(parent_dir):].replace("\\","/")
				if objects3d:
					for column_name in objects3d:
						path_material, path_texture = objects3d[column_name]
						for path, name in [[path_material, "material"], [path_texture, "texture"]]:
							if not path is None:
								name_path = "%s.%s" % (column_name, name)
								if not name_path in columns_new:
									columns_new.append(name_path)
								values[-1][name_path] = path[len(parent_dir):].replace("\\","/")
						
			columns = [column[0] for column in columns] + columns_new
		return columns, values
	
	def _fill_table(self, table, columns, values):
		# helper functiom for query and foreach
		# columns =[column_name, ...]
		# values = [{column_name: value, ...}, ...]
		
		self._cursor.execute("CREATE TABLE \"%s\" (%s);" % (table, ",".join(["\"%s\" TEXT" % column for column in columns])))
		for row in values:
			self._cursor.execute("INSERT INTO \"%s\" VALUES (%s)" % (table, ",".join(["%s"] * len(columns))), [(row[column] if (column in row) else "") for column in columns])
	
	def _get_query_code(self, table, columns):
		# helper functiom for query and foreach
		# columns = [column_name, ...]
		
		if table:
			return "pg_fetch_all(pg_query($db, 'SELECT %s FROM \"%s\";'))" % (", ".join([("\"%s\"" % (column)) for column in columns]), table)
		else:
			return "array()"
		
	def make(self, path_templates, path_observer, connstr):
		# compile an observer interface & database based on templates in path_templates and store it in path_observer & connstr
		
		self._path_resources = None
		self._cursor = None
		self._queries = {} # {query: [table, columns], ...}
		self._resources = {} # {filename: path, ...}
		self._existing_resources = {} # {filename: path, ...}
		
		if not self._connect_database(connstr):
			return
		
		path_templates = os.path.normpath(os.path.abspath(path_templates))
		path_observer = os.path.normpath(os.path.abspath(path_observer))
		self._path_resources = os.path.normpath(os.path.join(path_observer, "resources"))
		
		# clear database
		self._clear_database()
		
		# collect existing resources
		self._load_existing_resources()
		
		# check if self._path_resources is not present in path_templates
		if os.path.isdir(os.path.join(path_templates, "resources")):
			print("\nObserver Error: Path named 'resources' cannot be present in template directory.")
			return
		
		# iterate over all directories and files in path_templates & store parsed files in path_observer
		if not os.path.isdir(path_observer):
			os.makedirs(path_observer)
		if not os.path.isdir(self._path_resources):
			os.makedirs(self._path_resources)
		for filename in os.listdir(path_templates):
			path_src_filename = os.path.join(path_templates, filename)
			if os.path.isfile(path_src_filename):
				self._parse(path_src_filename, os.path.join(path_observer, filename), connstr)
		paths = get_dirs(path_templates)
		for path_src in paths:
			path_tgt = os.path.normpath(os.path.join(path_observer, path_src[len(path_templates) + 1:]))
			# if path already exists in path_observer, remove & re-create it
			if os.path.isdir(path_tgt):
				shutil.rmtree(path_tgt)
			os.makedirs(path_tgt)
			for filename in os.listdir(path_src):
				path_src_filename = os.path.join(path_src, filename)
				if os.path.isfile(path_src_filename):
					self._parse(path_src_filename, os.path.join(path_tgt, filename), connstr)
		
		# save changes in Observer database & disconnect
		self._commit_database()
		self._disconnect_database()
		
		self._remove_orphan_resources()
	
	@command("IDENT")
	def ident(self):
		
		return self.identifier().strip("#").split("/")[-1]
	
	@command("QUERY")
	def query(self, query):
		
		table = None
		query_hash = hash_name(query)
		if query_hash in self._queries:
			table, columns = self._queries[query_hash]
		else:
			columns, values = self._get_query_values(query)
			if columns and values:
				table = self.identifier() + normalize_name(query)
				self._queries[query_hash] = [table, columns]
				self._fill_table(table, columns, values)
		return self._get_query_code(table, columns)

	@command("FOREACH")
	def foreach(self, query_for, query_each):
		# $FOREACH(C.R.C.D, $obj().R.C.D)
		
		table = None
		query_hash = hash_name("_".join([query_for, query_each]))
		if query_hash in self._queries:
			table, columns_each = self._queries[query_hash]
		else:
			qry_for = Query(self.__store, query_for)
			if qry_for.objects:
				parent_dir = os.path.split(os.path.split(self._path_resources)[0])[0]
				table = self.identifier() + normalize_name("_".join([query_for, query_each]))
				
				columns_each = [] # [column_name, ...]
				values_each = [] # [{column_name: value, ...}, ...]
				
				# get columns from qry_for
				columns_for = [] # columns of query_for
				for cls_descr_id, label in qry_for.columns:
					columns_for.append([label.value + ".parent", cls_descr_id])
					columns_each.append(columns_for[-1][0])
				
				for obj_id in qry_for.objects:
					columns, values = self._get_query_values(query_each.replace("$obj()", "obj(%s)" % (obj_id[4:])))
					# add values from query_for
					if values:
						# add values from query_each
						for column in columns:
							if not column in columns_each:
								columns_each.append(column)
								for i in range(len(values_each)):
									values_each[i][column] = ""
						for column in columns_each:
							if not column in columns:
								for i in range(len(values)):
									values[i][column] = ""
						
						for name, cls_descr_id in columns_for:
							for i in range(len(values)):
								values[i][name] = qry_for[obj_id][cls_descr_id].value
						
					values_each += values
				
				self._queries[query_hash] = [table, columns_each]
				self._fill_table(table, columns_each, values_each)
		return self._get_query_code(table, columns_each)		
		