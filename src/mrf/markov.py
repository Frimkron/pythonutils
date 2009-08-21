
import mathutil
import structs

class Markov(object):

	START = 1
	END = 2

	def __init__(self, order=1, seq=None):
		self.graph = {}
		self.order = order
		if seq != None:
			self.add_seq(seq)
		
	def prepare_from(self, fr):
		"""checks items in from match order value and returns from items as tuple"""
		if self.order == 1:
			if structs.iscollection(fr):
				if len(fr) > 1 or len(fr) < 1:
					raise TypeError("Expected \"from\" param to have length of 1")
				return tuple(fr)
			else:
				return (fr,)
		else:
			if not structs.iscollection(fr):
				raise TypeError("Expected \"from\" param to have length of %d" % self.order)
			return tuple(fr)
			
		
	def has_from(self, fr):
		fr = self.prepare_from(fr)
		return self.graph.has_key(fr)
		
	def make_from(self, fr):
		fr = self.prepare_from(fr)
		if not self.has_from(fr):
			self.graph[fr] = {
				"count":0,
				"tos":{}
			}
		
	def has_to(self,fr,to):
		fr = self.prepare_from(fr)
		if not self.has_from(fr):
			return False
		
		return self.graph[fr]["tos"].has_key(to)
		
	def make_to(self, fr, to):
		fr = self.prepare_from(fr)
		self.make_from(fr)
		if not self.has_to(fr,to):
			self.graph[fr]["tos"][to] = {
				"count":0,
				"prob":0
			}
			
	def add(self, fr, to):
		fr = self.prepare_from(fr)
		self.make_to(fr,to)
		self.graph[fr]["tos"][to]["count"] += 1
		self.graph[fr]["count"] += 1
		self.evaluate_probs(fr)
		
	def add_seq(self, seq):
		# TODO: higher order adds		
		if len(seq) > 0:
			self.add(Markov.START,seq[0])
			for i in xrange(len(seq)-1):
				self.add(seq[i],seq[i+1])
			self.add(seq[len(seq)-1],Markov.END)
		else:
			self.add(Markov.START,Markov.END)
		
	def evaluate_probs(self, fr):
		fr = self.prepare_from(fr)
		self.make_from(fr)
		for k in self.graph[fr]["tos"]:
			total = self.graph[fr]["count"]
			prob = float(self.graph[fr]["tos"][k]["count"])/total
			self.graph[fr]["tos"][k]["prob"] = prob
	
	def get_prob(self, fr, to):
		fr = self.prepare_from(fr)
		self.make_to(fr,to)
		return self.graph[fr]["tos"][to]["prob"]
	
	def most_probable(self, fr):
		fr = self.prepare_from(fr)
		self.make_from(fr)
		best = None
		best_prob = 0
		for k in self.graph[fr]["tos"]:
			prob = self.graph[fr]["tos"][k]
			if best==None or prob > best_prob:
				best_prob = prob
				best = k
		return best
		
	def weighted_roulette(self, fr):
		fr = self.prepare_from(fr)
		self.make_from(fr)
		items = dict(((t,self.graph[fr]["tos"][t]["prob"]) for t in self.graph[fr]["tos"]))
		return mathutil.weighted_roulette(items,normalised=True)
		
	def random_chain(self):
		chain = []		
		next = Markov.START
		while next != Markov.END:
			next = self.weighted_roulette(next)
			if next != None and next != Markov.END:
				chain.append(next)
		return chain
				
	
#-----------------------------------------------------------------------
# Testing
#-----------------------------------------------------------------------	
if __name__ == "__main__":
	import unittest
	
	class Test(unittest.TestCase):
		
		def setUp(self):
			self.m = Markov()
			self.m.add_seq("book shop book mark book shop".split())
		
		def testMostProb(self):						
			self.assertAlmostEquals(self.m.get_prob("book","mark"),1.0/3.0,1)
			self.assertEquals(self.m.most_probable("book"),"shop")
		
		def testRoulette(self):
			results = {
				"shop" : 0,
				"mark" : 0
			}
			for i in xrange(10000):
				result = self.m.weighted_roulette("book")
				self.assert_(result in ["shop","mark"])
				results[result] += 1
			self.assertAlmostEquals(float(results["shop"])/10000.0,2.0/3.0,1)
			self.assertAlmostEquals(float(results["mark"])/10000.0,1.0/3.0,1)
	
	unittest.main()
