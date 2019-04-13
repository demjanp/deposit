from deposit import Broadcasts

from deposit.commander.ViewChild import (ViewChild)
from deposit.commander.usertools.Manager import (Manager)
from deposit.commander.usertools.SearchForm import (SearchForm)
from deposit.commander.usertools.EntryForm import (EntryForm)
from deposit.commander.usertools.Query import (Query)
from deposit.commander.usertools import (UserControls)
from deposit.commander.usertools import (UserGroups)
from deposit.commander.usertools.ColumnBreak import (ColumnBreak)
from deposit.commander.usertools.DialogSearchForm import (DialogSearchForm)
from deposit.commander.usertools.DialogEntryForm import (DialogEntryForm)
from deposit.store.Query.Parse import (find_quotes)

from PySide2 import (QtWidgets, QtCore, QtGui)

SELECTED_STR = "{selected}"

class UserTools(ViewChild):
	
	def __init__(self, model, view):
		
		self.toolbar = None
		self.action_manage = None
		self.edit_toolbar = None
		self.actions = {} # {name: QAction, ...}
		self.manager = None
		self.form_editor = None
		self.entry_form_geometry = None
		
		ViewChild.__init__(self, model, view)
		
		self.set_up()
		
	def set_up(self):
		
		self.view.addToolBarBreak()
		self.toolbar = self.view.addToolBar("User Tools")
		self.toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
		
		self.action_manage = QtWidgets.QAction("User Tools", self.view)
		self.action_manage.setToolTip("Manage User Tools")
		self.action_manage.triggered.connect(self.on_manage)
		
		self.update_tools()
		
		self.connect_broadcast(Broadcasts.STORE_LOADED, self.on_loaded)
		self.connect_broadcast(Broadcasts.STORE_DATA_CHANGED, self.on_data_changed)
	
	def add_tool(self, user_tool):
		
		self.model.user_tools.add(user_tool.to_dict())
	
	def update_tool(self, label, user_tool):
		
		self.model.user_tools.delete(label)
		self.model.user_tools.add(user_tool.to_dict())
	
	def del_tool(self, label):
		
		self.model.user_tools.delete(label)
	
	def user_tool_from_dict(self, data):
		
		user_tool = None
		if data["typ"] == "Query":
			return Query(data["label"], data["value"], self.view)
		else:
			typ = None
			if data["typ"] == "SearchForm":
				typ = SearchForm
			elif data["typ"] == "EntryForm":
				typ = EntryForm
			if typ is not None:
				user_tool = typ(data["label"], self.view)
				if typ in [SearchForm, EntryForm]:
					for element in data["elements"]:
						if element["typ"] in ["Group", "MultiGroup"]:
							user_tool.elements.append(getattr(UserGroups, element["typ"])(element["stylesheet"], element["label"]))
							for member in element["members"]:
								user_tool.elements[-1].members.append(getattr(UserControls, member["typ"])(member["stylesheet"], member["label"], member["dclass"], member["descriptor"]))
						elif element["typ"] == "ColumnBreak":
							user_tool.elements.append(ColumnBreak())
						else:
							user_tool.elements.append(getattr(UserControls, element["typ"])(element["stylesheet"], element["label"], element["dclass"], element["descriptor"]))
				return user_tool
		return None
	
	def export_tool(self, user_tool, path):
		
		with open(path, "w", encoding = "utf-8") as f:
			f.write(user_tool.to_markup())
	
	def import_tool(self, path):
		
		markup = ""
		with open(path, "r", encoding = "utf-8") as f:
			markup = f.read()
		
		elements = []
		# elements = [["Title", title], ["Type", type], tag, group, multigroup, select, ...]
		#	type = "Query" / "SearchForm" / "EntryForm"
		# 	tag = [control type, class.descriptor, label, stylesheet]
		# 	group = [["Group", label], tag, ...], multigroup = [["MultiGroup", label], tag, ...]
		#	select = [class.descriptor]
		collect = []
		idx0 = 0
		while True:
			idx = markup.find("<", idx0)
			value = markup[idx0:idx].strip()
			if value:
				collect[-1].append(value)
			idx0 = idx
			if idx0 == -1:
				break
			idx1 = markup.find(">", idx0)
			if idx1 == -1:
				break
			tag = markup[idx0+1:idx1].strip()
			if tag == "/":
				collect.append(-1)
			else:
				slash_end = tag.endswith("/")
				tag = tag.strip("/").strip()
				if tag:
					tag, quotes = find_quotes(tag)
					stylesheet = ""
					if " style=%(q" in tag:
						idxs1 = tag.find(" style=%(q")
						idxs2 = tag.find(")s", idxs1)
						if idxs2 == -1:
							idx0 = idx1 + 1
							continue
						key = tag[idxs1 + 9:idxs2]
						stylesheet = quotes[key]
						del quotes[key]
						tag = tag[:idxs1]
					tag = [fragment.strip() % quotes for fragment in tag.split(" ")]
					tag = [fragment for fragment in tag if fragment]
					if tag:
						collect.append(tag + [stylesheet])
				if slash_end:
					collect.append(-1)
			idx0 = idx1 + 1
			
		while collect:
			tag = collect.pop(0)
			if not isinstance(tag, list):
				return
			if tag[0] in ["Group", "MultiGroup"]:
				group = [tag]
				while True:
					tag = collect.pop(0)
					if tag == -1:
						break
					group.append(tag.copy())
					if collect.pop(0) != -1:
						return
				elements.append(group)
			else:
				elements.append(tag.copy())
				if collect.pop(0) != -1:
					return
		
		if len(elements) < 3:
			return
		if elements[0][0] != "Title":
			return
		if elements[1][0] != "Type":
			return
		
		data = dict(
			typ = elements[1][1],
			label = elements[0][2],
			elements = []
		)
		if elements[1][1] == "Query":
			if elements[2][0] != "QueryString":
				return
			data["value"] = elements[2][2]
		else:
			for element in elements[2:]:
				if element[0] == "ColumnBreak":
					data["elements"].append(dict(
						typ = "ColumnBreak",
					))
				elif element[0] == "Select":
					dclass, descriptor = element[1].split(".")
					data["elements"].append(dict(
						typ = "Select",
						dclass = dclass,
						descriptor = descriptor,
						label = "",
						stylesheet = "",
					))
				elif isinstance(element[0], list): # Group or MultiGroup
					data["elements"].append(dict(
						typ = element[0][0],
						stylesheet = element[0][1],
						label = element[0][2],
						members = [],
					))
					for typ, select, stylesheet, label in element[1:]:
						dclass, descriptor = select.split(".")
						data["elements"][-1]["members"].append(dict(
							typ = typ,
							dclass = dclass,
							descriptor = descriptor,
							label = label,
							stylesheet = stylesheet,
						))
				elif len(element) == 4:  # tag
					typ, select, stylesheet, label = element
					dclass, descriptor = select.split(".")
					data["elements"].append(dict(
						typ = typ,
						dclass = dclass,
						descriptor = descriptor,
						label = label,
						stylesheet = stylesheet,
					))
		
		self.model.user_tools.add(data)
		
	def update_tools(self):
		
		self.toolbar.clear()
		self.toolbar.addAction(self.action_manage)
		self.toolbar.addSeparator()
		for data in self.model.user_tools.to_list():
			user_tool = self.user_tool_from_dict(data)
			if user_tool is not None:
				self.toolbar.addAction(user_tool)
	
	def start_manager(self):
		
		self.manager = Manager(self.model, self.view)
		self.manager.show()
	
	def get_selected_id(self):
		
		current = self.view.mdiarea.get_current()
		if current:
			if hasattr(current, "get_selected_objects"):
				objects = list(current.get_selected_objects().values())
				if len(objects) == 1:
					return objects[0].id
			if hasattr(current, "object") and (current.object is not None):
				return current.object.id
				
		return None
	
	def open_query(self, form_tool):
		
		querystr = form_tool.value
		id = str(self.get_selected_id())
		while SELECTED_STR in querystr:
			idx1 = querystr.lower().find(SELECTED_STR)
			idx2 = idx1 + len(SELECTED_STR)
			querystr = querystr[:idx1] + id + querystr[idx2:]
		if querystr.startswith("SELECT "):
			self.view.mdiarea.create("Query", querystr)
		else:
			self.model.query(querystr)
	
	def open_search_form(self, form_tool):
		
		dialog = DialogSearchForm(self.model, self.view, form_tool)
		dialog.show()
	
	def open_entry_form(self, form_tool):
		
		dialog = DialogEntryForm(self.model, self.view, form_tool, self.get_selected_id())
		dialog.show()
	
	def on_manage(self, *args):
		
		self.start_manager()
	
	def on_loaded(self, *args):
		
		self.update_tools()
	
	def on_data_changed(self, *args):
		
		self.update_tools()
	
	def on_close(self):
		
		if self.form_editor is not None:
			self.form_editor.close()

