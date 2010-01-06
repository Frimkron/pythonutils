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
	Line		- 2D line
	Polygon		- 2D shape
	Rectangle	- 2D rectangle
"""

import math
import unittest
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
		return Angle(math.fabs(self.val))

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
		if type(w) != type(self): 
			return False
		return self.i == w.i and self.j == w.j
	
	def __ne__(self,w):
		if type(w) != type(self):
			return False
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
	
	def __getitem__(self, index):
		if index == 0:
			return self.i
		elif index == 1:
			return self.j
		else:
			raise IndexError("Index must be 0 or 1")
		
	def __setitem__(self, index, value):
		if index == 0:
			self.i = value
		elif index == 1:
			self.j = value
		else:
			raise IndexError("Index must be 0 or 1")
	
	
def sigmoid(x):
	"""	
	S-curve function. sigmoid(0) is almost 0 and sigmoid(1) is almost 1, with
	an S-shaped curve in between.
	"""
	return 1.0/(1.0+math.exp(-(x-0.5)*12.0))
	
def mean(values):
	n = len(values)
	return float(sum(values))/n if n>0 else 0.0

def standard_deviation(values):
	m = mean(values)
	sq_devs = [pow(x-m,2) for x in values]
	var = mean(sq_devs)
	return math.sqrt(var)

def deviation(values, val):
	"""
	returns "val"s absolute deviation from the mean of "values", in standard 
	deviations
	""" 
	m = mean(values)
	dev = abs(val-m)
	sd = standard_deviation(values)
	return float(dev)/sd if sd!=0 else 0.0 
	
	
def dist_to_line(line, point):
	"""	
	Finds a point's distance from a line of infinite length. To find a point's
	distance from a line segment, use dist_to_line_seg instead.
	 
	line: ((lx0,ly0), (lx1,ly1)) Two points on the line
	point: (px, py) The point to find the distance from
	
	returns: the distance between the point and the line
	"""
	x1,y1 = line[0]
	x2,y2 = line[1]
	x3,y3 = point
	
	# where on line the perpendicular is
	u = ( ((x3-x1)*(x2-x1) + (y3-y1)*(y2-y1))
			/  (math.pow(x1-x2,2) + math.pow(y1-y2,2)) )
	
	# intersection point
	x = x1 + u*(x2-x1)
	y = y1 + u*(y2-y1)
	
	dist = math.sqrt(math.pow(x-x3,2)+math.pow(y-y3,2))
	
	return dist
	
def dist_to_line_seg(line, point):
	"""	
	Finds a point's distance from a line segment. To find a point's distance
	from a line of infinite length, use dist_to_line instead.
	
	line: ((lx0,ly0), (lx1,ly1)) The start and end points of the line segment
	point: (px,py) The point to find the distance from
	
	returns: the distance between the point and the line
	"""
	x1,y1 = line[0]
	x2,y2 = line[1]
	x3,y3 = point
	
	# where on line the perpendicular is
	u = ( ((x3-x1)*(x2-x1) + (y3-y1)*(y2-y1))
			/ (math.pow(x1-x2,2) + math.pow(y1-y2,2)) )
	
	# closet to mid section or an end point?
	if 0.0 <= u <= 1.0:		
		x = x1 + u*(x2-x1)
		y = y1 + u*(y2-y1)
		
	elif u < 0:		
		x,y = x1,y1
		
	else:
		x,y = x2,y2
		
	dist = math.sqrt(math.pow(x-x3,2)+math.pow(y-y3,2))
	
	return dist

	
class Line(object):
	
	def __init__(self, a, b):
		"""	
		Takes 2 vectors - the start and end points of the line
		"""
		self.a = a
		self.b = b
	
	def dist_to_point(self, point):
		"""	
		Find the given point's distance from this line segment. point should be
		a Vector2d instance. Returns the distance between the point and the line
		segment.
		"""
		return dist_to_line_seg((self.a.to_tuple(),self.b.to_tuple()), point.to_tuple())

	def __repr__(self):
		return "Line(%s,%s)" % (repr(self.a),repr(self.b))

	def __eq__(self, other):
		if type(self) != type(other): return False
		return self.a == other.a and self.b == other.b

	def __ne__(self, other):
		if type(self) != type(other): return True
		return self.a != other.a or self.b != other.b

class Polygon(object):
	"""	
	A 2-dimensional shape
	"""

	def __init__(self, points):
		"""	
		points is a list of vectors representing the vertices of the shape
		"""
		self.points = points

	def get_points(self):
		return self.points

	def get_lines(self):
		lines = []
		for i in range(len(self.points)-1):
			a = self.points[i]
			b = self.points[i+1]
			lines.append(Line(a,b))
		a = self.points[-1]
		b = self.points[0]
		lines.append(Line(a,b))
		return lines

	def __repr__(self):
		return "Polygon(%s)" % repr(self.get_points())

	def __eq__(self, other):
		if type(self) != type(other): return False
		return self.points == other.points

	def __ne__(self, other):
		if type(self) != type(other): return True
		return self.points != other.points


class Rectangle(Polygon):
	"""	
	A 2-dimensional, axis-aligned shape with 2 pairs of parallel sides. 
	"""

	def __init__(self, a, b):
		"""	
		Takes 2 vectors - opposite corners of the rectangle	
		"""
		self.a = a
		self.b = b
		self.left = min(self.a[0],self.b[0])
		self.right = max(self.a[0],self.b[0])
		self.top = min(self.a[1],self.b[1])
		self.bottom = max(self.a[1],self.b[1])	
		self.points = (
			Vector2d(self.left, self.top),
			Vector2d(self.right, self.top),
			Vector2d(self.right, self.bottom),
			Vector2d(self.left, self.bottom)
		)
	
	def get_width(self):
		return self.right - self.left

	def get_height(self):
		return self.bottom - self.top

	def point_inside(self, point):
		return( point[0] >= self.left and point[0] < self.right
			and point[1] >= self.top and point[1] < self.bottom )

	def intersects(self, rect):
		"""	
		Return True if this Rectangle overlaps the given Rectangle rect.
		"""
		return ( rect.right >= self.left and rect.left < self.right
			and rect.bottom >= self.top and rect.top < self.bottom )
			

	def intersection(self, rect):
		"""	
		Returns a new Rectangle representing the area where this Rectangle
		and rect overlap, or None if they do not overlap
		"""
		if not self.intersects(rect):
			return None
		else:
			in_left = max(self.left, rect.left)
			in_right = min(self.right, rect.right)
			in_top = max(self.top, rect.top)
			in_bottom = min(self.bottom, rect.bottom)
			return Rectangle(
				Vector2d(in_left,in_top),
				Vector2d(in_right,in_bottom)
			)
			

def lead_angle(target_disp,target_speed,target_angle,bullet_speed):
	"""	
	Given the displacement, speed and direction of a moving target, and the speed
	of a projectile, returns the angle at which to fire in order to intercept the
	target. If no such angle exists (for example if the projectile is slower than
	the target), then None is returned.
	"""
	"""	
	                               One can imagine the gun, target and point of 
  target                           collision at some time t forming a triangle
  --o-.-.-.---  St     collision   of which one side has length St*t where St is
	  .    /' ' ' ' . . . o        the target speed, and another has length Sb*t
	    . /z            . .        where Sb is the bullet speed. We can eliminate
	      .           .  .         t by scaling all sides of the triangle equally
	        .      A.    .         leaving one side St and another Sb. This 
	          .   .     .  Sb      triangle can be split into 2 right-angled
	            .   a__ .          triangles which share line A. Angle z can then
	              . /  .           be calculated and length A found 
	                .  .           (A = sin(z)/St), and from this angle a can be
	             -----o-----       found (a = arcsin(A/Sb) leading to the
	                 gun	       calculation of the firing angle.                    
	"""	
	# Check for situations with no solution
	if target_speed > bullet_speed:
		return None
	if target_disp[0]==0 and target_disp[1]==0:
		return None
	
	# Find angle to target
	ang_to_targ = math.atan2(target_disp[1],target_disp[0])
	
	# Calculate angle
	return math.asin(target_speed/bullet_speed*math.sin(
			ang_to_targ-target_angle-math.pi
		)) + ang_to_targ


def weighted_roulette(item_dict, normalised=False, rand=None):
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
	if rand == None:
		val = random.random()
	else:
		val = rand.random()
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
			self.assertEqual(Angle(0), Angle(0))
			self.assertEqual(Angle(10),Angle(10))
			self.assertNotEqual(Angle(0),Angle(10))

			self.assertEqual(Angle(math.pi/2) + Angle(math.pi), Angle(-math.pi/2))
			self.assertEqual(Angle(-math.pi/2) - Angle(math.pi), Angle(math.pi/2))
			self.assertAlmostEqual(Angle(math.pi/2).to_deg(), 90, 4) 

		def testVector2dMath(self):
			self.assertEqual(Vector2d(0,0), Vector2d(0,0))
			self.assertNotEqual(Vector2d(0,0), Vector2d(0,1))

			self.assertEqual(Vector2d(1,2) + Vector2d(2,3), Vector2d(3,5))
			self.assertEqual(Vector2d(1,2) - Vector2d(2,3), Vector2d(-1,-1))
			self.assertEqual(Vector2d(1,2) * 5, Vector2d(5,10))
			self.assertAlmostEqual(Vector2d(dir=math.pi/2,mag=2).i, Vector2d(0,2).i, 4)
			self.assertAlmostEqual(Vector2d(dir=math.pi/2,mag=2).j, Vector2d(0,2).j, 4)
			self.assertAlmostEqual(Vector2d(3,4).get_mag(), 5, 4)
			self.assertAlmostEqual(Vector2d(3,3).get_dir().val, Angle(math.pi/4).val, 4)
			self.assertAlmostEqual(Vector2d(3,4).unit().get_mag(), 1.0, 4)

		def testStandardDeviation(self):
			self.assertEquals(8.0,mean([2,6,4,20]))
			self.assertEquals(0.0,mean([]))						
			self.assertAlmostEquals(7.071,standard_deviation([2,6,4,20]),3)
			self.assertEquals(0.0,standard_deviation([]))
			self.assertAlmostEquals(0.141,deviation([2,6,4,20],9),3)
			self.assertEquals(0.0,deviation([],5))

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

		def testLeadAngle(self):
			ang = lead_angle((math.sqrt(2),math.sqrt(2)),math.sqrt(2),math.pi,math.sqrt(2))
			self.assertAlmostEquals(math.pi/2.0,ang,2)
			self.assertEquals(None,lead_angle((0.0,0.0),1.0,0.0,1.0))
			self.assertEquals(None,lead_angle((1.0,1.0),1.0,0.0,0.9))

		
		def testLine(self):
			line1 = Line(Vector2d(0.0,0.0),Vector2d(1.0,1.0))
			line2 = Line(Vector2d(0.0,0.0),Vector2d(1.0,1.0))
			line3 = Line(Vector2d(0.0,0.0),Vector2d(1.0,0.0))
			self.assertEquals(line1, line2)
			self.assertNotEquals(line2, line3)
			self.assertNotEquals(line3, line1)
		
		def testPolygon(self):
			p = Polygon([Vector2d(0.0,0.0), Vector2d(1.0,0.0), Vector2d(1.0,1.0)])
			lines = [
				Line(Vector2d(0.0,0.0),Vector2d(1.0,0.0)),
				Line(Vector2d(1.0,0.0),Vector2d(1.0,1.0)),
				Line(Vector2d(1.0,1.0),Vector2d(0.0,0.0))
			]
			self.assertEquals(lines, p.get_lines())

		def testRectangle(self):
			r1 = Rectangle(Vector2d(0.0,0.0), Vector2d(5.0,10.0))
			r2 = Rectangle(Vector2d(0.0,0.0), Vector2d(5.0,10.0))
			r3 = Rectangle(Vector2d(-2.0,-3.0),Vector2d(5.0,5.0))

			self.assertEqual(r1, r2)
			self.assertNotEqual(r2, r3)
			self.assertNotEqual(r3, r1)

			noisec = [
				Rectangle(Vector2d(-4.0,-4.0),Vector2d(-2.0,-2.0)),
				Rectangle(Vector2d(2.0,-4.0),Vector2d(3.0,-2.0)),
				Rectangle(Vector2d(7.0,-4.0),Vector2d(9.0,-2.0)),
				Rectangle(Vector2d(-4.0,2.0),Vector2d(-2.0,8.0)),
				Rectangle(Vector2d(7.0,2.0),Vector2d(9.0,8.0)),
				Rectangle(Vector2d(-4.0,12.0),Vector2d(-2.0,14.0)),
				Rectangle(Vector2d(2.0,12.0),Vector2d(3.0,14.0)),
				Rectangle(Vector2d(7.0,12.0),Vector2d(9.0,14.0)),	

				Rectangle(Vector2d(-2.0,-4.0),Vector2d(7.0,-2.0)),
				Rectangle(Vector2d(-2.0,12.0),Vector2d(7.0,14.0)),
				Rectangle(Vector2d(-4.0,-2.0),Vector2d(-2.0,12.0)),
				Rectangle(Vector2d(7.0,-2.0),Vector2d(9.0,12.0))
			]
			yesisec = [
				Rectangle(Vector2d(-2.0,-2.0),Vector2d(2.0,2.0)),
				Rectangle(Vector2d(2.0,-2.0),Vector2d(3.0,2.0)),
				Rectangle(Vector2d(3.0,-2.0),Vector2d(7.0,2.0)),
				Rectangle(Vector2d(-2.0,2.0),Vector2d(2.0,8.0)),
				Rectangle(Vector2d(2.0,2.0),Vector2d(3.0,8.0)),
				Rectangle(Vector2d(3.0,2.0),Vector2d(7.0,8.0)),
				Rectangle(Vector2d(-2.0,8.0),Vector2d(2.0,12.0)),
				Rectangle(Vector2d(2.0,8.0),Vector2d(3.0,12.0)),
				Rectangle(Vector2d(3.0,8.0),Vector2d(7.0,12.0)),

				Rectangle(Vector2d(-2.0,-2.0),Vector2d(7.0,2.0)),
				Rectangle(Vector2d(-2.0,2.0),Vector2d(7.0,8.0)),
				Rectangle(Vector2d(-2.0,8.0),Vector2d(7.0,12.0)),
				Rectangle(Vector2d(-2.0,-2.0),Vector2d(2.0,12.0)),
				Rectangle(Vector2d(2.0,-2.0),Vector2d(3.0,12.0)),
				Rectangle(Vector2d(3.0,-2.0),Vector2d(7.0,12.0))
			]
	
			for r in yesisec:
				self.assertTrue(r1.intersects(r))
			for r in noisec:
				self.assertFalse(r1.intersects(r))

			isect = Rectangle(Vector2d(0.0,0.0),Vector2d(5.0,5.0))
			self.assertEqual(isect, r1.intersection(r3))
			self.assertEqual(r1, r1.intersection(r2))

	unittest.main()
    
    
    
    
    
    
