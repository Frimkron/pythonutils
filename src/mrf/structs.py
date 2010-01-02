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

import copy

class TicketQueue(object):
	"""	
	Queue for restricting actions to x per game cycle	
	"""
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
	"""	
	Metaclass allowing introspection of class definition
	on creation
	"""
	def __new__(typ, *args, **kargs):
		cls = type.__new__(typ, *args, **kargs)
		cls._class_init()
		return cls 
		

class TagLookup(object):	
	"""	
	Collection allowing groups of items to be associated with 
	multiple different keys and looked up using them.
	"""

	def __init__(self):
		self.clear()

	def has_item(self, item):
		return self.items.has_key(item)

	def has_tag(self, tag):
		return self.groups.has_key(tag)

	def add_item(self, item):
		if self.has_item(item):
			self.remove_item(item)
		self.items[item] = set()

	def remove_item(self, item):
		if self.has_item(item):
			item_tags = self.items[item]
			for tag in item_tags:
				self.untag_item(item, tag)
			del(self.items[item])

	def tag_item(self, item, tag):
		if not self.has_item(item):
			self.add_item(item)
		if not self.has_tag(tag):
			self.add_tag(tag)
		self.items[item].add(tag)
		self.groups[tag].add(item)

	def untag_item(self, item, tag):
		if self.has_item(item) and self.has_tag(tag):
			self.items[item].remove(tag)
			self.groups[tag].remove(item)

	def add_tag(self, tag):
		if self.has_tag(tag):
			self.remove_tag(tag)
		self.groups[tag] = set()

	def remove_tag(self, tag):
		if self.has_tag(tag):
			for item in self.groups[tag]:
				self.untag_item(item, tag)
			del(self.groups[tag])
			
	def get_items(self):
		return set(self.items.keys())

	def get_tags(self):
		return set(self.groups.keys())

	def get_item_tags(self, item):
		if self.has_item(item):
			return copy.copy(self.items[item])
		else:
			return set()	

	def get_tag_items(self, tag):
		if self.has_tag(tag):
			return copy.copy(self.groups[tag])
		else:
			return set()

	def clear(self):
		self.items = {}
		self.groups = {}
	
	def __getitem__(self, key):
		# index can be used to retrieve tag groups
		return self.get_tag_items(key)

	def __contains__(self, key):
		# "in" operator can be used to test if item is present
		return self.has_item(key)

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
	
	class TestTagLookup(unittest.TestCase):

		def testAddRemoveItem(self):
			t = TagLookup()
			t.remove_item("foo")
			t.add_item("foo")
			t.add_item("goo")
			self.assertEquals(True,t.has_item("foo"))
			self.assertEquals(False,t.has_item("hoo"))
			self.assertEquals(set(["foo","goo"]),t.get_items())
			t.remove_item("foo")
			self.assertEquals(set(["goo"]),t.get_items())
			t.remove_item("goo")
			self.assertEquals(set(),t.get_items())

		def testAddRemoveTag(self):
			t = TagLookup()
			t.remove_tag("bar")
			t.add_tag("bar")
			t.add_tag("car")
			self.assertEquals(True,t.has_tag("bar"))
			self.assertEquals(False,t.has_tag("dar"))
			self.assertEquals(set(["bar","car"]),t.get_tags())
			t.remove_tag("bar")
			self.assertEquals(set(["car"]),t.get_tags())
			t.remove_tag("car")
			self.assertEquals(set(),t.get_tags())

		def testTaggingUntagging(self):
			t = TagLookup()
			t.tag_item("foo", "bar")
			t.tag_item("goo", "car")
			t.tag_item("foo", "car")
			self.assertEquals(set(["foo","goo"]),t.get_items())
			self.assertEquals(set(["bar","car"]),t.get_tags())
			self.assertEquals(set(["bar","car"]),t.get_item_tags("foo"))
			self.assertEquals(set(["car"]),t.get_item_tags("goo"))
			self.assertEquals(set(),t.get_item_tags("hoo"))
			self.assertEquals(set(["foo"]),t.get_tag_items("bar"))
			self.assertEquals(set(["foo","goo"]),t.get_tag_items("car"))
			self.assertEquals(set(),t.get_tag_items("dar"))
			t.untag_item("hoo","dar")
			t.untag_item("foo","bar")
			self.assertEquals(set(["car"]),t.get_item_tags("foo"))
			self.assertEquals(set(),t.get_tag_items("bar"))

		def testClear(self):
			t = TagLookup()
			t.tag_item("foo", "bar")
			t.tag_item("foo", "car")
			t.tag_item("goo", "car")
			self.assertEquals(2, len(t.get_items()))
			self.assertEquals(2, len(t.get_tags()))
			t.clear()
			self.assertEquals(set(),t.get_items())
			self.assertEquals(set(),t.get_tags())

		def testSpecialMethods(self):
			t = TagLookup()
			t.tag_item("foo", "bar")
			t.tag_item("foo", "car")
			t.tag_item("goo", "car")
			self.assertEquals(set(["foo","goo"]),t["car"])
			self.assertEquals(set(),t["dar"])
			self.assertEquals(True, "foo" in t)
			self.assertEquals(False, "hoo" in t)

	unittest.main()
	
	



