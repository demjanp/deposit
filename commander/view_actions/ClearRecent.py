def triggered(model, view, state):
	
	model.clear_recent()

def get_state(model, view):
	
	return (len(model.recent()) > 0), False