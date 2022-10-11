#!/usr/bin/env python
# -*- coding: utf-8 -*-

import deposit

import os
import shutil

if __name__ == "__main__":
	
	store = deposit.Store()
	
	resp = store.load(path = "legacy_db/LAP_example.pickle")
	print("loaded:", resp)
	
	print()
	print(store.get_relation_labels())
	print()
	raise
	
#	query = store.get_query("SELECT Sample.*")
	query = store.get_query("SELECT !*")
	print()
	print(query.columns)
	print()
	for row in query:
		print(row)
	
