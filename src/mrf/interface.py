

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
			
