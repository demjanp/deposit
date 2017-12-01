from deposit.commander.plugins.PrototypePluginModel import PrototypePluginModel
from deposit import (Query)
import numpy as np

class PrototypeFormModel(PrototypePluginModel):
	
	def __init__(self, parent_model):
		
		super(PrototypeFormModel, self).__init__(parent_model)
	
	def get_class_id(self, name, create = False):
		
		if create:
			return self._parent_model.store.classes.add(name)
		return self._parent_model.store.queryfnc.get_class_by_label(name)
	
	def get_descr_id(self, descr_name):
		# get cls_id for Descriptor name (or create new)
		
		cls_id = self._parent_model.store.classes.add(descr_name)
		super_id = self._parent_model.store.classes.add(descr_name.split("_")[0])
		self._parent_model.store.members.add(super_id, cls_id)
		return cls_id
	
	def get_obj_id_by_id(self, id, class_name):
		
		res = self._parent_model.query("%s.Id == \"%s\"" % (class_name, id)).keys()
		if res:
			return res[0]
		return None
	
	def get_related(self, obj_id, relation):
		
		ret = [] # [[obj_id, Id, rel, cls], ...]
		if not obj_id is None:
			id_descr_name = "Id"
			elements = relation.split(".")
			if len(elements) % 2 == 1:
				id_descr_name = elements.pop()
			elements = elements[::-1]
			for i in range(len(elements)):
				if i % 2 == 1:
					if elements[i].startswith("~"):
						elements[i] = elements[i][1:]
					else:
						elements[i] = "~" + elements[i]
			qry = "%s.obj(%s) and %s.%s" % (".".join(elements), obj_id[4:], elements[0], id_descr_name)
			qry = Query(self._parent_model.store, qry)
			for obj_id2 in qry:
				id, = qry[obj_id2].values()
				ret.append([obj_id2, id.value, elements[-1], elements[-2]])
		return ret
	
	def get_images(self, obj_id, descr_name):
		
		ret = [] # [[thumbnail_path, orig_path, filename, rel_id, cls_id], ...]
		photo_cls = {} # {descr_name: cls_id, ...}
		if not obj_id is None:
			cls_id = self._parent_model.store.queryfnc.get_class_by_label(descr_name)
			query = []
			for cls_id2 in self._parent_model.store.members.get_subclasses(cls_id):
				name = self._parent_model.store.get_label(cls_id2).value
				photo_cls[name] = cls_id2
				query.append("obj(%s).%s" % (obj_id[4:], name))
			query = " or ".join(query)
			qry = Query(self._parent_model.store, query)
			if qry.objects:
				n = 1
				while True:
					name = "%s_%d" % (descr_name, n)
					if (name in photo_cls) and (photo_cls[name] in qry[obj_id]):
						label = qry[obj_id][photo_cls[name]]
						path, filename, storage_type, thumbnail_path = self._parent_model.store.resources.thumbnail(label.label, 256)
						ret.append([thumbnail_path, path, filename, label.relation, photo_cls[name]])
					elif not name in photo_cls:
						break
					n += 1
		return ret
	
	def is_member(self, obj_id, cls_id):
		
		return self._parent_model.store.members.is_member(obj_id, cls_id)
	
	def get_value(self, obj_id, query):
		
		if not obj_id is None:
			query1 = "obj(%s).%s" % (obj_id[4:], query)
			res = self._parent_model.query(query1).values()
			if res:
				return list(res[0].values())[0].value
		return ""
	
	def get_values(self, cls_id, obj_id, query):
		
		query1 = "%s.%s" % (self._parent_model.store.get_label(cls_id).value, query)
		res = self._parent_model.query(query1).values()
		values = [list(row.values())[0].value for row in res]
		values = sorted(np.unique(values).tolist())
		value = self.get_value(obj_id, query)
		return [value] + [val for val in values if val != value]
	
	def import_data(self, data, fields, targets, merges):
		
		self._parent_model.actions.import_data(data, fields, targets, merges, overwrite = True)
	
	def is_url_image(self, url):
		
		return self._parent_model.store.resources.is_external_image(url)
	
	def delete_image(self, rel_id):
		
		self._parent_model.store.relations.remove(rel_id)
	
	def delete_relations(self, relations):
		# relations = [[obj_id, rel, cls], ...]
		
		self._parent_model.store.begin_change()
		for obj_id, rel, cls in relations:
			neg_rel = rel.startswith("!")
			rel = rel.strip("!")
			rev = rel.startswith("~")
			rel = rel.strip("~")
			neg_cls = cls.startswith("!")
			cls = cls.strip("!")
			cls_id = self._parent_model.store.queryfnc.get_class_by_label(cls)
			obj_ids2 = self._parent_model.store.queryfnc.get_related(obj_id, rel, [cls_id], not rev, neg_rel, neg_cls)
			for obj_id2 in obj_ids2:
				rel_id = self._parent_model.store.queryfnc.get_related_by_label(obj_id, rel, obj_id2, not rev)
				self._parent_model.store.relations.remove(rel_id)
		self._parent_model.store.end_change()
	
	