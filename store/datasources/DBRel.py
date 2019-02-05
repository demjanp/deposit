'''

	Save Deposit database in form of a relational database
	
	Schema:
	
		Classes:
			table = [class name] or #classless
			columns:
				#obj_id (int)
				[descriptor name] = json(dlabel) or "" (text)
			

		Relations:
			table = #class1#relation#class2 or ##classless#relation#class2 (etc.)
			columns:
				source_id (int)
				target_id (int)

		Geotags:
			table = "#geotags"
			columns:
				obj_id (int)
				descriptor (text)
				geotag (text)

		Identifier:
			table = #identifier
			columns:
				url (text)

		Changed:
			table = #changed
			columns:
				timestamp (text)

		Local folder:
			table = #local_folder
			columns:
				path (text)
		
'''

from deposit import Broadcasts
from deposit.store.datasources.DB import (DB)
from deposit.store.DLabel.DLabel import (DLabel)
from deposit.store.DElements.DObjects import (DObject)

from collections import defaultdict
import json

class DBRel(DB):
	
	def __init__(self, store, connstr = None):
		
		DB.__init__(self, store, connstr = connstr)
	
	def is_valid(self):
		
		cursor, tables = self.connect()
		if cursor is None:
			return False
		
		cursor.connection.close()

		for name in ["#identifier", "#changed", "#local_folder", "#geotags"]:
			if not name in tables:
				return False
		
		return True
	
	def get_identifier(self):
		
		cursor, tables = self.connect()
		if cursor is None:
			return False
		
		identifier = None
		cursor.execute("SELECT * FROM \"%s\";" % ("#identifier",))
		for row in cursor.fetchall():
			identifier = json.loads(row[0])
			break
		
		cursor.connection.close()
		
		return identifier
	
	def save(self):
		
		if self.identifier is None:
			self.broadcast(Broadcasts.STORE_SAVE_FAILED)
			return False
		
		cursor, tables = self.connect()
		if cursor is None:
			self.broadcast(Broadcasts.STORE_SAVE_FAILED)
			return False
		
		for name in tables:
			cursor.execute("DROP TABLE \"%s\";" % (name))
		tables = []
		
		geotags = [] # [[obj_id, descr_name, geotag], ...]
		
		def save_class(class_name, descriptor_names, objects):
			
			table = class_name
			if descriptor_names:
				class_type = "\"#obj_id\" INTEGER, %s" % ", ".join([("\"%s\" TEXT" % descr_name) for descr_name in descriptor_names])
			else:
				class_type = "\"#obj_id\" INTEGER"
			columns = ", ".join([("\"%s\"" % descr_name) for descr_name in ["#obj_id"] + descriptor_names])
			cursor.execute("CREATE TABLE \"%s\" (%s);" % (table, class_type))
			data = [] # [{#obj_id: id, [descriptor_name]: json(label), ...}, ...]
			for obj in objects:
				row = {"#obj_id": obj.id}
				for descr_name in descriptor_names:
					if descr_name in obj.descriptors:
						row[descr_name] = json.dumps(obj.descriptors[descr_name].label.to_dict())
						if obj.descriptors[descr_name].geotag:
							geotags.append([obj.id, descr_name, json.dumps(geotag)])
					else:
						row[descr_name] = ""
				data.append(row)
			if data:
				cursor.execute("""
					DROP TYPE IF EXISTS class_;
					CREATE TYPE class_ as (%s);
					INSERT INTO \"%s\" SELECT %s FROM json_populate_recordset(null::class_, %%s);
				""" % (class_type, table, columns), (json.dumps(data),))
		
		for class_name in self.store.classes:
			cls = self.store.classes[class_name]
			save_class(class_name, cls.descriptors, [cls.objects[id] for id in cls.objects])
		
		class_name = "#classless"
		descriptor_names = []
		objects = []
		for id in self.store.objects:
			if not len(self.store.objects[id].classes):
				objects.append(self.store.objects[id])
				for descr_name in self.store.objects[id].descriptors:
					if not descr_name in descriptor_names:
						descriptor_names.append(descr_name)
		save_class(class_name, descriptor_names, objects)
		
		def get_classes(obj):
			
			if not len(obj.classes):
				return ["#classless"]
			return obj.classes.keys()
		
		data = defaultdict(list) # {#[src class]#[rel]#[tgt class]: [{source_id: id, target_id: id}, ...], ...}
		for cls1 in self.store.classes:
			for rel in self.store.classes[cls1].relations:
				for cls2 in self.store.classes[cls1].relations[rel]:
					table = "#%s#%s#%s" % (cls1, rel, cls2)
					data[table] = []
		for id1 in self.store.objects:
			obj1 = self.store.objects[id1]
			classes1 = get_classes(obj1)
			for rel in obj1.relations:
				if rel.startswith("~"):
					continue
				for id2 in obj1.relations[rel]:
					classes2 = get_classes(self.store.objects[id2])
					for cls1 in classes1:
						for cls2 in classes2:
							table = "#%s#%s#%s" % (cls1, rel, cls2)
							data[table].append({"source_id": id1, "target_id": id2})
		
		rel_type = "source_id INTEGER, target_id INTEGER"
		for table in data:
			cursor.execute("CREATE TABLE \"%s\" (%s);" % (table, rel_type))
			if data[table]:
				cursor.execute("""
					DROP TYPE IF EXISTS relation_;
					CREATE TYPE relation_ as (%s);
					INSERT INTO \"%s\" SELECT source_id, target_id FROM json_populate_recordset(null::relation_, %%s);
				""" % (rel_type, table), (json.dumps(data[table]),))
		
		table = "#geotags"
		geotag_type = "obj_id INTEGER, descriptor TEXT, geotag TEXT"
		cursor.execute("CREATE TABLE \"%s\" (%s);" % (table, geotag_type))
		data = []
		for obj_id, descr_name, geotag in geotags:
			data.append({"obj_id": obj_id, "descriptor": descr_name, "geotag": json.dumps(geotag)})
		if data:
			cursor.execute("""
				DROP TYPE IF EXISTS geotag_;
				CREATE TYPE geotag_ as (%s);
				INSERT INTO \"%s\" SELECT obj_id, descriptor, geotag FROM json_populate_recordset(null::geotag_, %%s);
			""" % (geotag_type, table), (json.dumps(data),))
		
		table = "#identifier"
		cursor.execute("CREATE TABLE \"%s\" (%s);" % (table, "uri TEXT"))
		cursor.execute("INSERT INTO \"%s\" VALUES ('%s');" % (table, json.dumps(self.identifier)))
		
		table = "#changed"
		cursor.execute("CREATE TABLE \"%s\" (%s);" % (table, "timestamp TEXT"))
		cursor.execute("INSERT INTO \"%s\" VALUES ('%s');" % (table, json.dumps(self.store.changed)))
		
		table = "#local_folder"
		cursor.execute("CREATE TABLE \"%s\" (%s);" % (table, "path TEXT"))
		if not self.store.local_folder is None:
			cursor.execute("INSERT INTO \"%s\" VALUES ('%s');" % (table, json.dumps(self.store.local_folder)))
		
		cursor.connection.commit()
		cursor.connection.close()
		
		self.broadcast(Broadcasts.STORE_SAVED)
		return True
	
	def load(self):
		
		cursor, tables = self.connect()
		if cursor is None:
			return False
		
		for name in ["#identifier", "#changed", "#local_folder", "#geotags"]:
			if not name in tables:
				return False
		
		self.stop_broadcasts()
		self.store.clear()
		
		cursor.execute("SELECT * FROM \"%s\";" % ("#identifier",))
		for row in cursor.fetchall():
			self.set_identifier(json.loads(row[0]))
			break
		
		cursor.execute("SELECT * FROM \"%s\";" % ("#changed",))
		for row in cursor.fetchall():
			self.store.changed = json.loads(row[0])
			break
		
		cursor.execute("SELECT * FROM \"%s\";" % ("#local_folder",))
		for row in cursor.fetchall():
			self.store.local_folder = json.loads(row[0])
			break
		
		# load classes
		for table in tables:
			if not table.startswith("#"):
				self.store.classes.add(table)
		
		resource_uris = []

		# load objects and their classes & descriptors
		for table in tables:
			if (not table.startswith("#")) or (table == "#classless"):
				cursor.execute("SELECT * FROM \"%s\";" % (table,))
				descr_names = [desc[0] for desc in cursor.description][1:]
				for descr in descr_names:
					self.store.classes[table].add_descriptor(descr)
				rows = cursor.fetchall()
				for row in rows:
					id = row[0]
					added = False
					if not id in self.store.objects:
						self.store.objects.add_naive(id, DObject(self.store.objects, id))
						added = True
					obj = self.store.objects[id]
					if table != "#classless":
						obj.classes.add(table)
					if added:
						for i in range(len(descr_names)):
							if row[i + 1] and (not descr_names[i] in obj.descriptors):
								data = json.loads(row[i + 1])
								label = DLabel("").asdtype(data["dtype"]).from_dict(data)
								obj.descriptors.add(descr_names[i], label)
								
								if (data["dtype"] == "DResource") and label.is_stored():
									if not label.value in resource_uris:
										resource_uris.append(label.value)
		
		# load relations
		for table in tables:
			if table.startswith("#") and not (table in ["#classless", "#identifier", "#changed", "#local_folder", "#geotags"]):
				if table.startswith("##classless#"):
					if table.endswith("##classless"): #  ##classless#rel##classless
						rel = table[12:].split("#")[0]
					else: #  ##classless#rel#cls
						rel, cls2 = table[12:].split("#")
				elif table.endswith("##classless"): #  #cls1#rel##classless
					_, cls1, rel = table[:-11].split("#")
					self.store.classes[cls1].add_relation(rel, "!*")
				else: #  #cls1#rel#cls2
					_, cls1, rel, cls2 = table.split("#")
					self.store.classes[cls1].add_relation(rel, cls2)
				cursor.execute("SELECT * FROM \"%s\";" % (table,))
				rows = cursor.fetchall()
				for row in rows:
					source_id, target_id = row
					self.store.objects[source_id].relations.add(rel, target_id)
		
		self.store.set_local_resource_uris(resource_uris)

		# load geotags
		table = "#geotags"
		cursor.execute("SELECT * FROM \"%s\";" % (table,))
		rows = cursor.fetchall()
		for row in rows:
			id, descr, geotag = row
			self.store.objects[id].descriptors[descr].geotag = json.loads(geotag)
		
		self.store.images.load_thumbnails()
		
		self.store.set_datasource(self)

		self.resume_broadcasts()
		self.broadcast(Broadcasts.STORE_LOADED)
		
		cursor.connection.close()
		
		return True