from mrf.interface import *
import unittest


class Test(unittest.TestCase):

    def test_impl(self):
    
        class MyIFace(Interface):
            alpha = 1
            beta = 2
            def one(self): pass
            def _two(self): pass
            def three(self): pass
            
        class MyObj(object):
            alpha = 2
            beta = 4
            gamma = 6
            def one(self): pass
            def three(self): pass
            def four(self): pass
            
        class MyObjTwo(object):
            alpha = 0            
            def one(self): pass
            def two(self): pass
            
        foo = MyObj()
        self.assertEqual(True, MyIFace.is_impl_by(foo))
        
        bar = MyObjTwo()
        self.assertEqual(False, MyIFace.is_impl_by(bar))
        
            
