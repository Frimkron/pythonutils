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


def _make_ref_property(aupdaters,bupdaters):
	_geta,_getsa,_seta,_adda,_rema = aupdaters
	_getb,_getsb,_setb,_addb,_remb = bupdaters
	
	def set(obj,val):
		# get currently referenced object(s)
		oldrefs = _getsa(obj)
		# remove from each their reference to this object
		for oldref in oldrefs:
			_remb(oldref,obj)
		# replace this object's reference(s)
		_seta(obj,val)
		# get newly referenced objects
		newrefs = _getsa(obj)
		# add to each a reference to this object
		for newref in newrefs:
			_addb(newref,obj)
			
	return property(_geta, set)
	
def _make_ref_updaters(reftype,refinner):

	if reftype == "ref":
	
		def _get(obj):
			return getattr(obj,refinner)
		def _gets(obj):
			r = getattr(obj,refinner)
			return ( r, ) if r is not None else ()
		def _set(obj, ref):
			setattr(obj,refinner,ref)
		def _add(obj, ref):
			setattr(obj,refinner,ref)
		def _rem(obj,ref):
			setattr(obj,refinner,None)			
			
	elif reftype == "seq":
	
		def _get(obj):
			return getattr(obj,refinner)
		def _gets(obj):
			return getattr(obj,refinner) or ()
		def _set(obj, refs):
			setattr(obj,refinner,tuple(refs) if refs is not None else None)
		def _add(obj,ref):
			s = getattr(obj,refinner) or ()
			s += (ref,)
			setattr(obj,refinner,s)
		def _rem(obj,ref):
			s = list(getattr(obj,refinner) or ())
			s.remove(ref)
			setattr(obj,refinner,tuple(s))
			
	return _get, _gets, _set, _add, _rem

