from deposit.DModule import (DModule)

from deposit.store.datasources.DB import (DB)
from deposit.store.datasources.DBRel import (DBRel)
from deposit.store.datasources.JSON import (JSON)
from deposit.store.datasources.RDFGraph import (RDFGraph)

class DataSources(DModule):
	
	def __init__(self, store):
		
		self.store = store
		self._classes = dict([(cls.__name__, cls) for cls in [DB, DBRel, JSON, RDFGraph]]) # {name: DataSource, ...}

		DModule.__init__(self)

	def __getattr__(self, name):
		
		def clsfunc(*args, **kwargs):
			
			return self._classes[name](self.store, *args, **kwargs)
		
		if name in self._classes:
			return clsfunc
		return self.__getattribute__(name)
	