from deposit.commander.ViewChild import (ViewChild)

class Frame(ViewChild):
	
	def __init__(self, model, view, parent):
		
		self.parent = parent
		self._closed = False
		
		super(Frame, self).__init__(model, view)
	
	def set_closed(self):
		
		self._closed = True
		self.disconnect_broadcast()
	
	def closed(self):
		
		if self._closed:
			return True
		if isinstance(self.parent, Frame):
			return self.parent.closed()
	
	def clear_layout(self, layout):
		# convenience function to clear a layout
		
		for i in reversed(range(layout.count())):
			item = layout.itemAt(i)
			if item.widget():
				item.widget().setParent(None)
			else:
				layout.removeItem(item)
	
	def name(self):
		
		return self.__class__.__name__
	
	def icon(self):
		
		return "dep_cube.svg"
	
	def get_selected(self):
		# re-implement to return a list of selected items
		
		return []
	