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
import tarfile
import os.path

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

def isindexable(item):
	try:
		item[0]
		return True
	except TypeError:
		return False
	except IndexError:
		return True
	
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
			for tag in self.get_item_tags(item):
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
			for item in self.get_tag_items(tag):
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


class ResourceBundle(object):

	class FilesystemStrategy(object):
		
		def open(self):
			pass
		
		def close(self):
			pass
		
		def get(self, name):
			return open(os.path.join(*name.split("/")),"r")
		
	class ArchiveStrategy(object):
		
		def __init__(self, filename):
			self.filename = filename
		
		def open(self):
			self.file = tarfile.open(self.filename,"r")
			
		def close(self):
			if self.file:
				self.file.close()
		
		def get(self, name):
			return self.file.extractfile(name)

	def __init__(self, filename, debug_mode=False):
		self.filename = filename
		self.is_open = False
		self.debug_mode = debug_mode
		if self.debug_mode:
			self.strategy = ResourceBundle.FilesystemStrategy()
		else:
			self.strategy = ResourceBundle.ArchiveStrategy(self.filename) 
		
	def open(self):
		if not self.is_open:
			self.strategy.open()
			self.is_open = True		
	
	def close(self):
		if self.is_open:
			self.strategy.close()
			self.is_open = False
			
	def __enter__(self):
		self.open()
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.close()
		
	def get(self, name):
		return self.strategy.get(name)
	
	def __getitem__(self, name):
		return self.get(name)


class DispatchLookupError(Exception):
	pass

class Dispatcher(object):

	# sequence of names from command object
	# method from handler object

	@staticmethod
	def by_type(handler,pattern="_handle_%s"):
	
		def command(val):
			return [pattern % t.__name__ for t in type(val).__mro__]
			
		lookup = Dispatcher._make_lookup_by_string(handler)
			
		return Dispatcher(handler,command,lookup)
		
	@staticmethod
	def by_str(handler,pattern="_handle_%s"):
		
		def command(val):
			return [ pattern % str(val) ]
			
		lookup = Dispatcher._make_lookup_by_string(handler)
		
		return Dispatcher(handler,command,lookup)
		
	@staticmethod	
	def _make_lookup_by_string(handler):
		# is it a dictionary?
		try:
			try:
				handler["foo"]
			except KeyError:
				pass
		except TypeError:
			# make attribute lookup function
			def lookup(val):
				try:
					return getattr(handler,val)
				except AttributeError as e:
					raise DispatchLookupError(e)
			return lookup
		else:
			# make dictionary lookup function
			def lookup(val):
				try:
					return handler[val]
				except KeyError as e:
					raise DispatchLookupError(e)
			return lookup
		
	def __init__(self,handler,commstrat,lookupstrat):
		self.commstrat = commstrat
		self.lookupstrat = lookupstrat
		
	def dispatch(self,comm,*args,**kargs):
		for n in self.commstrat(comm):
			try:
				f = self.lookupstrat(n)
			except DispatchLookupError:
				continue
			return f(comm, *args,**kargs)
		raise DispatchLookupError("Couldn't find function to dispatch to")
	
		
class FlagInitialiser(object):
	def __init__(self):
		self.val = 0
	def __iter__(self):
		return self
	def next(self):
		f = 1 << self.val
		self.val += 1
		return f


