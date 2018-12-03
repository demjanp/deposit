from deposit.commander.toolbar._Tool import (Tool)
from deposit.store.Conversions import (as_url)

from PyQt5 import (QtWidgets, QtCore)

class Save(Tool):

	def name(self):

		return self.__class__.__name__

	def icon(self):

		return "save.svg"

	def help(self):

		if self.model.data_source is None:
			return "Save As File"
		
		save_to = self.model.data_source.__class__.__name__
		
		if hasattr(self.model.data_source, "url") and self.model.data_source.url:
			save_to = self.model.data_source.url
		elif hasattr(self.model.data_source, "connstr") and self.model.data_source.connstr:
			save_to = self.model.data_source.connstr
		
		return "Save to %s" % (save_to)

	def enabled(self):

		return True

	def triggered(self, state):
		
		if self.model.data_source is None:
			
			directory = ""
			if not self.model.local_folder is None:
				directory = as_url(self.model.local_folder)
			url, format = QtWidgets.QFileDialog.getSaveFileUrl(self.view, caption = "Save Database As", filter = "JSON (*.json);;Resource Description Framework (*.rdf)", directory = directory)
			url = url.toString()
			if url:
				ds = None
				if format == "Resource Description Framework (*.rdf)":
					ds = self.model.datasources.RDFGraph(url = url)
				elif format == "JSON (*.json)":
					ds = self.model.datasources.JSON(url = url)
				if (not ds is None) and ds.save():
					self.model.set_datasource(ds)
					self.view.menu.add_recent_url(url)
			
		else:
			if (self.model.data_source.name == "DB") and (not self.model.data_source.identifier):
				self.view.dialogs.open("SetIdentifier", True)
				return
			self.model.save()

