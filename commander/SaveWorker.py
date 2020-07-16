from deposit.store.Store import (Store)

from PySide2 import (QtCore)
from copy import deepcopy

class SaveWorker(QtCore.QObject):
	
	signal_saved = QtCore.Signal(bool)
	
	@QtCore.Slot(object)
	def save(self, data):
		
		data = deepcopy(data)
		store = Store()
		data_source = getattr(store.datasources, data["data_source_class"])()
		data_source.from_dict(data)
		store.set_datasource(data_source)
		result = store.data_source.save()
		store = None
		self.signal_saved.emit(result)
