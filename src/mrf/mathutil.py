"""	
Copyright (c) 2010 Mark Frimston

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
	Rotation    - 3d rotation class
	Vector2d	- 2D vector class
	Vector3d    - 3D vector class
	Matrix      - n x m Matrix class
	Line		- 2D line
	Polygon		- 2D shape
	Rectangle	- 2D rectangle
"""

"""	
	TODO: test cuboid
	TODO: test 2d line intersection
	TODO: test 2d line clipping
"""

import math
import unittest
import random
from mrf.structs import isindexable, isiterable

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

	def __hash__(self):
		return hash("Angle") ^ hash(self.val)

	def __neg__(self):
		return Angle(-self.val)
		
	def matrix(self):
		"""	
		Returns a 2x2 rotation matrix suitable for rotating pairs of x,y coordinates.
		Uses a right-handed coordinate system so a positive rotation will be clockwise
		where the x axis points right and the y axis points down.
		"""
		return Matrix((
			( math.cos(self.val), -math.sin(self.val) ),
			( math.sin(self.val),  math.cos(self.val) )
		))

class Rotation(object):
	"""	
	A 3-dimensional orientation consisting of roll, pitch and yaw values.
	"""
	
	def __init__(self, roll, pitch, yaw):
		if hasattr(roll,"to_rad"):
			roll = roll.to_rad()
		self.roll = Angle(roll)
		if hasattr(pitch,"to_rad"):
			pitch = pitch.to_rad()
		self.pitch = Angle(pitch)
		if hasattr(yaw,"to_rad"):
			yaw = yaw.to_rad()
		self.yaw = Angle(yaw)
		
	def get_roll(self):
		return self.roll

	def get_pitch(self):
		return self.pitch

	def get_yaw(self):
		return self.yaw

	def to_tuple(self):
		return (self.roll.val,self.pitch.val,self.yaw.val)

	def __eq__(self,r):
		if not hasattr(r,"to_tuple"):
			return False
		return self.to_tuple() == r.to_tuple()

	def __ne__(self,r):
		if not hasattr(r,"to_tuple"):
			return True
		return self.to_tuple() != r.to_tuple()

	def __str__(self):
		return str(self.to_tuple())

	def __repr__(self):
		return "Rotation(%f,%f,%f)" % self.to_tuple()
	
	def __add__(self,r):
		if not hasattr(r,"to_tuple"):
			raise TypeError("Cannot add %s" % str(r))
		r_roll,r_pitch,r_yaw = r.to_tuple()	
		return Rotation(self.roll+r_roll, self.pitch+r_pitch, self.yaw+r_yaw)

	def __sub__(self,r):
		if not hasattr(r,"to_tuple"):
			raise TypeError("Cannot subtract %s" % str(r))
		r_roll,r_pitch,r_yaw = r.to_tuple()
		return Rotation(self.roll-r_roll, self.pitch-r_pitch, self.yaw-r_yaw)
		
	def __hash__(self):
		return hash("Rotation") ^ hash(self.to_tuple())
		
	def matrix(self):
		"""	
		Returns a 3x3 rotation matrix suitable for rotating sets of x,y,z coordinates.
		Uses a right-handed coordinate system where roll is about the x axis, pitch about
		the y and yaw about the z, so a positive rotation will be clockwise
		when looking in the direction of the axis. Rotation uses a z-y-x convention, 
		applying yaw, then pitch, then roll.
		"""
		# apply yaw, then pitch, then roll
		return Matrix((
			(	1,	0,							0							),
			(	0,	math.cos(self.roll.val),	-math.sin(self.roll.val)	),
			(	0,	math.sin(self.roll.val),	math.cos(self.roll.val)		)
		))* Matrix((
			(	math.cos(self.pitch.val),	0,	math.sin(self.pitch.val)	),
			(	0,							1,	0 							),
			(	-math.sin(self.pitch.val),	0,	math.cos(self.pitch.val)	)
		)) * Matrix((
			(	math.cos(self.yaw.val),	-math.sin(self.yaw.val),	0	),
			(	math.sin(self.yaw.val),	math.cos(self.yaw.val),		0	),
			(	0,						0,							1	)
		))

