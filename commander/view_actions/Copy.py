from PyQt5 import (QtWidgets)

def get_state(model, view):
	
	active = view.active()
	return (not active is None) and hasattr(active, "grid_data") and (len(active.selected()) > 0), False

def triggered(model, view, checked):
	
	active = view.active()
	grid = active.grid_data(selected = True)
	if grid:
		QtWidgets.QApplication.clipboard().setText("\n".join(["\t".join([str(val) for val in row]) for row in grid[1:]]))
	