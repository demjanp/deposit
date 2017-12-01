from deposit.commander.ClassList import ClassList

def get_state(model, view):
	
	active = view.active()
	if (not active is None) and isinstance(active, ClassList):
		selected = active.selected()
		if (len(selected) == 1) and ("cls_id" in selected[0]["data"]) and (selected[0]["data"]["cls_id"]):
			return True, False
	return False, False
