from deposit import Broadcasts
from deposit.commander.dialogs._Dialog import (Dialog)

from PySide2 import (QtWidgets, QtCore, QtGui)

class AddRelation(Dialog):
	
	def title(self):
		
		return "Add Relation"
	
	def set_up(self, objects_classes):
		
		self.objects_classes = objects_classes
		self.objects_classes2 = []
		self.is_objects = False
		
		self.setMinimumWidth(256)
		self.setModal(False)
		self.layout = QtWidgets.QVBoxLayout()
		self.setLayout(self.layout)
		
		self.labels_layout = QtWidgets.QHBoxLayout()
		self.labels = QtWidgets.QWidget()
		self.labels.setLayout(self.labels_layout)
		self.label_source = QtWidgets.QLabel("")
		self.label_relation = QtWidgets.QLineEdit()
		self.label_relation.textEdited.connect(self.on_relation_edited)
		self.label_target = QtWidgets.QLabel("")
		self.labels_layout.addWidget(self.label_source)
		self.labels_layout.addWidget(self.label_relation)
		self.labels_layout.addWidget(self.label_target)
		self.layout.addWidget(self.labels)

		self.connect_broadcast(Broadcasts.VIEW_ACTION, self.update_label)

		self.is_objects = (self.objects_classes[0].__class__.__name__ == "DObject")
		
		self.update_label([])
	
	def on_relation_edited(self, text):

		self.view.toolbar.set_combo_value("RelationName", text.strip())

	def update_label(self, args):
		
		rel = self.view.toolbar.get_combo_value("RelationName")
		self.label_relation.setText(rel)
		fm = QtGui.QFontMetrics(QtGui.QFont("", 0))
		width = 50
		if rel != "":
			width = max(width, fm.width(rel))
		self.label_relation.setFixedSize(width, fm.height())

		self.objects_classes2 = []
		current = self.view.mdiarea.get_current()
		if current:
			if self.is_objects:
				if current.__class__.__name__ == "QueryObj":
					self.objects_classes2 = [current.object]
				else:
					for row in current.get_selected():
						for item in row:
							if (item.element.__class__.__name__ == "DObject") and (not item.element in self.objects_classes2) and (not item.element in self.objects_classes):
								self.objects_classes2.append(item.element)

				obj1 = "obj(%s) \u2192 " % (", ".join([str(obj.id) for obj in self.objects_classes]))
				self.label_source.setText(obj1)
				obj2 = " \u2192 "
				if self.objects_classes2:
					obj2 = " \u2192 obj(%s)" % (", ".join([str(obj.id) for obj in self.objects_classes2]))
				self.label_target.setText(obj2)
			else:
				if current.__class__.__name__ == "ClassVis":
					for cls in current.graph_view.get_selected()[0]:
						cls = self.model.classes[cls]
						if cls not in self.objects_classes:
							self.objects_classes2.append(cls)
				else:
					for name in current.query.classes:
						if name != "!*":
							self.objects_classes2.append(self.model.classes[name])
				cls1 = "%s \u2192 " % (", ".join([cls.name for cls in self.objects_classes]))
				self.label_source.setText(cls1)
				cls2 = " \u2192 "
				if self.objects_classes2:
					cls2 = " \u2192 %s" % (", ".join([cls.name for cls in self.objects_classes2]))
				self.label_target.setText(cls2)

		self.set_enabled((rel != "") and (self.objects_classes2 != []))

	def process(self):
		
		rel = self.label_relation.text()
		if rel and self.objects_classes and self.objects_classes2:
			if self.is_objects:
				for obj1 in self.objects_classes:
					for obj2 in self.objects_classes2:
						obj1.relations.add(rel, obj2)
			else:
				for cls1 in self.objects_classes:
					for cls2 in self.objects_classes2:
						cls1.add_relation(rel, cls2.name)
	
