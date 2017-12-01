from PyQt5 import (QtWidgets)
import os
from deposit import (DB, Store)

def triggered(model, view, checked):
	
	ident, _ = QtWidgets.QFileDialog.getOpenFileUrl(model._view, caption = "Load Database", filter = "Resource Description Framework (*.rdf)")
	ident = ident.toString()
	if ident:
		model.set_store(Store(DB(os.path.splitext(ident)[0] + "#")))

def get_state(model, view):
	
	return True, False
