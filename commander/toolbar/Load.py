from deposit.commander.toolbar._Tool import (Tool)
from deposit.store.Conversions import (as_url)
from PySide2 import (QtWidgets)
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
		
		url, format = QtWidgets.QFileDialog.getOpenFileUrl(self.view, caption = "Load Data", filter = "(*.json *.rdf *.xlsx *.csv *.shp)", directory = directory)
		url = str(url.toString())
		format = url.split(".")[-1].lower()
		if url:
			ds = None
			if format == "rdf":
				ds = self.model.datasources.RDFGraph(url = url)
			elif format == "json":
				ds = self.model.datasources.JSON(url = url)
			
			if (ds is not None) and ds.load():
				self.model.set_datasource(ds)
				self.view.menu.add_recent_url(url)
				return
			
			es = None
			if format == "xlsx":
				es = self.model.externalsources.XLSX(url)
			if format == "csv":
				es = self.model.externalsources.CSV(url)
			if format == "shp":
				es = self.model.externalsources.Shapefile(url)
			if (es is not None) and es.load():
				self.view.mdiarea.create(es.name, es)


