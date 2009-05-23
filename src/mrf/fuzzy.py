
import lexer
import sys

class FuzzySymbol(lexer.ParserSymbol):

	def evaluate(self, classes, input_values, cache):
		pass

class And(FuzzySymbol):

	def evaluate(self, classes, input_values, cache):
		lhs = self.children[0].evaluate(classes, input_values, cache)
		rhs = self.children[2].evaluate(classes, input_values, cache)
		return min(lhs, rhs)
		
class Or(FuzzySymbol):
	
	def evaluate(self, classes, input_values, cache):
		lhs = self.children[0].evaluate(classes, input_values, cache)
		rhs = self.children[2].evaluate(classes, input_values, cache)
		return max(lhs, rhs)
		
class Is(FuzzySymbol):

	def _get_dom_for_input_class(self, classes, input_name, input_value, class_name, cache):
		if cache.has_key((input_name,class_name)):
			return cache[(input_name,class_name)]
		else:
			dom = classes[input_name][class_name].get_dom(input_value)
			cache[(input_name,class_name)] = dom
			return dom 

	def evaluate(self, classes, input_values, cache):
		return self._get_dom_for_input_class(classes, self.get_flv_name(),
			input_values[self.get_flv_name()], self.get_class_name(), cache)
	
	def get_flv_name(self):
		return self.children[0].data
	
	def get_class_name(self):
		return self.children[2].data
		
class  Term(FuzzySymbol):
	
	def evaluate(self, classes, input_values, cache):
		if isinstance(self.children[0],Is):
			return self.children[0].evaluate(classes, input_values, cache)
		else:
			return self.children[1].evaluate(classes, input_values, cache)
		
class Expression(FuzzySymbol):

	def evaluate(self, classes, input_values, cache):
		return self.children[0].evaluate(classes, input_values, cache)
		
class Rule(FuzzySymbol):

	def evaluate(self, classes, input_values, cache):
		# evaluate a rule and return output class dom
		return self.children[1].evaluate(classes, input_values, cache)
		
	def _get_output_is(self):
		return self.children[3]
		
	def get_output_class(self):
		return self._get_output_is().get_class_name()
		
	def get_output_name(self):
		return self._get_output_is().get_flv_name()

class RuleParser(object):

	def __init__(self):
		self.lexer = lexer.Lexer([
			("whitespace","[ \n\r\t]+",None,lexer.Lexer.cb_ignore),
			("if","IF"),
			("and","AND"),
			("or","OR"),
			("is","IS"),
			("then","THEN"),
			("name","[a-z][a-zA-Z0-9]*"),
			("lbracket","\("),
			("rbracket","\)")			
		])
		self.parser = lexer.LrParser([
			("S -> R"),
			("R -> if E then I", Rule),
			("I -> name is name", Is),
			("A -> E and T", And),
			("O -> E or T", Or),
			("E -> T | A | O", Expression),
			("T -> I | lbracket E rbracket", Term)
		])

	def parse(self, rule):
		self.lexer.prepare(rule)
		return self.parser.parse(self.lexer)

class FuzzyClass(object):

	def get_dom(self, input_val):
		pass
		
	def get_start(self):
		pass
		
	def get_end(self):
		pass
		
class TriangularClass(FuzzyClass):

	def __init__(self, centre, width):
		FuzzyClass.__init__(self)
		self.centre = centre
		self.width = width
		self.start = centre-width/2
		self.end = centre+width/2

	def get_dom(self, input_val):
	
		# outside triangle
		if input_val < self.start or input_val > self.end :		
			return 0.0
			
		# left side
		elif input_val <= self.centre:			
			return (input_val-self.start) / (self.width/2)
			
		# right side
		else:
			return 1.0 - (input_val-self.centre) / (self.width/2)
			
	def get_start(self):
		return self.start
		
	def get_end(self):
		return self.end

RULE_PARSER = RuleParser()

class RuleSet(object):

	TRIANGULAR = 0
	LEFT_SHOULDER = 1
	RIGHT_SHOULDER = 2
	TRAPEZOID = 3
	BELL = 4

	def __init__(self):
		# dicts of classes hashed by flv name
		self.flvs = {}
		# lists of rules hashed by output name
		self.rules = {}
		
	def add_flv(self, name):
		self.flvs[name] = {}
		
	def add_class(self, flv, name, position, type=TRIANGULAR):
	
		if type == RuleSet.TRIANGULAR:
			fclass = TriangularClass(*position)
			
		self.flvs[flv][name] = fclass
		
	def add_rule(self, rule):
		parsed = RULE_PARSER.parse(rule)
		output_name = parsed.get_output_name()
		#print "rule output name: %s" % output_name
		if not self.rules.has_key(output_name):
			self.rules[output_name] = []
		self.rules[output_name].append(parsed)
		
	def evaluate(self, input_values):
		
		ev_output = {}
		cache = {}
		# for each output
		print self.rules
		for output in self.rules:
			ruleset = self.rules[output]
			ev_output[output] = self._evaluate_rules(output, ruleset, self.flvs, 
					input_values, cache)
			
		return ev_output
		
	def _evaluate_rules(self, output_name, ruleset, classes, input_values, cache):
		# evaluate rules concerning a particular output
		doms_cache = {}
		out_doms = {}
		for cname in classes[output_name]:
			out_doms[cname] = 0.0
		for r in ruleset:
			r_dom = r.evaluate(classes, input_values, cache)
			cname = r.get_output_class()
			out_doms[cname] += r_dom
				
		return self._fuzzy_centroid(out_doms, classes[output_name])
		
	def _fuzzy_centroid(self, doms, classes):
		print "doms %s" % doms
	
		# find range of classes
		start = min([classes[cname].get_start() for cname in classes])
		end = max([classes[cname].get_end() for cname in classes])
		print "start %f, end %f" % (start,end)
		
		# do integration
		total_area = 0.0
		weighted_values = 0.0
		for i in range(100):
			v = start + (end-start)/100*i
			dom = max([min(classes[cname].get_dom(v),doms[cname]) for cname in classes])
			weighted_values += dom * v
			total_area += dom
		print "wv: %f, total: %f" % (weighted_values,total_area)
			
		return weighted_values / total_area
			

r = RuleSet()

r.add_flv("health")
r.add_class("health","low",(2,4))
r.add_class("health","medium",(6,6))
r.add_class("health","high",(10,4))

r.add_flv("danger")
r.add_class("danger","low",(0.1,0.3))
r.add_class("danger","medium",(0.5,0.4))
r.add_class("danger","high",(0.8,0.4))

r.add_flv("flee")
r.add_class("flee","flee",(0.2, 0.4))
r.add_class("flee","fight",(0.8, 0.4))

r.add_flv("stealth")
r.add_class("stealth","quiet",(0.2, 0.4))
r.add_class("stealth","normal",(0.5, 0.5))
r.add_class("stealth","loud",(0.8, 0.4))

r.add_rule("IF danger IS high OR health IS low THEN stealth IS quiet")
r.add_rule("IF danger IS high THEN flee IS flee")
r.add_rule("IF danger IS low AND health IS high THEN flee IS fight")

print r.evaluate({"health":8, "danger":0.2})		
			

		
