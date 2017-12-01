from deposit.commander.QueryLstView import QueryLstView

def get_state(model, view):
	
	active = view.active()
	return isinstance(active, QueryLstView) and (len(active.selected()) == 1), False

def triggered(model, view, checked):
	
	active = view.active()
	selected = active.selected()
	
	model.store.objects.duplicate(selected[0]["data"]["obj_id"])
