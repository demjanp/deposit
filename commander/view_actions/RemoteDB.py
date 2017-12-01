from deposit import (Store, DB, File)

def clicked(model, view, checked):
	
	db, file = view.get_database(title = "Connect Remote Database")
	if not db is None:
		model.store.connect_remote(db, file)

def get_state(model, view):
	
	return model.has_store(), False
