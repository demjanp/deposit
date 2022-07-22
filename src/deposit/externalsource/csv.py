from deposit.externalsource.abstract_externalsource import AbstractExternalsource

import csv

class CSV(AbstractExternalsource):
	
	def __init__(self):
		
		AbstractExternalsource.__init__(self)
		
		self._columns = {} # {column_idx: name, ...}
		self._data = [] # [{column_idx: value, ...}, ...]
	
	def sheets(self):
		
		return ["0"]
	
	def column_count(self, sheet):
		
		return len(self._columns)
	
	def row_count(self, sheet):
		
		return len(self._data)
	
	def column_name(self, sheet, column_idx):
		
		if column_idx not in self._columns:
			return None
		return self._columns[column_idx]
	
	def data(self, sheet, row_idx, column_idx):
		
		if row_idx > len(self._data) - 1:
			return None
		if column_idx not in self._data[row_idx]:
			return None
		return self._data[row_idx][column_idx]
	
	def save(self, get_header, get_item, n_rows, n_cols, path = None, url = None, *args, **kwargs):
		# get_header(col, user_role = False) = column_name or (class_name, descriptor_name) if user_role = True
		# get_item(row, col) = deposit_gui.QueryItem
		
		self.set_path(path, url)
		path = self.get_path()
		if path is None:
			return False
		
		with open(path, "w", newline = "") as f:
			writer = csv.writer(f, dialect=csv.excel, quoting=csv.QUOTE_ALL)
			writer.writerow(self.get_header_data(get_header, n_cols))
			for row in range(n_rows):
				writer.writerow(self.get_row_data(row, get_item, n_cols))
		
		return True
	
	def load(self, path = None, url = None, *args, **kwargs):
		
		self.set_path(path, url)
		path = self.get_path()
		if path is None:
			return False
		
		self._columns.clear()
		self._data.clear()
		
		with open(path, "r", newline = "") as f:
			reader = csv.reader(f, dialect = csv.excel, quoting=csv.QUOTE_ALL)
			idx_lookup = {} # {i: idx, ...}
			for row in reader:
				if not self._columns:
					idx = 0
					for i, value in enumerate(row):
						value = value.strip()
						if value:
							self._columns[idx] = value
							idx_lookup[i] = idx
							idx += 1
					if not self._columns:
						return True
				else:
					self._data.append(dict([(idx_lookup[i], value.strip()) for i, value in enumerate(row) if i in idx_lookup]))
		return True

