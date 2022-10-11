from shapely import wkt, geometry

if __name__ == "__main__":
	
	coords1 = [1,2,-1]
	
	coords2 = [
		[1,2,-1],
		[3,4,-1],
		[5,6,-1],
	]
	
	coords3 = [
		[	# exterior
			(1,2,-1),
			(3,4,-1),
			(5,6,-1),
		],
		[	# holes
			[
				[7,8,-1],
				[9,10,-1],
				[11,12,-1],
			],
			[
				[13,14,-1],
				[15,16,-1],
				[17,18,-1],
			]
		]
	]

	coords4 = [
		[
			[ # exterior 1
				[1,2,-1],
				[3,4,-1],
				[5,6,-1],
			],
			[ # holes 1
				[
					[7,8,-1],
					[9,10,-1],
					[11,12,-1],
				]
			]
		],
		[
			[ # exterior 2
				[13,14,-1],
				[15,16,-1],
				[17,18,-1],
			],
			[ # holes 2
				[
					[19,20,-1],
					[21,22,-1],
					[23,24,-1],
				]
			]
		]
	]
	
	wktstr = geometry.Point(coords1).wkt
	print(wktstr)
	geo = wkt.loads(wktstr)
#	print(geo.geom_type, list(geo.coords))
	
	wktstr = geometry.MultiPoint(coords2).wkt
	print(wktstr)
	geo = wkt.loads(wktstr)
#	print(geo.geom_type, [list(point.coords) for point in geo.geoms])
	
	wktstr = geometry.LineString(coords2).wkt
	print(wktstr)
	geo = wkt.loads(wktstr)
#	print(geo.geom_type, list(geo.coords))
	
	wktstr = geometry.Polygon(coords3[0], holes = coords3[1]).wkt
	print(wktstr)
	geo = wkt.loads(wktstr)
#	print(geo.geom_type, [list(geo.exterior.coords), [list(polygon.coords) for polygon in geo.interiors]])
	
	wktstr = geometry.MultiPolygon(coords4).wkt
	print(wktstr)
	geo = wkt.loads(wktstr)
#	print(geo.geom_type, [[list(polygon.exterior.coords), [list(interior.coords) for interior in polygon.interiors]] for polygon in geo.geoms])
