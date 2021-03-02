from deposit.commander.dialogs._Dialog import (Dialog)

from PySide2 import (QtWidgets, QtCore, QtGui)

class RemoveRelation(Dialog):
	
	def title(self):
		
		if len(self.items) > 1:
			return "Remove Relations"
		else:
			return "Remove Relation"
	
	def set_up(self, items):
		
		self.items = items
		
		self.setMinimumWidth(300)
		self.setModal(True)
		self.layout = QtWidgets.QVBoxLayout()
		self.setLayout(self.layout)
		
		self.form_layout = QtWidgets.QFormLayout()
		self.form = QtWidgets.QWidget()
		self.form.setLayout(self.form_layout)
		self.layout.addWidget(self.form)
		
		label = QtWidgets.QLabel("Remove the selected relation%s?" % ("s" if (len(self.items) > 1) else ""), self)
		
		self.layout.addWidget(label)
	
	def process(self):
		
		for item in self.items:
			if item.element.__class__.__name__ == "DObject":
				del self.model.objects[item.relation.source.id].relations[item.relation.name][item.element.id]
			elif item.element.__class__.__name__ == "DClass":
				cls1 = item.element.name
				rel, cls2 = item.relation
				self.model.classes[cls1].del_relation(rel, cls2)

