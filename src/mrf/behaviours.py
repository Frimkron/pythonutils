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
# TODO: Ability to define behaviour functions in Behavables as well as Behaviours
# 		so that Behavables can begin life with chain items before any Behaviours
#		are added. This means giving Behaviour and Behavable a common base class
#		and gathering behaviour functions when the first instance is created
#		(rather than in get_chain_items). The Behavable would replace each of 
#		it's behaviour function defs with a lambda which starts the chain  

import types


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
	
	def __init__(self):
		self.beh_chains = {}
		self.behaviours = {}
	
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
			for item in beh.get_chain_items():
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
		else:
			raise BehaviourError("Behaviour %s already added" % beh.__class__.__name__)
		  
	
	def _make_beh_chain_starter(self, chain_name):
		"""
		Internal function for creating the function which is called to start the 
		behaviour function chain
		"""
		return lambda s, *p, **kp: s.beh_chains[chain_name].function(
					s.beh_chains[chain_name].behaviour, s, 
					s.beh_chains[chain_name], *p, **kp) 
	
	
	def has_behaviour(self, beh):
		"""
		Returns true if the behavable already has the given behaviour type, or 
		false if it doesn't. The beh parameter may be a behaviour class or 
		instance.
		"""
		if type(beh)==type:
			return self.behaviours.has_key(beh)
		else:
			return self.behaviours.has_key(beh.__class__)
		


