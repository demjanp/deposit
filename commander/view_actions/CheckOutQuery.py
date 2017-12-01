from PyQt5 import (QtWidgets)

def triggered(model, view, checked):
	
	active = view.active()
	if hasattr(active, "grid_data") and active.selected():
		objects = []
		grid = active.grid_data(selected = True)
		for row_data in grid:
			for value in row_data:
				if value.relation:
					if not value.relation in objects:
						objects.append(value.relation)
	else:
		objects = active.objects()
	if objects:
		path, _ = QtWidgets.QFileDialog.getSaveFileName(view, caption = "Check Out Objects", filter = "Resource Description Framework (*.rdf)")
		if path:
			model.store.check_out(path, objects)
	
def get_state(model, view):
	
	if not model.is_checked_out():
		active = view.active()
		return (not active is None) and hasattr(active, "objects") and (len(active.objects()) > 0), False
	return False, False
