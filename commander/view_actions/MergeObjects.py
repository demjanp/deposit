from deposit.commander.QueryLstView import QueryLstView
from PyQt5 import (QtWidgets)

def get_state(model, view):
	
	active = view.active()
	if isinstance(active, QueryLstView):
		selected = active.selected()
		obj_ids = []
		for data in selected:
			if (not "obj_id2" in data["data"]) and (not data["data"]["obj_id"] in obj_ids):
				obj_ids.append(data["data"]["obj_id"])
		return (len(obj_ids) > 1), False
	return False, False

def triggered(model, view, checked):
	
	active = view.active()
	selected = active.selected()
	obj_ids = []
	for data in selected:
		if (not "obj_id2" in data["data"]) and (not data["data"]["obj_id"] in obj_ids):
			obj_ids.append(data["data"]["obj_id"])
	if len(obj_ids) > 1:
		reply = QtWidgets.QMessageBox.question(view, "Merge Objects?", "Merge %d selected Objects?" % (len(obj_ids)), QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.Yes)
		if reply == QtWidgets.QMessageBox.Yes:
			model.store.begin_change()
			while len(obj_ids) > 1:
				obj_id1 = obj_ids[0]
				obj_id2 = obj_ids.pop()
				model.store.objects.merge(obj_id1, obj_id2)
			model.store.end_change()
