
class Parse(object):
	
	def __init__(self, store, querystr):
		
		self.store = store
		self.querystr = querystr
		self.selects = [] # [[class, descriptor], [class], ...]
		self.chains = [] # [[class], [class, descriptor], [class, relation, class], [class, relation, class, descriptor], ...]
		self.eval_str = "" # e.g. "%s and %s > 3"; num. of %s == num. of chains
		self.quantifiers = {} # {alias: [select_query, chain_query], ...}
		
		self._process()
		
	def _find_quotes(self, qry):
		
		evals = []
		quotes = {}
		q = 0
		i0 = 0
		to_find = None
		for i in range(len(qry)):
			if qry[i] == to_find:
				quotes["q%d" % q] = qry[i0:i]
				q += 1
				i0 = i + 1
				to_find = None
			elif qry[i] in "\"'":
				evals.append(qry[i0:i])
				i0 = i + 1
				to_find = qry[i]
			elif i == len(qry) - 1:
				evals.append(qry[i0:])
		
		eval_str = ""
		for i, ev in enumerate(evals):
			eval_str += ev
			if i < len(quotes):
				eval_str += "%%(q%d)s" % i
		
		return eval_str, quotes
		
	def _check_select(self, fragment, pos):
		
		if pos == 0:
			return (fragment in self.store.class_names + ["*", "!*"])
		else:
			return (fragment in self.store.descriptor_names + ["*", "!*"])
	
	def _find_selects(self, qry_select, quotes):
		
		collect = []
		fragments = qry_select.split(",")
		for fragment in fragments:
			fragment = fragment.strip()
			selects = [select % quotes for select in fragment.split(".")]
			if all(self._check_select(selects[i], i) for i in range(len(selects))):
				collect.append(selects)
			else:
				return []
		return collect
	
	def _check_where(self, fragment, pos):
		if not fragment:
			return False
		if pos % 2 == 0:
			# should be class or obj(id)
			if fragment.startswith("obj(") and fragment.endswith(")"):
				return True
			valid_names = self.store.class_names + ["*", "!*"]
			return (fragment in valid_names) or ((fragment[0] == "!") and (fragment[1:] in valid_names))
		else:
			# should be relation or descriptor
			valid_names = self.store.relation_names + self.store.descriptor_names + ["*", "!*"]
			return (fragment in valid_names) or ((fragment[0] == "!") and (fragment[1:] in valid_names))
	
	def _find_chain(self, qry, quotes):
		
		fragments = qry.split(".")
		collect = []
		for fragment in fragments:
			if self._check_where(fragment % quotes, len(collect)):
				collect.append(fragment % quotes)
			else:
				found = None
				for i in range(len(fragment)):
					if (fragment[i] in " ()[]") and self._check_where(fragment[:i], len(collect)):
						found = fragment[:i] % quotes
				if not found is None:
					collect.append(found)
					if collect:
						return collect, len(".".join(collect))
				return [], len(".".join(collect))
		
		if collect:
			return collect, len(qry)
		return [], len(".".join(collect))
	
	def _collect_chains(self, qry, quotes):
		
		eval_str = ""
		chains = []
		i0, i1 = 0, 0
		i0_last = 0
		while i0 < len(qry):
			if (i0 == 0) or (qry[i0 - 1] in " ()[]"):
				chain, l = self._find_chain(qry[i0:], quotes)
				i1 = i0 + l
				if chain:
					if (len(chain) % 2 == 0) and (chain[-1].strip("!") in self.store.relation_names):
						chain.append("*")
					chains.append(chain)
					eval_str += qry[i0_last:i0] + ("%%s" if quotes else "%s")
					i0_last = i1
				i0 = i1 + 1
			else:
				i0 += 1
		eval_str += qry[i0_last:]
		
		if quotes:
			eval_str = eval_str % dict([(key, "\"%s\"" % quotes[key]) for key in quotes])
		
		return eval_str, chains
	
	def _collect_quantifiers(self, qry, quotes):
		
		quantifiers = {}
		started = True
		qry_where = ""
		while qry:
			idx_q = qry.lower().find(" quantify ")
			if idx_q > -1:
				if started:
					qry_where = qry[:idx_q]
				idx_a = qry.lower().find(" as ", idx_q)
				if idx_a == -1:
					raise Exception("QUANTIFY without AS in query:", self.querystr)
				qry_chain = qry[idx_q + 10:idx_a]
				alias = qry[idx_a + 4:].lstrip()
				idx = alias.find(" ")
				if idx == -1:
					qry = ""
				else:
					qry = alias[idx:]
					alias = alias[:idx]
				quantifiers[alias.strip() % quotes] = qry_chain.strip() % quotes
			else:
				if started:
					qry_where = qry
				qry = ""
			started = False
		
		# find sum strings
		for alias in quantifiers:
			qry = quantifiers[alias]
			idx = qry.lower().find(" sum ")
			if idx > -1:
				qry_chain = qry[:idx].strip()
				qry_sum = qry[idx + 4:].strip()
			else:
				qry_chain = qry.strip()
				qry_sum = "*"
			quantifiers[alias] = [qry_sum, qry_chain]
		
		return qry_where, quantifiers
	
	def _process(self):
		
		qry = self.querystr.strip()
		
		qry, quotes = self._find_quotes(qry)
		
		if not qry.lower().startswith("select "):
			return
		idx_where = qry.lower().find(" where ")
		if idx_where > -1:
			qry_select = qry[7:idx_where].strip()
			qry_where = qry[idx_where + 6:].strip()
		else:
			idx_quan = qry.lower().find(" quantify ")
			if idx_quan > -1:
				qry_select = qry[7:idx_quan].strip()
				qry_where = qry[idx_quan:]
			else:
				qry_select = qry[7:].strip()
				qry_where = ""
		
		# collect selects
		self.selects = self._find_selects(qry_select, quotes) # [[class, descriptor], [class], ...]
		if not self.selects:
			return
		
		self.quantifiers = {} # {alias: [select_query, chain_query], ...}
		if qry_where:
			qry_where, self.quantifiers = self._collect_quantifiers(qry_where, quotes)
		
		# collect where chains
		self.eval_str = ""
		self.chains = []
		if qry_where:
			self.eval_str, self.chains = self._collect_chains(qry_where, quotes)
			# if not self.chains:
			# 	raise Exception("No chain specified in WHERE string:", qry_where)
		
		
		