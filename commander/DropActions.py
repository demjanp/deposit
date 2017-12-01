from deposit import (DB, Store)
from deposit.File import file_from_db
from deposit.DLabel import (DGeometry)
from PyQt5 import (QtWidgets, QtCore)
from urllib.parse import urlparse
import os

class PrototypeAction(object):
	
	def __init__(self, model, view, parent, source_data, target_data, event, relation = None):
		'''
			model = MainWindowModel
			view = MainWindowView
			event = drop event
			parent = name of parent class
			source_data / target_data = dict(
				obj_id = obj_id,
				row = row,
				column = column,
				cls_id = cls_id,
				rel_id = rel_id,
				value = value,
				field = external table field,
				target = external table target,
				read_only = True/False,
				image = True/False
				geometry = True/False
				obj_id2 = obj_id (related),
				rel_label = label,
				reversed = True/False,
				parent_class = cls_id
				coords = [[x, y], ...]
				path = path
				filename = filename
			)
			relation = set to avoid prompting for Relation label
		'''
		
		self._model = model
		self._view = view
		self._parent = parent
		self._source_data = source_data
		self._target_data = target_data
		self._event = event
		self._relation = relation # [label, reversed]; set if a Relation was created
		
		self.exec()
	
	def _get_class_names(self):
		
		return [self._model.store.get_label(cls_id).value for cls_id in self._model.store.classes.get()]
	
	def relation(self):
		# return [label, reversed]
		
		return self._relation
	
	def exec(self):
		
		pass

class ADD_CLASS(PrototypeAction):
	def exec(self):
		
		values = self._view.get_values("Add Class", ("name", "Name:"))
		if values and values["name"]:
			self._model.store.classes.add(values["name"])

class ADD_DESCRIPTOR(PrototypeAction):
	
	def exec(self):
		
		label, name = None, None
		show_dialog = False
		last = self._model.last_descriptor()
		if "rel_id" in self._source_data:
			label = self._model.store.get_label(self._source_data["rel_id"])
		elif "coords" in self._source_data:
			srid = self._source_data["srid"] if ("srid" in self._source_data) else -1
			label = DGeometry(self._source_data["coords"], srid = srid)
		elif "value" in self._source_data:
			label = self._source_data["value"]
		
		if "cls_id" in self._target_data:
			name = self._model.store.get_label(self._target_data["cls_id"]).value
		elif "cls_id" in self._source_data:
			name = self._model.store.get_label(self._source_data["cls_id"]).value
		elif ("target" in self._source_data) and self._source_data["target"] and not (("." in self._source_data["target"]) or ("#" in self._source_data["target"])):
			name = self._source_data["target"]
			show_dialog = True
		
		if (label is None) or (name is None) or show_dialog:
			names = self._get_class_names()
			if not name is None:
				names = [name] + [val for val in names if val != name]
			elif not last is None:
				names = [last] + [name for name in names if name != last]
			else:
				names = [""] + names
			if label is None:
				values = self._view.get_values("Add Descriptor", ("name", ["Name:", names]), ("label", "Label:"))
				if values and values["name"] and values["label"]:
					name = values["name"]
					label = values["label"]
			else:
				values = self._view.get_values("Add Descriptor", ("name", ["Name:", names]))
				if values and values["name"]:
					name = values["name"]
		if not ((label is None) or (name is None)):
			self._model.actions.add_descriptor(name, self._target_data["obj_id"], label)
			self._model.set_last_descriptor(name)

class ADD_GEOTAG(PrototypeAction):
	
	def exec(self):
		
		last = self._model.last_descriptor()
		if "obj_id" in self._source_data:
			obj_id = self._source_data["obj_id"]
		else:
			obj_id = self._model.store.objects.add()
		
		names = self._get_class_names()
		if not last is None:
			names = [last] + [name for name in names if name != last]
		else:
			names = [""] + names
		values = self._view.get_values("Add Geotag", ("name", ["Name:", names]))
		if values and values["name"]:
			if "coords" in self._target_data:
				coords = self._target_data["coords"]
			else:
				pos = self._event.pos()
				coords = [[pos.x(), pos.y()]]
			self._model.actions.add_geotag(values["name"], obj_id, self._target_data["value"], coords)
			self._model.set_last_descriptor(values["name"])

