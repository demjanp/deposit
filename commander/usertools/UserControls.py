from deposit.commander.usertools._UserElement import (UserElement)
from deposit.commander.usertools._UserLabeledElement import (UserLabeledElement)
from deposit.commander.usertools._UserSelect import (UserSelect)

class UserControl(UserLabeledElement, UserSelect):
	
	def __init__(self, stylesheet, label, dclass, descriptor):
		
		UserLabeledElement.__init__(self, stylesheet, label)
		UserSelect.__init__(self, dclass, descriptor)
	
	def to_dict(self):
		
		out = dict(**UserLabeledElement.to_dict(self))
		out.update(dict(**UserSelect.to_dict(self)))
		return out

class ComboBox(UserControl):
	
	def __init__(self, stylesheet, label, dclass, descriptor):
		
		UserControl.__init__(self, stylesheet, label, dclass, descriptor)

class CheckBox(UserControl):
	
	def __init__(self, stylesheet, label, dclass, descriptor):
		
		UserControl.__init__(self, stylesheet, label, dclass, descriptor)

class LineEdit(UserControl):
	
	def __init__(self, stylesheet, label, dclass, descriptor):
		
		UserControl.__init__(self, stylesheet, label, dclass, descriptor)

class PlainTextEdit(UserControl):
	
	def __init__(self, stylesheet, label, dclass, descriptor):
		
		UserControl.__init__(self, stylesheet, label, dclass, descriptor)

class Select(UserSelect):
	
	def __init__(self, stylesheet, label, dclass, descriptor):
		
		UserSelect.__init__(self, dclass, descriptor)
		
	def to_dict(self):
		
		return dict(
			stylesheet = "",
			label = "",
			**UserSelect.to_dict(self),
		)

