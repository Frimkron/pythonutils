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

Data Structures Module

Contains data structures:

	TicketQueue - queue for restricting actions to x per frame
	IntrospectType - metaclass which invokes setup method on classes created
	
"""
class TicketQueue(object):

	def __init__(self, max_sim=1):
		self.max_sim = max_sim
		self.queue = [set([])]
		self.next_ticket = 0
		
	def enter(self):
		t = self.next_ticket
		self.next_ticket += 1
		if len(self.queue[-1]) >= self.max_sim:
			self.queue.append(set([]))
		self.queue[-1].add(t)
		return t
		
	def at_front(self, ticket):
		return ticket in self.queue[0]
		
	def advance(self):
		self.queue.pop(0)
		if len(self.queue)==0:
			self.queue.append(set([]))
			
			
def isiterable(item):
	try:
		iter(item)
		return True
	except TypeError:
		return False
		
def iscollection(item):
	if isinstance(item,basestring):
		return False
	return isiterable(item)
	
	
class IntrospectType(type):
	
	def __new__(typ, *args, **kargs):
		cls = type.__new__(typ, *args, **kargs)
		cls._class_init()
		return cls 
		
		
# -- Testing -----------------------------

if __name__ == "__main__":

	import unittest
	
	class TestTicketQueue(unittest.TestCase):
	
		def testTicketQueue(self):
			
			q = TicketQueue(2)
			t1 = q.enter()
			t2 = q.enter()
			t3 = q.enter()
			self.assertTrue(q.at_front(t1))
			self.assertTrue(q.at_front(t2))
			self.assertFalse(q.at_front(t3))
			q.advance()
			self.assertTrue(q.at_front(t3))
			t4 = q.enter()
			t5 = q.enter()
			self.assertTrue(q.at_front(t4))
			self.assertFalse(q.at_front(t5))
			q.advance()
			self.assertTrue(q.at_front(t5))
			q.advance()
			q.advance()
			self.assertEquals(1,len(q.queue))
	
	unittest.main()
	
	



