from deposit.utils.fnc_files import (as_url, url_to_path)

import os

class AbstractExternalsource(object):
	
	def __init__(self):
		
		self._path = None
	
	def get_name(self):
		
		if self._path is not None:
			name = os.path.basename(self._path)
			if name:
				return name
		return self.__class__.__name__
	
	def get_url(self):
		
		if self._path is not None:
			return as_url(self._path)
		return None
	
	def get_path(self):
		
		return self._path
	
	def set_path(self, path = None, url = None):
		
		if (path is None) and (url is not None):
			path = url_to_path(url)
		if path is None:
			self._path = None
			return
		self._path = os.path.normpath(os.path.abspath(path))
	
	def get_header_data(self, get_header, n_cols):
		# get_header(col, user_role = False) = column_name or (class_name, descriptor_name) if user_role = True
		
		return [get_header(col) for col in range(n_cols)]
	
	def get_row_data(self, row, get_item, n_cols):
		# get_item(row, col) = deposit_gui.QueryItem
		
		data = []
		for col in range(n_cols):
			item = get_item(row, col)
			if item.is_geometry():
				data.append(item.value.wkt)
			elif item.is_resource():
				data.append(item.value.url)
			else:
				data.append(item.get_display_data())
		return data
	
	def sheets(self):
		# re-implement
		
		return []
	
	def column_count(self, sheet):
		# re-implement
		
		return 0
	
	def row_count(self, sheet):
		# re-implement
		
		return 0
	
	def column_name(self, sheet, column_idx):
		# re-implement
		
		pass
	
	def data(self, sheet, row_idx, column_idx):
		# re-implement
		
		pass
	
	def save(self, get_header, get_item, n_rows, n_cols, path = None, url = None, *args, **kwargs):
		# get_header(col, user_role = False) = column_name or (class_name, descriptor_name) if user_role = True
		# get_item(row, col) = deposit_gui.QueryItem
		#
		# re-implement
		
		pass
	
	def load(self, path = None, url = None, *args, **kwargs):
		# re-implement
		
		pass
	
	def __str__(self):
		
		return self.__class__.__name__

