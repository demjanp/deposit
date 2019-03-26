from deposit.commander.usertools.UserElement import (UserElement)

class ColumnBreak(UserElement):
	
	def __init__(self):
		
		UserElement.__init__(self)
	
	def to_markup(self):
		
		return "<ColumnBreak/>"