class ADD_RELATION(PrototypeAction):
	
	def exec(self):
		
		values = {}
		if (not "parent_class" in self._target_data) and (not "obj_id2" in self._target_data) and ("rel_label" in self._target_data) and ("obj_id" in self._target_data) and ("reversed" in self._target_data):
			values["label"] = self._target_data["rel_label"]
			values["reversed"] = self._target_data["reversed"]
		elif self._relation is None:
			labels = self._model.store.relations.get_labels().tolist()
			last = self._model.last_relation()
			if not last is None:
				labels = [last] + [label for label in labels if label != last]
			values = self._view.get_values("Add Relation", ("label", ["Label:", labels]), ("reversed", ["Reversed:", False]))
		else:
			values["label"], values["reversed"] = self._relation
		if values and values["label"]:
			if "obj_id" in self._source_data:
				src_obj_id = self._source_data["obj_id"]
			else:
				src_obj_id = self._model.store.objects.add()
			if "obj_id" in self._target_data:
				tgt_obj_id = self._target_data["obj_id"]
			else:
				tgt_obj_id = self._target_data["obj_id2"]
			if src_obj_id != tgt_obj_id:
				if values["reversed"]:
					src_obj_id, tgt_obj_id = tgt_obj_id, src_obj_id
				self._model.store.relations.add(src_obj_id, tgt_obj_id, values["label"])
				self._model.set_last_relation(values["label"])
				self._relation = values["label"], values["reversed"]

class ADD_RESOURCE(PrototypeAction):
	
	def exec(self):
		
		name = None
		local = self._model.local_resources()
		if "cls_id" in self._target_data:
			name = self._model.store.get_label(self._target_data["cls_id"]).value
		if (name is None) or (local is None):
			names = self._get_class_names()
			if not name is None:
				names = [name] + [val for val in names if val != name]
			else:
				names = [""] + names
			values = self._view.get_values("Add Descriptor", ("name", ["Name:", names]), ("local", ["Save local:", local == True]))
			if values and values["name"]:
				name = values["name"]
				local = values["local"]
			else:
				name = None
				local = None
		if not name is None:
			self._model.actions.add_resource(name, self._target_data["obj_id"], self._source_data["value"], local)

class SET_CLASS_MEMBER(PrototypeAction):
	
	def exec(self):
		
		id_src, id_tgt = None, None
		if self._parent in ["ClassList", "ClassLabel"]:
			if "cls_id" in self._target_data: # target is ClassList
				id_src = self._target_data["cls_id"]
				id_tgt = self._source_data["cls_id"]
			else: # target is ClassesFrame
				id_src = self._source_data["cls_id"]
				id_tgt = self._target_data["obj_id"]
		elif self._parent == "MdiClass":
			values = self._view.get_values("Add Class", ("name", "Name:"))
			if values and values["name"]:
				cls_id = self._model.store.classes.add(values["name"])
				if "cls_id" in self._target_data: # target is ClassList
					id_src = self._target_data["cls_id"]
					id_tgt = cls_id # target is ClassesFrame
				else: 
					id_src = cls_id
					id_tgt = self._target_data["obj_id"]
		elif self._parent in ["QueryLstView", "QueryImgView", "ObjectLabel", "MdiObject"]:
			if "obj_id" in self._source_data:
				id_tgt = self._source_data["obj_id"]
			else:
				id_tgt = self._model.store.objects.add()
			if ("parent_class" in self._target_data) and (not "cls_id" in self._target_data): # target is QueryLstView
				id_src = self._target_data["parent_class"]
			else: # target is ClassList
				id_src = self._target_data["cls_id"]
		if (not id_src is None) and (not id_tgt is None) and (id_src != id_tgt) and (id_src != "!*"):
			self._model.store.members.add(id_src, id_tgt)

class SET_CLASS_MEMBER_ADD_RELATION(PrototypeAction):
	
	def exec(self):
		label = self._target_data["rel_label"]
		cls_id = self._target_data["parent_class"]
		if "obj_id" in self._source_data:
			src_obj_id = self._source_data["obj_id"]
		else:
			src_obj_id = self._model.store.objects.add()
		if "obj_id" in self._target_data:
			tgt_obj_id = self._target_data["obj_id"]
		else:
			tgt_obj_id = self._target_data["obj_id2"]
		if src_obj_id != tgt_obj_id:
			self._model.store.members.add(cls_id, src_obj_id)
			if ("reversed" in self._target_data) and self._target_data["reversed"]:
				src_obj_id, tgt_obj_id = tgt_obj_id, src_obj_id
			self._model.store.relations.add(src_obj_id, tgt_obj_id, label)

