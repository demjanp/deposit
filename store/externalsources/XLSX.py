from deposit.store.externalsources._ExternalSource import (ExternalSource)

class XLSX(ExternalSource):
	
	def __init__(self, store):

		ExternalSource.__init__(self, store)
	
