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

-------------------

State Machine Module 

Utils for implementing the state machine pattern:

	StateMachine	- class which can be extended to create stateful objects 
						by overriding __getattribute__
"""

def statemethod(fn):
	"""
	Decorator for explicitly defining methods which may be overidden in states.
	For use with StateMachineBase for more efficient implementation of state 
	machine which does not use __getattribute__ for implicit attribute overriding
	"""
	def new_fn(self, *args, **kargs):
		fname = fn.__name__
		if hasattr(self,"state") and self.state!=None:
			if hasattr(self.state, fname):
				return getattr(self.state, fname)(*args,**kargs)
			else:
				return fn(self,*args,**kargs)
		else:
			return fn(self,*args,**kargs)
	return new_fn


class StateMachineBase(object):
	"""
	Version of StateMachine without the __getattribute__ definition. Allows 
	explicit definition of overridable methods using the @statemethod decorator 
	for efficiency rather than implicit overriding of all attributes as used by 
	StateMachine.
	"""
	
	class State(object):
		"""
		Base class for state machine states
		"""

		def __init__(self, mach):
			self.machine = mach

		def get_state(self):
			return self.__class__.__name__

		def enter_state(self):
			pass
		
		def exit_state(self):
			pass
		
	def __init__(self):
		#initialise state member to no state
		self.state = None
		#find States defined in class and store new instance of each in states dict
		self.states = {}
		for membkey in dir(self.__class__):
			if not membkey.startswith("_"):
				memb = getattr(self.__class__,membkey)
				if( type(memb) == type and issubclass(memb, StateMachine.State)
						and memb != StateMachine.State ):                
					self.states[membkey] = memb(self)    

	@statemethod
	def get_state(self):
		return None

	def change_state(self, statename):
		if self.state != None:
			self.state.exit_state()
		self.state = self.states[statename]
		if self.state != None:
			self.state.enter_state()


class StateMachine(StateMachineBase):
	"""
	Classes may extends this class to implement the state pattern. When an 
	instance is initialised, any members which are classes extending 
	StateMachine.State are instantiated and stored internally. The current state
	can be changed to any of these states by using the change_state method.
	States can override the behaviour of any attribute of the class instance 
	(apart from anything beginning with underscore) by declaring the same 
	attribute themselves. States can access the parent instance by using their
	"machine" attribute.
	
	Example:
	
	>>> class ToggleSwitch(StateMachine):
	...
	... 	class OnState(StateMachine.State):
	...		
	... 		def push(self):
	... 			self.machine.is_on = False
	... 			self.machine.change_state("OffState")
	...			
	>>> 	class OffState(StateMachine.State):
	... 	
	... 		def push(self):
	... 			self.machine.is_on = True
	... 			self.machine.change_state("OnState")
	...				
	... 	def __init__(self):
	... 		StateMachine.__init__(self)
	... 		self.change_state("OffState")
	...				
	>>> toggler = ToggleSwitch()
	>>> print toggler.is_on
	False
	>>> toggler.push()
	>>> print toggler.is_on
	True
	>>> toggler.push()
	>>> print toggler.is_on
	False
	"""

	def __getattribute__(self, attr):
		if( not attr.startswith("_") and attr != "state" 
				and hasattr(self, "state") and self.state != None ):
			try:
				return self.state.__getattribute__(attr)
			except AttributeError, error:
				return object.__getattribute__(self, attr)
		else:
			return object.__getattribute__(self, attr)

	def get_state(self):
		return None   
	


# ----------- Testing ------------------------------------------------      
if __name__ == "__main__":
	import unittest
	
	class Cat(StateMachine):
		
		def __init__(self):
			StateMachine.__init__(self)
			self.hunger = 0
		
		class Asleep(StateMachine.State):		
			def be_stroked(self):
				self.machine.change_state("Awake")
				return "cat wakes up"
			def be_fed(self):
				self.machine.change_state("Eating")
				return "cat starts eating"
			def exit_state(self):
				self.machine.hunger += 2
		
		class Awake(StateMachine.State):
			def be_stroked(self):
				self.machine.change_state("Asleep")
				return "cat goes to sleep"
			def be_fed(self):
				self.machine.change_state("Eating")
				return "cat starts eating"
			def be_played_with(self):
				self.machine.hunger += 1
				return "cat plays"
		
		class Eating(StateMachine.State):
			def enter_state(self):
				if self.machine.hunger > 0:
					self.machine.hunger -= 1
			def be_played_with(self):
				self.machine.change_state("Awake")
				return "cat stops eating"
			
		def be_stroked(self):
			return "cat does not like"
		
		def be_fed(self):
			return "cat does not want"
		
		def be_played_with(self):
			return "cat not interested"
		
	class SneezyCat(Cat):
		
		class Sneezing(StateMachine.State):
			
			def be_played_with(self):
				return Cat.__getattribute__(self.machine, "be_played_with")(self.machine)
			
			def __repr__(self):
				return "ACHOOOOOOOOOOOO"
			
			def __str__(self):
				return "ACHOOOOOOOOOOOO"
	
	class Test(unittest.TestCase):

		def testPropertyOverride(self):
			tiddles = Cat()
			tiddles.change_state("Asleep")
			self.assertEquals("cat not interested",tiddles.be_played_with())
			self.assertEquals("cat wakes up",tiddles.be_stroked())
			self.assertEquals("cat plays",tiddles.be_played_with())
			
		def testEnterExitHooks(self):
			tiddles = Cat()
			tiddles.change_state("Asleep")
			tiddles.be_stroked()
			self.assertEquals(2,tiddles.hunger)
			tiddles.be_fed()
			self.assertEquals(1,tiddles.hunger)
			tiddles.be_played_with()
			tiddles.be_stroked()
			tiddles.be_stroked()
			tiddles.be_fed()
			self.assertEquals(2,tiddles.hunger)
			
		def testStateName(self):
			tiddles = Cat()
			self.assertEquals(None, tiddles.get_state())
			tiddles.change_state("Asleep")
			self.assertEquals("Asleep", tiddles.get_state())
			
		def testInheritance(self):
			ginger = SneezyCat()
			self.assertEquals(4, len(ginger.states))
			
		def testMagicMethods(self):
			ginger = SneezyCat()
			ginger.change_state("Sneezing")
			self.assertNotEquals("ACHOOOOOOOOOOOO",str(ginger))
			self.assertNotEquals("ACHOOOOOOOOOOOO",ginger)
			self.assertEquals(SneezyCat,ginger.__class__)
			
	class FastCat(StateMachineBase):
		
		def __init__(self):
			StateMachineBase.__init__(self)
			self.hunger = 0
		
		class Asleep(StateMachine.State):		
			def be_stroked(self):
				self.machine.change_state("Awake")
				return "cat wakes up"
			def be_fed(self):
				self.machine.change_state("Eating")
				return "cat starts eating"
			def exit_state(self):
				self.machine.hunger += 2
		
		class Awake(StateMachine.State):
			def be_stroked(self):
				self.machine.change_state("Asleep")
				return "cat goes to sleep"
			def be_fed(self):
				self.machine.change_state("Eating")
				return "cat starts eating"
			def be_played_with(self):
				self.machine.hunger += 1
				return "cat plays"
		
		class Eating(StateMachine.State):
			def enter_state(self):
				if self.machine.hunger > 0:
					self.machine.hunger -= 1
			def be_played_with(self):
				self.machine.change_state("Awake")
				return "cat stops eating"
			
		@statemethod
		def be_stroked(self):
			return "cat does not like"
		
		@statemethod
		def be_fed(self):
			return "cat does not want"
		
		@statemethod
		def be_played_with(self):
			return "cat not interested"
		
	class FastTest(unittest.TestCase):
		
		def testPropertyOverride(self):
			tiddles = FastCat()
			tiddles.change_state("Asleep")
			self.assertEquals("cat not interested",tiddles.be_played_with())
			self.assertEquals("cat wakes up",tiddles.be_stroked())
			self.assertEquals("cat plays",tiddles.be_played_with())
			
		def testEnterExitHooks(self):
			tiddles = FastCat()
			tiddles.change_state("Asleep")
			tiddles.be_stroked()
			self.assertEquals(2,tiddles.hunger)
			tiddles.be_fed()
			self.assertEquals(1,tiddles.hunger)
			tiddles.be_played_with()
			tiddles.be_stroked()
			tiddles.be_stroked()
			tiddles.be_fed()
			self.assertEquals(2,tiddles.hunger)
			
		def testStateName(self):
			tiddles = FastCat()
			self.assertEquals(None, tiddles.get_state())
			tiddles.change_state("Asleep")
			self.assertEquals("Asleep", tiddles.get_state())
    		
	unittest.main()
    		
            