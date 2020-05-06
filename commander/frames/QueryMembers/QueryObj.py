from deposit.commander.frames._Frame import (Frame)
from deposit.commander.frames.QueryMembers.QueryObjMembers.BrowseFrame import (BrowseFrame)
from deposit.commander.frames.QueryMembers.QueryObjMembers.ObjView import (ObjView)
from deposit.commander.frames.QueryMembers.QueryObjMembers.RelView import (RelView)

from PySide2 import (QtWidgets, QtCore, QtGui)

class QueryObj(Frame, QtWidgets.QWidget):
	
	def __init__(self, model, view, parent, query):
		
		self.query = query
		self.object = None
		self.row = None
		self.query_lst = None

		self.browse_frame = None
		self.obj_view = None
		self.rel_view = None

		Frame.__init__(self, model, view, parent)
		QtWidgets.QWidget.__init__(self, parent)
		
		self.layout = QtWidgets.QVBoxLayout()
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.layout.setSpacing(0)
		self.setLayout(self.layout)
		
		self.set_up()
	
	def set_up(self):
		
		self.browse_frame = BrowseFrame(self.model, self.view, self)
		self.obj_view = ObjView(self.model, self.view, self, self.query)
		visible_widgets = self.rel_view.visible_widgets if (self.rel_view is not None) else {}  # TODO hack to preserve relation widget visibility
		self.rel_view = RelView(self.model, self.view, self, self.query, visible_widgets)
		self.clear_layout(self.layout)
		
		self.layout.addWidget(self.browse_frame)
		self.layout.addWidget(self.obj_view)
		self.layout.addWidget(self.rel_view)
	
	def set_query(self, query):
		
		self.query = query
		self.set_up()
	
	def filter(self, text):
		
		pass
	
	def get_mime_data(self, indexes):
		
		return self.parent.get_mime_data(indexes)
	
	def get_selected(self):
		
		return self.obj_view.get_selected() + self.rel_view.get_selected()
	
	def get_row_count(self):
		
		return 1
	
	def populate_data(self, query_lst, obj, row):

		self.stop_broadcasts()
		self.query_lst = query_lst
		self.row = row
		self.object = obj
		self.obj_view.populate_data(self.query_lst, self.row)
		self.rel_view.populate_data(self.object)
		self.browse_frame.populate_data(self.object)
		self.populate = False
		self.resume_broadcasts()

	def update(self):

		if self.object is not None:
			self.stop_broadcasts()
			self.obj_view.populate_data(self.query_lst, self.row)
			self.rel_view.populate_data(self.object)
			self.browse_frame.populate_data(self.object)
			self.resume_broadcasts()