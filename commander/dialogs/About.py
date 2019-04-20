#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from deposit.commander.dialogs._Dialog import (Dialog)

from PySide2 import (QtWidgets, QtCore, QtGui)

class About(Dialog):
	
	def title(self):
		
		return "About Deposit"
	
	def set_up(self):
		
		self.setMinimumWidth(400)
		self.setModal(True)
		self.setLayout(QtWidgets.QVBoxLayout())
		
		self.content = QtWidgets.QFrame()
		self.content.setLayout(QtWidgets.QHBoxLayout())
		self.layout().addWidget(self.content)
		
		self.logo = QtWidgets.QLabel()
		self.logo.setPixmap(QtGui.QPixmap("deposit/res/deposit_logo.svg"))
		self.label = QtWidgets.QLabel('''
<h2>Deposit</h2>
<h4>Graph-based data storage and exchange</h4>
<p>Version 1.1</p>
<p>Copyright © <a href="mailto:peter.demjan@gmail.com">Peter Demján</a> 2013 - 2019</p>
<p>&nbsp;</p>
<p>Licensed under the <a href="https://www.gnu.org/licenses/gpl-3.0.en.html">GNU General Public License</a></p>
<p><a href="https://github.com/demjanp/deposit">Source Code</a></p>
		''')
		self.label.setOpenExternalLinks(True)
		self.content.layout().addWidget(self.logo)
		self.content.layout().addWidget(self.label)
	
	def button_box(self):
		
		return True, False