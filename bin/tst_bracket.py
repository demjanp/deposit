import re

#substr = "Area.Name, _Area_, *.[My Name], Area.* WHERE My Name@ One-two (One.[My Name] is not None) and Find.[Name].startswith('A1.') Name"
substr = "Area.contains.Feature, [Feature].Name.Find"
#substr = "SELECT Area.Name, _Area_, Feature.[My Name] WHERE My Name@ One-two (One.[My Name] is not None) and Find.[Name].startswith('A1.')"
#substr = "Area"

classes = set(["Area", "Feature", "Find", "Name", "One", "One-two", "My Name"])
descriptors = set(["Name", "My Name"])

substr1 = substr

names = []  # [[i, j, text, bracketed], ...]
for classname in sorted(list(classes), key = lambda name: len(name))[::-1]:
	for m in re.finditer(r"(\A|[^a-zA-Z0-9_])(%s)([^a-zA-Z0-9_]|\Z)" % (classname), substr):
		i, j = m.start(0), m.end(0)
		found = False
		if (substr[i] == "[") and (substr[j-1] == "]"):
			names.append([i, j, substr[i:j], True])
			substr = substr[:i] + (j-i)*" " + substr[j:]
			found = True
		else:
			if substr[i:].startswith(classname):
				i -= 1
			if substr[:j].endswith(classname):
				j += 1
			if substr[i+1:j-1].isidentifier():
				i += 1
				j -= 1
				names.append([i, j, substr[i:j], False])
				substr = substr[:i] + len(substr[i:j])*" " + substr[j:]
				found = True
		if found:
			if substr[:i].endswith("*."):
				names.append([i-2, i-1, "*", False])
				substr = substr[:i-2] + " " + substr[i-1:]
			if substr[j:].startswith(".*"):
				names.append([j+1, j+2, "*", False])
				substr = substr[:j+1] + " " + substr[j+2:]

names = sorted(names, key = lambda row: row[0])
fragments = []  # [[text, is_class], ...]
j_last = 0
for i, j, name, bracketed in names:
	if i > j_last:
		fragments.append([substr[j_last:i], False])
	if bracketed:
		name = name[1:-1]
	fragments.append([name, True])
	j_last = j
if j_last < len(substr):
	fragments.append([substr[j_last:], False])


for text, is_class in fragments:
	if is_class:
		text = "[%s]" % text
	print(text)
		

substr2 = "".join([text for text, _ in fragments])

print()
print("*%s*" % substr1)
print("*%s*" % substr)
print("*%s*" % substr2)
print()