class Vector2d(object):

	def __init__(self, i=0, j=0, dir=0, mag=0):
		if dir!=0 or mag!=0:
			if hasattr(dir, "to_rad"):
				dir = dir.to_rad()
			self.i = math.cos(dir) * mag
			self.j = math.sin(dir) * mag
		elif isiterable(i):
			self.i,self.j = i
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
		return str(self.to_tuple())
	
	def __eq__(self,w):
		if type(w) != type(self): 
			return False
		return self.i == w.i and self.j == w.j
	
	def __ne__(self,w):
		if type(w) != type(self):
			return False
		return self.i != w.i or self.j != w.j
	
	def __repr__(self):
		return "Vector2d(%f,%f)" % self.to_tuple()
	
	def get_dir(self):
		return Angle(math.atan2(self.j,self.i))
		
	def get_mag(self):
		return math.sqrt(math.pow(self.i,2)+math.pow(self.j,2))
	
	def unit(self):
		if self.get_mag() != 0:
			return self / self.get_mag()
		else:
			return Vector2d(0,0)
	
	def to_tuple(self):
		return (self.i, self.j)
	
	def to_matrix(self):
		return Matrix((self.to_tuple()))
	
	def __getitem__(self, index):
		if index == 0:
			return self.i
		elif index == 1:
			return self.j
		else:
			raise IndexError("Index must be 0 or 1")

	def __hash__(self):
		return hash("Vector2d") ^ hash(self.i) ^ hash(self.j)
	
	def __len__(self):
		return 2
	
	def __neg__(self):
		return Vector2d(-self.i,-self.j)
	
	def rotate(self, angle):
		"""	
		Rotate the vector by the given Angle or radian value. Uses 
		a right-hand coordinate system so positive angle will rotate
		clockwise where the x axis points right and the y axis points
		down.
		"""
		if not isinstance(angle, Angle):
			angle = Angle(angle)
		return angle.matrix() * self
		
	def rotate_about(self, angle, point):
		"""	
		Rotate the vector by the given Angle or radian value, about
		the given Vector2d or (x,y) point. Uses a right-hand coordinate
		system so a positive angle will rotate clockwise where the x
		axis points right and the y axis points down.
		"""
		if not isinstance(point, Vector2d):
			point = Vector2d(*point)
		return (self - point).rotate(angle) + point

class Vector3d(object):
	
	def __init__(self, i=0, j=0, k=0, dir=0, mag=0):
		"""	
		Can construct from i,j,k parameters, dir and mag parameters
		or with a single (i,j,k) tuple.	
		"""
		if dir!=0 or mag!=0:
			if hasattr(dir, "to_tuple"):
				dir = dir.to_tuple()
			roll = dir[0]
			pitch = dir[1]
			yaw = dir[2]
			fwd = math.cos(pitch) * mag
			up = math.sin(pitch) * mag
			self.i = math.cos(yaw) * fwd
			self.j = math.sin(yaw) * fwd
			self.k = up
		elif isiterable(i):
			self.i,self.j,self.k = i
		else:
			self.i = i
			self.j = j
			self.k = k

	def __add__(self, w):
		# addition of another Vector3d
		return Vector3d(self.i + w[0], self.j + w[1], self.k + w[2])

	def __sub__(self, w):
		# subtraction of another Vector3d
		return Vector3d(self.i - w[0], self.j - w[1], self.k - w[2])
	
	def __mul__(self, w):
		# multiplication with scalar value
		return Vector3d(self.i * w, self.j * w, self.k * w)
	
	def __div__(self, w):
		# division by scalar value
		return Vector3d(self.i / w, self.j / w, self.k / w)
	def __truediv__(self, w):
		# division by scalar value
		return Vector3d(self.i / w, self.j / w, self.k / w)
	
	def __str__(self):
		return str(self.to_tuple())
	
	def __eq__(self,w):
		if type(w) != type(self): 
			return False
		return self.i == w.i and self.j == w.j and self.k == w.k
	
	def __ne__(self,w):
		if type(w) != type(self):
			return False
		return self.i != w.i or self.j != w.j or self.i != w.k
	
	def __repr__(self):
		return "Vector3d(%f,%f,%f)" % self.to_tuple()
	
	def get_dir(self):
		yaw = math.atan2(self.j,self.i)
		fwd = math.sqrt(math.pow(self.i,2)+math.pow(self.j,2))
		pitch = math.atan2(self.k,fwd)
		return Rotation(0.0, pitch, yaw)
		
	def get_mag(self):
		return math.sqrt(math.pow(self.i,2)+math.pow(self.j,2)+math.pow(self.k,2))
	
	def dot(self, w):
		return self.i*w.i + self.j*w.j + self.k*w.k

	def cross(self, w):
		return Vector3d(self.j*w.k-self.k*w.j, self.k*w.i-self.i*w.k, self.i*w.j-self.j*w.i)

	def unit(self):
		if self.get_mag() != 0:
			return self / self.get_mag()
		else:
			return Vector3d(0,0,0)
	
	def to_tuple(self):
		return (self.i, self.j, self.k)

	def to_matrix(self):
		return Matrix((self.to_tuple()))
	
	def __getitem__(self, index):
		if index == 0:
			return self.i
		elif index == 1:
			return self.j
		elif index == 2:
			return self.k
		else:
			raise IndexError("Index must be 0, 1 or 2")
	
	def __hash__(self):
		return hash("Vector3d") ^ hash(self.i) ^ hash(self.j) ^ hash(self.k)

	def __len__(self):
		return 3
		
	def __neg__(self):
		return Vector3d(-self.i, -self.j, -self.k)
		
	def rotate(self, rotation):
		"""	
		Rotate the vector by the given Rotation or (roll,pitch,yaw) value.
		Uses a right-handed coordinate system so a positive angle will 
		result in a clockwise rotation when looking in the axis direction.
		"""
		if not isinstance(rotation,Rotation):
			rotation = Rotation(*rotation)
		return rotation.matrix() * self
		
	def rotate_about(self, rotation, point):
		"""	
		Rotate the vector by the given Rotation or (roll,pitch,yaw) value,
		about the given Vector3d or (x,y,z) point. Uses a right-handed
		coordinate system so a positive angle will result in a clockwise
		rotation when looking in the axis direction.	
		"""
		if not isinstance(point,Vector3d):
			point = Vector3d(*point)
		return (self - point).rotate(rotation) + point

