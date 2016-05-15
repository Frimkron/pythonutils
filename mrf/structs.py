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
"""

import json
import copy
import tarfile
import os.path

try:
    basestring
    unicode
except NameError:
    basestring = str
    unicode = str


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
        return item in self.items

    def has_tag(self, tag):
        return tag in self.groups

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
        
    __next__ = next


def _make_ref_updaters(innername):
    def get(obj):
        return getattr(obj,innername,None)
    def gets(obj):
        v = getattr(obj,innername,None)
        return (v,) if v else ()
    def set(obj,val):
        setattr(obj,innername,val)
    def add(obj,val):
        setattr(obj,innername,val)
    def rem(obj,val):
        setattr(obj,innername,None)
    return get,gets,set,add,rem
    
def _make_tuple_ref_updaters(innername):
    def get(obj):
        return getattr(obj,innername,None)
    def gets(obj):
        return getattr(obj,innername,None) or ()
    def set(obj,val):
        setattr(obj,innername,tuple(val) if val else None)
    def add(obj,val):
        v = getattr(obj,innername,None) or ()
        v += (val,)
        setattr(obj,innername,v)
    def rem(obj,val):
        v = list(getattr(obj,innername,None) or ())
        v.remove(val)
        setattr(obj,innername,tuple(v))
    return get,gets,set,add,rem

def two_way_ref(aname,bname,atype=object,btype=object):
    """    
    Returns a property which behaves as a self-maintaining two-way reference.
    When the property is set, the object it points to will have its reference 
    set to point back. A corresponding property should be declared on the 
    class(es) to be referenced.
    
    Parameters:
        aname    - the name of this property
        bname    - the name of the corresponding property on the referenced class
        atype    - the type of reference for this property. See below.
        btype    - the type of reference for the corresponding property on the 
                    referenced class. See below.
    Reference Types:
        object    - a singular object reference (e.g. if the object references one 
                    other object)
        tuple    - a tuple of object references (e.g. if the object references a 
                    collection of other objects)
                    
    Example:
        >>> class Parent(object):
        ...     children = two_way_ref("children","parent",tuple,object)
        ...     def __init__(self,name):
        ...         self.name = name
        ...     def __repr__(self):
        ...         return self.name
        ... 
        >>> class Child(object):
        ...     parent = two_way_ref("parent","children",object,tuple)
        ...     def __init__(self,name):
        ...         self.name = name
        ...     def __repr__(self):
        ...         return self.name
        ... 
        >>> p = Parent("Senior")
        >>> c = Child("Junior")
        >>> p.children = ( c, )
        >>> p.children
        (Junior,)
        >>> c.parent
        Senior
    """
    for p in (atype,btype):
        if not p in (object,tuple):
            raise ValueError("Unknown ref type %s" % atype)
    
    makers = {
        object: _make_ref_updaters,
        tuple: _make_tuple_ref_updaters,
    }
    geta,getsa,seta,adda,rema = makers[atype]("_"+aname)
    getb,getsb,setb,addb,remb = makers[btype]("_"+bname)
    
    def setter(self,val):
        for oldref in getsa(self):
            remb(oldref,self)
        seta(self,val)
        for newref in getsa(self):
            addb(newref,self)
    
    return property(geta,setter)


DONT_PAD = object()
    
def chunk(seq,size=2,pad=DONT_PAD):
    """Returns an iterator that yields consequtive subsequences of the given size from the given sequence.
       By default the last subsequence, if shorter, is not padded to full size. However the pad parameter
       can be used to specify a value to use as padding"""
    buff = []
    itr = iter(seq)
    try:
        while True:
            buff = []
            while len(buff) < size:
                buff.append(next(itr))
            yield tuple(buff)
    except StopIteration:
        pass
    if len(buff) > 0:
        if pad is not DONT_PAD:
            buff.extend([pad]*(size-len(buff)))
        yield tuple(buff)


class JsonSerialiser(object):
    """Serialises an object structure to and from JSON format, using an example structure as the specification for what
       is expected in both cases.
       
       Accepted types:
         * int (will accept any integer value)
         * float (will accept any float value)
         * string (will accept any string value)
         * bool (will accept any boolean value)
         * list (example must contain 1 example value. Will accept a list of any size, containing values of the type 
                 demonstrated )
         * tuple (Will accept tuples with the length and value types indicated in the example)
         * set (example must contain 1 example value. Will accept a set of any size, containing value of the type
                demonstrated)
         * dict (Example must use string keys. Will accept dictionary only with the keys and value types indicated in
                 the example)
         * other objects (Will accept objects with the same fields as the example)
         
       Example:
       
       >>> from mrf.structs import JsonSerialiser
       >>> class Foo(object):
       ...     name = "dave"
       ...     age = 20
       ...     curltongue = True
       ...     petsnames = ["fluffles"]
       ...     coordinates = 45.2,23.1
       ...     other = {"favcake": "battenberg", "gradyear": 2010}
       ...
       >>> j = JsonSerialiser(Foo())
       >>> o = Foo()
       >>> o.name = "sarah"
       >>> o.age = 99
       >>> o.curltongue = False
       >>> o.petsnames = ["ben","bill"]
       >>> o.coordinates = 12.3, 45.6
       >>> o.other = {"favcake": "marble", "gradyear": 1066}
       >>> with open("myfile","w") as f:
       ...     j.serialise(o,f)
       ...
       >>> with open("myfile","r") as f:
       ...     o2 = j.deserialise(f)
       ...
       >>> o2.name
       u'sarah'
       >>> o2.petsnames
       [u'ben', u'bill']"""

    class IntSpec(object):
        def simplify(self, val):
            if not isinstance(val, (int,float)): raise ValueError()
            return int(val)
        desimplify = simplify
                    
    class FloatSpec(object):
        def simplify(self, val):
            if not isinstance(val, (int,float)): raise ValueError()
            return float(val)
        desimplify = simplify
        
    class StringSpec(object):
        def simplify(self, val):
            if not isinstance(val, basestring): raise ValueError()
            return unicode(val)
        desimplify = simplify
            
    class BoolSpec(object):
        def simplify(self, val):
            if not isinstance(val, bool): raise ValueError()
            return bool(val)
        desimplify = simplify

    class ListSpec(object):
        def __init__(self,inner_spec):
            self.inner_spec = inner_spec
        def simplify(self,val):
            if not isinstance(val,(list,tuple,set)): raise ValueError()
            return [ self.inner_spec.simplify(x) for x in val ]
        def desimplify(self, val):
            if not isinstance(val,(list,tuple,set)): raise ValueError()
            return [ self.inner_spec.desimplify(x) for x in val ]
            
    class TupleSpec(object):
        def __init__(self,inner_specs):
            self.inner_specs = inner_specs
        def simplify(self,val):
            if not isinstance(val,(list,tuple)): raise ValueError()
            if len(val) != len(self.inner_specs): raise ValueError()
            return [ self.inner_specs[i].simplify(x) for i,x in enumerate(val) ]
        def desimplify(self, val):
            if not isinstance(val,(list,tuple)): raise ValueError()
            if len(val) != len(self.inner_specs): raise ValueError()
            return tuple([ self.inner_specs[i].desimplify(x) for i,x in enumerate(val) ])

    class SetSpec(object):
        def __init__(self,inner_spec):
            self.inner_spec = inner_spec
        def simplify(self,val):
            if not isinstance(val,(list,tuple,set)): raise ValueError()
            return [ self.inner_spec.simplify(x) for x in val ]
        def desimplify(self, val):
            if not isinstance(val,(list,tuple,set)): raise ValueError()
            return set([ self.inner_spec.desimplify(x) for x in val ])
            
    class DictSpec(object):
        def __init__(self,property_specs):
            self.property_specs = property_specs
        def simplify(self,val):
            if not isinstance(val,dict): raise ValueError()
            result = {}
            for name,spec in self.property_specs.items():
                if name not in val: raise ValueError()
                result[unicode(name)] = spec.simplify(val[name])
            return result
        def desimplify(self,val):
            if not isinstance(val,dict): raise ValueError()
            result = {}
            for name,spec in self.property_specs.items():
                if name not in val: raise ValueError()
                result[unicode(name)] = spec.desimplify(val[name])
            return result
                
    class ObjectSpec(object):
        def __init__(self,obj_type,property_specs):
            self.obj_type = obj_type
            self.property_specs = property_specs
        def simplify(self,val):
            if not isinstance(val,self.obj_type): raise ValueError()
            result = {}
            for name,spec in self.property_specs.items():
                if not hasattr(val,name): raise ValueError()
                result[unicode(name)] = spec.simplify(getattr(val,name))
            return result
        def desimplify(self,val):
            if not isinstance(val,dict): raise ValueError()
            result = self.obj_type()
            for name,spec in self.property_specs.items():
                if name not in val: raise ValueError()
                setattr(result,unicode(name),spec.desimplify(val[name]))
            return result

    def __init__(self, example):
        """Constructs a new serialiser using the given value as an example of the specification. See class docstring for
           more info."""
        self.spec = self._make_spec(example)

    def serialise(self, val, filepointer):
        """Writes the given object as json to the given file handle. If the object doesn't meet the established spec,
           ValueError is raised"""
        return json.dump(self.spec.simplify(val),filepointer,indent=4)
        
    def deserialise(self, filepointer):
        """Reads json from the given file handle and converts it to an object according to the established spec. If the
           JSON structure doesn't meet the specification, ValueError is raised."""
        return self.spec.desimplify(json.load(filepointer))
        
    def _make_spec(self,val):        
        if isinstance(val, bool):
            return JsonSerialiser.BoolSpec()
        elif isinstance(val, int):
            return JsonSerialiser.IntSpec()
        elif isinstance(val, float):
            return JsonSerialiser.FloatSpec()
        elif isinstance(val, basestring):
            return JsonSerialiser.StringSpec()        
        elif isinstance(val, list):
            if len(val)!=1: raise ValueError()
            return JsonSerialiser.ListSpec(self._make_spec(next(iter(val))))
        elif isinstance(val, tuple):
            return JsonSerialiser.TupleSpec([self._make_spec(x) for x in val])
        elif isinstance(val, set):
            if len(val)!=1: raise ValueError()
            return JsonSerialiser.SetSpec(self._make_spec(next(iter(val))))
        elif isinstance(val, dict):
            props = {}
            for k,v in val.items():
                if not isinstance(k,basestring): raise ValueError()
                props[unicode(k)] = self._make_spec(v)
            return JsonSerialiser.DictSpec(props)
        else:
            props = {}
            for pname in [p for p in dir(val) if not p.startswith('_') and not callable(getattr(val,p))]:
                props[unicode(pname)] = self._make_spec(getattr(val,pname))
            return JsonSerialiser.ObjectSpec(type(val),props)


class YieldFrom(object):    
    """Helper class to capture StopIteration return values from generators in Python2 (similar to Python3's 
       "yield from" syntax
       
    >>> from mrf.structs import YieldFrom
    >>> def gen():
    ...     yield 1
    ...     yield 2
    ...     raise StopIteration("example")
    ... 
    >>> itr = YieldFrom(gen())
    >>> for i in itr: pass
    ... 
    >>> itr.return_value
    'example'"""
       
    return_value = None
    _iterator = None
    
    def __init__(self,iterator):
        self._iterator = iterator
        self.return_value = None
    
    def __iter__(self):
        return self
        
    def __next__(self):
        try:
            return next(self._iterator)
        except StopIteration as e:
            if len(e.args) > 0:
                self.return_value = e.args[0]
            raise
    
    next = __next__


def generator(fn):
    """Decorator to make a generator out of a regular function, for instances where one requires a zero-length iterable 
       without including a yield statement. Return values will be ignored."""
    def gen(*args,**kargs):
        if False: yield
        fn(*args,**kargs)
    return gen
