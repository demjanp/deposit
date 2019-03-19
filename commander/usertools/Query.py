from deposit.commander.usertools._UserTool import (UserTool)

class Query(UserTool):
	
	def __init__(self, label, value, view):
		
		self.value = value
		UserTool.__init__(self, label, view)
		
		self.setIcon(view.get_icon("query.svg"))
		
	def on_triggered(self, state):
		
		pass
		
	def to_dict(self):
		
		return dict(
			value = self.value,
			**UserTool.to_dict(self),
		)

