def toggled(model, view, state):
	
	if state:
		model.set_local_resources(False)

def get_state(model, view):
	
	return True, model.local_resources() is False