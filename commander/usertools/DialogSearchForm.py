from deposit.commander.usertools.DialogForm import (DialogForm)

class DialogSearchForm(DialogForm):
	
	def __init__(self, model, view, form_tool):
		
		self.selects = []
		
		DialogForm.__init__(self, model, view, form_tool)
	
	def submit(self):
		
		query = "SELECT %s" % (", ".join([".".join(select) for select in self.selects]))
		conditions = []
		frames, _ = self.frames()
		for frame in frames:
			value = frame.get_value()
			if value:
				conditions.append("(%s.%s == '%s')" % (frame.dclass, frame.descriptor, value))
		if conditions:
			query += " WHERE %s" % (" and ".join(conditions))
		self.view.mdiarea.create("Query", query)
	
	def clear(self):
		
		frames, _ = self.frames()
		for frame in frames:
			frame.set_value("")
	
	def on_submit(self, *args):
		
		self.submit()
		self.hide()
	
	def on_reset(self, *args):
		
		self.clear()

