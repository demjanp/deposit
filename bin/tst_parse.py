from deposit.query.parse import Parse
#import re
#import ast

if __name__ == "__main__":
	
#	querystr = "SELECT Class1.Descr1, Class2.Descr2"
#	querystr = "SELECT Class1.Descr1, Class2.Descr2, [My class].Descr1, [SELECT].[WHERE] , [SELECT].Descr1, Class1.[WHERE], SUM(Class1.Descr1) AS [Sum Descr1], COUNT([My class].Descr2) AS Count_Descr2 RELATED Class1.relation1.Class2, [My class].[rel 2].Class2 WHERE Class1.Descr1 == 8 and Class1.Descr2 == \" SELECT1 \" and ' \"SELECT2\" ' and [SELECT].[WHERE] > 'SELECT'+' WHERE ' GROUP BY Class2.Descr2, [My class].Descr1, [SELECT].[WHERE]"
#	querystr = "SELECT Class1.Descr1, Class2.Descr2 WHERE Class1.Descr1 == [1,2,3][1]"
#	querystr = "SELECT Class1.Descr1, Class2.Descr2 WHERE Class1.Descr1[1] == 'x'"
	querystr = "SELECT Class1.Descr1, Class2, [My class] WHERE (Class2 is None) and ([My class] is None)"
#	querystr = "SELECT Class1, [My class], *.*, *.Descr1, Class1.*, Class2.Descr2, [My class].*, [SELECT].[WHERE] , [SELECT].Descr1, *.[WHERE], COUNT(Class1) AS [Count Class1], SUM(Class1.Descr1) AS [Sum Descr1], COUNT([My class].Descr2) AS Count_Descr2"
	
	classes = set([
		"Class1",
		"Class2",
		"SELECT",
		"My class",
	])
	descriptors = set([
		"Descr1",
		"Descr2",
		"WHERE",
	])
	
	P = Parse(querystr, classes, descriptors)
	
#	SELECT c.d, c.d COUNT(c.d) AS a, SUM(c.d) AS a, RELATED c1.r.c2, c1.r.c2 WHERE [expr] GROUP BY c.d, c.d
	
	print("columns:")
	for class_name, descriptor_name in P.columns:
		print("\t", class_name, ".", descriptor_name)
	
	print("SELECT:")
	for class_name, descriptor_name in P.selects:
		print("\t", class_name, ".", descriptor_name)
	print("GROUP BY:")
	for class_name, descriptor_name in P.group_by:
		print("\t", class_name, ".", descriptor_name)
	print("COUNT:")
	for alias, class_name, descriptor_name in P.counts:
		print("\t", alias, ":", class_name, ".", descriptor_name)
	print("SUM:")
	for alias, class_name, descriptor_name in P.sums:
		print("\t", alias, ":", class_name, ".", descriptor_name)
	print("RELATED:")
	for class1, relation, class2 in P.relations:
		print("\t", class1, ".", relation, ".", class2)
	print("WHERE:")
	print(P.where_expr)
	for key in P.where_vars:
		print("\t", key, P.where_vars[key])
	
