from mrf.statemachine import *
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
        self.assertEqual("cat not interested",tiddles.be_played_with())
        self.assertEqual("cat wakes up",tiddles.be_stroked())
        self.assertEqual("cat plays",tiddles.be_played_with())
        
    def testEnterExitHooks(self):
        tiddles = Cat()
        tiddles.change_state("Asleep")
        tiddles.be_stroked()
        self.assertEqual(2,tiddles.hunger)
        tiddles.be_fed()
        self.assertEqual(1,tiddles.hunger)
        tiddles.be_played_with()
        tiddles.be_stroked()
        tiddles.be_stroked()
        tiddles.be_fed()
        self.assertEqual(2,tiddles.hunger)
        
    def testStateName(self):
        tiddles = Cat()
        self.assertEqual(None, tiddles.get_state())
        tiddles.change_state("Asleep")
        self.assertEqual("Asleep", tiddles.get_state())
        
    def testInheritance(self):
        ginger = SneezyCat()
        self.assertEqual(4, len(ginger.states))
        
    def testMagicMethods(self):
        ginger = SneezyCat()
        ginger.change_state("Sneezing")
        self.assertNotEqual("ACHOOOOOOOOOOOO",str(ginger))
        self.assertNotEqual("ACHOOOOOOOOOOOO",ginger)
        self.assertEqual(SneezyCat,ginger.__class__)

        
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
        self.assertEqual("cat not interested",tiddles.be_played_with())
        self.assertEqual("cat wakes up",tiddles.be_stroked())
        self.assertEqual("cat plays",tiddles.be_played_with())
        
    def testEnterExitHooks(self):
        tiddles = FastCat()
        tiddles.change_state("Asleep")
        tiddles.be_stroked()
        self.assertEqual(2,tiddles.hunger)
        tiddles.be_fed()
        self.assertEqual(1,tiddles.hunger)
        tiddles.be_played_with()
        tiddles.be_stroked()
        tiddles.be_stroked()
        tiddles.be_fed()
        self.assertEqual(2,tiddles.hunger)
        
    def testStateName(self):
        tiddles = FastCat()
        self.assertEqual(None, tiddles.get_state())
        tiddles.change_state("Asleep")
        self.assertEqual("Asleep", tiddles.get_state())
        
        
        
