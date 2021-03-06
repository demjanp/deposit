import winreg

class Registry(object):
	
	def __init__(self, app_name):
		
		self.app_name = app_name
		self._vars = {}
		self.key = None
		
		self.key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, "SOFTWARE\%s" % (self.app_name))
		for i in range(winreg.QueryInfoKey(self.key)[1]):
			var, value, _ = winreg.EnumValue(self.key, i)
			self._vars[var] = value
	
	def get(self, var):
		
		if var not in self._vars:
			return ""
		return self._vars[var]
	
	def set(self, var, value):
		
		self._vars[var] = value
		winreg.SetValueEx(self.key, var, 0, winreg.REG_SZ, value)
	
	def vars(self):
		
		return list(self._vars.keys())