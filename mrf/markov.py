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

------------------------

Markov chains module

"""

import mrf.mathutil
import mrf.structs

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
			if mrf.structs.iscollection(fr):
				if len(fr) > 1 or len(fr) < 1:
					raise TypeError("Expected \"from\" param to have length of 1")
				return tuple(fr)
			else:
				return (fr,)
		else:
			if not mrf.structs.iscollection(fr):
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
		# add enough start items to start
		newseq = [Markov.START]*self.order + seq		
		# add sequence items
		for i in xrange(len(seq)):
			seqindex = self.order+i
			self.add(newseq[seqindex-self.order:seqindex],newseq[seqindex])
		# add end
		self.add(newseq[-self.order:],Markov.END)
		
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
		return mrf.mathutil.weighted_roulette(items,normalised=True)
	
	def chain(self, strat):
		chain = []		
		fr = [Markov.START]*self.order
		t = None
		while t != Markov.END:
			t = strat(fr)
			if t != None and t != Markov.END:
				chain.append(t)
				fr = fr[1:] + [t]
		return chain		

	def random_chain(self):
		return self.chain(self.weighted_roulette)
		
	def best_chain(self):
		return self.chain(self.most_probable)
	
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
		
		def testHigherOrder(self):
			self.m = Markov(2)
			self.m.add_seq("book shop book mark book shop".split())

			self.assertAlmostEquals(self.m.get_prob(("book","shop"),"book"),1.0/2.0,1)
			self.assertEquals(self.m.most_probable(("shop","book")),"mark")

	unittest.main()
