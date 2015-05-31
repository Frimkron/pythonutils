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

--------------------

Behaviours Module

Module for implementing runtime-changable object behaviours - a system similar to 
the Decorator pattern, but with some differences.
"""

# TODO: Removing behaviours 

import types
import mrf.structs


class BehaviourError(Exception):
    """    
    Thrown by functions in this module
    """
    pass


class Behavable(object):
    """    
    A behavable object may change the way it works depending on the behaviours
    that are attached to it at runtime.
    """
    
    __metaclass__ = mrf.structs.IntrospectType
    
    @classmethod
    def _class_init(cls):
        # called by metaclass when class created
        cls._cache_behaviour_functions()
    
    @classmethod
    def _cache_behaviour_functions(cls):
        # examine the class functions and catalog behaviour functions
        funcs = []
        for membkey in dir(cls):
            if not membkey.startswith("_"):
                member = getattr(cls, membkey)
                if( callable(member)
                        and hasattr(member,"beh_function")
                        and isinstance(member.beh_function, BehaviourFunction) ):
                    funcs.append(member)
        cls.beh_functions = funcs    
    
    def __init__(self):
        self.beh_chains = {}
        self.behaviours = {}
        
        #set up own behaviour functions as chains
        self._add_behavable_chain_items(self)
    
    def _get_chain_items(self):
        """    
        Returns list of BehaviourChainItem instances, one for each behaviour 
        function defined in this Behavable.
        """
        items = []
        for f in self.__class__.beh_functions:
            items.append(BehaviourChainItem(self, f))
        
        return items
    
    def _add_behavable_chain_items(self, able):
        for item in able._get_chain_items():
            #set behavable reference
            item.owner = self
            #add to chain
            if not self.beh_chains.has_key(item.name):
                self.beh_chains[item.name] = item
                #create new instance method to expose the chain as a function                    
                setattr(self, item.name, types.MethodType(
                        self._make_beh_chain_starter(item.name),
                        self, self.__class__))
            else:
                self.beh_chains[item.name] = self.beh_chains[item.name].insert_item(item)    
    
    def add_behaviour(self, beh):
        """    
        Adds the given behaviour to this behavable. Beh should be a behaviour 
        instance. Only one instance of a behaviour type may be added to a 
        behavable instance - further instances are ignored
        """
        if not self.behaviours.has_key(beh.__class__):
            #record behaviour instance
            self.behaviours[beh.__class__] = beh
            #update chains
            self._add_behavable_chain_items(beh)
        else:
            raise BehaviourError("Behaviour %s already added" % beh.__class__.__name__)
          
    
    def _make_beh_chain_starter(self, chain_name):
        """    
        Internal function for creating the function which is called to start the 
        behaviour function chain
        """
        # define starter function
        def start_chain(s, *p, **kp):
            # construct new context object
            context = BehaviourChainContext()
            context.owner = s
            context.nested = s.beh_chains[chain_name] # when called, the chain item invokes its successor
            # execute the first item's function and return value
            return s.beh_chains[chain_name].function(s.beh_chains[chain_name].behaviour,
                context, *p, **kp)
        # return the starter function
        return start_chain
    
    
    def has_behaviour(self, beh):
        """    
        Returns true if the behavable already has the given behaviour type, or 
        false if it doesn't. The beh parameter may be a behaviour class or 
        instance.
        """
        if isinstance(beh,type):
            return self.behaviours.has_key(beh)
        else:
            return self.behaviours.has_key(beh.__class__)
        


class BehaviourFunction(object):
    """    
    Decorator for indicating which methods of a Behaviour class are behaviour
    functions which should be added, chained together, to a behavable when the 
    behaviour is applied.
    
    A behaviour function should be an instancemethod, with its second parameter 
    (after "self") being a reference to a mutable object in which chain-scope 
    information can be stored. The following special attributes are provided
    in this object:
        owner    - a reference to the behavable the behaviour is attached to
        nested    - a callable which should be called to invoke the next item
                in the chain. For best results, always call this method.
    
    The nested function will take the same parameters as the function itself, 
    not including "self". i.e. the mutable object described above must be passed
    on along with any custom parameters - all of which can of course have been 
    altered. The nested function returns the results of the next behaviour function 
    in the chain. If there is no next function, None is returned.
    
    When a behaviour function is attached to a behavable instance, only the custom
    parameters are required to call it as an instance method.
    
    Params:
        priority - determines the order in which chained behaviour functions 
                    execute
                    
    Example:
    
        # a behaviour class extending behaviour
        class MyBehaviour(Behaviour):
        
            # the BehaviourFunction decorator is used to declare a behaviour function
            @BehaviourFunction(priority=1.0)
            # "self" is a reference to the behaviour, "context" is an object containing 
            # various information about the behaviour chain, and "foo" is a cutom parameter
            def print_foo(self, context, foo):            
                print foo
                # nested function must be called with the same parameters
                context.nested(context, foo)
        
        # create a behavable
        foo = Behavable()
        
        #add MyBehaviour to it
        foo.add_behaviour(MyBehaviour())
        
        #call newly introduced print_text method
        foo.print_foo("hullo thar")
    """
    
    def __init__(self, **params):
        self.__dict__.update(params)
        
    def __call__(self, fn):
        fn.beh_function = self
        return fn


class BehaviourChainItem(object):
    """    
    Object for creating the chains of behaviour functions inside a behavable as
    behaviours are added to it
    """
    
    def __init__(self, behaviour, function):
        self.next_item = None
        self.behaviour = behaviour
        self.function = function
        self.name = function.__name__
        if not hasattr(function.beh_function, "priority"):
            self.priority = 1.0
        else:
            self.priority = function.beh_function.priority
        
        
    def insert_item(self, item):
        """    
        Inserts a new BehaviourChainItem into the chain according to its priority.
        Returns the item which should replace it
        """
        if item.priority >= self.priority:
            #should wrap around this item
            item.next_item = self
            return item
        else:
            #should go inside this item - compare against current nested item,
            #if there is one
            if self.next_item != None:
                self.next_item = self.next_item.insert_item(item)
            else:
                self.next_item = item
            return self
        
        item.concept = self.concept
        
    
    def __call__(self, context, *params, **kwparams):
        """    
        Calling the class like a function invokes the function of the next item
        in the chain, if one exists, or does nothing otherwise
        """
        if self.next_item != None:
            # preserve the existing special context attributes
            specials = context.get_special_attrs()
            # prepare the context object with new "nested"
            context.nested = self.next_item
            # call the function with the prepared context
            retval = self.next_item.function(self.next_item.behaviour, 
                    context, *params, **kwparams)
            # restore the context's original "nested" value
            context.set_special_attrs(specials)
            # return
            return retval
        else:
            return None
        

class BehaviourChainContext(object):
    """    
    Used to store information accessible to all items in a behaviour chain.
    """
    SPECIAL_ATTRS = ( "owner", "nested" )

    def __init__(self):
        for a in BehaviourChainContext.SPECIAL_ATTRS:
            setattr(self, a, None)

    def get_special_attrs(self):
        d = {}
        for a in BehaviourChainContext.SPECIAL_ATTRS:
            d[a] = getattr(self, a)
        return d    
        
    def set_special_attrs(self, attrdict):
        for a in BehaviourChainContext.SPECIAL_ATTRS:
            setattr(self, a, attrdict[a])        


class Behaviour(Behavable):
    """    
    A Behaviour is designed to encapsulate some functionality which could be 
    applied to many different Behavable objects at runtime to dynamically change 
    the way they work. This is acheived by marking certain methods of the 
    Behaviour object as behaviour functions and then adding these functions as 
    methods of the Behavable object when the Behaviour is attached to it. Where 
    different Behaviour types share behaviour functions with the same name, these
    are chained together in the Behavable object such that the version with the 
    lower priority is nested inside the one with the higher priority. 
    
    To mark a method as a behaviour function, decorate  it with the 
    BehaviourFunction decorator. A behaviour function must take the Behavable
    instance and a nested function as second and third parameters after "self".
    See the BehaviourFunction docstring for more information.
    
    Note that Behaviour is itself a subclass of Behavable as such may have 
    behaviours attached to it. 
    """
    pass
   
   
class BehavableRecipe(object):
    """    
    Class for creating templates to which behaviours can be added and from which
    Behavable instances can be created with all of the behaviours already added
    """
    
    def __init__(self, base, *base_args, **base_kargs):
        """    
        base - the Behavable class to instantiate with Behaviours attached
        *base_args - arguments to pass into Behavable when instantiating
        **base_kargs - keyword args to pass into Behavable when instantiating
        """
        self.base = base
        self.base_args = base_args
        self.base_kargs = base_kargs
        self.behs = []
        
    def add_behaviour(self, beh, *beh_args, **beh_kargs):
        """    
        Adds a behaviour to the recipe which will be added to Behavable 
        instances created from this recipe.
        beh - the Behaviour class to instantiate and add to each Behavable
        *beh_args - arguments to pass into Behaviour when instantiating
        *beh_kargs - keywords args to pass into Behaviour when instantiating
        """
        if not self.has_behaviour(beh):
            self.behs.append((beh, beh_args, beh_kargs))
        else:
            raise BehaviourError("Recipe already contains behaviour %s" % beh.__class__.__name__)
        
    def has_behaviour(self, beh):
        beh = beh if isinstance(beh, type) else beh.__class__
        for bdata in self.behs:
            if type(bdata[0]) == beh:
                return True
        return False
        
    def create(self):
        """    
        Returns a new instance of the Behavable with the specified Behaviours
        instantiated and added to it.
        """
        new = self.base(*self.base_args, **self.base_kargs)
        for bdata in self.behs:
            new.add_behaviour(bdata[0](*bdata[1], **bdata[2]))
        return new
        
        
