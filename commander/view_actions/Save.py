from urllib.parse import urlparse

def triggered(model, view, checked):
	
	if model.store.has_database():
		view.save_store_in_database()
	else:
		view.save_store_in_file()

def get_state(model, view):
	
	if model.has_store() and (model.last_changed() != model.store.get_changed()):
		return True, False
	return False, False
