from deposit import (Store)
from PyQt5 import (QtWidgets, QtCore)
from urllib.parse import urlparse

def triggered(model, view, checked):

	if model.has_store() and (urlparse(model.store.identifier()).scheme == "file"):
		reply = QtWidgets.QMessageBox.question(view, "New database", "Discard any unsaved changes?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.Yes)
		if reply == QtWidgets.QMessageBox.No:
			return
	model.set_store(Store())

def get_state(model, view,):
	
	return True, False
