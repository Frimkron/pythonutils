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
"""

class StateMachine(object):

	class State(object):
        
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
       
	def __getattribute__(self, attr):
		if attr != "state" and hasattr(self, "state") and self.state != None:
			try:
				return self.state.__getattribute__(attr)
			except AttributeError, error:
				return object.__getattribute__(self, attr)
		else:
			return object.__getattribute__(self, attr)
        
	def change_state(self, statename):
		if self.state != None:
			self.state.exit_state()
		self.state = self.states[statename]
		if self.state != None:
			self.state.enter_state()
  
  
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
			
			pass
	
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
			tiddles.change_state("Asleep")
			self.assertEquals("Asleep", tiddles.get_state())
			
		def testInheritance(self):
			ginger = SneezyCat()
			self.assertEquals(4, len(ginger.states))
    		
	unittest.main()
    		
            