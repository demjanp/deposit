from deposit import res

from PyQt5 import (uic, QtWidgets, QtCore, QtGui)
from collections import defaultdict
import os

class View(*uic.loadUiType(os.path.join(os.path.dirname(res.__file__), "C14Search", "View.ui"), resource_suffix = "", from_imports = True, import_from = "deposit.res.C14Search")):

	def __init__(self, parent):

		self.parent = parent
		# model = self.parent.parent.model
		# view = self.parent.parent.view
		
		QtWidgets.QMainWindow.__init__(self)
		self.setupUi(self)
		
		self._keys = [
			["comboCountry", "Country.Name"], 
			["comboCadastre", "Cadastre.Name"], 
			["comboSite", "Site.Name"], 
			["comboContext", "Context.Name"], 
			["comboRelative_Dating", "Relative_Dating.Name"], 
			["comboMaterial", "Material.Name"],
		]
		
		self.store = self.parent.parent.model
	
	def set_control(self, ctrl, values, value = ""):
		
		if value is None:
			value = ""
		if (not value) and (len(values) == 1):
			value = values[0]
		values = [val for val in values if (val not in ["", value, None])]
		values = [value] + sorted(values)
		ctrl.blockSignals(True)
		ctrl.clear()
		if values:
			ctrl.addItems(values)
		ctrl.blockSignals(False)
	
	def get_obj_by_descr(self, cls, descr, value):
		
		if (descr is None) or (value is None):
			return None
		for id in self.store.classes[cls].objects:
			value2 = self.store.objects[id].descriptors[descr].label.value
			if value2 is not None:
				if str(value2) == str(value):
					return id
		return None
	
	def get_all_values(self, cls, descr):
		
		cls = self.store.classes[cls]
		values = []
		for id in cls.objects:
			value = self.store.objects[id].descriptors[descr].label.value
			if value not in values:
				values.append(value)
		return values
	
	def reset(self):
		
		for key, cls in self._keys:
			cls, descr = cls.split(".")
			values = self.get_all_values(cls, descr)
			ctrl = self.__dict__[key]
			self.set_control(ctrl, values)
	
	def search(self):
		
		def get_value(key):
			
			ctrl = self.__dict__[key]
			return ctrl.currentText().strip()
		
		value_country = get_value("comboCountry")
		value_cadastre = get_value("comboCadastre")
		value_site = get_value("comboSite")
		value_context = get_value("comboContext")
		value_dating = get_value("comboRelative_Dating")
		value_material = get_value("comboMaterial")
		
		queries = []
		if value_context:
			queries.append("(Context.Name == '%s')" % value_context)
		if value_site:
			queries.append("(Site.Name == '%s')" % value_site)
		if value_cadastre:
			queries.append("(Cadastre.Name == '%s')" % value_cadastre)
		if value_country:
			queries.append("(Country.Name == '%s')" % value_country)
		if value_dating:
			queries.append("(Relative_Dating.Name == '%s')" % value_dating)
		if value_material:
			queries.append("(Material.Name == '%s')" % value_material)
		
		query = "SELECT C_14_Analysis.Lab_Code, C_14_Analysis.C_14_Activity_BP, Material.Name, Context.Name, Country.Name, Relative_Dating.Name"
		if queries:
			query += " WHERE %s" % (" and ".join(queries))
		self.parent.parent.view.mdiarea.create("Query", query)
	
	def on_activate(self):
		
		self.reset()
		self.activateWindow()
		self.raise_()
	
	@QtCore.pyqtSlot()
	def on_resetButton_clicked(self):
		
		self.reset()
	
	@QtCore.pyqtSlot()
	def on_searchButton_clicked(self):
		
		self.search()