class Matrix(object):

	@staticmethod
	def identity(size):
		return Matrix._make_new(lambda i,j: 1 if i==j else 0, size, size)

	def __init__(self,data):
		"""	
		Can construct from singly or doubly nested iterable. Each inner item
		forms a row in the matrix. E.g:
		
		(1,2,3) => | 1 |
		           | 2 |
		           | 3 |
		          
		(
			(1,2,3),  =>  | 1 2 3 |
			(4,5,6)       | 4 5 6 |
		)          
		"""
		self.data = tuple([tuple(x) if isiterable(x) else (x,) for x in data])
		self.rows = len(self.data)
		self.cols = len(self.data[0]) if len(self.data)>0 else 0
		
	def get(self, ref):
		return self.data[ref[0]][ref[1]]
		
	def __getitem__(self, index):
		return self.data[index]
		
	def __str__(self):
		col_widths = []
		for i in range(self.cols):
			widest = 0
			for j in range(self.rows):
				l = len(str(self.data[j][i]))
				if l > widest:
					widest = l
			col_widths.append(widest)
		s = "\n"
		for r in self.data:
			s += "|"
			for i in range(len(r)):
				s += str(r[i]).rjust(col_widths[i]+1)
			s += " |\n"
		return s
				
	def __repr__(self):
		return "Matrix(%s)" % str(self.data)
		
	def __eq__(self,oth):
		if not isinstance(oth, Matrix):
			return False
		return self.data == oth.data
		
	def __ne__(self,oth):
		if not isinstance(oth, Matrix):
			return True
		return self.data != oth.data
		
	@staticmethod
	def _make_new(callback, rows, cols):
		new_data = []
		for i in range(rows):
			new_row = []
			for j in range(cols):
				new_row.append(callback(i,j))
			new_data.append(new_row)
		return Matrix(new_data)
		
	def _unnest(self):
		return [x if len(x)!=1 else x[0] for x in self.data]
		
	def _add(self, oth):
		if self.rows != oth.rows or self.cols != oth.cols:
			raise TypeError("Matrices must be the same size")
		return Matrix._make_new(lambda i,j: self.data[i][j] + oth.data[i][j], 
			self.rows, self.cols)
		
	def __add__(self, oth):
		"""	
		Can add another matrix of the same size or any similar nested iterable.
		The result is a matrix.
		"""
		if not isinstance(oth, Matrix):
			oth = Matrix(oth)
		return self._add(oth)		
			
	def __radd__(self, oth):
		"""	
		Can add the matrix to another matrix or any similar nested iterable
		which can be constructed like a list. The result is of the same type
		as the operand
		"""
		oth_m = oth
		if not isinstance(oth_m, Matrix):
			oth_m = Matrix(oth_m)
		res_m = oth_m._add(self)
		if isinstance(oth,Matrix):
			return res_m
		else:
			return type(oth)(res_m._unnest())
			
	def _sub(self, oth):
		if self.rows != oth.rows or self.cols != oth.cols:
			raise TypeError("Matrices must be the same size")
		return Matrix._make_new(lambda i,j: self.data[i][j] - oth.data[i][j], 
			self.rows, self.cols)
			
	def __sub__(self, oth):
		"""	
		Can subtract another matrix of the same size or any similar nested iterable.
		The result is a matrix.
		"""
		if not isinstance(oth, Matrix):
			oth = Matrix(oth)
		return self._sub(oth)
		
	def __rsub__(self,oth):
		"""	
		Subtract the matrix from another matrix or any similar nested iterable
		which can be constructed like a list. The result is of the same type as
		the operand
		"""
		oth_m = oth
		if not isinstance(oth_m,Matrix):
			oth_m = Matrix(oth_m)
		res_m = oth_m._sub(self)
		if isinstance(oth,Matrix):
			return res_m
		else:
			return type(oth)(res_m._unnest())
		
	def _mat_mul(self,oth):
		if self.cols != oth.rows:
			raise TypeError("Cols in left matrix must equal rows in right matrix")
		return Matrix._make_new(lambda i,j: sum([
				self.data[i][x] * oth.data[x][j] for x in range(self.cols) ]), 
				self.rows, oth.cols)						
		
	def __mul__(self, oth):
		"""	
		Can apply this matrix to another matrix or any similar nested iterable 
		(where cols in lhs equals rows in rhs), resulting in the same type as 
		the operand, or can apply to scalar, resulting in a matrix.
		"""
		if isinstance(oth, Matrix) or isiterable(oth):
			# matrix
			oth_m = oth
			if not isinstance(oth_m, Matrix):
				oth_m = Matrix(oth_m)			
			res_m = self._mat_mul(oth_m)
			if isinstance(oth, Matrix):
				return res_m
			else:
				return type(oth)(res_m._unnest())
		else:
			# scalar
			return Matrix._make_new(lambda i,j: self.data[i][j] * oth, self.rows, self.cols)
		
	def __rmul__(self,oth):
		"""	
		Can apply another matrix or similar nested iterable (where cols in lhs equals
		rows in rhs), or a scalar value, to this matrix. The result is a matrix.
		"""
		if isinstance(oth,Matrix) or isiterable(oth):
			# matrix
			oth_m = oth
			if not isinstance(oth_m,Matrix):
				oth_m = Matrix(oth_m)
			return oth_m._mat_mul(self)
		else:
			# scalar
			return Matrix._make_new(lambda i,j: oth * self.data[i][j], self.rows, self.cols)
		
	def __div__(self, oth):
		"""	
		Can divide by a scalar
		"""
		return Matrix._make_new(lambda i,j: self.data[i][j] / oth, self.rows, self.cols)
			
	def __truediv__(self, oth):
		return Matrix._make_new(lambda i,j: self.data[i][j] / oth, self.rows, self.cols)
		
	def __rdiv__(self, oth):
		return Matrix._make_new(lambda i,j: self.data[i][j] / oth, self.rows, self.cols)
		
	def __rtruediv__(self, oth):
		return Matrix._make_new(lambda i,j: self.data[i][j] / oth, self.rows, self.cols)
		
	def transpose(self):
		return Matrix._make_new(lambda i,j: self.data[j][i], self.cols, self.rows)

	def __hash__(self):
		return hash("Matrix") ^ hash(self.data)
	
