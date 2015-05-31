import unittest

from mrf.behaviours import *


class TestLiving(Behaviour):

    def __init__(self, health):
        self.health = health
    
    @BehaviourFunction(priority=1.0)
    def get_health(self, context):            
        return self.health
    
    @BehaviourFunction(priority=1.0)
    def hurt(self, context, power):
        self.health -= power
        if self.health < 0:
            self.health = 0
        context.nested(context,power)
        
    @BehaviourFunction(priority=1.0)
    def heal(self, context, power):
        self.health += power
        if self.health > 100:
            self.health = 100
        context.nested(context,power)

        
class TestArmoured(Behaviour):
    
    def __init__(self, strength):
        self.strength = strength
        
    @BehaviourFunction(priority=2.0)
    def hurt(self, context, power):
        if self.strength > 0:
            context.nested(context,power/2)
        else:
            context.nested(context,power)
        self.strength -= power


class TestGuy(Behavable):
    
    def __init__(self, title, age):
        Behavable.__init__(self)
        self.title = title
        self.age = age

    @BehaviourFunction(priority=0.5)
    def get_health(self, context):
        return 10


class TestBehaviours(unittest.TestCase):
    
    def testAdding(self):
        fred = Behavable()
        self.assertRaises(AttributeError, lambda: fred.get_health())
        fred.add_behaviour(TestLiving(100))
        self.assertEqual(fred.get_health(), 100)
        self.assertRaises(BehaviourError, fred.add_behaviour, TestLiving(100))
        
    def testHasBeh(self):
        fred = Behavable()
        self.assertEqual(fred.has_behaviour(TestLiving), False)
        self.assertEqual(fred.has_behaviour(TestLiving(100)), False)
        fred.add_behaviour(TestLiving(100))
        self.assertEqual(fred.has_behaviour(TestLiving), True)
        self.assertEqual(fred.has_behaviour(TestLiving(100)), True)
        
    def testChained(self):
        fred = Behavable()
        fred.add_behaviour(TestLiving(100))
        self.assertEqual(fred.get_health(), 100)
        fred.hurt(10)
        self.assertEqual(fred.get_health(), 90)
        fred.add_behaviour(TestArmoured(100))
        fred.hurt(10)
        self.assertEqual(fred.get_health(), 85)
        
    def testInstances(self):
        fred = Behavable()
        fred.add_behaviour(TestLiving(100))
        gail = Behavable()
        gail.add_behaviour(TestLiving(100))
        self.assertEqual(fred.get_health(), 100)
        fred.hurt(10)
        self.assertEqual(fred.get_health(), 90)
        self.assertEqual(gail.get_health(), 100)
        gail.hurt(10)
        self.assertEqual(gail.get_health(), 90)
        fred.add_behaviour(TestArmoured(100))
        fred.hurt(10)
        self.assertEqual(fred.get_health(),85)
        self.assertEqual(gail.get_health(),90)
        gail.add_behaviour(TestArmoured(100))
        gail.hurt(10)
        self.assertEqual(gail.get_health(), 85)
        self.assertEqual(fred.get_health(), 85)

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
    
    def testBehavableFunctions(self):
        bob = TestGuy("Mr", 25)
        self.assertEquals(True, hasattr(bob, "get_health"))
        self.assertEquals(10, bob.get_health())
        bob.add_behaviour(TestLiving(100))
        self.assertEquals(100, bob.get_health())
    
    def testInheritance(self):

        class Cat(Behavable):
            @BehaviourFunction()
            def meow(self, context):
                return "meow"    
            @BehaviourFunction()
            def purr(self, context):
                return "purr"

        c = Cat()
        self.assertEquals("meow",c.meow())
        self.assertEquals("purr",c.purr())
        
        class Tiddles(Cat):
            @BehaviourFunction()
            def meow_louder(self, context):
                return "MEOW"
            @BehaviourFunction()
            def purr(self, context):
                return "*ahem* "+Cat.purr(self,context)

        t = Tiddles()
        self.assertEquals("meow",t.meow())
        self.assertEquals("MEOW",t.meow_louder())
        self.assertEquals("*ahem* purr",t.purr())

        class MeowWhenPurr(Behaviour):
            @BehaviourFunction()
            def purr(self,context):
                return context.owner.meow()+" "+context.nested(context)+" "+context.owner.meow()

        t.add_behaviour(MeowWhenPurr())
        self.assertEquals("meow *ahem* purr meow",t.purr())
        
        class MeowWhenPurrThenMew(MeowWhenPurr):
            @BehaviourFunction()
            def purr(self,context):
                return MeowWhenPurr.purr(self,context)+" mew"

        t2 = Tiddles()
        t2.add_behaviour(MeowWhenPurrThenMew())
        self.assertEquals("meow *ahem* purr meow mew",t2.purr())
    
    def testContext(self):
        
        class Button(Behavable):
            @BehaviourFunction()
            def push(self,context):
                s = ""
                n = context.nested(context)
                if not n is None:
                    s += n
                return s
            
        class LightActivation(Behaviour):
            @BehaviourFunction()
            def push(self,context):
                s = ""
                if( not hasattr(context,"dinged")
                        or not context.dinged):
                    s += "ding! "
                    context.dinged = True
                s += "click! "
                n = context.nested(context)
                if not n is None:
                    s += n
                return s

        class FanActivation(Behaviour):
            @BehaviourFunction()
            def push(self,context):
                s = ""
                if( not hasattr(context,"dinged")
                        or not context.dinged):
                    s += "ding! "
                    context.dinged = True
                s += "wrrr! "
                n = context.nested(context)
                if not n is None:
                    s += n
                return s

        # do nothing button
        b = Button()
        self.assertEquals("", b.push())

        # light-only button
        b = Button()
        b.add_behaviour(LightActivation())
        self.assertEquals("ding! click! ", b.push())

        # fan-only button
        b = Button()
        b.add_behaviour(FanActivation())
        self.assertEquals("ding! wrrr! ", b.push())

        # light and fan button - one ding only
        b = Button()
        b.add_behaviour(LightActivation())
        b.add_behaviour(FanActivation())
        self.assertEquals("ding! wrrr! click! ", b.push())
        self.assertEquals("ding! wrrr! click! ", b.push())