def two_way_ref(classa,classb,abtype="ref",batype="ref",abname=None,baname=None):
	"""	
	Declare self-updating references between the given two classes.
	abname and baname define the name of class a's reference to b
	and b's to a, respectively. abtype and batype define the nature 
	of these references:
		ref - a single object reference
		seq - a tuple of object references
	"""
	if not abtype in ("ref","seq"):
		raise ValueError("Unknown abtype %s" % abtype)
	if not batype in ("ref","seq"):
		raise ValueError("Unknown batype %s" % batype)
	
	if abname is None:
		abname = classb.__name__.lower()
		if abtype == "seq": abname += "s"
	if baname is None:
		baname = classa.__name__.lower()
		if batype == "seq": baname += "s"

	abinner = "_"+abname
	bainner = "_"+baname		
	aupdaters = _make_ref_updaters(abtype,abinner)
	bupdaters = _make_ref_updaters(batype,bainner)
	
	setattr(classa, abname, _make_ref_property(aupdaters,bupdaters))
	setattr(classa, abinner, None)
	
	setattr(classb, baname, _make_ref_property(bupdaters,aupdaters))
	setattr(classb, bainner, None)
	

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

	class TestTwoWayRef(unittest.TestCase):
	
		def testOneToOne(self):
			
			class Foo(object): pass
			class Bar(object): pass			
			two_way_ref(Foo,Bar,abtype="ref",batype="ref")
			
			foo = Foo()
			bar = Bar()
			
			self.assertIn("bar", dir(foo))
			self.assertIn("foo", dir(bar))
			
			self.assertIs(None, foo.bar)
			self.assertIs(None, bar.foo)			
			foo.bar = bar
			self.assertIs(bar, foo.bar)
			self.assertIs(foo, bar.foo)			
			foo.bar = None
			self.assertIs(None, foo.bar)
			self.assertIs(None, bar.foo)
			bar.foo = foo
			self.assertIs(bar, foo.bar)
			self.assertIs(foo, bar.foo)
			bar.foo = None
			self.assertIs(None, foo.bar)
			self.assertIs(None, bar.foo)

		def testOneToMany(self):
		
			class Foo(object): pass
			class Bar(object): pass
			two_way_ref(Foo,Bar,abtype="seq",batype="ref")
			
			foo = Foo()
			bar = Bar()
			bar2 = Bar()
			
			self.assertIn("bars", dir(foo))
			self.assertIn("foo", dir(bar))
			self.assertIn("foo", dir(bar2))
			
			self.assertIs(None, foo.bars)
			self.assertIs(None, bar.foo)
			self.assertIs(None, bar.foo)
			foo.bars = ( bar, )
			self.assertEquals(( bar, ), foo.bars)
			self.assertIs(foo, bar.foo)
			self.assertIs(None, bar2.foo)
			bar2.foo = foo
			self.assertEquals(( bar,bar2 ), foo.bars)
			self.assertIs(foo, bar.foo)
			self.assertIs(foo, bar2.foo) 
			foo.bars = ( bar2, )
			self.assertEquals(( bar2, ), foo.bars)
			self.assertIs(None, bar.foo)
			self.assertIs(foo, bar2.foo)
			bar2.foo = None
			self.assertEquals((), foo.bars)
			self.assertIs(None, bar.foo)
			self.assertIs(None, bar2.foo)
			
		def testManyToOne(self):
		
			class Foo(object): pass
			class Bar(object): pass
			two_way_ref(Foo,Bar,abtype="ref",batype="seq")
			
			foo = Foo()
			foo2 = Foo()
			bar = Bar()
			
			self.assertIn("bar", dir(foo))
			self.assertIn("bar", dir(foo2))
			self.assertIn("foos", dir(bar))
			
			self.assertIs(None, foo.bar)
			self.assertIs(None, foo2.bar)
			self.assertIs(None, bar.foos)
			bar.foos = ( foo, )
			self.assertEquals(( foo, ), bar.foos)
			self.assertIs(bar, foo.bar)
			self.assertIs(None, foo2.bar)
			foo2.bar = bar
			self.assertEquals(( foo, foo2 ), bar.foos)
			self.assertIs(bar, foo.bar)
			self.assertIs(bar, foo2.bar)
			bar.foos = ( foo2, )
			self.assertEquals(( foo2, ), bar.foos)
			self.assertIs(None, foo.bar)
			self.assertIs(bar, foo2.bar)
			foo2.bar = None
			self.assertEquals((), bar.foos)
			self.assertIs(None, foo.bar)
			self.assertIs(None, foo2.bar)
			
		def testManyToMany(self):
		
			class Foo(object): pass
			class Bar(object): pass
			two_way_ref(Foo,Bar,abtype="seq",batype="seq")
			
			foo = Foo()
			foo2 = Foo()
			bar = Bar()
			bar2 = Bar()
			
			self.assertIn("bars", dir(foo))
			self.assertIn("bars", dir(foo2))
			self.assertIn("foos", dir(bar))
			self.assertIn("foos", dir(bar2))
			
			self.assertIs(None, foo.bars)
			self.assertIs(None, foo2.bars)
			self.assertIs(None, bar.foos)
			self.assertIs(None, bar2.foos)
			foo.bars = ( bar, )
			self.assertEquals(( bar, ), foo.bars)
			self.assertIs(None, foo2.bars)
			self.assertEquals(( foo, ), bar.foos)
			self.assertIs(None, bar2.foos)
			bar2.foos = ( foo, )
			self.assertEquals(( bar, bar2 ), foo.bars)
			self.assertIs(None, foo2.bars)
			self.assertEquals(( foo, ), bar.foos)
			self.assertEquals(( foo, ), bar2.foos)
			foo2.bars = ( bar2, bar )
			self.assertEquals(( bar,bar2 ), foo.bars)
			self.assertEquals(( bar2,bar ), foo2.bars)
			self.assertEquals(( foo,foo2 ), bar.foos)
			self.assertEquals(( foo,foo2 ), bar2.foos)
			foo.bars = ( bar2, )
			self.assertEquals(( bar2, ), foo.bars)
			self.assertEquals(( bar2,bar ), foo2.bars)
			self.assertEquals(( foo2, ), bar.foos)
			self.assertEquals(( foo2,foo ), bar2.foos)
			bar2.foos = None
			self.assertEquals((), foo.bars)
			self.assertEquals(( bar, ), foo2.bars)
			self.assertEquals(( foo2, ), bar.foos)
			self.assertIs(None, bar2.foos)
			
		def testNames(self):
		
			class Foo(object): pass
			class Bar(object): pass
			two_way_ref(Foo,Bar,abtype="ref",batype="ref",abname="thisbar",baname="thatfoo")
			
			foo = Foo()
			bar = Bar()
			
			self.assertIn("thisbar", dir(foo))
			self.assertIn("thatfoo", dir(bar))
			
			self.assertIs(None, foo.thisbar)
			self.assertIs(None, bar.thatfoo)
			foo.thisbar = bar
			self.assertIs(bar, foo.thisbar)
			self.assertIs(foo, bar.thatfoo)
			bar.thatfoo = None
			self.assertIs(None, foo.thisbar)
			self.assertIs(None, bar.thatfoo)

		def testSelfReference(self):
		
			class Foo(object): pass
			two_way_ref(Foo,Foo,abtype="seq",batype="ref",abname="children",baname="parent")
			
			foo = Foo()
			foo2 = Foo()
			
			self.assertIn("children", dir(foo))
			self.assertIn("parent", dir(foo2))
			
			self.assertIs(None, foo.children)
			self.assertIs(None, foo.parent)
			self.assertIs(None, foo2.children)
			self.assertIs(None, foo2.parent)
			foo.children = ( foo2, )
			self.assertEquals(( foo2, ), foo.children)
			self.assertIs(None, foo.parent)
			self.assertIs(None, foo2.children)
			self.assertIs(foo, foo2.parent)
			foo2.parent = None
			self.assertEquals((), foo.children)
			self.assertIs(None, foo.parent)
			self.assertIs(None, foo2.children)
			self.assertIs(None, foo2.parent)

	unittest.main()
	
	