def sigmoid(x):
	"""	
	S-curve function. sigmoid(0) is almost 0 and sigmoid(1) is almost 1, with
	an S-shaped curve in between.
	"""
	return 1.0/(1.0+math.exp(-(x-0.5)*12.0))
	
def smooth_step(x):
	return x*x * (3 - 2*x)
	
def smooth_steps(steps):
	for i in range(int(steps)):
		x = float(i)/steps
		yield smooth_step(x)
	
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
	
	
def dist_to_line2d(line, point):
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
	
def dist_to_line2d_seg(line, point):
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

	
class Line2d(object):
	
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
		return dist_to_line2d_seg((self.a.to_tuple(),self.b.to_tuple()), point.to_tuple())

	def __repr__(self):
		return "Line2d(%s,%s)" % (repr(self.a),repr(self.b))

	def __eq__(self, other):
		if type(self) != type(other): return False
		return self.a == other.a and self.b == other.b

	def __ne__(self, other):
		if type(self) != type(other): return True
		return self.a != other.a or self.b != other.b

	def __hash__(self):
		return hash("Line2d") ^ hash(self.a) ^ hash(self.b)

	def intersects(self, line):
		"""	
		Returns true if the line intersects the given Line2d
		"""
		return self.intersection(lint) != None
		
	def intersection(self, line):
		"""	
		Returns the intersection point of this line and the given Line2d as
		a Vector2d if the segments intersect, or None otherwise. Will return
		None if the lines are coincident.
		"""
		denom = (line.b[1]-line.a[1])*(self.b[0]-self.a[0]) - (line.b[0]-line.a[0])*(self.b[1]-self.a[1])
		# denominator is 0 if lines are parallel
		if denom == 0:
			return None
		
		num_a = (line.b[0]-line.a[0])*(self.a[1]-line.a[1]) - (line.b[1]-line.a[1])*(self.a[0]-line.a[0])
		num_b = (self.b[0]-self.a[0])*(self.a[1]-line.a[1]) - (self.b[1]-self.a[1])*(self.a[0]-line.a[0])
		# if both numerators are 0 then lines are coincident
		if num_a==0 and num_b==0:
			return None
			
		u_a = num_a/denom
		u_b = num_b/denom
			
		if 0 <= u_a <= 1 and 0 <= u_b <= 1:
			return self.a + uA*(self.b-self.a)
		else:
			return None
		

	def clip(self, rect):
		"""	
		Returns a new Line2d which has been clipped to the given Rectangle,
		or None if no line segment is within the rectangle.
		"""
		a_in = rect.point_inside(self.a)
		b_in = rect.point_inside(self.b)
		
		# if point a outside and point b inside
		if not a_in and b_in:
			# test intersection with each side
			new_a = self.a
			for side in rect.lines:
				isect = self.intersection(side)
				if isect != None:
					new_a = isect
					break
			return Line2d(new_a,self.b)
		
		# if point a inside and point b outside
		elif a_in and not b_in:
			# test intersection with each side
			new_b = self.b
			for side in rect.lines:
				isect = self.intersection(side)
				if isect != None:
					new_b = isect
					break
			return Line2d(self.a,new_b)
		
		# both points inside
		elif a_in and b_in:
			return self
			
		# both points outside
		else:
			return None
		

class Line3d(object):
	"""	
	A line between two 3-dimensional points.
	"""
	
	def __init__(self, a, b):
		"""	
		Takes two 3d  vectors - the start and end points of the line
		"""
		self.a = a
		self.b = b

	def __repr__(self):
		return "Line3d(%s,%s)" % (repr(self.a),repr(self.b),repr(self.c))

	def __eq__(self, other):
		if type(self) != type(other): return False
		return self.a == other.a and self.b == other.b

	def __ne__(self, other):
		if type(self) != type(other): return True
		return self.a != other.a or self.b != other.b

	def __hash__(self):
		return hash("Line3d") ^ hash(self.a) ^ hash(self.b)

