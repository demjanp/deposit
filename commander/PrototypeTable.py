from PyQt5 import (QtWidgets, QtCore, QtGui)
from deposit.store.Resources import (Resources)
from natsort import (natsorted)

class PrototypeTableItem(QtWidgets.QTableWidgetItem):
	
	def __init__(self):
		
		super(PrototypeTableItem, self).__init__()
	
	def __lt__(self, other):
		
		values = [("" if val is None else val) for val in [self.data(QtCore.Qt.DisplayRole), other.data(QtCore.Qt.DisplayRole)]]
		return values == natsorted(values)

class PrototypeTable(object):
	
	def __init__(self):
		
		self._model = None
		
		super(PrototypeTable, self).__init__()
		
		self._icon_wf_remote = QtGui.QIcon(":res/res/link_wf_remote.svg")
		self._icon_wf = QtGui.QIcon(":res/res/link_wf.svg")
		self._icon_link_remote = QtGui.QIcon(":res/res/link_remote.svg")
		self._icon_link = QtGui.QIcon(":res/res/link.svg")
		self._icon_3d = QtGui.QIcon(":res/res/3d_obj.svg")
		self._icon_geo = QtGui.QIcon(":res/res/geometry.svg")
	
	def _get_table_item(self, row, column):
		
		item = PrototypeTableItem()
		
		data = self._model.table_data(row, column)
		
		item.setData(QtCore.Qt.UserRole, data)
		
		read_only = False
		if "value" in data["data"]:
			if "read_only" in data["data"]:
				read_only = data["data"]["read_only"]
			label = data["data"]["value"]
			# value is geometry
			if data["data"]["geometry"]:
				read_only = True
				item.setData(QtCore.Qt.DecorationRole, self._icon_geo)
				label = label.split("(")[0].strip()
			# value is a resource
			elif data["data"]["storage_type"]:
				read_only = True
				if data["data"]["obj3d"]:
					item.setData(QtCore.Qt.DecorationRole, self._icon_3d)
				elif data["data"]["storage_type"] in (Resources.RESOURCE_ONLINE, Resources.RESOURCE_CONNECTED_ONLINE):
					item.setData(QtCore.Qt.DecorationRole, self._icon_link_remote)
				else:
					item.setData(QtCore.Qt.DecorationRole, self._icon_link)
			item.setData(QtCore.Qt.DisplayRole, label)
			if read_only:
				item.setData(QtCore.Qt.BackgroundRole, QtCore.QVariant(QtGui.QColor(240, 240, 240, 255)))
				item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled | QtCore.Qt.ItemIsSelectable)
			else:
				item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable)
		else:
			item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable)
		return item, data
	
	def _count_visible(self):
		# return number of visible rows (e.g. after filtering)
		
		return len([row for row in range(self.rowCount()) if not self.isRowHidden(row)])
	
	def _set_item(self, row, column):
		# re-implement
		
		pass
	
	def on_set_model(self):
		
		self._populate()
	
	def resizeEvent(self, event):
		
		super(PrototypeTable, self).resizeEvent(event)
		
	def showEvent(self, event):
		
		self._populate()
		super(PrototypeTable, self).showEvent(event)
		self._parent_view.on_count_changed(self._count_visible())
		
		