def one_to_many(classa,classb,abname=None,baname=None):

	if abname is None:
		abname = classb.__name__.lower()+"s"
	if baname is None:
		baname = classa.__name__.lower()
		
	abinner = "_"+abname
	bainner = "_"+baname
	
	def a_get_b(self):
		return getattr(self,abinner)
	def a_set_b(self,val):
		# unset old bs' refs
		for b in getattr(self,abinner) or []:
			setattr(b,bainner,None)
		# set new b collection
		val = tuple(val)
		setattr(self,abinner,val)
		#  set new bs' refs
		for b in val or []:
			setattr(b,bainner,self)
	setattr(classa,abname, property(a_get_b,a_set_b))
	setattr(classa,abinner, None)
	
	def b_get_a(self):
		return getattr(self,bainner)
	def b_set_a(self,val):
		# remove self from old a's collection
		a = getattr(self,bainner)
		if a:
			old = list(getattr(a,abinner) or [])
			old.remove(self)
			new = tuple(old)		
			setattr(a,abinner,new)
		# set new a
		setattr(self,bainner,val)
		# add self to new a's collection
		a = getattr(self,bainner)
		if a:
			old = list(getattr(a,abinner) or [])
			old.append(self)
			new = tuple(old)
			setattr(a,abinner,new)		
	setattr(classb,baname, property(b_get_a,b_set_a))
	setattr(classb,bainner, None)
	

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

		def testRemoveTagsAndItems(self):
			t = TagLookup()
			t.tag_item("foo", "bar")
			t.tag_item("foo", "car")
			t.tag_item("foo", "dar")
			self.assertEquals(set(["foo"]),t.get_items())
			self.assertEquals(set(["bar","car","dar"]),t.get_tags())
			t.remove_tag("car")
			self.assertEquals(set(["bar","dar"]),t.get_tags())
			t.remove_item("foo")
			self.assertEquals(set([]),t.get_items())
			self.assertEquals(set(["bar","dar"]),t.get_tags())

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

	class TestDispatcher(unittest.TestCase):
	
		def testByType(self):
		
			calls = []
		
			class Handler(object):
				def _handle_Foo(self, foo):
					calls.append("foo")
				def _handle_Bar(self, bar):
					calls.append("bar")
					
			class Foo(object):
				pass
			class Bar(object):
				pass
				
			d = Dispatcher.by_type(Handler())
			self.assertEquals(0,len(calls))
			
			d.dispatch(Foo())
			self.assertEquals(1,len(calls))
			self.assertEquals("foo",calls[0])
			
			d.dispatch(Bar())
			self.assertEquals(2,len(calls))
			self.assertEquals("bar",calls[1])
			
		def testByTypeReturn(self):
		
			class Handler(object):
				def _handle_Foo(self,foo):
					return "yawn"
			class Foo(object):
				pass
				
			d = Dispatcher.by_type(Handler())
			r = d.dispatch(Foo())
			self.assertEquals("yawn", r)
			
		def testByTypeSuperType(self):
		
			calls = []
			
			class Handler(object):
				def _handle_Foo(self,foo):
					calls.append("foo")
				def _handle_Bar(self,bar):
					calls.append("bar")
					
			class Foo(object):
				pass
			class Bar(Foo):
				pass
			class Weh(Foo):
				pass
				
			d = Dispatcher.by_type(Handler())
			self.assertEquals(0, len(calls))
			
			d.dispatch(Bar())
			self.assertEquals(1, len(calls))
			self.assertEquals("bar", calls[0])
			
			d.dispatch(Weh())
			self.assertEquals(2, len(calls))
			self.assertEquals("foo", calls[1])
			
		def testByTypeArgs(self):
		
			args = []
			class Handler(object):
				def _handle_Foo(self,foo,blah,yadda=1,meh=2):
					args.extend([foo,blah,yadda,meh])
			class Foo(object):
				pass
				
			d = Dispatcher.by_type(Handler())
			f = Foo()
			d.dispatch(f,"lol",meh=42)
			self.assertEquals([f,"lol",1,42],args)
			
		def testByTypePattern(self):
		
			calls = []
			class Handler(object):
				def do_Foo(self, foo):
					calls.append(True)
			class Foo(object):
				pass
				
			d = Dispatcher.by_type(Handler(),"do_%s")
			d.dispatch(Foo())
			self.assertEquals(1, len(calls))
			self.assertEquals(True, calls[0])
			
		def testByTypeDict(self):
		
			calls = []		
			handler = {
				"_handle_Foo": lambda foo: calls.append("foo"),
				"_handle_Bar": lambda bar: calls.append("bar")
			}
			class Foo(object): pass
			class Bar(object): pass
			
			d = Dispatcher.by_type(handler)
			self.assertEquals(0, len(calls))
			
			d.dispatch(Foo())
			self.assertEquals(1, len(calls))
			self.assertEquals("foo", calls[0])
			
			d.dispatch(Bar())
			self.assertEquals(2, len(calls))
			self.assertEquals("bar", calls[1])
			
		def testByStr(self):
			
			calls = []
			class Handler(object):
				def _handle_phoo(self,val):
					calls.append("ph")
				def _handle_bagh(self,val):
					calls.append("ba")
			class Foo(object):
				def __str__(self):
					return "phoo"
			class Bar(object):
				def __str__(self):
					return "bagh"
					
			d = Dispatcher.by_str(Handler())
			self.assertEquals(0, len(calls))
			
			d.dispatch(Foo())
			self.assertEquals(1, len(calls))
			self.assertEquals("ph", calls[0])
			
			d.dispatch(Bar())
			self.assertEquals(2, len(calls))
			self.assertEquals("ba", calls[1])

	class TestFlagInitialiser(unittest.TestCase):
	
		def testIterator(self):
			flags = []
			for i,f in enumerate(FlagInitialiser()):
				if i >= 8:
					break
				flags.append(f)
			self.assertEquals([1,2,4,8,16,32,64,128], flags)

	unittest.main()
	
	



