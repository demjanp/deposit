from deposit import Broadcasts
from deposit.commander.frames._Frame import (Frame)

from PyQt5 import (QtWidgets, QtCore, QtGui)

class Class(Frame, QtWidgets.QWidget):
	
	def __init__(self, model, view, parent, dclass_name):
		
		self.dclass = None
		
		Frame.__init__(self, model, view, parent)
		QtWidgets.QWidget.__init__(self, parent)
		
		self.set_up(dclass_name)
		
		self.connect_broadcast(Broadcasts.ELEMENT_CHANGED, self.on_store_changed)
	
	def set_up(self, dclass_name):
		
		self.dclass = self.model.classes[dclass_name]
		self.setLayout(QtWidgets.QGridLayout())
		self.layout().setContentsMargins(10, 10, 10, 10)
		self.layout().setSpacing(10)
		self.populate()
	
	def populate(self):
		
		self.clear_layout(self.layout())
		row = 0
		for rel in self.dclass.relations:
			for cls2 in self.dclass.relations[rel]:
				
				clsA, clsB = self.dclass.name, cls2
				formatstr = "<strong>%s</strong>.%s.%s"
				if rel.startswith("~"):
					formatstr = "%s.%s.<strong>%s</strong>"
					clsA, clsB = clsB, clsA
					rel = rel[1:]
				
				self.layout().addWidget(QtWidgets.QLabel(formatstr % (clsA, rel, clsB)), row, 0)
				button = QtWidgets.QToolButton(self)
				button._rel = rel
				button._clsA = clsA
				button._clsB = clsB
				button.setIcon(self.view.get_icon("unlink.svg"))
				button.setIconSize(QtCore.QSize(24, 24))
				button.setToolTip("Unlink Class")
				button.clicked.connect(self.on_unlink)
				self.layout().addWidget(button, row, 1)
				row += 1
		
		self.layout().addItem(QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding), row, 0)
		self.parent.adjustSize()
		
	def name(self):
		
		return self.dclass.name
	
	def icon(self):
		
		return "link_class.svg"
	
	def get_selected(self):
		
		return []
	
	def on_store_changed(self, *args):
		
		self.populate()
	
	def on_unlink(self, *args):
		
		self.view.dialogs.open("RemoveClassRelation", self.sender()._clsA, self.sender()._rel, self.sender()._clsB)

