from deposit import Broadcasts
from deposit.DModule import (DModule)
from deposit.commander.usertools._UserTool import (UserTool)

class Query(DModule, UserTool):
	
	def __init__(self, label, value, view):
		
		self.value = value
		
		DModule.__init__(self)
		UserTool.__init__(self, label, view)
		
		self.setIcon(view.get_icon("query.svg"))
		self.setToolTip("Query: %s" % self.label)
		
		self.update()
		
		self.connect_broadcast(Broadcasts.VIEW_ACTION, self.on_view_action)
	
	def on_view_action(self, *args):
		
		self.update()
	
	def update(self):
		
		if (self.view.usertools.SELECTED_STR not in self.value) or (self.view.usertools.get_selected_id() is not None):
			self.setEnabled(True)
		else:
			self.setEnabled(False)
	
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

