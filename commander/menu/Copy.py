from deposit.commander.toolbar._Tool import (Tool)

from PySide2 import (QtWidgets)

class Copy(Tool):
	
	def icon(self):
		
		return ""
	
	def help(self):
		
		return "Copy"
	
	def enabled(self):
		
		current = self.view.mdiarea.get_current()
		if current:
			for item in current.get_selected():
				if item:
					return True
		return False
	
	def shortcut(self):
		
		return "Ctrl+C"
	
	def triggered(self, state):
		
		current = self.view.mdiarea.get_current()
		selected = current.get_selected() # [[QueryItem(), ...], ...]
		grid = []
		for row in selected:
			if row:
				grid.append([])
				for item in row:
					value = ""
					if item.element.__class__.__name__ == "DObject":
						value = str(item.element.id)
					elif item.element.__class__.__name__ == "DDescriptor":
						value = str(item.element.label.value)
					grid[-1].append(value)
		text = "\n".join(["\t".join(row) for row in grid])
		indexes = []
		for row in selected.indexes:
			for column in selected.indexes[row]:
				indexes.append(selected.indexes[row][column])
		data = current.get_mime_data(indexes)
		data.setData("text/plain", bytes(text, "utf-8"))
		QtWidgets.QApplication.clipboard().setMimeData(data)

