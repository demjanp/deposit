from deposit.commander.frames.QueryMembers.QueryItem import (QueryItem)

from PySide2 import QtCore
from collections import defaultdict

class QuerySelectionRow(object):

	def __init__(self, model, view, indexes, col_min, col_max):
		# columns = {column: QModelIndex, ...}

		self.model = model
		self.view = view
		self._indexes = indexes
		self._col_min = col_min
		self._col_max = col_max
		self._pos = 0
	
	@property
	def indexes(self):		
		
		return {0:self._indexes}
	
	def __len__(self):

		return self._col_max - self._col_min + 1

	def __getitem__(self, column):

		column += self._col_min
		if column in self._indexes:
			return self._indexes[column].data(QtCore.Qt.UserRole)
		return QueryItem(None, None)

	def __iter__(self):

		for column in range(self.__len__()):
			yield self[column]

	def __next__(self):

		if self._pos < self.__len__():
			self._pos += 1
			return self[self._pos - 1]
		self._pos = 0
		raise StopIteration()

class QuerySelection(object):

	def __init__(self, model, view, indexes):
		# indexes = QModelIndexList
		
		self.model = model
		self.view = view
		self._indexes = indexes # {row: {column: QModelIndex, ...}, ...}
		self._pos = 0
		self._col_min, self._col_max = None, -1
		self._row_min, self._row_max = None, -1

	@property
	def indexes(self):

		if isinstance(self._indexes, defaultdict):
			return self._indexes
		collect = defaultdict(dict)
		for index in self._indexes:
			row, column = index.row(), index.column()
			self._row_min = row if (self._row_min is None) else min(self._row_min, row)
			self._row_max = max(self._row_max, row)
			self._col_min = column if (self._col_min is None) else min(self._col_min, column)
			self._col_max = max(self._col_max, column)
			collect[row][column] = index
		self._indexes = collect
		return self._indexes
	
	def rows(self):
		# return [row, ...]; row = row number in table (not selection)

		return list(self.indexes.keys())

	def row_count(self):

		return self.__len__()

	def column_count(self):

		return self._col_max - self._col_min + 1
	
	def update(self, indexes):
		
		self.indexes
		row0 = 0 if self._row_min is None else self._row_min
		for row in indexes:
			for column in indexes[row]:
				index = indexes[row][column]
				row += row0
				self._row_min = row if (self._row_min is None) else min(self._row_min, row)
				self._row_max = max(self._row_max, row)
				self._col_min = column if (self._col_min is None) else min(self._col_min, column)
				self._col_max = max(self._col_max, column)
				self._indexes[row][column] = index
	
	def __len__(self):

		return len(self.indexes)

	def __getitem__(self, row):

		return QuerySelectionRow(self.model, self.view, self.indexes[self.rows()[row]], self._col_min, self._col_max)

	def __iter__(self):

		for row in range(self.__len__()):
			yield self[row]

	def __next__(self):

		if self._pos < self.__len__():
			self._pos += 1
			return self[self._pos - 1]
		self._pos = 0
		raise StopIteration()

