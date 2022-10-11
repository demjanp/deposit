# -*- coding: utf-8 -*-
#!/usr/bin/env python
#
from deposit.utils.fnc_files import (get_free_subfolder, extract_filename, sanitize_filename, get_unique_path)
import os

if __name__ == "__main__":
	
	fn1 = "name.ext"
	fn2 = "ščščťť.šľš"
	fn3 = '''!@#$%^&() .xx.yy.zz'''
	fn4 = "noext"
	
	dir1 = "some_path"
	dir2 = "ščščťť.šľš"
	dir3 = '''!@#$%^&() .xx.yy.zz'''
	
	for dirname in [dir1,dir2,dir3]:
		for fn in [fn1,fn2,fn3,fn4]:
			path = os.path.join(dirname, fn)
			filename = extract_filename(path)
			path_dst = get_unique_path(sanitize_filename(filename), "test_db")
			print(path)
			print(path_dst)
			print("\t", filename)
