from deposit.commander.toolbar._Tool import (Tool)

from PySide2 import (QtCore, QtWidgets)
from collections import defaultdict
from urllib.parse import urlparse
import json

class Paste(Tool):
	
	def icon(self):
		
		return ""
	
	def help(self):
		
		return "Paste"
	
	def get_mime_formats(self, mime_data):
		
		try:
			return mime_data.formats()
		except:
			return []
	
	def enabled(self):
		
		def is_selected():
			
			current = self.view.mdiarea.get_current()
			if current.__class__.__name__ == "QueryLst":
				for row in current.get_selected():
					for item in row:
						if item.element.__class__.__name__ == "DDescriptor":
							return True
						return False
			return False
		
		return is_selected() and ((QtWidgets.QApplication.clipboard().text() != "") or (self.get_mime_formats(QtWidgets.QApplication.clipboard().mimeData()) != []))
	
	def shortcut(self):
		
		return "Ctrl+V"
	
	def triggered(self, state):
		
		def deposit_to_mime(element):
			
			data = QtCore.QMimeData()
			data.setData("application/deposit", bytes(json.dumps([element]), "utf-8"))
			return data
		
		def url_to_mime(url):
			
			data = QtCore.QMimeData()
			data.setUrls([url])
			return data
		
		def check_url(text):
			
			parsed = urlparse(text)
			return parsed.scheme in ["file", "http", "https", "ftp", "ftps"]
		
		def text_to_mime(text):
			
			if check_url(text):
				return url_to_mime(text)
			data = QtCore.QMimeData()
			data.setData("text/plain", bytes(text, "utf-8"))
			return data
		
		data = []
		cb = QtWidgets.QApplication.clipboard()
		mime_data = cb.mimeData()
		formats = self.get_mime_formats(mime_data)
		if formats:
			found_elements = False
			if "application/deposit" in formats:
				elements = json.loads(mime_data.data("application/deposit").data().decode("utf-8"))
				collect = defaultdict(dict)
				row_min, column_min = None, None
				row_max, column_max = 0, 0
				for element in elements:
					if [element["identifier"], element["connstr"]] != [self.model.identifier, self.model.connstr]:
						continue
					row, column = element["row"], element["column"]
					row_min = row if (row_min is None) else min(row_min, row)
					column_min = column if (column_min is None) else min(column_min, column)
					row_max = max(row_max, row)
					column_max = max(column_max, column)
					collect[row][column] = deposit_to_mime(element)
					found_elements = True
				
				if found_elements:
					for r in range(row_max - row_min + 1):
						data.append([])
						for c in range(column_max - column_min + 1):
							if (column_min + c) in collect[row_min + r]:
								data[-1].append(collect[row_min + r][column_min + c])
							else:
								data[-1].append(None)
			if (not found_elements) and mime_data.hasUrls():
				data = [[url_to_mime(url)] for url in mime_data.urls()]
		else:
			text = QtWidgets.QApplication.clipboard().text()
			for row in text.split("\n"):
				if row:
					data.append([text_to_mime(value.strip()) for value in row.split("\t")])
		
		if not data:
			return
		
		current = self.view.mdiarea.get_current()
		indexes = current.get_selected().indexes
		for row0 in indexes:
			for column0 in indexes[row0]:
				break
			break
		row_diff = len(data) - (current.get_row_count() - row0)
		if row_diff > 0:
			cls = current.query.classes[0]
			self.stop_broadcasts()
			for i in range(row_diff):
				if cls == "!*":
					self.model.objects.add()
				else:
					self.model.classes[cls].objects.add()
			self.resume_broadcasts()
			current.parent.update()
		
		rows = len(data)
		columns = min(len(data[0]), current.get_column_count() - column0)
		for row in range(rows):
			for column in range(columns):
				if data[row][column] is None:
					continue
				item = current.get_query_item(row0 + row, column0 + column)
				if item.element.__class__.__name__ == "DDescriptor":
					current.process_drop(item, data[row][column])

