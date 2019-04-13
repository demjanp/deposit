from deposit.commander.ViewChild import (ViewChild)
from deposit.commander.navigator.ClassWidget import (ClassWidget)
from deposit.commander.navigator.DatabaseWidget import (DatabaseWidget)

from PySide2 import (QtWidgets, QtCore, QtGui)

class Navigator(ViewChild, QtWidgets.QToolBox):
	
	def __init__(self, model, view):
		
		self.classwidget = None
		self.databasewidget = None
		
		ViewChild.__init__(self, model, view)
		QtWidgets.QToolBox.__init__(self, view)
		
		self.set_up()
	
	def set_up(self):
		
		self.layout().setSpacing(0)
		self.setStyleSheet('''
			QToolBox {
				icon-size: 32px;
			}
			QToolBox::tab {
				font: bold 14px;
			}
		''')
		
		self.classwidget = ClassWidget(self.model, self.view, self)
		self.databasewidget = DatabaseWidget(self.model, self.view, self)
		
		self.addItem(self.classwidget, self.view.get_icon("class.svg"), "Classes")
		self.addItem(self.databasewidget, self.view.get_icon("link_db.svg"), "Linked Databases")
		
		size = self.size()
		size.setWidth(340)
		self.resize(size)

