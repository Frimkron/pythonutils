
import lexer



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
		else
			return 1.0 - (input_val-self.centre) / (self.width/2)

class RuleSet(object):

	TRIANGULAR = 0
	LEFT_SHOULDER = 1
	RIGHT_SHOULDER = 2
	TRAPEZOID = 3
	BELL = 4

	def __init__(self):
		self.flvs = {}
		
	def add_flv(self, name):
		self.flvs[name] = {}
		
	def add_class(self, flv, name, position, type=RuleSet.TRIANGULAR):
	
		if type == RuleSet.TRIANGULAR:
			fclass = TriangularClass(*position)
			
		self.inputs[input][name] = fclass
		
	def add_rule(self, )
	
		
		
			
	
		
