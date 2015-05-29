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

---------------------

Interface Module

A simple interface implementation
"""

class Interface(object):

    @classmethod
    def is_impl_by(clazz, object):        
        for a in dir(clazz):
            if not a.startswith("_") and not a=="is_impl_by":
                if not hasattr(object, a):            
                    return False
                attr = getattr(clazz,a)
                if callable(attr):
                    if not callable(getattr(object,a)):
                        return False
        return True
        
        
# --- Testing ------------------------------------------------------------------        
        
if __name__ == "__main__":

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
            self.assertEquals(True, MyIFace.is_impl_by(foo))
            
            bar = MyObjTwo()
            self.assertEquals(False, MyIFace.is_impl_by(bar))
            
    unittest.main()
            
