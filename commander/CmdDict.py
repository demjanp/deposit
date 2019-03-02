from collections import OrderedDict

class CmdDict(OrderedDict):
	
	def __init__(self, *classes):
		
		self.classes = dict([(cls.__name__, cls) for cls in classes]) # {name: class, ...}
		
		OrderedDict.__init__(self)