class DELETE_CLASS_MEMBER(PrototypeAction):
	def exec(self):
		if self._parent == "ClassList":
			self._model.store.members.remove(self._source_data["parent_class"], self._source_data["cls_id"])
		elif self._parent == "ClassLabel":
			self._model.store.members.remove(self._source_data["cls_id"], self._source_data["obj_id"])

class DELETE_CLASS(PrototypeAction):
	def exec(self):
		self._model.store.classes.remove(self._source_data["cls_id"])

class DELETE_DESCRIPTOR(PrototypeAction):
	def exec(self):
		self._model.store.relations.remove(self._source_data["rel_id"])

class DELETE_OBJECT(PrototypeAction):
	def exec(self):
		self._model.store.objects.remove(self._source_data["obj_id"])

class DELETE_RELATION(PrototypeAction):
	def exec(self):
		self._model.actions.delete_relation(self._source_data["obj_id"], self._source_data["rel_label"], self._source_data["obj_id2"], self._source_data["reversed"])

class OPEN_CLASS(PrototypeAction):
	def exec(self):
		cls_id = None
		if "cls_id" in self._source_data:
			cls_id = self._source_data["cls_id"]
		else:
			values = self._view.get_values("Add Class", ("name", "Name:"))
			if values and values["name"]:
				cls_id = self._model.store.classes.add(values["name"])
		if not cls_id is None:
			self._view.open_class(cls_id)

class OPEN_DESCRIPTOR(PrototypeAction):
	def exec(self):
		self._view.open_descriptor(self._source_data["obj_id"], self._source_data["rel_id"])

class OPEN_OBJECT(PrototypeAction):
	def exec(self):
		if "obj_id" in self._source_data:
			obj_id = self._source_data["obj_id"]
		else:
			obj_id = self._model.store.objects.add()
		self._view.open_object(obj_id)

class OPEN_EXTERNAL(PrototypeAction):
	
	def exec(self):
		
		if self._model.store.file.shapefiles.is_shapefile(self._source_data["value"]):
			self._view.open_shapefile(self._source_data["value"])
		elif self._model.store.file.xlsx.is_xlsx(self._source_data["value"]):
			self._view.open_xlsx(self._source_data["value"])

class OPEN_DATABASE(PrototypeAction):
	
	def exec(self):
		
		db = None
		scheme = urlparse(self._source_data["value"]).scheme
		if scheme in ["http", "https"]:
			db = DB(self._source_data["value"])
		elif scheme == "file":
			ident = os.path.splitext(self._source_data["value"])[0] + "#"
			db = DB(ident)
		if not db is None:
			if self._model.has_store() and (db.check_out_source == self._model.store.identifier()):
				reply = QtWidgets.QMessageBox.question(self._view, "Check In", "Check In database?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.Yes)
				if reply == QtWidgets.QMessageBox.Yes:
					self._model.actions.check_in(ident)
					return
			self._model.set_store(Store(db))

class OPEN_REMOTE(PrototypeAction):
	
	def exec(self):
		
		scheme = urlparse(self._source_data["value"]).scheme
		if scheme in ["http", "https"]:
			db = DB(self._source_data["value"])
			self._model.store.connect_remote(db, Store(db).file)
		elif scheme == "file":
			ident = os.path.splitext(self._source_data["value"])[0] + "#"
			db = DB(ident)
			self._model.store.connect_remote(db, Store(db).file)

class DropActions(object):
	
	ADD_CLASS = ADD_CLASS
	ADD_DESCRIPTOR = ADD_DESCRIPTOR
	ADD_GEOTAG = ADD_GEOTAG
	ADD_RELATION = ADD_RELATION
	ADD_RESOURCE = ADD_RESOURCE
	SET_CLASS_MEMBER = SET_CLASS_MEMBER
	SET_CLASS_MEMBER_ADD_RELATION = SET_CLASS_MEMBER_ADD_RELATION
	DELETE_CLASS_MEMBER = DELETE_CLASS_MEMBER
	DELETE_CLASS = DELETE_CLASS
	DELETE_DESCRIPTOR = DELETE_DESCRIPTOR
	DELETE_OBJECT = DELETE_OBJECT
	DELETE_RELATION = DELETE_RELATION
	OPEN_CLASS = OPEN_CLASS
	OPEN_DESCRIPTOR = OPEN_DESCRIPTOR
	OPEN_OBJECT = OPEN_OBJECT
	OPEN_EXTERNAL = OPEN_EXTERNAL
	OPEN_REMOTE = OPEN_REMOTE
	OPEN_DATABASE = OPEN_DATABASE

