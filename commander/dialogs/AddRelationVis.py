from deposit.commander.dialogs._Dialog import (Dialog)

from PySide2 import (QtWidgets, QtCore, QtGui)

class AddRelationVis(Dialog):
	
	def title(self):
		
		return "Add Relation"
	
	def set_up(self, cls1, cls2):
		
		self.setMinimumWidth(256)
		self.setModal(False)
		
		self.setLayout(QtWidgets.QVBoxLayout())
		
		labels = QtWidgets.QWidget()
		labels.setLayout(QtWidgets.QHBoxLayout())
		
		self.label_source = QtWidgets.QLabel(cls1)
		self.label_relation = QtWidgets.QComboBox(self)
		self.label_relation.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
		self.label_relation.setEditable(True)
		self.label_relation.addItems(self.model.relation_names)
		self.label_target = QtWidgets.QLabel(cls2)
		
		labels.layout().addWidget(self.label_source)
		labels.layout().addWidget(self.label_relation)
		labels.layout().addWidget(self.label_target)
		
		buttons = QtWidgets.QWidget()
		buttons.setLayout(QtWidgets.QHBoxLayout())
		
		reverse_button = QtWidgets.QPushButton("Reverse")
		reverse_button.clicked.connect(self.on_reverse)
		buttons.layout().addStretch()
		buttons.layout().addWidget(reverse_button)
		buttons.layout().addStretch()
		
		self.layout().addWidget(labels)
		self.layout().addWidget(buttons)
		
	
	@QtCore.Slot()
	def on_reverse(self):
		
		cls2 = self.label_source.text()
		cls1 = self.label_target.text()
		self.label_source.setText(cls1)
		self.label_target.setText(cls2)
	
	def process(self):
		
		cls1 = self.label_source.text()
		cls2 = self.label_target.text()
		rel = self.label_relation.currentText().strip()
		if not rel:
			return
		self.model.classes[cls1].add_relation(rel, cls2)
		
