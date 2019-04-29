from deposit import Broadcasts
from deposit.commander.toolbar._Tool import (Tool)

class RemoveDescriptor(Tool):
	
	def name(self):
		
		return "Remove Descriptor"
	
	def icon(self):
		
		return "remove_descriptor.svg"
	
	def help(self):
		
		return "Remove Descriptor"
	
	def enabled(self):

		current = self.view.mdiarea.get_current()
		if current:
			for row in current.get_selected():
				for item in row:
					if item.element.__class__.__name__ == "DDescriptor":
						return True
					return False
		return False
	
	def shortcut(self):
		
		return "Del"
	
	def triggered(self, state):
		
		descriptors = []
		current = self.view.mdiarea.get_current()
		if current:
			for row in current.get_selected():
				for item in row:
					if item.element.__class__.__name__ == "DDescriptor":
						descr = item.element
						del descr.target.descriptors[descr.dclass.name]
