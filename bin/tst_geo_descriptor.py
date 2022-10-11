
import deposit

if __name__ == "__main__":
	
	coords_point = [1,2]
	
	coords_multipoint_z = [
		[1,2,7],
		[3,4,8],
		[5,6,9],
	]
	
	coords_linestring_m = [
		[1,2,7,10],
		[3,4,8,11],
		[5,6,9,12],
	]
	
	coords_polygon_1 = [
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
	
	coords_polygon_z_2 = [
		# exterior
		[
			[1,2,7],
			[3,4,8],
			[5,6,9],
		],
	]

	coords_multipolygon_z_1 = [
		[
			# exterior 1
			[
				(1,2,25),
				(3,4,26),
				(5,6,27),
			],
			# holes 1
			[
				[7,8,28],
				[9,10,29],
				[11,12,30],
			]
		],
		[
			# exterior 2
			[
				[13,14,31],
				[15,16,32],
				[17,18,33],
			],
			# holes 2
			[
				[19,20,34],
				[21,22,35],
				[23,24,36],
			]
		]
	]

	coords_multipolygon_m_2 = [
		[
			# exterior 1
			[
				(1,2,25,37),
				(3,4,26,18),
				[5,6,27,39],
			],
		],
		[
			# exterior 2
			[
				[13,14,31,40],
				[15,16,32,41],
				[17,18,33,42],
			],
			# holes 2
			[
				[19,20,34,43],
				[21,22,35,44],
				[23,24,36,45],
			]
		]
	]
	
	store = deposit.Store()
	
	obj = store.add_object()
	obj.set_geometry_descriptor("Geo Point", "Point", coords_point, srid = 1234, srid_vertical = 5678)
	obj.set_geometry_descriptor("Geo MultiPoint", "MultiPointZ", coords_multipoint_z, srid = 1234)
	obj.set_geometry_descriptor("Geo LineString", "LineString", coords_linestring_m)
	obj.set_geometry_descriptor("Geo Polygon 1", "POLYGON", coords_polygon_1)
	obj.set_geometry_descriptor("Geo Polygon 2", "PolygonZ", coords_polygon_z_2)
	obj.set_geometry_descriptor("Geo MultiPolygon 1", "MultiPolygonZ", coords_multipolygon_z_1)
	obj.set_geometry_descriptor("Geo MultiPolygon 2", "MULTIPOLYGON", coords_multipolygon_m_2)
	
	expected = [
		['SRID=1234;VERT_SRID=5678;POINT(1 2)', 'Point', [1, 2], 1234, 5678],
		['SRID=1234;MULTIPOINTZ(1 2 7, 3 4 8, 5 6 9)', 'MultiPointZ', [[1, 2, 7], [3, 4, 8], [5, 6, 9]], 1234, None],
		['LINESTRINGM(1 2 7 10, 3 4 8 11, 5 6 9 12)', 'LineString', [[1, 2, 7, 10], [3, 4, 8, 11], [5, 6, 9, 12]], None, None],
		['POLYGON((1 2, 3 4, 5 6, 1 2), (7 8, 9 10, 11 12, 7 8), (13 14, 15 16, 17 18, 13 14))', 'POLYGON', [[[1, 2], [3, 4], [5, 6], [1, 2]], [[7, 8], [9, 10], [11, 12], [7, 8]], [[13, 14], [15, 16], [17, 18], [13, 14]]], None, None],
		['POLYGONZ((1 2 7, 3 4 8, 5 6 9, 1 2 7))', 'PolygonZ', [[[1, 2, 7], [3, 4, 8], [5, 6, 9], [1, 2, 7]]], None, None],
		['MULTIPOLYGONZ(((1 2 25, 3 4 26, 5 6 27, 1 2 25), (7 8 28, 9 10 29, 11 12 30, 7 8 28)), ((13 14 31, 15 16 32, 17 18 33, 13 14 31), (19 20 34, 21 22 35, 23 24 36, 19 20 34)))', 'MultiPolygonZ', [[[[1, 2, 25], [3, 4, 26], [5, 6, 27], [1, 2, 25]], [[7, 8, 28], [9, 10, 29], [11, 12, 30], [7, 8, 28]]], [[[13, 14, 31], [15, 16, 32], [17, 18, 33], [13, 14, 31]], [[19, 20, 34], [21, 22, 35], [23, 24, 36], [19, 20, 34]]]], None, None],
		['MULTIPOLYGONM(((1 2 25 37, 3 4 26 18, 5 6 27 39, 1 2 25 37)), ((13 14 31 40, 15 16 32 41, 17 18 33 42, 13 14 31 40), (19 20 34 43, 21 22 35 44, 23 24 36 45, 19 20 34 43)))', 'MULTIPOLYGON', [[[[1, 2, 25, 37], [3, 4, 26, 18], [5, 6, 27, 39], [1, 2, 25, 37]]], [[[13, 14, 31, 40], [15, 16, 32, 41], [17, 18, 33, 42], [13, 14, 31, 40]], [[19, 20, 34, 43], [21, 22, 35, 44], [23, 24, 36, 45], [19, 20, 34, 43]]]], None, None],
	]
	for name, exp in zip(obj.get_descriptor_names(ordered = True), expected):
		geo = obj.get_descriptor(name)
		geometry_type, coords, srid, srid_vertical = geo.value
		wkt = geo.to_dict()["value"]
		
		print([wkt, geometry_type, coords, srid, srid_vertical] == exp)