class Polygon2d(object):
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
			lines.append(Line2d(a,b))
		a = self.points[-1]
		b = self.points[0]
		lines.append(Line2d(a,b))
		return lines

	def __repr__(self):
		return "Polygon2d(%s)" % repr(self.get_points())

	def __eq__(self, other):
		if type(self) != type(other): return False
		return self.points == other.points

	def __ne__(self, other):
		if type(self) != type(other): return True
		return self.points != other.points

	def __hash__(self):
		return hash("Polygon2d") ^ hash(self.points)


class Rectangle(Polygon2d):
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

class Polygon3d(object):
	"""	
	A 3-dimensional shape
	"""

	def __init__(self, lines):
		"""	
		lines is a list of 3d lines representing the edges of the shape.
		"""
		self.lines = lines
		self.points = set()
		for l in lines:
			if not l.a in self.points:
				self.points.add(l.a)
			if not l.b in self.points:
				self.points.add(l.b)

	def get_points(self):
		return self.points

	def get_lines(self):
		return self.lines

	def __repr__(self):
		return "Polygon3d(%s)" % repr(self.get_lines())

	def __eq__(self, other):
		if type(self) != type(other): return False
		return self.lines == other.lines

	def __ne__(self, other):
		if type(self) != type(other): return True
		return self.lines != other.lines

	def __hash__(self):
		return hash("Polygon3d") ^ hash(self.lines)

