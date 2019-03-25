from deposit.commander.usertools._UserTool import (UserTool)

class Query(UserTool):
	
	def __init__(self, label, value, view):
		
		self.value = value
		UserTool.__init__(self, label, view)
		
		self.setIcon(view.get_icon("query.svg"))
		self.setToolTip("Query: %s" % self.label)
		
	def on_triggered(self, state):
		
		self.view.usertools.open_query(self)
	
	def to_markup(self):
		
		return UserTool.to_markup(self) + '''
<QueryString>%s</>
		''' % (self.value)
	
	def to_dict(self):
		
		return dict(
			value = self.value,
			**UserTool.to_dict(self),
		)

