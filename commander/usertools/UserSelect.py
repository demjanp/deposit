from deposit.commander.usertools.UserElement import (UserElement)

class UserSelect(UserElement):
	
	def __init__(self, dclass, descriptor):
		
		self.dclass = dclass
		self.descriptor = descriptor
		
		UserElement.__init__(self)
	
	def to_dict(self):
		
		return dict(
			dclass = self.dclass,
			descriptor = self.descriptor,
			**UserElement.to_dict(self),
		)

