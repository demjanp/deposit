from deposit.commander.toolbar._Tool import (Tool)
from deposit.store.Conversions import (as_url)

from PySide2 import (QtWidgets, QtCore)
import os

class SaveAs(Tool):
	
	def name(self):
		
		return "Save As File"
	
	def icon(self):
		
		return ""
	
	def help(self):
		
		return "Save As File"
	
	def enabled(self):
		
		return True
	
	def triggered(self, state):

		directory = ""
		if not self.model.local_folder is None:
			directory = as_url(self.model.local_folder)
		url, format = QtWidgets.QFileDialog.getSaveFileUrl(self.view, caption = "Save Database As", filter = "JSON (*.json);;Resource Description Framework (*.rdf)", directory = directory)
		url = str(url.toString())
		if url:
			ds = None
			if format == "Resource Description Framework (*.rdf)":
				ds = self.model.datasources.RDFGraph(url = url)
			elif format == "JSON (*.json)":
				ds = self.model.datasources.JSON(url = url)
			if (not ds is None) and ds.save():
				self.model.set_datasource(ds)
				self.view.menu.add_recent_url(url)
		

		