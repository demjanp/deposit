def triggered(model, view, checked):
	
	view.save_store_in_file(save_as = True)

def get_state(model, view):
	
	return model.has_store(), False
