from deposit import (Store, DB, File)

def triggered(model, view, checked):
	
	view.save_store_in_database(save_as = True)

def get_state(model, view):
	
	return model.has_store(), False
