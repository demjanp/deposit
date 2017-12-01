def get_state(model, view):
	
	active = view.active()
	return (not active is None) and (len(active.selected()) > 0), False