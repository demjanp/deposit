from deposit.store.externalsources._ExternalSource import (ExternalSource)
from deposit.store.DLabel.DString import (DString)
from deposit.store.Conversions import (as_path)

import csv

class CSV(ExternalSource):
	
	def __init__(self, store, url):

		self._columns = {} # {column_idx: name, ...}
		self._data = {} # [{column_idx: value, ...}, ...]
		
		ExternalSource.__init__(self, store, url)
	
	def load(self):
		
		self._columns = {}
		self._data = []
		
		path = as_path(self.url)
		if path is None:
			return False
		
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
					self._data.append(dict([(idx_lookup[i], DString(value.strip())) for i, value in enumerate(row) if i in idx_lookup]))
		return True
	
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
	
	def export_data(self, query):
		
		def get_value(item):
			
			value = item.descriptor
			if value is None:
				return ""
			value = value.label.value
			if value is None:
				return ""
			return value
		
		path = as_path(self.url, check_if_exists = False)
		if path is None:
			return
		
		with open(path, "w", newline = "") as f:
			writer = csv.writer(f, dialect=csv.excel, quoting=csv.QUOTE_ALL)
			writer.writerow(query.columns)
			for row in query:
				writer.writerow([get_value(row[column]) for column in query.columns])


