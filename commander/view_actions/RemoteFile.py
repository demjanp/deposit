from PyQt5 import (QtWidgets)
import os
from deposit import (DB, Store)

def clicked(model, view, checked):
	
	ident, _ = QtWidgets.QFileDialog.getOpenFileUrl(model._view, caption = "Connect Remote File", filter = "Resource Description Framework (*.rdf)")
	ident = ident.toString()
	if ident:
		db = DB(os.path.splitext(ident)[0] + "#")
		model.store.connect_remote(db, Store(db).file)
	
def get_state(model, view):
	
	return model.has_store(), False
