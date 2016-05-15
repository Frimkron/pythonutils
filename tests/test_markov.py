from mrf.markov import *
import unittest


class Test(unittest.TestCase):
    
    def setUp(self):
        self.m = Markov()
        self.m.add_seq("book shop book mark book shop".split())
    
    def testMostProb(self):
        self.assertAlmostEqual(self.m.get_prob("book","mark"),1.0/3.0,1)
        self.assertEqual(self.m.most_probable("book"),"shop")
    
    def testRoulette(self):
        results = {
            "shop" : 0,
            "mark" : 0
        }
        for i in range(10000):
            result = self.m.weighted_roulette("book")
            self.assertTrue(result in ["shop","mark"])
            results[result] += 1
        self.assertAlmostEqual(float(results["shop"])/10000.0,2.0/3.0,1)
        self.assertAlmostEqual(float(results["mark"])/10000.0,1.0/3.0,1)
    
    def testHigherOrder(self):
        self.m = Markov(2)
        self.m.add_seq("book shop book mark book shop".split())

        self.assertAlmostEqual(self.m.get_prob(("book","shop"),"book"),1.0/2.0,1)
        self.assertEqual(self.m.most_probable(("shop","book")),"mark")

