from deposit.commander.ClassList import ClassList

def get_state(model, view):
	
	active = view.active()
	if (not active is None) and isinstance(active, ClassList):
		selected = active.selected()
		if (len(selected) == 1) and ("row" in selected[0]["data"]):
			row = selected[0]["data"]["row"]
			if row and (row < active.topLevelItemCount() - 1):
				return True, False
	return False, False
