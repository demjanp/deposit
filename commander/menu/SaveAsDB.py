from deposit.commander.toolbar._Tool import (Tool)

class SaveAsDB(Tool):

	def name(self):

		return "Save As Database"

	def icon(self):

		return ""

	def help(self):

		return "Save As Database"

	def enabled(self):

		return (self.model.data_source is None)

	def triggered(self, state):

		self.view.dialogs.open("SaveAsDB")


