class Query(object):
	
	def __init__(self):
		
		pass
	
	def __getitem__(self, idx):
		
		return idx


query = Query()

print(query[10, 2])
print(query[10, "Class", "Descriptor"])
print(query[10, "Class.Descriptor"])