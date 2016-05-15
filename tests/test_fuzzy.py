from mrf.fuzzy import *
import unittest
    
    
class TestClasses(unittest.TestCase):

    def testTriangular(self):
    
        c = TriangularClass(0,2)
        self.assertAlmostEqual(0.0, c.get_dom(-1.5), 2)
        self.assertAlmostEqual(0.0, c.get_dom(-1), 2)
        self.assertAlmostEqual(0.25, c.get_dom(-0.75), 2)
        self.assertAlmostEqual(0.75, c.get_dom(-0.25), 2)
        self.assertAlmostEqual(1.0, c.get_dom(0), 2)
        self.assertAlmostEqual(0.75, c.get_dom(0.25), 2)
        self.assertAlmostEqual(0.25, c.get_dom(0.75), 2)
        self.assertAlmostEqual(0.0, c.get_dom(1), 2)
        self.assertAlmostEqual(0.0, c.get_dom(1.5), 2)
        
    def testTrapezoid(self):
        
        c = TrapezoidClass(0,4,2)
        self.assertAlmostEqual(0.0, c.get_dom(-2.5), 2)
        self.assertAlmostEqual(0.0, c.get_dom(-2.0), 2)
        self.assertAlmostEqual(0.25, c.get_dom(-1.75), 2)
        self.assertAlmostEqual(0.75, c.get_dom(-1.25), 2)
        self.assertAlmostEqual(1.0, c.get_dom(-1),2)
        self.assertAlmostEqual(1.0, c.get_dom(-0.5), 2)
        self.assertAlmostEqual(1.0, c.get_dom(0),2)
        self.assertAlmostEqual(1.0, c.get_dom(0.5), 2)
        self.assertAlmostEqual(1.0, c.get_dom(1), 2)
        self.assertAlmostEqual(0.75, c.get_dom(1.25), 2)
        self.assertAlmostEqual(0.25, c.get_dom(1.75), 2)
        self.assertAlmostEqual(0, c.get_dom(2), 2)
        self.assertAlmostEqual(0, c.get_dom(2.5), 2)
        
    def testLeftShoulder(self):
    
        c = LeftShoulderClass(-1,1,2)
        self.assertAlmostEqual(0.0, c.get_dom(-2), 2)
        self.assertAlmostEqual(1.0, c.get_dom(-1), 2)
        self.assertAlmostEqual(1.0, c.get_dom(0), 2)
        self.assertAlmostEqual(1.0, c.get_dom(1), 2)
        self.assertAlmostEqual(0.75, c.get_dom(1.25), 2)
        self.assertAlmostEqual(0.25, c.get_dom(1.75), 2)
        self.assertAlmostEqual(0, c.get_dom(2), 2)
        self.assertAlmostEqual(0, c.get_dom(2.5), 2)


class TestRuleParser(unittest.TestCase):

    def testParsing(self):
        
        r = RuleParser()
        rule = r.parse("IF foo IS high THEN bar IS low")
        self.assertEqual("if", rule.children[0].type)
        self.assertEqual("E", rule.children[1].type)
        self.assertEqual("T", rule.children[1].children[0].type)
        self.assertEqual("I", rule.children[1].children[0].children[0].type)
        self.assertEqual("name", rule.children[1].children[0].children[0].children[0].type)
        self.assertEqual("foo", rule.children[1].children[0].children[0].children[0].data)
        self.assertEqual("is", rule.children[1].children[0].children[0].children[1].type)
        self.assertEqual("name", rule.children[1].children[0].children[0].children[2].type)
        self.assertEqual("high", rule.children[1].children[0].children[0].children[2].data)
        self.assertEqual("then", rule.children[2].type)
        self.assertEqual("I", rule.children[3].type)
        self.assertEqual("name", rule.children[3].children[0].type)
        self.assertEqual("bar", rule.children[3].children[0].data)
        self.assertEqual("is", rule.children[3].children[1].type)
        self.assertEqual("name", rule.children[3].children[2].type)
        self.assertEqual("low", rule.children[3].children[2].data)
        
        rule = r.parse("IF foo IS high AND bar IS low THEN wah IS flibble")
        self.assertEqual("E", rule.children[1].type)
        self.assertEqual("A", rule.children[1].children[0].type)
        self.assertEqual("E", rule.children[1].children[0].children[0].type)
        self.assertEqual("T", rule.children[1].children[0].children[0].children[0].type)
        self.assertEqual("T", rule.children[1].children[0].children[2].type)


class TestRuleSet(unittest.TestCase):
    
    def setUp(self):
        
        self.r = RuleSet()
        """ 
        |    .    .    .
        |   /|\  /|\  /|\
        |  / | \/ | \/ | \
        +-+-+-+'+-+-+'+-+-+-+
        0 1 2 3 4 5 6 7 8 9 10 
        """
        self.r.add_flv("alpha")
        self.r.add_class("alpha","low",(2.5,3.0))
        self.r.add_class("alpha","med",(5.0,3.0))
        self.r.add_class("alpha","high",(7.5,3.0))
        
        self.r.add_flv("beta")
        self.r.add_class("beta","low",(2.5,3.0))
        self.r.add_class("beta","med",(5.0,3.0))
        self.r.add_class("beta","high",(7.5,3.0))
        
        self.r.add_flv("gamma")
        self.r.add_class("gamma","tall",(2.5,3.0))
        self.r.add_class("gamma","regular",(5.0,3.0))
        self.r.add_class("gamma","grande",(7.5,3.0))
        
        self.r.add_rule("IF alpha IS low THEN beta IS high") 
        self.r.add_rule("IF alpha IS med THEN beta IS med") 
        self.r.add_rule("IF alpha IS high THEN beta IS low")
        self.r.add_rule("IF alpha IS low AND beta IS high THEN gamma IS tall") 
        self.r.add_rule("IF alpha IS high AND beta IS low THEN gamma IS grande") 
        self.r.add_rule("IF alpha IS med OR beta IS med THEN gamma IS regular")
    
    def testRuleSet(self):
        
        out = self.r.evaluate({"alpha":2.5,"beta":7.5})
        self.assertAlmostEqual(2.5, out["gamma"], 2)
        self.assertAlmostEqual(7.5, out["beta"], 2)
        
        out = self.r.evaluate({"alpha":5.0,"beta":5.0})
        self.assertAlmostEqual(5.0, out["beta"], 2)
        self.assertAlmostEqual(5.0, out["gamma"], 2)
        
        out = self.r.evaluate({"alpha":3.75, "beta":6.25})
        self.assertAlmostEqual(6.25, out["beta"], 2)
        self.assertAlmostEqual(3.75, out["gamma"], 2)
        
        out = self.r.evaluate({"alpha":0.5, "beta":3.75})
        self.assertAlmostEqual(5.0, out["gamma"], 2)
        self.assertFalse("beta" in out)