class BehaviourFunction(object):
	"""
	Decorator for indicating which methods of a Behaviour class are behaviour
	functions which should be added, chained together, to a behavable when the 
	behaviour is applied.
	
	A behaviour function should be an instancemethod, with its second parameter 
	(after "self") being a reference to the behavable it is attached to, and the 
	third parameter being the next function in the chain to call. 
	
	The nested function will take the same parameters as the function itself, 
	not including "self", the behavable or the nested function. The nested 
	function returns the results of the next behaviour function in the chain. If 
	there is no next function, None is returned.
	
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
			# "self" is a reference to the behaviour, "owner" is a reference to 
			# the behavable it is attached to, "nested" is the nested function to 
			# call within this function, "text" is a custom parameter
			def print_text(self, owner, nested, text):			
				print text
				# nested function must be called with the custom params
				nested(text)
		
		# create a behavable
		foo = Behavable()
		
		#add MyBehaviour to it
		foo.add_behaviour(MyBehaviour())
		
		#call newly introduced print_text method
		foo.print_text("hullo thar")
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
		
	
	def __call__(self, *params, **kwparams):
		"""
		Calling the class like a function invokes the function of the next item
		in the chain, if one exists, or does nothing otherwise
		"""
		if self.next_item != None:
			return self.next_item.function(self.next_item.behaviour, 
					self.next_item.owner, self.next_item, *params, **kwparams)
		else:
			return None
		

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
	
	def get_chain_items(self):
		"""
		Returns list of BehaviourChainItem instances, one for each behaviour 
		function defined in this behaviour.
		"""					
		# cache the behaviour functions in the behaviour's class
		if not hasattr(self.__class__, "beh_functions"):
			funcs = []
			for membkey in dir(self.__class__):
				if not membkey.startswith("_"):
					member = getattr(self.__class__, membkey)
					if( callable(member)
							and hasattr(member,"beh_function")
							and isinstance(member.beh_function, BehaviourFunction) ):
						funcs.append(member)
			self.__class__.beh_functions = funcs	
		
		items = []
		for f in self.__class__.beh_functions:
			items.append(BehaviourChainItem(self, f))
		
		return items
   
   
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
		
		
# -----------------------------------------------------------------------------	
# Testing 
# -----------------------------------------------------------------------------

if __name__ == "__main__":
	
	import unittest

	class TestLiving(Behaviour):
	
		def __init__(self, health):
			self.health = health
		
		@BehaviourFunction(priority=1.0)
		def get_health(self, owner, nested):
			nested()
			return self.health
		
		@BehaviourFunction(priority=1.0)
		def hurt(self, owner, nested, power):
			self.health -= power
			if self.health < 0:
				self.health = 0
			nested(power)
			
		@BehaviourFunction(priority=1.0)
		def heal(self, owner, nested, power):
			self.health += power
			if self.health > 100:
				self.health = 100
			nested(power)
			
	class TestArmoured(Behaviour):
		
		def __init__(self, strength):
			self.strength = strength
			
		@BehaviourFunction(priority=2.0)
		def hurt(self, owner, nested, power):
			if self.strength > 0:
				nested(power/2)
			else:
				nested(power)
			self.strength -= power
	
	class TestGuy(Behavable):
		
		def __init__(self, title, age):
			Behavable.__init__(self)
			self.title = title
			self.age = age
	
	class TestBehaviours(unittest.TestCase):
		
		def setUp(self):
			self.fred = Behavable()
		
		def testAdding(self):
			self.assertRaises(AttributeError, lambda: self.fred.get_health())
			self.fred.add_behaviour(TestLiving(100))
			self.assertEqual(self.fred.get_health(), 100)
			self.assertRaises(BehaviourError, self.fred.add_behaviour, TestLiving(100))
			
		def testHasBeh(self):
			self.assertEqual(self.fred.has_behaviour(TestLiving), False)
			self.assertEqual(self.fred.has_behaviour(TestLiving(100)), False)
			self.fred.add_behaviour(TestLiving(100))
			self.assertEqual(self.fred.has_behaviour(TestLiving), True)
			self.assertEqual(self.fred.has_behaviour(TestLiving(100)), True)
			
		def testChained(self):
			self.fred.add_behaviour(TestLiving(100))
			self.assertEqual(self.fred.get_health(), 100)
			self.fred.hurt(10)
			self.assertEqual(self.fred.get_health(), 90)
			self.fred.add_behaviour(TestArmoured(100))
			self.fred.hurt(10)
			self.assertEqual(self.fred.get_health(), 85)
			
		def testInstances(self):
			self.fred.add_behaviour(TestLiving(100))
			self.gail = Behavable()
			self.gail.add_behaviour(TestLiving(100))
			self.assertEqual(self.fred.get_health(), 100)
			self.fred.hurt(10)
			self.assertEqual(self.fred.get_health(), 90)
			self.assertEqual(self.gail.get_health(), 100)
			self.gail.hurt(10)
			self.assertEqual(self.gail.get_health(), 90)
			self.fred.add_behaviour(TestArmoured(100))
			self.fred.hurt(10)
			self.assertEqual(self.fred.get_health(),85)
			self.assertEqual(self.gail.get_health(),90)
			self.gail.add_behaviour(TestArmoured(100))
			self.gail.hurt(10)
			self.assertEqual(self.gail.get_health(), 85)
			self.assertEqual(self.fred.get_health(), 85)

		def testRecipe(self):
			recipe = BehavableRecipe(TestGuy, "Mr", age=25)
			dave = recipe.create()
			self.assertEquals(dave.has_behaviour(TestLiving), False)
			recipe.add_behaviour(TestLiving, 100)
			keith = recipe.create()
			self.assertEquals(dave.has_behaviour(TestLiving), False)
			self.assertEquals(keith.has_behaviour(TestLiving), True)
			self.assertEquals(keith.get_health(), 100)
			keith.hurt(5)
			self.assertEquals(keith.get_health(), 95)
			charlie = recipe.create()
			self.assertEquals(charlie.get_health(), 100)
			self.assertEquals(keith.get_health(), 95)
			keith.hurt(10)
			self.assertEquals(keith.get_health(), 85)
			self.assertEquals(charlie.get_health(), 100)
			recipe.add_behaviour(TestArmoured, 100)
			simon = recipe.create()
			simon.hurt(20)
			self.assertEquals(simon.get_health(), 90)
	
	unittest.main()

	