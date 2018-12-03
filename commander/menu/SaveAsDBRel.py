from deposit.commander.toolbar._Tool import (Tool)

class SaveAsDBRel(Tool):

	def name(self):

		return "Save As Relational Database"

	def icon(self):

		return ""

	def help(self):

		return "Save As Relational Database"

	def enabled(self):

		return True

	def triggered(self, state):

		self.view.dialogs.open("SaveAsDBRel")


