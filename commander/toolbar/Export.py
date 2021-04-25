from deposit.commander.toolbar._Tool import (Tool)

from PySide2 import (QtWidgets, QtCore, QtGui)

class Export(Tool):
	
	FORMAT_XLSX = "Excel 2007+ Workbook (*.xlsx)"
	FORMAT_CSV = "Comma-separated Values (*.csv)"
	FORMAT_Shapefile = "ESRI Shapefile (*.shp)"
	
	def name(self):
		
		return "Export"
	
	def icon(self):
		
		return "export.svg"
	
	def help(self):
		
		return "Export Data"
	
	def enabled(self):

		return self.view.mdiarea.get_current().__class__.__name__ == "QueryLst"
	
	def triggered(self, state):
		
		query = self.view.mdiarea.get_current().query
		if not query:
			return
		formats = ";;".join([self.FORMAT_XLSX, self.FORMAT_CSV, self.FORMAT_Shapefile])
		url, format = QtWidgets.QFileDialog.getSaveFileUrl(self.view, caption = "Export Query As", filter = formats)
		url = str(url.toString())
		if not url:
			return
		es = None
		if format == self.FORMAT_XLSX:
			es = self.model.externalsources.XLSX(url)
		elif format == self.FORMAT_CSV:
			es = self.model.externalsources.CSV(url)
		elif format == self.FORMAT_Shapefile:
			es = self.model.externalsources.Shapefile(url)
		if es is not None:
			es.export_data(query)
		
