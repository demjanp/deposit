from PyQt5 import (uic, QtWidgets, QtCore, QtGui)
from collections import defaultdict
import os

class View(*uic.loadUiType(os.path.join(os.path.dirname(__file__), "ui", "View.ui"), resource_suffix = "", from_imports = True, import_from = "deposit.commander.plugins.C14SearchMembers.ui")):

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
			ctrl.editTextChanged.connect(self.on_combo)
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
			queries.append("(C_14_Analysis.analyses.Sample.~contains.Context.Name == \"%s\") and (C_14_Analysis.analyses.Sample.~contains.Context.~contains.Site.~contains.Cadastre.~contains.Country)" % value_context)
		elif value_site:
			queries.append("(C_14_Analysis.analyses.Sample.~contains.Context.~contains.Site.Name == \"%s\") and (C_14_Analysis.analyses.Sample.~contains.Context.~contains.Site.~contains.Cadastre.~contains.Country)" % value_site)
		elif value_cadastre:
			queries.append("(C_14_Analysis.analyses.Sample.~contains.Context.~contains.Site.~contains.Cadastre.Name == \"%s\") and (C_14_Analysis.analyses.Sample.~contains.Context.~contains.Site.~contains.Cadastre.~contains.Country)" % value_cadastre)
		elif value_country:
			queries.append("(C_14_Analysis.analyses.Sample.~contains.Context.~contains.Site.~contains.Cadastre.~contains.Country.Name == \"%s\")" % value_country)
		else:
			queries.append("C_14_Analysis.analyses.Sample.~contains.Context.~contains.Site.~contains.Cadastre.~contains.Country")
		
		if value_dating:
			queries.append("(C_14_Analysis.analyses.Sample.~contains.Context.~dates.Relative_Dating.Name == \"%s\")" % value_dating)
		else:
			queries.append("(C_14_Analysis.analyses.Sample.~contains.Context.~dates.Relative_Dating)")
		
		if value_material:
			queries.append("(C_14_Analysis.analyses.Sample.descr.Material.Name == \"%s\")" % value_material)
		else:
			queries.append("(C_14_Analysis.analyses.Sample.descr.Material)")
		
		if queries:
			query = "SELECT C_14_Analysis.Lab_Code, C_14_Analysis.C_14_Activity_BP, Material.Name, Context.Name, Country.Name, Relative_Dating.Name WHERE %s" % (" and ".join(queries))
			print(query)  # DEBUG
			self.parent.parent.view.mdiarea.create("Query", query)
	
	def on_activate(self):
		
		self.reset()
		self.activateWindow()
		self.raise_()
	
	@QtCore.pyqtSlot(str)
	def on_combo(self, value):
		
		if self.sender() == self.comboCountry:
			id1 = self.get_obj_by_descr("Country", "Name", value)
			if id1 is None:
				values_cadastre = self.get_all_values("Cadastre", "Name")
				values_site = self.get_all_values("Site", "Name")
				values_context = self.get_all_values("Context", "Name")
				values_relative_dating = self.get_all_values("Relative_Dating", "Name")
				values_material = self.get_all_values("Material", "Name")
			else:
				values_cadastre = []
				values_site = []
				values_context = []
				values_relative_dating = []
				values_material = []
				for row in self.store.query("SELECT Material.Name WHERE id(Country) == %d" % id1):
					value = row["Material.Name"].descriptor.label.value
					if value not in values_material:
						values_material.append(value)
				for id2 in self.store.objects[id1].relations["contains"]:
					name = self.store.objects[id2].descriptors["Name"].label.value
					if name not in values_cadastre:
						values_cadastre.append(name)
					for id3 in self.store.objects[id2].relations["contains"]:
						name = self.store.objects[id3].descriptors["Name"].label.value
						if name not in values_site:
							values_site.append(name)
							for id4 in self.store.objects[id3].relations["contains"]:
								name = self.store.objects[id4].descriptors["Name"].label.value
								if name not in values_context:
									values_context.append(name)
									for id5 in self.store.objects[id4].relations["~dates"]:
										name = self.store.objects[id5].descriptors["Name"].label.value
										if name not in values_relative_dating:
											values_relative_dating.append(name)
			self.set_control(self.comboCadastre, values_cadastre)
			self.set_control(self.comboSite, values_site)
			self.set_control(self.comboContext, values_context)
			self.set_control(self.comboRelative_Dating, values_relative_dating)
			self.set_control(self.comboMaterial, values_material)
		
		elif self.sender() == self.comboCadastre:
			id1 = self.get_obj_by_descr("Cadastre", "Name", value)
			if id1 is None:
				values_site = self.get_all_values("Site", "Name")
				values_context = self.get_all_values("Context", "Name")
				values_relative_dating = self.get_all_values("Relative_Dating", "Name")
				values_material = self.get_all_values("Material", "Name")
			else:
				values_material = []
				for row in self.store.query("SELECT Material.Name WHERE id(Cadastre) == %d" % id1):
					value = row["Material.Name"].descriptor.label.value
					if value not in values_material:
						values_material.append(value)
				for id2 in self.store.objects[id1].relations["~contains"]:
					values = self.get_all_values("Country", "Name")
					value = self.store.objects[id2].descriptors["Name"].label.value
					self.set_control(self.comboCountry, values, value)
					break
				values_site = []
				values_context = []
				values_relative_dating = []
				for id2 in self.store.objects[id1].relations["contains"]:
					name = self.store.objects[id2].descriptors["Name"].label.value
					if name not in values_site:
						values_site.append(name)
					for id3 in self.store.objects[id2].relations["contains"]:
						name = self.store.objects[id3].descriptors["Name"].label.value
						if name not in values_context:
							values_context.append(name)
							for id4 in self.store.objects[id3].relations["~dates"]:
								name = self.store.objects[id4].descriptors["Name"].label.value
								if name not in values_relative_dating:
									values_relative_dating.append(name)
			self.set_control(self.comboSite, values_site)
			self.set_control(self.comboContext, values_context)
			self.set_control(self.comboRelative_Dating, values_relative_dating)
			self.set_control(self.comboMaterial, values_material)

		elif self.sender() == self.comboSite:
			id1 = self.get_obj_by_descr("Site", "Name", value)
			if id1 is None:
				values_context = self.get_all_values("Context", "Name")
				values_relative_dating = self.get_all_values("Relative_Dating", "Name")
				values_material = self.get_all_values("Material", "Name")
			else:
				values_material = []
				for row in self.store.query("SELECT Material.Name WHERE id(Site) == %d" % id1):
					value = row["Material.Name"].descriptor.label.value
					if value not in values_material:
						values_material.append(value)
				for id2 in self.store.objects[id1].relations["~contains"]:
					values = self.get_all_values("Cadastre", "Name")
					value = self.store.objects[id2].descriptors["Name"].label.value
					self.set_control(self.comboCadastre, values, value)
					for id3 in self.store.objects[id2].relations["~contains"]:
						values = self.get_all_values("Country", "Name")
						value = self.store.objects[id3].descriptors["Name"].label.value
						self.set_control(self.comboCountry, values, value)
						break
					break
				values_context = []
				values_relative_dating = []
				for id2 in self.store.objects[id1].relations["contains"]:
					name = self.store.objects[id2].descriptors["Name"].label.value
					if name not in values_context:
						values_context.append(name)
					for id3 in self.store.objects[id2].relations["~dates"]:
						name = self.store.objects[id3].descriptors["Name"].label.value
						if name not in values_relative_dating:
							values_relative_dating.append(name)
			self.set_control(self.comboContext, values_context)
			self.set_control(self.comboRelative_Dating, values_relative_dating)
			self.set_control(self.comboMaterial, values_material)
		
		elif self.sender() == self.comboContext:
			id1 = self.get_obj_by_descr("Context", "Name", value)
			if id1 is None:
				values_relative_dating = self.get_all_values("Relative_Dating", "Name")
				values_material = self.get_all_values("Material", "Name")
			else:
				values_material = []
				for row in self.store.query("SELECT Material.Name WHERE id(Context) == %d" % id1):
					value = row["Material.Name"].descriptor.label.value
					if value not in values_material:
						values_material.append(value)
				for id2 in self.store.objects[id1].relations["~contains"]:
					values = self.get_all_values("Site", "Name")
					value = self.store.objects[id2].descriptors["Name"].label.value
					self.set_control(self.comboSite, values, value)
					for id3 in self.store.objects[id2].relations["~contains"]:
						values = self.get_all_values("Cadastre", "Name")
						value = self.store.objects[id3].descriptors["Name"].label.value
						self.set_control(self.comboCadastre, values, value)
						for id4 in self.store.objects[id3].relations["~contains"]:
							values = self.get_all_values("Country", "Name")
							value = self.store.objects[id4].descriptors["Name"].label.value
							self.set_control(self.comboCountry, values, value)
							break
						break
					break
				values_relative_dating = []
				for id2 in self.store.objects[id1].relations["~dates"]:
					name = self.store.objects[id2].descriptors["Name"].label.value
					if name not in values_relative_dating:
						values_relative_dating.append(name)
			self.set_control(self.comboRelative_Dating, values_relative_dating)
			self.set_control(self.comboMaterial, values_material)
	
	@QtCore.pyqtSlot()
	def on_resetButton_clicked(self):
		
		self.reset()
	
	@QtCore.pyqtSlot()
	def on_searchButton_clicked(self):
		
		self.search()

