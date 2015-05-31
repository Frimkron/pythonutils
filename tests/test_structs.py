from mrf.structs import *
import unittest
import doctest


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
        
        class Foo(object):
            bar = two_way_ref("bar","foo")
        class Bar(object):
            foo = two_way_ref("foo","bar")        
        
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
    
        class Foo(object):
            bars = two_way_ref("bars","foo",tuple,object)
        class Bar(object):
            foo = two_way_ref("foo","bars",object,tuple)
        
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
    
        class Foo(object):
            bar = two_way_ref("bar","foos",object,tuple)
        class Bar(object):
            foos = two_way_ref("foos","bar",tuple,object)
        
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
    
        class Foo(object):
            bars = two_way_ref("bars","foos",tuple,tuple)
        class Bar(object):
            foos = two_way_ref("foos","bars",tuple,tuple)
        
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
        
    def testSelfReference(self):
    
        class Foo(object):
            parent = two_way_ref("parent","children",object,tuple)
            children = two_way_ref("children","parent",tuple,object)
        
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


    



