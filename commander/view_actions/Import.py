from deposit.commander.ExternalLstView import ExternalLstView
from PyQt5 import (QtWidgets)

def get_state(model, view):
	
	active = view.active()
	return isinstance(active, ExternalLstView) and model.has_store(), False

def triggered(model, view, checked):

	active = view.active()
	has_selected = (len(active.selected()) > 0)
	grid = active.grid_data(selected = has_selected)
	if not grid:
		return
	
	# collect fields, targets, merges
	fields = [] # [name, ...]
	targets = []# [traverse, traverse#Class.Descriptor, ...]; traverse: C.D / C.R.C.D
				#	specify multiple targets by separating traverses by ;
				#	in case traverse#Class.Descriptor is used, handle value as a quantifier of traverse summed over the specified Descriptor. Traverse must end in a Descriptor which is filled with the original column name
				#		e.g.: C1.R1.C2.D1 # CX.D2 -> C1.R1.C2.D1 = column name; CX.D2 = value; CX can be C1 or C2
	merges = []	# [True/False, ...]; in order of targets; specifies whether imported row should be merged with existing Objects based on this Descriptor
	rows = len(grid)
	for value in grid[0]:
		field, target, merge = value.relation
		if target:
			fields.append(field)
			targets.append(target)
			merges.append(merge)
	if not fields:
		return
	
	reply = QtWidgets.QMessageBox.question(view, "Import Data?", "Import %d rows and %d columns?" % (rows, len(fields)), QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.Yes)
	if reply != QtWidgets.QMessageBox.Yes:
		return
	
	# collect data
	data = [] # [{column: DLabel, ...}, ...]; in order of rows
	for row_data in grid:
		data.append([])
		for value in row_data:
			if value.relation[1]:
				data[-1].append(value)
	
	model.actions.import_data(data, fields, targets, merges)
	
