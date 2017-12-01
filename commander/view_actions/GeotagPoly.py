def get_state(model, view):
	
	active = view.active()
	return True, (not active is None) and hasattr(active, "is_drawing") and active.is_drawing()