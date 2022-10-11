#!/usr/bin/env python
# -*- coding: utf-8 -*-

import deposit

import os
import shutil

if __name__ == "__main__":
	
	store = deposit.Store()
	
	areas = store.add_class("Area")
	a = areas.add_member()
	a = areas.add_member()
	a = areas.add_member()
#	a.set_descriptor("Name", "A1")

	query = store.get_query("SELECT Area.*")
	print()
	print(query.columns)
	print()
	for row in query:
		print(row)
