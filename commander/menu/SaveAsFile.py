from deposit.commander.toolbar._Tool import (Tool)

from PySide2 import (QtWidgets, QtCore, QtGui)

class SaveAsFile(Tool):
	
	FORMAT_Pickle = "Pickle (*.pickle)"
	FORMAT_JSON = "JSON (*.json)"
	
	def name(self):
		
		return "Save As File"
	
	def icon(self):
		
		return ""
	
	def help(self):
		
		return "Save Database As File"
	
	def enabled(self):
		
		return True
	
	def triggered(self, state):
		
		formats = ";;".join([self.FORMAT_Pickle, self.FORMAT_JSON])
		url, format = QtWidgets.QFileDialog.getSaveFileUrl(self.view, caption = "Save Database As", filter = formats)
		url = str(url.toString())
		if not url:
			return
		if format not in [self.FORMAT_Pickle, self.FORMAT_JSON]:
			return
		
		data = dict(
			data_source_class = None,
			identifier = None,
			url = None,
			connstr = None,
			local_folder = self.model.local_folder,
			changed = self.model.changed,
			classes = self.model.classes.to_dict(), # {name: class data, ...}
			objects = self.model.objects.to_dict(), # {id: object data, ...}
			events = self.model.events.to_list(),
			user_tools = self.model.user_tools.to_list(),
			queries = self.model.queries.to_dict(),
		)
		self.model.load(url)
		self.model.add_objects(data, None, localise = True)
		self.model.save()
