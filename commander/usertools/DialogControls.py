from PyQt5 import (QtWidgets, QtCore, QtGui)

class DialogControl(object):
	
	def __init__(self, model, user_control):
		
		self.model = model
		self.user_control = user_control
	
	def set_object(self, id):
		
		value = self.model.objects[id].descriptors[self.user_control.descriptor].label.value
		if value is None:
			value = ""
		self.set_value(value)
	
	def set_value(self, value):
		
		return None
	
	def get_value(self):
		
		return None
	
class LineEdit(DialogControl, QtWidgets.QLineEdit):
	
	def __init__(self, model, user_control):
		
		DialogControl.__init__(self, model, user_control)
		QtWidgets.QLineEdit.__init__(self)
	
	def set_value(self, value):
		
		self.setText(str(value))
	
	def get_value(self):
		
		return self.text().strip()
	
class PlainTextEdit(DialogControl, QtWidgets.QPlainTextEdit):
	
	def __init__(self, model, user_control):
		
		DialogControl.__init__(self, model, user_control)
		QtWidgets.QPlainTextEdit.__init__(self)
	
	def set_value(self, value):
		
		self.setPlainText(str(value))
		
	def get_value(self):
		
		return self.toPlainText().strip()
	
class ComboBox(DialogControl, QtWidgets.QComboBox):
	
	def __init__(self, model, user_control):
		
		DialogControl.__init__(self, model, user_control)
		QtWidgets.QComboBox.__init__(self)
		self.setEditable(True)
		
		self.set_value(None)
	
	def set_value(self, value):
		
		values = set()
		for id in self.model.classes[self.user_control.dclass].objects:
			val = self.model.objects[id].descriptors[self.user_control.descriptor].label.value
			if val is not None:
				values.add(val)
		values = sorted(list(values))
		self.clear()
		if values:
			self.addItems([""] + values)
		if value is not None:
			value = str(value)
			if value in values:
				self.setCurrentIndex(values.index(value) + 1)
			elif values:
				self.setItemText(0, value)
			else:
				self.setCurrentText(value)
		
	def get_value(self):
		
		return self.currentText().strip()

class CheckBox(DialogControl, QtWidgets.QCheckBox):
	
	def __init__(self, model, user_control):
		
		DialogControl.__init__(self, model, user_control)
		QtWidgets.QCheckBox.__init__(self)
	
	def set_value(self, value):
		
		try:
			value = bool(int(value))
		except:
			value = False
		self.setChecked(value)
	
	def get_value(self):
		
		return str(int(self.isChecked()))

