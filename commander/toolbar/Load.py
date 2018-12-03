from deposit.commander.toolbar._Tool import (Tool)
from deposit.store.Conversions import (as_url)
from PyQt5 import (QtWidgets)
import os

class Load(Tool):

	def name(self):

		return self.__class__.__name__

	def icon(sel):

		return "open.svg"

	def help(self):

		if self.model.data_source.__class__.__name__ in ["DB", "DBRel"]:
			return "Load from database"
		return "Load from file"

	def enabled(self):

		return True

	def triggered(self, state):
		
		if not self.model.data_source is None:
			if (self.model.data_source.name == "DBRel") and self.model.data_source.load():
				self.view.menu.add_recent_db(self.model.data_source.identifier, self.model.data_source.connstr)
				return
			
			if (self.model.data_source.name == "DB") and self.model.data_source.is_valid():
				self.view.dialogs.open("LoadDB")
				return
		
		directory = ""
		if not self.model.local_folder is None:
			directory = as_url(self.model.local_folder)
		url, format = QtWidgets.QFileDialog.getOpenFileUrl(self.view, caption = "Load Database", filter = "JSON (*.json);;Resource Description Framework (*.rdf)", directory = directory)
		url = url.toString()
		if url:
			ds = None
			if format == "Resource Description Framework (*.rdf)":
				ds = self.model.datasources.RDFGraph(url = url)
			elif format == "JSON (*.json)":
				ds = self.model.datasources.JSON(url = url)
			if (not ds is None) and ds.load():
				self.model.set_datasource(ds)
				self.view.menu.add_recent_url(url)

