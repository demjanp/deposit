from deposit import (DB, File, Store)

def triggered(model, view, params_db, path, *args):
	
	model.set_store(Store(DB(*params_db), File(path)))

def get_state(model, view):
	
	return True, False