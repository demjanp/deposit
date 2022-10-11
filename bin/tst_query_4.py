#!/usr/bin/env python
# -*- coding: utf-8 -*-

import deposit

import os
import shutil

if __name__ == "__main__":
	
	store = deposit.Store()
	
	finds = store.add_class("Find")
	
	f111 = finds.add_member()
	f111.set_descriptor("Name", "A1.F1.1")
	f111.set_descriptor("Material", "Bone")
	
	for obj in store.get_objects():
		print(obj)
	
	for querystr in [
#		"SELECT Find.Name",
		"SELECT Find WHERE Find == 1",
	]:
		query = store.get_query(querystr)
		print()
		print("\"%s\"" % querystr)
		print()
		print(query.columns)
		print()
		print([row for row in query])
		print()
