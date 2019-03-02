from deposit.DModule import (DModule)

from deposit.store.externalsources.CSV import (CSV)
from deposit.store.externalsources.Shapefile import (Shapefile)
from deposit.store.externalsources.XLSX import (XLSX)

class ExternalSources(DModule):
	
	def __init__(self, store):
		
		self.store = store
		self._classes = dict([(cls.__name__, cls) for cls in [CSV, Shapefile, XLSX]]) # {name: DataSource, ...}

		DModule.__init__(self)

	def __getattr__(self, name):
		
		def clsfunc(url):
			
			return self._classes[name](self.store, url)
		
		if name in self._classes:
			return clsfunc
		return self.__getattribute__(name)

