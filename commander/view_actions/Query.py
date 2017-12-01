def submitted(model, view, lineEdit, *args):
	
	query = lineEdit.text().strip()
	if query:
		view.open_query(query)

def get_state(model, view):
	
	return model.has_store(), False