from PyQt5 import (QtWidgets)

def get_state(model, view):
	
	active = view.active()
	if (not active is None) and hasattr(active, "paste") and (QtWidgets.QApplication.clipboard().text() != ""):
		selected = active.selected()
		if selected and (QtWidgets.QApplication.clipboard().text() != ""):
			for data in selected:
				if not "obj_id2" in data["data"]:
					return True, False
	return False, False

def triggered(model, view, checked):
	
	active = view.active()
	text = QtWidgets.QApplication.clipboard().text()
	selected = active.selected()
	if text and selected:
		active.paste(text)
	