def toggled(model, view, state):
	
	if state:
		model.set_check_in_collisions_overwrite(True)

def get_state(model, view):
	
	return True, model.check_in_collisions_overwrite() is True