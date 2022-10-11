from deposit.store.dgeometry import coords_to_wkt, wkt_to_coords

if __name__ == "__main__":
	
	coords1 = [1,2,-1]
	
	coords2 = [
		[1,2,-1],
		[3,4,-1],
		[5,6,-1],
	]
	
	coords3 = [
		# exterior
		[
			[1,2],
			[3,4],
			[5,6],
		],
		# holes
		[
			[7,8],
			[9,10],
			[11,12],
		],
		[
			[13,14],
			[15,16],
			[17,18],
		]
	]

	coords4 = [
		[
			# exterior 1
			[
				(1,2,-1),
				(3,4,-1),
				(5,6,-1),
			],
			# holes 1
			[
				[7,8,-1],
				[9,10,-1],
				[11,12,-1],
			]
		],
		[
			# exterior 2
			[
				[13,14,-1],
				[15,16,-1],
				[17,18,-1],
			],
			# holes 2
			[
				[19,20,-1],
				[21,22,-1],
				[23,24,-1],
			]
		]
	]
	
	wkt = coords_to_wkt("Point", coords1, srid = 123)
	print(wkt)
	print(coords_to_wkt(*wkt_to_coords(wkt)))
	wkt = coords_to_wkt("MultiPoint", coords2, srid_vertical = 456)
	print(wkt)
	print(coords_to_wkt(*wkt_to_coords(wkt)))
	wkt = coords_to_wkt("LineString", coords2)
	print(wkt)
	print(coords_to_wkt(*wkt_to_coords(wkt)))
	wkt = coords_to_wkt("Polygon", coords3)
	print(wkt)
	print(coords_to_wkt(*wkt_to_coords(wkt)))
	wkt = coords_to_wkt("MultiPolygon", coords4)
	print(wkt)
	print(coords_to_wkt(*wkt_to_coords(wkt)))
