from deposit.commander.toolbar._Tool import (Tool)

class SaveAsDB(Tool):

	def name(self):

		return "Save As Database"

	def icon(self):

		return ""

	def help(self):

		return "Save As Database"

	def enabled(self):

		return True

	def triggered(self, state):

		self.view.dialogs.open("SaveAsDB")


