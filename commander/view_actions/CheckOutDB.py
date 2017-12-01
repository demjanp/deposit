from PyQt5 import (QtWidgets)

def triggered(model, view, checked):
	
	path, _ = QtWidgets.QFileDialog.getSaveFileName(view, caption = "Check Out Database As", filter = "Resource Description Framework (*.rdf)")
	if path:
		model.store.check_out(path)
	
def get_state(model, view):
	
	return model.has_store() and (not model.is_checked_out()), False

