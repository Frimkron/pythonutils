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

