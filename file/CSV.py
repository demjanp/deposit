'''
	Deposit file store - CSV
	--------------------------
	
	Created on 10. 4. 2017
	
	@author: Peter Demjan <peter.demjan@gmail.com>
	
	accessible as file.csv
'''

import os
import csv

class CSV(object):
	
	def __init__(self, store):
		
		self.__store = store
	
	def __getattr__(self, key):
		
		return getattr(self.__store, key)
	
	def is_csv(self, uri):
		# return True if uri is a csv file
		
		return (os.path.splitext(uri)[-1].lower() == ".csv")
	
	def get_data(self, uri):
		# return columns, data
		# columns: [name, ...]
		# data: [{column: value, ...}, ...]
		
		path, filename, local = self.get_source(uri)
		if path is None:
			return None
		
		if not local:
			raise NotImplementedError # TODO support remotely stored files

		f = open(path, "r", newline = "")
		reader = csv.reader(f, dialect = csv.excel, quoting=csv.QUOTE_ALL)
		columns = None
		data = []
		for row in reader:
			if columns is None:
				columns = row
			else:
				data.append(dict([(columns[i], row[i]) for i in range(len(row)) if (i < len(columns)) and (columns[i] != "")]))
		f.close()
		columns = [col for col in columns if (col != "")]
		return columns, data
	
	def write(self, path, fields = [], data = []):
		# create a CSV file
		# fields: [name, ...]
		# data: [{field: value, ...}, ...]
		
		f = open(path, "w", newline = "")
		writer = csv.writer(f, dialect=csv.excel, quoting=csv.QUOTE_ALL)
		writer.writerow(fields)
		for row in data:
			writer.writerow([(row[field] if field in row else "") for field in fields])
		f.close()
	