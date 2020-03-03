from deposit.commander.usertools.UserElement import (UserElement)
from deposit.commander.usertools.UserLabeledElement import (UserLabeledElement)
from deposit.commander.usertools.UserSelect import (UserSelect)
from deposit.commander.usertools.UserUnique import (UserUnique)

class UserControl(UserLabeledElement, UserSelect):
	
	def __init__(self, stylesheet, label, dclass, descriptor):
		
		UserLabeledElement.__init__(self, stylesheet, label)
		UserSelect.__init__(self, dclass, descriptor)
	
	def to_markup(self):
		
		return "<%s %s.%s style=\"%s\">%s</>" % (self.__class__.__name__, self.dclass, self.descriptor, self.stylesheet, self.label)
	
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
	
	def to_markup(self):
		
		return "<%s %s.%s/>" % (self.__class__.__name__, self.dclass, self.descriptor)
	
	def to_dict(self):
		
		return dict(
			stylesheet = "",
			label = "",
			**UserSelect.to_dict(self),
		)

class Unique(UserUnique):
	
	def __init__(self, stylesheet, label, dclass):
		
		UserUnique.__init__(self, dclass)
	
	def to_markup(self):
		
		return "<%s %s/>" % (self.__class__.__name__, self.dclass)
	
	def to_dict(self):
		
		return dict(
			stylesheet = "",
			label = "",
			**UserUnique.to_dict(self),
		)

