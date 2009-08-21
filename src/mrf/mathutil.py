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

------------------------

Math Utils Module

Math utilities. Notably:

	Angle		- angle class
	Vector2d	- 2D vector class
"""

import math
import random


class Angle(object):

	def __init__(self, rad=0):
		self.val = rad
		self._normalise()

	def __add__(self, w):
		if type(w)==Angle:
			return Angle(self.val + w.val)
		else:
			return Angle(self.val + w)

	def __sub__(self, w):
		if type(w)==Angle:
			return Angle(self.val - w.val)
		else:
			return Angle(self.val - w)

	def __mul__(self, w):
		return Angle(self.val * w)

	def __div__(self, w):
		return Angle(self.val / w)
	def __truediv__(self, w):
		return Angle(self.val / w)

	def _normalise(self):
		while(self.val > math.pi):
			self.val -= math.pi*2
		while(self.val < -math.pi):
			self.val += math.pi*2

	def to_rad(self):
		return self.val

	def to_deg(self):
		return self.val * (180.0/math.pi)

	def abs(self):
		return Angle(math.abs(self.val))

	def __eq__(self,w):
		if not hasattr(w, "val"): return False
		return self.val == w.val

	def __ne__(self,w):
		if not hasattr(w, "val"): return True
		return self.val != w.val

	def __lt__(self,w):
		if not hasattr(w, "val"): raise TypeError("expected val attribute")
		return self.val < w.val

	def __le__(self,w):
		if not hasattr(w, "val"): raise TypeError("expected val attribute")
		return self.val <= w.val

	def __gt__(self,w):
		if not hasattr(w, "val"): raise TypeError("expected val attribute")
		return self.val > w.val

	def __ge__(self,w):
		if not hasattr(w, "val"): raise TypeError("expected val attribute")
		return self.val >= w.val

	def __str__(self):
		return "%f rad" % self.val

	def __repr__(self):
		return "Angle(%f)" % self.val


class Vector2d(object):

	def __init__(self, i=0, j=0, dir=0, mag=0):
		if dir!=0 or mag!=0:
			if hasattr(dir, "to_rad"):
				dir = dir.to_rad()
			self.i = math.cos(dir) * mag
			self.j = math.sin(dir) * mag
		else:
			self.i = i
			self.j = j

	def __add__(self, w):
		return Vector2d(self.i + w.i, self.j + w.j)

	def __sub__(self, w):
		return Vector2d(self.i - w.i, self.j - w.j)

	def __mul__(self, w):
		return Vector2d(self.i * w, self.j * w)

	def __div__(self, w):
		return Vector2d(self.i / w, self.j / w)
	def __truediv__(self, w):
		return Vector2d(self.i / w, self.j / w)

	def dot(self, w):
		return self.i*w.i + self.j*w.j

	def __str__(self):
		return "vec(%f, %f)" % (self.i,self.j) 

	def __eq__(self,w):
		if type(w) != Vector2d: 
			raise TypeError("expected Vector2d type")
		return self.i == w.i and self.j == w.j

	def __ne__(self,w):
		if type(w) != Vector2d:
			raise TypeError("expected Vector2d type")
		return self.i != w.i or self.j != w.j

	def __repr__(self):
		return "Vector2d(%f,%f)" % (self.i,self.j)

	def get_dir(self):
		return Angle(math.atan2(self.j,self.i))

	def get_mag(self):
		return math.sqrt(math.pow(self.i,2)+math.pow(self.j,2))

	def unit(self):
		return self / self.get_mag()

	def to_tuple(self):
		return (self.i, self.j)


class Line(object):

	def __init__(self, a, b):
		self.a = a
		self.b = b

class Polygon(object):

	def __init__(self, points):
		self.points = points


def weighted_roulette(item_dict, normalised=False):
	d = item_dict.copy()
	
	if not normalised:
		# count total
		total = 0.0
		for k in d:
			total += d[k]
			
		# normalise scores
		for k in d:
			d[k] = float(d[k])/total
		
	# get random value and find where this lands
	val = random.random()
	count = 0.0
	for k in d:
		count += d[k]
		if count > val:
			return k
	return None

#---------------------------------------------------------------------------------
# Testing
#---------------------------------------------------------------------------------
if __name__ == '__main__':

	import unittest

	class Test(unittest.TestCase):

		def testAngles(self):
			self.assertEqual(Angle(math.pi/2) + Angle(math.pi), Angle(-math.pi/2))
			self.assertEqual(Angle(-math.pi/2) - Angle(math.pi), Angle(math.pi/2))
			self.assertAlmostEqual(Angle(math.pi/2).to_deg(), 90, 4) 

		def testVector2dMath(self):
			self.assertEqual(Vector2d(1,2) + Vector2d(2,3), Vector2d(3,5))
			self.assertEqual(Vector2d(1,2) - Vector2d(2,3), Vector2d(-1,-1))
			self.assertEqual(Vector2d(1,2) * 5, Vector2d(5,10))
			self.assertAlmostEqual(Vector2d(dir=math.pi/2,mag=2).i, Vector2d(0,2).i, 4)
			self.assertAlmostEqual(Vector2d(dir=math.pi/2,mag=2).j, Vector2d(0,2).j, 4)
			self.assertAlmostEqual(Vector2d(3,4).get_mag(), 5, 4)
			self.assertAlmostEqual(Vector2d(3,3).get_dir().val, Angle(math.pi/4).val, 4)
			self.assertAlmostEqual(Vector2d(3,4).unit().get_mag(), 1.0, 4)

		def testRoulette(self):
			items = {
				"alpha": 1,
				"beta": 2,
				"gamma": 7
			}
			results = {
				"alpha":0,
				"beta":0,
				"gamma":0
			}
			for i in range(1000):
				result = weighted_roulette(items)
				self.assert_(result!=None)
				results[result] += 1
				
			self.assertAlmostEquals(results["alpha"]/1000.0,1.0/10.0,1)
			self.assertAlmostEquals(results["beta"]/1000.0,2.0/10.0,1)
			self.assertAlmostEquals(results["gamma"]/1000.0,7.0/10.0,1)
	
	unittest.main()



