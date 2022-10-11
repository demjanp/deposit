#from deposit.store.query.Parse import Parse
import ast

class SelectsToVarsTransformer(ast.NodeTransformer):
	
	def __init__(self, classes, descriptors):
		# classes = {class_name, ...}
		# descriptors = {descriptor_name, ...}
		
		ast.NodeTransformer.__init__(self)
		
		self.selects = {}  # {(class_name, descriptor_name): variable_name, ...}
		
		self._classes = classes
		self._descriptors = descriptors
		self._done = set([])
	
	def visit_Attribute(self, node):
		
		self.generic_visit(node)
		
		if (type(node.value) is ast.Name) and \
			(node.value.id not in __builtins__.__dict__) and \
			(node.value.id in self._classes) and \
			(node.attr not in __builtins__.__dict__) and \
			(node.attr in self._descriptors):
				key = (node.value.id, node.attr)
				if key in self.selects:
					name = self.selects[key]
				else:
					name = "_".join([node.value.id, node.attr])
					while name in self._done:
						name += "_"
					self._done.add(name)
					self.selects[key] = name
				return ast.Name(id = name, ctx = node.ctx)
		
		return node

if __name__ == "__main__":
	
#	querystr = "SELECT Class1.Descr1, Class2.Descr2 RELATED Class1.relation1.Class2 WHERE Class1.Descr1 == 8 COUNT Class1.Descr2 == 4 AS Count_Descr2_4 SUM Class1.Descr1 AS Sum_Descr1"
	
#	P = Parse(None, querystr)
	
	values = {("c1","a"): 11, ("c1","b"): 2, ("c1","c"): 3, ("c1","s"): 'abc ', ("a_b","c_d"): 11, ("a","b_c_d"): 2, ("a_b_c","d"): 3}
	
	classes = set([])
	descriptors = set([])
	for cls, descr in values:
		classes.add(cls)
		descriptors.add(descr)
	
#	eq = "c1.a == c1.b + c1.c*3"
	eq = "a_b.c_d == a.b_c_d + a_b_c.d*3"
#	eq = "c1.b + c1.c*3"
#	eq = "str(c1.b + c1.c*3) + 'X'"
#	eq = "c1.s.endswith('c')"
#	eq = "c1.s.strip().endswith('c')"
	
	tree = ast.parse(eq)
	transformer = SelectsToVarsTransformer(classes, descriptors)
	tree = transformer.visit(tree)
	
	data = {}
	for key in transformer.selects:
		# key = (cls, descr)
		data[transformer.selects[key]] = values[key]
	
	eq = ast.unparse(tree)
	
	print(eq)
	print(data)
	
	res = eval(eq, data)
	
	print()
	print(res)
	print()

	