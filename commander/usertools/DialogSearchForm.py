from deposit.commander.usertools.DialogForm import (DialogForm)

class DialogSearchForm(DialogForm):
	
	def __init__(self, model, view, form_tool):
		
		self.selects = []
		
		DialogForm.__init__(self, model, view, form_tool)
		
		self.setMinimumWidth(600)
	
	def submit(self):
		
		def value_to_str(value):
			
			try:
				value = float(value)
				if value - int(value) == 0:
					value = int(value)
			except:
				value = str(value)
			if isinstance(value, str):
				return "'%s'" % (value)
			return "%s" % str(value)
		
		conditions = []
		frames, _ = self.frames()
		for frame in frames:
			value = frame.get_value()
			if value:
				conditions.append("(%s.%s == %s)" % (frame.dclass, frame.descriptor, value_to_str(value)))
				if [frame.dclass, frame.descriptor] not in self.selects:
					self.selects.append([frame.dclass, frame.descriptor])
		querystr = "SELECT %s" % (", ".join([".".join(select) for select in self.selects]))
		if conditions:
			querystr += " WHERE %s" % (" and ".join(conditions))
		self.view.query(querystr)
	
	def clear(self):
		
		frames, _ = self.frames()
		for frame in frames:
			frame.set_value("")
	
	def on_submit(self, *args):
		
		self.submit()
		self.hide()
	
	def on_reset(self, *args):
		
		self.clear()

