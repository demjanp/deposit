from deposit import (Store, DB)

def clicked(model, view, checked):
	
	values = view.get_values("Connect Remote Server", ("url", ["Url:", ""]))
	if values and values["url"]:
		db = DB(values["url"])
		model.store.connect_remote(db, Store(db).file)

def get_state(model, view):
	
	return model.has_store(), False
