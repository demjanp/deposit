from deposit.DModule import (DModule)

class UserTools(DModule):
	
	def __init__(self, store):
		
		self.store = store
		self._user_tools = []
		
		DModule.__init__(self)
		
	def add(self, user_tool):
		
		self._user_tools.append(user_tool)
		self.store.on_data_changed()
	
	def delete(self, label):
		
		self._user_tools = [user_tool for user_tool in self._user_tools if user_tool["label"] != label]
		self.store.on_data_changed()
	
	def clear(self):
		
		self._user_tools = []
	
	def to_list(self):
		
		return self._user_tools.copy()
	
	def from_list(self, data):
		
		self._user_tools = data.copy()

