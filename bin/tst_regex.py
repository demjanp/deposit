import re

def decode(name, matchstrs):
	
	for typ, matchstr in matchstrs:
		res = re.match(matchstr, name)
		if res:
			return(typ, res.groups())
	return None

if __name__ == "__main__":
	
	tables = [
		"#reserved name",
		"##reserved name",
		"#@reserved name",
		"@class name",
		"@@class name",
		"@#class name",
		"#source name#label text#target name",
		"##source name#label text##target name",
		"#@source name#@label text##target name",
	]
	
	matchstrs = [
		("relation", '#(.*?[^#])#(.*?[^#])#(.*)'),
		("class", '@(.*)'),
		("reserved", '#(.*)'),
	]
	
	for table in tables:
		typ, data = decode(table, matchstrs)
		print(table, typ, data)
	