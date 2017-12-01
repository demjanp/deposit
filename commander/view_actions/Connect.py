from deposit import (Store)

def toggled(model, view, checked):
	
	if checked:
		db, file = view.get_database(title = "Connect to Database")
		if not db is None:
			model.set_store(Store(db, file))
		else:
			view.update_action_states()
		
	else:
		model.set_store(None)

def get_state(model, view):
	
	return True, model.has_store()
	
