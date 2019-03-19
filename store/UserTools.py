from deposit import Broadcasts
from deposit.DModule import (DModule)

class UserTools(DModule):
	
	def __init__(self, store):
		
		self.store = store
		self._user_tools = []
		
		DModule.__init__(self)
		
	def add(self, user_tool):
		
		self._user_tools.append(user_tool)
		self.broadcast(Broadcasts.STORE_DATA_CHANGED)
	
	def delete(self, label):
		
		self._user_tools = [user_tool for user_tool in self._user_tools if user_tool["label"] != label]
		self.broadcast(Broadcasts.STORE_DATA_CHANGED)
	
	def to_list(self):
		
		return self._user_tools.copy()
	
	def from_list(self, data):
		
		self._user_tools = data.copy()