class Cuboid(Polygon3d):
	"""	
	A 3-dimensional, axis-aligned shape with 3 pairs of parallel sides. 
	"""

	def __init__(self, a, b):
		"""	
		Takes 2 vectors - opposite corners of the cuboid	
		"""
		# the cuboid faces down the x axis so the front is the greater x,
		# the left is the lesser y and the top is the lesser z.
		self.a = a
		self.b = b
		self.front = max(self.a[0],self.b[0])
		self.back = min(self.a[0],self.b[0])
		self.left = min(self.a[1],self.b[1])
		self.right = max(self.a[1],self.b[1])
		self.top = min(self.a[2],self.b[2])
		self.bottom = max(self.a[2],self.b[2])	
		# call polygon constructor with lines
		Polygon3d.__init__(self, (
			Line3d(Vector3d(self.front,self.left,self.top),Vector3d(self.front,self.right,self.top)),
			Line3d(Vector3d(self.front,self.right,self.top),Vector3d(self.back,self.right,self.top)),
			Line3d(Vector3d(self.back,self.right,self.top),Vector3d(self.back,self.left,self.top)),
			Line3d(Vector3d(self.back,self.left,self.top),Vector3d(self.front,self.left,self.top)),

			Line3d(Vector3d(self.front,self.left,self.bottom),Vector3d(self.front,self.right,self.bottom)),
			Line3d(Vector3d(self.front,self.right,self.bottom),Vector3d(self.back,self.right,self.bottom)),
			Line3d(Vector3d(self.back,self.right,self.bottom),Vector3d(self.back,self.left,self.bottom)),
			Line3d(Vector3d(self.back,self.left,self.bottom),Vector3d(self.front,self.left,self.bottom)),

			Line3d(Vector3d(self.front,self.left,self.top),Vector3d(self.front,self.left,self.bottom)),
			Line3d(Vector3d(self.front,self.right,self.top),Vector3d(self.front,self.right,self.bottom)),
			Line3d(Vector3d(self.back,self.right,self.top),Vector3d(self.back,self.right,self.bottom)),
			Line3d(Vector3d(self.back,self.left,self.top),Vector3d(self.back,self.left,self.bottom)),
		))
	
	def get_depth(self):
		# returns the x axis size
		return self.front - self.back

	def get_width(self):
		# returns the y axis size
		return self.right - self.left

	def get_height(self):
		# returns the z axis size
		return self.bottom - self.top

	def point_inside(self, point):
		# returns true if the given vector point is inside the shape
		return( point[0] >= self.back and point[0] < self.front
			and point[1] >= self.left and point[1] < self.right
			and point[2] >= self.top and point[2] < self.bottom )

	def intersects(self, cuboid):
		"""	
		Return True if this Cuboid overlaps the given Cuboid.
		"""
		return ( cuboid.front >= self.back and cuboid.back < self.front
			and cuboid.right >= self.left and cuboid.left < self.right
			and cuboid.bottom >= self.top and cuboid.top < self.bottom )
			

	def intersection(self, cuboid):
		"""	
		Returns a new Cuboid representing the area where this Cuboid
		and cuboid overlap, or None if they do not overlap
		"""
		if not self.intersects(cuboid):
			return None
		else:
			in_back = max(self.back, cuboid.back)
			in_front = min(self.front, cuboid.front)
			in_left = max(self.left, cuboid.left)
			in_right = min(self.right, cuboid.right)
			in_top = max(self.top, cuboid.top)
			in_bottom = min(self.bottom, cuboid.bottom)
			return Cuboid(
				Vector3d(in_back,in_left,in_top),
				Vector3d(in_front,in_right,in_bottom)
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
		# TODO target being faster than bullet does not necessarily mean no collision
		# - e.g. head on collision
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

			self.assertTrue(Angle(10) in set([Angle(10)]))
			self.assertFalse(Angle(10) in set([Angle(11)]))
			
			self.assertAlmostEquals((Angle(math.pi/2).matrix() * (4,8))[0], (-8,4)[0], 4)
			self.assertAlmostEquals((Angle(math.pi/2).matrix() * (4,8))[1], (-8,4)[1], 4)
		
		def testRotations(self):
			self.assertEqual(Rotation(0.5,1.5,2.5),Rotation(0.5,1.5,2.5))
			self.assertEqual(Rotation(0.5,1.5,2.5),Rotation(2*math.pi+0.5, 2*math.pi+1.5, 2*math.pi+2.5))
			self.assertNotEqual(Rotation(0.5,1.5,2.5),Rotation(0.5,1.5,2.6))
			self.assertNotEqual(Rotation(0.5,1.5,2.5),0.0)

			self.assertEqual(Rotation(0.5,1.5,2.5) + Rotation(0.1,0.0,0.0), Rotation(0.6,1.5,2.5))
			self.assertEqual(Rotation(0.5,1.5,2.5) + Rotation(0.0,4*math.pi,0.0), Rotation(0.5,1.5,2.5))
			self.assertEqual(Rotation(0.5,1.5,2.5) + Rotation(0.0,0.0,0.2), Rotation(0.5,1.5,2.7))

			self.assertEqual(Rotation(0.5,1.5,2.5) - Rotation(0.1,0.0,0.0), Rotation(0.4,1.5,2.5))
			self.assertEqual(Rotation(0.5,1.5,2.5) - Rotation(0.0,4*math.pi,0.0), Rotation(0.5,1.5,2.5))
			self.assertEqual(Rotation(0.5,1.5,2.5) - Rotation(0.0,0.0,0.2), Rotation(0.5,1.5,2.3))

			self.assertTrue(Rotation(1,2,3) in set([Rotation(1,2,3)]))
			self.assertFalse(Rotation(1,2,3) in set([Rotation(2,3,4)]))
			
			self.assertAlmostEquals((Rotation(-math.pi/2,0,math.pi/2).matrix() * (8,0,-2))[0], (0,-2,-8)[0], 4)
			self.assertAlmostEquals((Rotation(-math.pi/2,0,math.pi/2).matrix() * (8,0,-2))[1], (0,-2,-8)[1], 4)
			self.assertAlmostEquals((Rotation(-math.pi/2,0,math.pi/2).matrix() * (8,0,-2))[2], (0,-2,-8)[2], 4)			
			

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

			a = Vector2d(2,0)
			b = Vector2d(2,2)
			self.assertAlmostEqual(a.dot(b), a.get_mag()*b.get_mag()*math.cos(math.pi/4), 4)

			self.assertEqual(Vector2d(1,2)[0], 1.0)
			self.assertEqual(Vector2d(1,2)[1], 2.0)

			self.assertAlmostEqual((Vector2d(1,2).rotate(math.pi/2))[0], Vector2d(-2,1)[0], 4)
			self.assertAlmostEqual((Vector2d(1,2).rotate(math.pi/2))[1], Vector2d(-2,1)[1], 4)

			self.assertAlmostEqual((Vector2d(1,2).rotate_about(math.pi/2,(2,3)))[0], Vector2d(3,2)[0], 4)
			self.assertAlmostEqual((Vector2d(1,2).rotate_about(math.pi/2,(2,3)))[1], Vector2d(3,2)[1], 4)

			self.assertTrue(Vector2d(1,2) in set([Vector2d(1,2)]))
			self.assertFalse(Vector2d(1,2) in set([Vector2d(2,3)]))
		
		def testVector3dMath(self):
			self.assertEqual(Vector3d(0,0,0), Vector3d(0,0,0))
			self.assertNotEqual(Vector3d(0,0,0), Vector3d(0,1,2))

			self.assertEqual(Vector3d(1,2,3) + Vector3d(2,3,4), Vector3d(3,5,7))
			self.assertEqual(Vector3d(1,2,3) - Vector3d(2,3,4), Vector3d(-1,-1,-1))
			self.assertEqual(Vector3d(1,2,3) * 5, Vector3d(5,10,15))

			self.assertAlmostEqual(Vector3d(dir=Rotation(0.5,math.pi/4,math.pi/2),mag=2).i, Vector3d(0,1.4142,1.4142).i, 4)
			self.assertAlmostEqual(Vector3d(dir=Rotation(0.5,math.pi/4,math.pi/2),mag=2).j, Vector3d(0,1.4142,1.4142).j, 4)
			self.assertAlmostEqual(Vector3d(dir=Rotation(0.5,math.pi/4,math.pi/2),mag=2).k, Vector3d(0,1.4142,1.4142).k, 4)

			self.assertAlmostEqual(Vector3d(0,4,3).get_mag(), 5, 4)

			self.assertAlmostEqual(Vector3d(0,4,4).get_dir().roll.val,  Rotation(0.0,math.pi/4,math.pi/2).roll.val,  4)	
			self.assertAlmostEqual(Vector3d(0,4,4).get_dir().pitch.val, Rotation(0.0,math.pi/4,math.pi/2).pitch.val, 4)	
			self.assertAlmostEqual(Vector3d(0,4,4).get_dir().yaw.val,   Rotation(0.0,math.pi/4,math.pi/2).yaw.val,   4)

			self.assertAlmostEqual(Vector3d(9,8,7).unit().get_mag(), 1.0, 4)

			self.assertAlmostEqual(Vector3d(1,2,3).dot(Vector3d(4,5,6)), 1*4+2*5+3*6 ,4)
			self.assertEqual(Vector3d(1,2,3).cross(Vector3d(4,5,6)), Vector3d(2*6-3*5,3*4-1*6,1*5-2*4))

			self.assertEqual(Vector3d(9,8,7)[0], 9.0)
			self.assertEqual(Vector3d(9,8,7)[1], 8.0)
			self.assertEqual(Vector3d(9,8,7)[2], 7.0)

			self.assertAlmostEqual((Vector3d(5,0,0).rotate((-math.pi/2,math.pi/2,math.pi/2)))[0],Vector3d(0,0,-5)[0], 4)
			self.assertAlmostEqual((Vector3d(5,0,0).rotate((-math.pi/2,math.pi/2,math.pi/2)))[1],Vector3d(0,0,-5)[1], 4)
			self.assertAlmostEqual((Vector3d(5,0,0).rotate((-math.pi/2,math.pi/2,math.pi/2)))[2],Vector3d(0,0,-5)[2], 4)

			self.assertAlmostEqual((Vector3d(5,0,0).rotate_about((-math.pi/2,0,0),(5,-5,0)))[0], Vector3d(5,-5,-5)[0], 4)
			self.assertAlmostEqual((Vector3d(5,0,0).rotate_about((-math.pi/2,0,0),(5,-5,0)))[1], Vector3d(5,-5,-5)[1], 4)
			self.assertAlmostEqual((Vector3d(5,0,0).rotate_about((-math.pi/2,0,0),(5,-5,0)))[2], Vector3d(5,-5,-5)[2], 4)

			self.assertTrue(Vector3d(1,2,3) in set([Vector3d(1,2,3)]))
			self.assertFalse(Vector3d(1,2,3) in set([Vector3d(2,3,4)]))

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

		
		def testLine2d(self):
			line1 = Line2d(Vector2d(0.0,0.0),Vector2d(1.0,1.0))
			line2 = Line2d(Vector2d(0.0,0.0),Vector2d(1.0,1.0))
			line3 = Line2d(Vector2d(0.0,0.0),Vector2d(1.0,0.0))
			self.assertEquals(line1, line2)
			self.assertNotEquals(line2, line3)
			self.assertNotEquals(line3, line1)

			self.assertTrue(Line2d(Vector2d(0,0),Vector2d(1,2)) in set([Line2d(Vector2d(0,0),Vector2d(1,2))]))
			self.assertFalse(Line2d(Vector2d(0,0),Vector2d(1,2)) in set([Line2d(Vector2d(0,0),Vector2d(2,3))]))
			
		def testLine3d(self):
			line1 = Line3d(Vector3d(0.0,0.0,0.0),Vector3d(1.0,1.0,1.0))
			line2 = Line3d(Vector3d(0.0,0.0,0.0),Vector3d(1.0,1.0,1.0))
			line3 = Line3d(Vector3d(0.0,0.0,0.0),Vector3d(1.0,0.0,1.0))
			self.assertEquals(line1, line2)
			self.assertNotEquals(line2, line3)
			self.assertNotEquals(line3, line1)

			self.assertTrue(Line3d(Vector3d(0,0,0),Vector3d(1,2,3)) in set([Line3d(Vector3d(0,0,0),Vector3d(1,2,3))]))
			self.assertFalse(Line3d(Vector3d(0,0,0),Vector3d(1,2,3)) in set([Line3d(Vector3d(0,0,0),Vector3d(2,3,4))]))
	
		def testPolygon2d(self):
			p = Polygon2d([Vector2d(0.0,0.0), Vector2d(1.0,0.0), Vector2d(1.0,1.0)])
			lines = [
				Line2d(Vector2d(0.0,0.0),Vector2d(1.0,0.0)),
				Line2d(Vector2d(1.0,0.0),Vector2d(1.0,1.0)),
				Line2d(Vector2d(1.0,1.0),Vector2d(0.0,0.0))
			]
			self.assertEquals(lines, p.get_lines())

			self.assertTrue(Polygon2d((Vector2d(0,0),Vector2d(1,2),Vector2d(2,3))) 
				in set([Polygon2d((Vector2d(0,0),Vector2d(1,2),Vector2d(2,3)))]))
			self.assertFalse(Polygon2d((Vector2d(0,0),Vector2d(1,2),Vector2d(2,3))) 
				in set([Polygon2d((Vector2d(0,0),Vector2d(1,2),Vector2d(4,5)))]))

		def testPolygon3d(self):
			p = Polygon3d([
				Line3d(Vector3d(0.0,0.0,0.0),Vector3d(1.0,0.0,0.0)),
				Line3d(Vector3d(1.0,0.0,0.0),Vector3d(0.0,1.0,0.0)),
				Line3d(Vector3d(0.0,1.0,0.0),Vector3d(0.0,0.0,0.0)),
				Line3d(Vector3d(0.0,0.0,0.0),Vector3d(0.0,0.0,1.0)),
				Line3d(Vector3d(1.0,0.0,0.0),Vector3d(0.0,0.0,1.0)),
				Line3d(Vector3d(0.0,1.0,0.0),Vector3d(0.0,0.0,1.0))
			])
			points = set([
				Vector3d(0.0,0.0,0.0), Vector3d(1.0,0.0,0.0),
				Vector3d(0.0,1.0,0.0), Vector3d(0.0,0.0,1.0)
			])
			self.assertEquals(points, p.get_points())

			self.assertTrue(Polygon3d((
					Line3d(Vector3d(0,0,0),Vector3d(1,0,0)),
					Line3d(Vector3d(0,0,0),Vector3d(0,1,0)),
					Line3d(Vector3d(1,0,0),Vector3d(0,1,0)),
					Line3d(Vector3d(0,0,1),Vector3d(0,0,0)),
					Line3d(Vector3d(0,0,1),Vector3d(1,0,0)),
					Line3d(Vector3d(0,0,1),Vector3d(0,1,0))
				))
				in set([Polygon3d((
					Line3d(Vector3d(0,0,0),Vector3d(1,0,0)),
					Line3d(Vector3d(0,0,0),Vector3d(0,1,0)),
					Line3d(Vector3d(1,0,0),Vector3d(0,1,0)),
					Line3d(Vector3d(0,0,1),Vector3d(0,0,0)),
					Line3d(Vector3d(0,0,1),Vector3d(1,0,0)),
					Line3d(Vector3d(0,0,1),Vector3d(0,1,0))
				))]))
			self.assertFalse(Polygon3d((
					Line3d(Vector3d(0,0,0),Vector3d(1,0,0)),
					Line3d(Vector3d(0,0,0),Vector3d(0,1,0)),
					Line3d(Vector3d(1,0,0),Vector3d(0,1,0)),
					Line3d(Vector3d(0,0,1),Vector3d(0,0,0)),
					Line3d(Vector3d(0,0,1),Vector3d(1,0,0)),
					Line3d(Vector3d(0,0,1),Vector3d(0,1,0))
				))
				in set([Polygon3d((
					Line3d(Vector3d(0,9,0),Vector3d(1,0,0)),
					Line3d(Vector3d(0,0,0),Vector3d(0,1,0)),
					Line3d(Vector3d(1,0,0),Vector3d(0,1,0)),
					Line3d(Vector3d(0,0,1),Vector3d(0,0,0)),
					Line3d(Vector3d(0,0,1),Vector3d(1,0,0)),
					Line3d(Vector3d(0,0,1),Vector3d(0,1,0))
				))]))
	
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

		def testMatrix(self):
		
			self.assertEqual(Matrix(((1,2),(3,4))),Matrix(((1,2),(3,4))))
			self.assertNotEqual(Matrix(((1,2),(3,4))),Matrix(((5,6,7),(8,9,10))))
			
			self.assertEquals( Matrix(((1,2,3),(4,5,6)))+Matrix(((3,4,5),(6,7,8))), 
				Matrix(((4,6,8),(10,12,14))) )
			self.assertEquals( Matrix(((1,2,3),(4,5,6)))-Matrix(((3,4,5),(6,7,8))),
				Matrix(((-2,-2,-2),(-2,-2,-2))) )
				
			self.assertRaises(TypeError, 
				lambda: Matrix(((1,2,3),(4,5,6))) + Matrix(((1,2),(3,4),(5,6))) )
			self.assertRaises(TypeError,
				lambda: Matrix(((1,2,3),(4,5,6))) - Matrix(((1,2),(3,4),(5,6))) )

			self.assertEquals( Matrix((2,3,4)) + (1,2,3), Matrix((3,5,7)) )
			self.assertEquals( Matrix((2,3,4)) - (1,2,3), Matrix((1,1,1)) )

			self.assertEquals( Matrix(((1,2,3),(4,5,6))) * 2.0, Matrix(((2,4,6),(8,10,12))) )
			self.assertEquals( 2.0 * Matrix(((1,2,3),(4,5,6))), Matrix(((2,4,6),(8,10,12))) )

			self.assertEquals( Matrix(((1,2,3),(4,5,6))) / 2.0, Matrix(((0.5,1,1.5),(2,2.5,3))) )
			
			self.assertEquals( Matrix(((1,2,3),(4,5,6))) * Matrix(((1,2),(3,4),(5,6))),
				Matrix(((1*1+2*3+3*5, 1*2+2*4+3*6),(4*1+5*3+6*5, 4*2+5*4+6*6))) )
				
			self.assertEquals( [[1,2,3],[4,5,6]] * Matrix([9,8,7]),
				Matrix([1*9+2*8+3*7,4*9+5*8+6*7]) )
				
			self.assertEquals( Matrix(((1,2,3),(4,5,6))) * [[9],[8],[7]],
				 [1*9+2*8+3*7, 4*9+5*8+6*7] )
				
			self.assertEquals(Matrix.identity(2), Matrix(((1,0),(0,1))))
			
			self.assertEquals(Matrix(((1,2),(3,4),(5,6))).transpose(), Matrix(((1,3,5),(2,4,6))))
			
			self.assertTrue(Matrix(((1,2),(3,4))) in set([Matrix(((1,2),(3,4)))]))
			self.assertFalse(Matrix(((1,2),(3,4))) in set([Matrix(((9,8),(7,6)))]))
			
			

	unittest.main()
    
    
    
    
    
    
