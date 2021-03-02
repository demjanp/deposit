from deposit.DModule import (DModule)

from PySide2 import (QtWidgets, QtCore, QtGui)

class QueryItem(DModule):
	
	def __init__(self, index, element, icons = None, relation = None):
		
		self.index = index
		self.element = element
		self.icons = icons
		self.relation = relation

		DModule.__init__(self)
	
	def is_read_only(self):
		
		if self.element is None:
			return True
		if self.element.__class__.__name__ == "DObject":
			return True
		if self.element.label.__class__.__name__ in ["DResource", "DGeometry"]:
			return True
		return False
	
	def is_object(self):
		
		return (self.element.__class__.__name__ == "DObject")
	
	def is_resource(self):
		
		return (self.element.__class__.__name__ == "DDescriptor") and (self.element.label.__class__.__name__ == "DResource")
	
	def is_geometry(self):
		
		return (self.element.__class__.__name__ == "DDescriptor") and (self.element.label.__class__.__name__ == "DGeometry")
	
	def data(self, role):
		
		if role in [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole]:
			if self.element.__class__.__name__ == "DObject":
				return str(self.element.id)
			if self.element.__class__.__name__ == "DDescriptor":
				if self.element.label.__class__.__name__ == "DResource":
					return self.element.label.filename
				if self.element.label.__class__.__name__ == "DGeometry":
					return self.element.label.type
				if self.element.label.__class__.__name__ == "DNone":
					return None
				return str(self.element.label.value)
			return None
		
		if role == QtCore.Qt.DecorationRole:
			if self.element.__class__.__name__ == "DDescriptor":
				if self.element.label.__class__.__name__ == "DResource":
					stored = self.element.label.is_stored()
					if self.element.label.worldfile:
						return self.icons["georaster" if stored else "remote_georaster"]
					if self.element.label.is_image():
						return self.icons["image" if stored else "remote_image"]
					return self.icons["file" if stored else "remote_file"]
				if self.element.label.__class__.__name__ == "DGeometry":
					return self.icons["geo"]
			return None
		
		if role == QtCore.Qt.UserRole:
			return self
		
		if role == QtCore.Qt.BackgroundRole:
			if self.is_read_only():
				return QtGui.QColor(240, 240, 240, 255)
			return None
		
		return None


class DModelIndex(object):
	
	def __init__(self, row, column, element, relation = None):
		
		self._column = column
		self._row = row
		self._data = QueryItem(self, element, None, relation)
	
	def column(self):
		
		return self._column
	
	def data(self, role):
		
		return self._data
	
	def row(self):
		
		return self._row
