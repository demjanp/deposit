from shapefile import (Reader, Writer)
from shapely.geometry import shape as shapely_shape
from shapely import wkt as shapely_wkt

from deposit.store.dgeometry import DGeometry
from deposit.utils.fnc_geometry import (add_srid_to_wkt, split_srid_from_wkt)

if __name__ == "__main__":
	
	'''
	path = "c:/documents_synced/Deposit/deposit/bin/samples/polygon.shp"
#	path = "c:/data_processed/sample_data/more/georef_tst.shp"
#	path = "c:/data_processed/sample_data/more/graves.shp"
#	path = "c:/data_processed/sample_data/more/test_poly.sbn"
	sf = Reader(path)
	for shape in sf.shapes():
		g = shapely_shape(shape.__geo_interface__)
		print(g.wkt)
	'''
	
	wkt = "POLYGON ((-7986762.389182076 -12647076.523558993, 9639195.9869439 -12316589.804006632, 9969682.706496246 -26858005.464310557, -8096924.629032861 -26858005.464310557, -7986762.389182076 -12647076.523558993))"
	
	wkt = add_srid_to_wkt(wkt, 1234, 5678)
	
	geo = DGeometry((wkt))
	
	wkt, srid, srid_vertical = split_srid_from_wkt(geo.wkt)
	
	print()
	print(geo.geometry_type)
	print(wkt)
	print(geo.srid)
	print(geo.srid_vertical)
	print(geo.coords)
	print()
	
	'''
	g = shapely_wkt.loads(wkt)
	print()
	print(g)
	print(type(g))
	print()
	'''
	
#	w = Writer('test.shp')
#	w.field('name', 'C')
#	w.record('polygon')
#	w.shape(g.__geo_interface__)
#	w.close()
	
	