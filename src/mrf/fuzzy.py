
import lexer
import sys

class FuzzySymbol(lexer.ParserSymbol):

	def evaluate(self):
		pass

class And(FuzzySymbol):

	def evaluate(self):
		pass
		
class Or(FuzzySymbol):
	
	def evaluate(self):
		pass
		
class Is(FuzzySymbol):

	def _get_doms_for_input(self, classes, input_name, input_value, cache):
		if cache.has_key(input_name):
			return cache[input_name]
		else:
			doms = {}
			for cname, c in enumerate(classes[input_name]):
				d = c.get_dom(input_value)
				doms[cname] = d
			cache[input_name] = doms
			return doms 

	def evaluate(self):
		pass
		
class  Term(FuzzySymbol):
	
	def evaluate(self):
		pass
		
class Expression(FuzzySymbol):

	def evaluate(self):
		pass
		
class Rule(FuzzySymbol):

	def evaluate(self):
		pass
		
	def get_output_name(self):
		return self.children[3].children[0].data

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
		if not self.rules.has_key(output_name):
			self.rules[output_name] = []
		self.rules[output_name].append(parsed)
		
	def evaluate(self, input_values):
		
		ev_output = {}
		# for each output
		for output, ruleset in enumerate(self.rules):
			ev_output[output] = self._evaluate_rules(ruleset, self.flvs, input_values)
			
		return ev_output
		
	def _evaluate_rules(self, ruleset, classes, input_values):
		# evaluate rules concerning a particular output
		doms_cache = {}
		for r in ruleset:
			r.evaluate()
		
		
			

		
