from deposit.commander.toolbar._Tool import (Tool)
from deposit.commander.toolbar.Export import (Export)

from PySide2 import (QtWidgets)

class LoadExternal(Tool):

	def name(self):

		return "Load External Data"

	def icon(self):

		return "load_external.svg"

	def help(self):
		
		return "Load External Data"

	def enabled(self):

		return True

	def triggered(self, state):
		
		formats = ";;".join([Export.FORMAT_XLSX, Export.FORMAT_CSV, Export.FORMAT_Shapefile])
		url, format = QtWidgets.QFileDialog.getOpenFileUrl(self.view, caption = "Load External Data", filter = formats)
		url = url.toString()
		if url:
			self.view.mdiarea.open_external(url)

