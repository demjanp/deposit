'''
	
	User tools:
		Query (opens a query)
		Search Form (opens a search dialog, see C14Search plugin)
		Entry Form (opens a form dialog, see C14Form plugin)

	Specified in .cfg files in the "user_tools" folder.
	
	filename: _ordering.cfg
	contents:
	--------------------------------
	[name]
	_separator
	...
	
	
	filename: [name].cfg
	contents:
	--------------------------------
	<Title>[name of tool]</>
	<Type [Query / SearchForm / EntryForm] />
	[content specification]


	Query - content specification:
	--------------------------------
	<QueryString>[query string]</>


	SearchForm - content specification:
	--------------------------------
	<[control type] [class].[descriptor]>[label]</>
	<[control type] [class].[descriptor] bold>[label]</>
	<Select [class.descriptor]/>
	...


	EntryForm - content specification:
	--------------------------------
	<[control type] [class].[descriptor]>[label]</>
	<[control type] [class].[descriptor] bold>[label]</>
	<Group>[label]
		<[control type] [class].[descriptor]>[label]</>
		...
	</>

	<ColumnBreak/>

	<MultiGroup>[label]
		<[control type] [class].[descriptor]>[label]</>
		...
	</>
	...


	control type:
	---------------------------
	LineEdit
	PlainTextEdit
	ComboBox
	CheckBox

	TODO future:
	Resource (image or other file)
	Coordinates
	
'''

from deposit.commander.ViewChild import (ViewChild)
from deposit.store.Query.Parse import (find_quotes)
from deposit.commander.userforms.SearchForm import (SearchForm)
from deposit.commander.userforms.EntryForm import (EntryForm)

from PyQt5 import (QtWidgets, QtCore, QtGui)
import os

DC_USER_TOOLS_DIR = "user_tools"
DC_ORDERING = "_ordering.cfg"

def parse(data):
	# returns [["Title", title], ["Type", type], tag, group, multigroup, select, ...]
	#	type = "Query" / "SearchForm" / "EntryForm"
	# 	tag = [control type, class.descriptor, label]
	# 	group = [["Group", title], tag, ...], multigroup = [["MultiGroup", title], tag, ...]
	#	select = [class.descriptor]
	
	elements = []
	collect = []
	idx0 = 0
	while True:
		idx = data.find("<", idx0)
		value = data[idx0:idx].strip()
		if value:
			collect[-1].append(value)
		idx0 = idx
		if idx0 == -1:
			break
		idx1 = data.find(">", idx0)
		if idx1 == -1:
			break
		tag = data[idx0+1:idx1].strip()
		if tag == "/":
			collect.append(-1)
		else:
			slash_end = tag.endswith("/")
			tag = tag.strip("/").strip()
			if tag:
				tag, quotes = find_quotes(tag)
				tag = [fragment.strip() % quotes for fragment in tag.split(" ")]
				tag = [fragment for fragment in tag if fragment]
				if tag:
					collect.append(tag)
			if slash_end:
				collect.append(-1)
		idx0 = idx1 + 1
		
	while collect:
		tag = collect.pop(0)
		if not isinstance(tag, list):
			return []
		if tag[0] in ["Group", "MultiGroup"]:
			group = [tag]
			while True:
				tag = collect.pop(0)
				if tag == -1:
					break
				group.append(tag.copy())
				if collect.pop(0) != -1:
					return []
			elements.append(group)
		else:
			elements.append(tag.copy())
			if collect.pop(0) != -1:
				return []
	
	if len(elements) < 3:
		return []
	if elements[0][0] != "Title":
		return []
	if elements[1][0] != "Type":
		return []
	
	return elements

class UserToolbar(ViewChild):
	
	def __init__(self, model, view):
		
		self.toolbar = None
		self.actions = {} # {name: QAction, ...}
		
		ViewChild.__init__(self, model, view)
		
		self.set_up()
	
	def set_up(self):
		
		path = os.path.join(DC_USER_TOOLS_DIR, DC_ORDERING)
		if not os.path.isfile(path):
			return
		ordering = []
		with open(path, "r") as f:
			ordering = [name.strip() for name in f.read().split("\n")]
		collect = []
		found = 0
		for name in ordering:
			if not name:
				continue
			if os.path.isfile(os.path.join(DC_USER_TOOLS_DIR, "%s.cfg" % (name))):
				collect.append(name)
				found += 1
			elif name == "_separator":
				collect.append(name)
		ordering = collect
		if not found:
			return
		
		self.view.addToolBarBreak()
		self.toolbar = self.view.addToolBar("User Toolbar")
		self.toolbar.setIconSize(QtCore.QSize(36,36))
			
		for name in ordering:
			if name == "_separator":
				self.toolbar.addSeparator()
				continue
			with open(os.path.join(DC_USER_TOOLS_DIR, "%s.cfg" % (name)), "r", encoding = "utf-8") as f:
				data = f.read()
				elements = parse(data)
				if not elements:
					continue
				if elements[0][0] != "Title":
					continue
				title = elements[0][1]
				self.actions[name] = QtWidgets.QAction(title, self.view)
				self.actions[name].setData(elements)
				self.toolbar.addAction(self.actions[name])
		
		self.toolbar.actionTriggered.connect(self.on_triggered)
	
	def on_triggered(self, action):
		
		elements = action.data()  # [["Title", title], ["Type", type], tag, group, multigroup, ...]; tag = [control type, class.descriptor, label], group = [["Group", title], tag, ...], multigroup = [["MultiGroup", title], tag, ...]
		if elements[1][1] == "Query":
			if elements[2][0] != "QueryString":
				return
			self.view.mdiarea.create("Query", elements[2][1])
		elif elements[1][1] == "SearchForm":
			dialog = SearchForm(self.model, self.view, elements)
			dialog.show()
		elif elements[1][1] == "EntryForm":
			dialog = EntryForm(self.model, self.view, elements)
			dialog.show()

