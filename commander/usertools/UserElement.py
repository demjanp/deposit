
class UserElement(object):
	
	def __init__(self):
		
		pass
	
	def to_dict(self):
		
		return dict(
			typ = self.__class__.__name__,
		)

