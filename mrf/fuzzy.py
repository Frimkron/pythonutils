"""
Copyright (c) 2009 Mark Frimston

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

---------------

Fuzzy Logic module

Contains RuleSet class for evaluating fuzzy logic rules.
"""

import mrf.parser
import sys

class FuzzySymbol(mrf.parser.ParserSymbol):

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
		self.lexer = mrf.parser.Lexer([
			("whitespace","[ \n\r\t]+",None,mrf.parser.Lexer.cb_ignore),
			("if","IF"),
			("and","AND"),
			("or","OR"),
			("is","IS"),
			("then","THEN"),
			("name","[a-z][a-zA-Z0-9]*"),
			("lbracket","\("),
			("rbracket","\)")			
		])
		self.parser = mrf.parser.LrParser([
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

class TrapezoidClass(FuzzyClass):

	def __init__(self, centre, bottom_width, top_width):
		FuzzyClass.__init__(self)
		self.centre = centre
		self.bottom_width = bottom_width
		self.top_width = top_width
		self.start = centre-bottom_width/2
		self.end = centre+bottom_width/2
		self.top_start = centre-top_width/2
		self.top_end = centre+top_width/2
		
	def get_dom(self, input_val):
		
		# outside trapezoid
		if input_val < self.start or input_val > self.end:
			return 0.0
			
		# flat middle section
		elif self.top_start <= input_val <= self.top_end:
			return 1.0
			
		# left side
		elif input_val < self.top_start:
			return (input_val-self.start) / (self.top_width/2)	
			
		# right_side
		else:
			return 1.0 - (input_val-self.top_end) / (self.top_width/2)
		
	def get_start(self): 
		return self.start
		
	def get_end(self):
		return self.end

class LeftShoulderClass(FuzzyClass):

	def __init__(self, start, top, bottom):
		self.start = start
		self.top_end = top
		self.end = bottom
		
	def get_dom(self, input_val):
		
		# outside of shape
		if input_val < self.start or input_val > self.end:
			return 0.0
			
		# flat area
		elif input_val <= self.top_end:
			return 1.0
			
		# sloped area
		else:
			return 1.0 - (input_val-self.top_end) / (self.end-self.top_end)	
		
	def get_start(self):
		return self.start
		
	def get_end(self):
		return self.end
		
class RightShoulderClass(FuzzyClass):

	def __init__(self, bottom, top, end):
		self.start = bottom
		self.top_start = top
		self.end = end
		
	def get_dom(self, input_val):
		
		# outside of shape
		if input_val < self.start or input_val > self.end: 
			return 0.0
			
		# flat area
		elif input_val >= self.top_start:
			return 1.0
			
		# sloped area
		else:
			return (input_val-self.start) / (self.top_start-self.start)	
					
	def get_start(self):
		return self.start
		
	def get_end(self):
		return self.end
		

RULE_PARSER = RuleParser()

class RuleSet(object):
	"""
	Represents a set of fuzzy logic rules. Fuzzy linguistic variables with 
	multiple fuzzy classes can be created along with rules to determine the 
	value of output variables from input variables.
	"""
	TRIANGULAR = 0
	LEFT_SHOULDER = 1
	RIGHT_SHOULDER = 2
	TRAPEZOID = 3

	def __init__(self):
		# dicts of classes hashed by flv name
		self.flvs = {}
		# lists of rules hashed by output name
		self.rules = {}
		
	def add_flv(self, name):
		"""
		Adds a new fuzzy linguistic variable with the given name
		"""
		self.flvs[name] = {}
		
	def add_class(self, flv, name, position, type=TRIANGULAR):
		"""
		Adds a new flv class with the given name for the given flv. 
		type parameter determines the class shape. By default this is a
		symmetrical triangle.
		position is a tuple providing the size and position parameters for the 
		class. These depend on what the shape is. For a triangular class, the 
		parameters are the centre position and the width.
		"""
		if type == RuleSet.TRIANGULAR:
			fclass = TriangularClass(*position)
		elif type == RuleSet.TRAPEZOID:
			fclass = TrapezoidClass(*position)
		elif type == RuleSet.LEFT_SHOULDER:
			fclass = LeftShoulderClass(*position)
		elif type == RuleSet.RIGHT_SHOULDER:
			fclass = RightShoulderClass(*position)
			
		self.flvs[flv][name] = fclass
		
	def add_rule(self, rule):
		"""
		Adds a new rule which is parsed from the given string. Rules should be 
		of the form:
		
			<rule> := IF <expression> THEN <is>
			<expression> := <term> | <expression> AND <term> | <expression> OR <term>
			<term> := <is> | ( <expression> )
			<is> := flv IS class
			
		For example:
			IF health IS low AND nearby_enemies IS high THEN speed IS fast
		"""
		parsed = RULE_PARSER.parse(rule)
		output_name = parsed.get_output_name()
		#print "rule output name: %s" % output_name
		if not self.rules.has_key(output_name):
			self.rules[output_name] = []
		self.rules[output_name].append(parsed)
		
	def evaluate(self, input_values):
		"""
		Evaluates the given input values against the rule set to determine the 
		output values. 
		input_values is a dictionary of values hashed by flv name. Values for 
		all inputs must be provided.
		Returns a dictionary of output values hashed by flv name. 
		Note that if no rule is defined to describe the value of an output 
		for the given input values, then this output will not be present in the 
		dictionary.
		"""
		ev_output = {}
		cache = {}
		# for each output
		for output in self.rules:
			ruleset = self.rules[output]
			rules_result = self._evaluate_rules(output, ruleset, self.flvs, 
					input_values, cache)
			if rules_result != None:
				ev_output[output] = rules_result 
			
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
		# find range of classes
		start = min([classes[cname].get_start() for cname in classes])
		end = max([classes[cname].get_end() for cname in classes])
		
		# do integration
		total_area = 0.0
		weighted_values = 0.0
		for i in range(100):
			v = start + (end-start)/100*i
			dom = max([min(classes[cname].get_dom(v),doms[cname]) for cname in classes])
			weighted_values += dom * v
			total_area += dom
			
		if total_area > 0:			
			return weighted_values / total_area
		else:
			return None
			
			
# ------------------------------------------------------------------------------
# Testing
# ------------------------------------------------------------------------------			

if __name__ == "__main__":
	
	import unittest
	
	class TestClasses(unittest.TestCase):
	
		def testTriangular(self):
		
			c = TriangularClass(0,2)
			self.assertAlmostEquals(0.0, c.get_dom(-1.5), 2)
			self.assertAlmostEquals(0.0, c.get_dom(-1), 2)
			self.assertAlmostEquals(0.25, c.get_dom(-0.75), 2)
			self.assertAlmostEquals(0.75, c.get_dom(-0.25), 2)
			self.assertAlmostEquals(1.0, c.get_dom(0), 2)
			self.assertAlmostEquals(0.75, c.get_dom(0.25), 2)
			self.assertAlmostEquals(0.25, c.get_dom(0.75), 2)
			self.assertAlmostEquals(0.0, c.get_dom(1), 2)
			self.assertAlmostEquals(0.0, c.get_dom(1.5), 2)
			
		def testTrapezoid(self):
			
			c = TrapezoidClass(0,4,2)
			self.assertAlmostEquals(0.0, c.get_dom(-2.5), 2)
			self.assertAlmostEquals(0.0, c.get_dom(-2.0), 2)
			self.assertAlmostEquals(0.25, c.get_dom(-1.75), 2)
			self.assertAlmostEquals(0.75, c.get_dom(-1.25), 2)
			self.assertAlmostEquals(1.0, c.get_dom(-1),2)
			self.assertAlmostEquals(1.0, c.get_dom(-0.5), 2)
			self.assertAlmostEquals(1.0, c.get_dom(0),2)
			self.assertAlmostEquals(1.0, c.get_dom(0.5), 2)
			self.assertAlmostEquals(1.0, c.get_dom(1), 2)
			self.assertAlmostEquals(0.75, c.get_dom(1.25), 2)
			self.assertAlmostEquals(0.25, c.get_dom(1.75), 2)
			self.assertAlmostEquals(0, c.get_dom(2), 2)
			self.assertAlmostEquals(0, c.get_dom(2.5), 2)
			
		def testLeftShoulder(self):
		
			c = LeftShoulderClass(-1,1,2)
			self.assertAlmostEquals(0.0, c.get_dom(-2), 2)
			self.assertAlmostEquals(1.0, c.get_dom(-1), 2)
			self.assertAlmostEquals(1.0, c.get_dom(0), 2)
			self.assertAlmostEquals(1.0, c.get_dom(1), 2)
			self.assertAlmostEquals(0.75, c.get_dom(1.25), 2)
			self.assertAlmostEquals(0.25, c.get_dom(1.75), 2)
			self.assertAlmostEquals(0, c.get_dom(2), 2)
			self.assertAlmostEquals(0, c.get_dom(2.5), 2)
	
	class TestRuleParser(unittest.TestCase):
	
		def testParsing(self):
			
			r = RuleParser()
			rule = r.parse("IF foo IS high THEN bar IS low")
			self.assertEquals("if", rule.children[0].type)
			self.assertEquals("E", rule.children[1].type)
			self.assertEquals("T", rule.children[1].children[0].type)
			self.assertEquals("I", rule.children[1].children[0].children[0].type)
			self.assertEquals("name", rule.children[1].children[0].children[0].children[0].type)
			self.assertEquals("foo", rule.children[1].children[0].children[0].children[0].data)
			self.assertEquals("is", rule.children[1].children[0].children[0].children[1].type)
			self.assertEquals("name", rule.children[1].children[0].children[0].children[2].type)
			self.assertEquals("high", rule.children[1].children[0].children[0].children[2].data)
			self.assertEquals("then", rule.children[2].type)
			self.assertEquals("I", rule.children[3].type)
			self.assertEquals("name", rule.children[3].children[0].type)
			self.assertEquals("bar", rule.children[3].children[0].data)
			self.assertEquals("is", rule.children[3].children[1].type)
			self.assertEquals("name", rule.children[3].children[2].type)
			self.assertEquals("low", rule.children[3].children[2].data)
			
			rule = r.parse("IF foo IS high AND bar IS low THEN wah IS flibble")
			self.assertEquals("E", rule.children[1].type)
			self.assertEquals("A", rule.children[1].children[0].type)
			self.assertEquals("E", rule.children[1].children[0].children[0].type)
			self.assertEquals("T", rule.children[1].children[0].children[0].children[0].type)
			self.assertEquals("T", rule.children[1].children[0].children[2].type)
	
	class TestRuleSet(unittest.TestCase):
		
		def setUp(self):
			
			self.r = RuleSet()
			""" 
			|    .    .    .
			|   /|\  /|\  /|\
			|  / | \/ | \/ | \
			+-+-+-+'+-+-+'+-+-+-+
			0 1 2 3 4 5 6 7 8 9 10 
			"""
			self.r.add_flv("alpha")
			self.r.add_class("alpha","low",(2.5,3.0))
			self.r.add_class("alpha","med",(5.0,3.0))
			self.r.add_class("alpha","high",(7.5,3.0))
			
			self.r.add_flv("beta")
			self.r.add_class("beta","low",(2.5,3.0))
			self.r.add_class("beta","med",(5.0,3.0))
			self.r.add_class("beta","high",(7.5,3.0))
			
			self.r.add_flv("gamma")
			self.r.add_class("gamma","tall",(2.5,3.0))
			self.r.add_class("gamma","regular",(5.0,3.0))
			self.r.add_class("gamma","grande",(7.5,3.0))
			
			self.r.add_rule("IF alpha IS low THEN beta IS high") 
			self.r.add_rule("IF alpha IS med THEN beta IS med") 
			self.r.add_rule("IF alpha IS high THEN beta IS low")
			self.r.add_rule("IF alpha IS low AND beta IS high THEN gamma IS tall") 
			self.r.add_rule("IF alpha IS high AND beta IS low THEN gamma IS grande") 
			self.r.add_rule("IF alpha IS med OR beta IS med THEN gamma IS regular")
		
		def testRuleSet(self):
			
			out = self.r.evaluate({"alpha":2.5,"beta":7.5})
			self.assertAlmostEquals(2.5, out["gamma"], 2)
			self.assertAlmostEquals(7.5, out["beta"], 2)
			
			out = self.r.evaluate({"alpha":5.0,"beta":5.0})
			self.assertAlmostEquals(5.0, out["beta"], 2)
			self.assertAlmostEquals(5.0, out["gamma"], 2)
			
			out = self.r.evaluate({"alpha":3.75, "beta":6.25})
			self.assertAlmostEquals(6.25, out["beta"], 2)
			self.assertAlmostEquals(3.75, out["gamma"], 2)
			
			out = self.r.evaluate({"alpha":0.5, "beta":3.75})
			self.assertAlmostEquals(5.0, out["gamma"], 2)
			self.assertFalse(out.has_key("beta"))
	
	unittest.main()
