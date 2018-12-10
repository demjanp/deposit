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

		return not self.model.is_saved()

	def triggered(self, state):
		
		self.view.save()

