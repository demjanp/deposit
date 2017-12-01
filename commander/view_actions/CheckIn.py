from PyQt5 import (QtWidgets)
import os
import pathlib

def triggered(model, view, checked):
	# TODO display results via GUI
	
	path, _ = QtWidgets.QFileDialog.getOpenFileName(view, caption = "Check In Database", filter = "Resource Description Framework (*.rdf)")
	if path:
		model.actions.check_in(os.path.splitext(pathlib.Path(path).as_uri())[0] + "#")
	
def get_state(model, view):
	
	return model.has_store() and (not model.is_checked_out()), False
