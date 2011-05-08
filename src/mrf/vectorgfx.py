"""	
Copyright (c) 2011 Mark Frimston

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

Vector Graphics Module

"""

import xml.dom.minidom as mdom
import xml.dom as dom
import re
import mrf.mathutil as mu

# TODO: Update path segment code for new structure: _convert_Path - TEST
# TODO: Ensure groups are parsed and handled in conversion - TEST
# TODO: Implement transforms - TEST
# TODO: Need difference between "none" and "not specified" for colours/widths to allow inheritence - TEST
# TODO: Can groups define inherited stroke/fill colours? YES - implement. - TEST
# TODO: Implement transform parsing - TEST
# TODO: Separate colour and alpha in command objects to allow separate inheritance - TEST
# TODO: Adjust colour conversion for new alpha in structure - TEST



RENDERER_PYGAME = "pygame"
RENDERER_OPENGL = "opengl"

CAP_STROKE = (1<<0)
CAP_FILL = (1<<1)
CAP_SCALE = (1<<2)
CAP_ROTATION = (1<<3)
CAP_STROKE_ALPHA = (1<<4)
CAP_FILL_ALPHA = (1<<5)
CAP_MULTI_STROKE_COL = (1<<6)
CAP_MULTI_STROKE_WIDTH = (1<<7)
CAP_MULTI_FILL_COL = (1<<8)
CAP_ALL = (1<<32)-1


# Command objects:

class Inherited(object): pass


class Vector(object):
	
	def __init__(self, size, components, strokecolour=None, strokealpha=1.0, 
			strokewidth=1.0, fillcolour=None, fillalpha=1.0):
		self.size = size
		self.components = components
		self.strokecolour = strokecolour
		self.strokealpha = strokealpha
		self.strokewidth = strokewidth
		self.fillcolour = fillcolour
		self.fillalpha = fillalpha
		
	def __repr__(self):
		return "Vector(size=%s,components=%s,strokecolour=%s,strokealpha=%s,strokewidth=%s,fillcolour=%s,fillalpha=%s)" % tuple(map(repr,(
			self.size, self.components, self.strokecolour, self.strokealpha, 
			self.strokewidth, self.fillcolour, self.fillalpha)))


class Group(object):

	def __init__(self,components,strokecolour=None,strokealpha=1.0,
			strokewidth=1.0,fillcolour=None,fillalpha=1.0,transforms=[]):
		self.components = components
		self.strokecolour = strokecolour
		self.strokealpha = strokealpha
		self.strokewidth = strokewidth
		self.fillcolour = fillcolour
		self.fillalpha = fillalpha
		self.transforms = transforms
		
	def __repr__(self):
		return "Group(components=%s,strokecolour=%s,strokealpha=%s,strokewidth=%s,fillcolour=%s,fillalpha=%s,transforms=%s)" % tuple(map(repr,(
			self.components, self.strokecolour, self.strokealpha, self.strokewidth, 
			self.fillcolour, self.fillalpha, self.transforms )))
		
		
class TranslateTransform(object):

	def __init__(self,trans):
		self.trans = trans
		
	def __repr__(self):
		return "TranslateTransform(trans=%s)" % tuple(map(repr,(
			self.trans, )))


class ScaleTransform(object):

	def __init__(self,scale):
		self.scale = scale
		
	def __repr__(self):
		return "ScaleTransform(scale=%s)" % tuple(map(repr,(
			self.scale, )))
			
			
class RotateTransform(object):
	
	def __init__(self,angle):
		self.angle = angle
		
	def __repr__(self):
		return "RotateTransform(angle=%s)" % tuple(map(repr,(
			self.angle, )))


class XSkewTransform(object):
	
	def __init__(self,angle):
		self.angle = angle
		
	def __repr__(self):
		return "XSkewTransform(angle=%s)" % tuple(map(repr,(
			self.angle, )))
			

class YSkewTransform(object):

	def __init__(self,angle):
		self.angle = angle
		
	def __repr__(self):
		return "YSkewTransform(angle=%s)" % tuple(map(repr,(
			self.angle, )))


class MatrixTransform(object):

	def __init__(self,cols):
		self.cols = cols
		
	def __repr__(self):
		return "MatrixTransform(cols=%s)" % tuple(map(repr,(
			self.cols, )))
			

class Line(object):
	
	def __init__(self, start, end, strokecolour=None, strokealpha=1.0, strokewidth=1.0):
		self.start = start
		self.end = end
		self.strokecolour = strokecolour
		self.strokealpha = strokealpha
		self.strokewidth = strokewidth
		
	def __repr__(self):
		return "Line(start=%s,end=%s,strokecolour=%s,strokealpha=%s,strokewidth=%s)" % tuple(map(repr,(
			self.start, self.end, self.strokecolour, self.strokealpha, self.strokewidth )))


class Polyline(object):
	
	def __init__(self, points, strokecolour=None, strokealpha=1.0, 
			strokewidth=1.0, fillcolour=None, fillalpha=1.0):
		self.points = points
		self.strokecolour = strokecolour
		self.strokealpha = strokealpha
		self.strokewidth = strokewidth
		self.fillcolour = fillcolour
		self.fillalpha = fillalpha
		
	def __repr__(self):
		return "Polyline(points=%s,strokecolour=%s,strokealpha=%s,strokewidth=%s,fillcolour=%s,fillalpha=%s)" % tuple(map(repr,(
			self.points, self.strokecolour, self.strokealpha, 
			self.strokewidth, self.fillcolour, self.fillalpha )))


class Polygon(object):

	def __init__(self, points, strokecolour=None, strokealpha=1.0, 
			strokewidth=1.0, fillcolour=None, fillalpha=1.0):
		self.points = points
		self.strokecolour = strokecolour
		self.strokealpha = strokealpha
		self.strokewidth = strokewidth
		self.fillcolour = fillcolour
		self.fillalpha = fillalpha
		
	def __repr__(self):
		return "Polygon(points=%s,strokecolour=%s,strokealpha=%s,strokewidth=%s,fillcolour=%s,fillalpha=%s)" % tuple(map(repr,(
			self.points, self.strokecolour, self.strokealpha, 
			self.strokewidth, self.fillcolour, self.fillalpha )))

		
class Rectangle(object):

	def __init__(self,topleft,size,strokecolour=None, strokealpha=1.0, 
			strokewidth=1.0, fillcolour=None, fillalpha=1.0):
		self.topleft = topleft
		self.size = size
		self.strokecolour = strokecolour
		self.strokealpha = strokealpha
		self.strokewidth = strokewidth
		self.fillcolour = fillcolour
		self.fillalpha = fillalpha
		
	def __repr__(self):
		return "Rectangle(topleft=%s,size=%s,strokecolour=%s,strokealpha=%s,strokewidth=%s,fillcolour=%s,fillalpha=%s)" % tuple(map(repr,(
			self.topleft, self.size, self.strokecolour, self.strokealpha,
			self.strokewidth, self.fillcolour, self.fillalpha )))

		
class Circle(object):

	def __init__(self,centre,radius,strokecolour=None, strokealpha=1.0, 
			strokewidth=1.0, fillcolour=None, fillalpha=1.0):
		self.centre = centre
		self.radius = radius
		self.strokecolour = strokecolour
		self.strokealpha = 1.0
		self.strokewidth = strokewidth
		self.fillcolour = fillcolour
		self.fillalpha = fillalpha

	def __repr__(self):
		return "Circle(centre=%s,radius=%s,strokecolour=%s,strokealpha=%s,strokewidth=%s,fillcolour=%s,fillalpha=%s)" % tuple(map(repr,(
			self.centre, self.radius, self.strokecolour, self.strokealpha,
			self.strokewidth, self.fillcolour, self.fillalpha )))


class Ellipse(object):
	
	def __init__(self,centre,radii,strokecolour=None, strokealpha=1.0,
			strokewidth=1.0, fillcolour=None, fillalpha=1.0):
		self.centre = centre
		self.radii = radii
		self.strokecolour = strokecolour
		self.strokealpha = strokealpha
		self.strokewidth = strokewidth
		self.fillcolour = fillcolour
		self.fillalpha = fillalpha

	def __repr__(self):
		return "Ellipse(centre=%s,radii=%s,strokcolour=%s,strokealpha=%s,strokewidth=%s,fillcolour=%s,fillalpha=%s)" % tuple(map(repr,(
			self.centre, self.radii, self.strokecolour, self.strokealpha,
			self.strokewidth, self.fillcolour, self.fillalpha )))


class Path(object):

	def __init__(self,segments,strokecolour=None,strokealpha=1.0,
			strokewidth=1.0,fillcolour=None,fillalpha=1.0):
		self.segments = segments
		self.strokecolour = strokecolour
		self.strokealpha = strokealpha
		self.strokewidth = strokewidth
		self.fillcolour = fillcolour
		self.fillalpha = fillalpha
		
	def __repr__(self):
		return "Path(segments=%s,strokecolour=%s,strokealpha=%s,strokewidth=%s,fillcolour=%s,fillalpha=%s)" % tuple(map(repr,(
			self.segments, self.strokecolour, self.strokealpha, 
			self.strokewidth, self.fillcolour, self.fillalpha)))


class MoveSegment(object):

	def __init__(self,relative,points):
		self.relative = relative
		self.points = points
		
	def __repr__(self):
		return "MoveSegment(relative=%s,points=%s)" % tuple(map(repr,(
			self.relative, self.points )))


class LineSegment(object):

	def __init__(self,relative,points):
		self.relative = relative
		self.points = points

	def __repr__(self):	
		return "LineSegment(relative=%s,points=%s)" % tuple(map(repr,(
			self.relative, self.points )))
			
			
class HLineSegment(object):

	def __init__(self,relative,coords):
		self.relative = relative
		self.coords = coords
		
	def __repr__(self):
		return "HLineSegment(relative=%s,coords=%s)" % tuple(map(repr,(
			self.relative, self.coords )))
			
			
class VLineSegment(object):
	
	def __init__(self,relative,coords):
		self.relative = relative
		self.coords = coords

	def __repr__(self):
		return "VLineSegment(relative=%s,coords=%s)" % tuple(map(repr,(
			self.relative, self.coords )))


class Arc(object):

	def __init__(self,topoint,ellsize,ellrot,long,clockwise):
		self.topoint = topoint
		self.ellsize = ellsize
		self.ellrot = ellrot
		self.long = long
		self.clockwise = clockwise
		
	def __repr__(self):
		return "Arc(topoint=%s,ellsize=%s,ellrot=%s,long=%s,clockwise=%s)" % tuple(map(repr,(
			self.topoint,self.ellsize,self.ellrot,self.long,self.clockwise )))


class ArcSegment(object):
	
	def __init__(self,relative,arcs):
		self.relative = relative
		self.arcs = arcs
		
	def __repr__(self):
		return "ArcSegment(relative=%s,arcs=%s)" % tuple(map(repr,(
			self.relative, self.arcs )))


class Quadratic(object):

	def __init__(self,topoint,ctlpoint):
		self.topoint = topoint
		self.ctlpoint = ctlpoint
		
	def __repr__(self):
		return "Quadratic(topoint=%s,ctlpoint=%s)" % tuple(map(repr,(
			self.topoint, self.ctlpoint )))
		

class QuadraticSegment(object):

	def __init__(self,relative,curves):
		self.relative = relative
		self.curves = curves
		
	def __repr__(self):
		return "QuadraticSegment(relative=%s,curves=%s)" % tuple(map(repr,(
			self.relative, self.curves )))
	
	
class Cubic(object):
	
	def __init__(self,topoint,ctlpoint1,ctlpoint2):
		self.topoint = topoint
		self.ctlpoint1 = ctlpoint1
		self.ctlpoint2 = ctlpoint2
		
	def __repr__(self):
		return "Cubic(topoint=%s,ctlpoint1=%s,ctlpoint2=%s)" % tuple(map(repr,(
			self.topoint, self.ctlpoint1, self.ctlpoint2 )))
	
	
class CubicSegment(object):

	def __init__(self,relatie,curves):
		self.relative = relative
		self.curves = curves	
	
	def __repr__(self):
		return "CubicSegment(relative=%s,curves=%s)" % tuple(map(repr,(
			self.relative, self.curves )))
	

class CloseSegment(object):
	
	def __init__(self):
		pass
		
	def __repr__(self):
		return "CloseSegment()"
		
	
# file loaders

class SvgReader(object):

	COLOUR_KEYWORDS = {
		"aliceblue"	: (240, 248, 255), "antiquewhite":	(250, 235, 215), "aqua":	( 0, 255, 255),	
		"aquamarine":	(127, 255, 212), "azure":(240, 255, 255), "beige":	(245, 245, 220),
		"bisque": (255, 228, 196), "black": (0, 0, 0), "blanchedalmond":	(255, 235, 205),
		"blue": ( 0, 0, 255), "blueviolet":	(138, 43, 226), "brown":	(165, 42, 42),
		"burlywood":(222, 184, 135), "cadetblue":( 95, 158, 160),"chartreuse":(127, 255, 0),
		"chocolate":(210, 105, 30),"coral":(255, 127, 80),"cornflowerblue":(100, 149, 237),
		"cornsilk":(255, 248, 220),"crimson":(220, 20, 60),"cyan":( 0, 255, 255),
		"darkblue":( 0, 0, 139),"darkcyan":( 0, 139, 139),"darkgoldenrod":(184, 134, 11),
		"darkgray":(169, 169, 169),"darkgreen":( 0, 100, 0),"darkgrey":	(169, 169, 169),
		"darkkhaki":(189, 183, 107),"darkmagenta":(139, 0, 139),"darkolivegreen":( 85, 107, 47),
		"darkorange":(255, 140, 0),"darkorchid":(153, 50, 204),"darkred":(139, 0, 0),
		"darksalmon":(233, 150, 122),"darkseagreen":(143, 188, 143),"darkslateblue":( 72, 61, 139),
		"darkslategray":( 47, 79, 79),"darkslategrey":( 47, 79, 79),"darkturquoise":( 0, 206, 209),
		"darkviolet":(148, 0, 211),"deeppink":(255, 20, 147),"deepskyblue":( 0, 191, 255),
		"dimgray":(105, 105, 105),"dimgrey":(105, 105, 105),"dodgerblue":( 30, 144, 255),
		"firebrick":(178, 34, 34),"floralwhite":(255, 250, 240),"forestgreen":( 34, 139, 34),
		"fuchsia":(255, 0, 255),"gainsboro":(220, 220, 220),"ghostwhite":(248, 248, 255),
		"gold":(255, 215, 0),"goldenrod":(218, 165, 32),"gray":(128, 128, 128),
		"grey":(128, 128, 128),"green":( 0, 128, 0),"greenyellow":(173, 255, 47),
		"honeydew":	(240, 255, 240),"hotpink":(255, 105, 180),"indianred":(205, 92, 92),
		"indigo":( 75, 0, 130),"ivory":(255, 255, 240),"khaki":(240, 230, 140),
		"lavender":	(230, 230, 250),"lavenderblush":(255, 240, 245),"lawngreen":(124, 252, 0),
		"lemonchiffon":(255, 250, 205),"lightblue":(173, 216, 230),"lightcoral":(240, 128, 128),
		"lightcyan":(224, 255, 255),"lightgoldenrodyellow":(250, 250, 210),"lightgray":(211, 211, 211),
		"lightgreen":(144, 238, 144),"lightgrey":(211, 211, 211),"lightpink":(255, 182, 193),
		"lightsalmon":(255, 160, 122),"lightseagreen":( 32, 178, 170),"lightskyblue":(135, 206, 250),
		"lightslategray":(119, 136, 153),"lightslategrey":(119, 136, 153),"lightsteelblue":(176, 196, 222),
		"lightyellow":(255, 255, 224),"lime":( 0, 255, 0),"limegreen":( 50, 205, 50),
		"linen":(250, 240, 230),"magenta":(255, 0, 255),"maroon":(128, 0, 0),
		"mediumaquamarine":(102, 205, 170),"mediumblue":( 0, 0, 205),"mediumorchid":(186, 85, 211),
		"mediumpurple":(147, 112, 219),"mediumseagreen":( 60, 179, 113),"mediumslateblue":(123, 104, 238),
		"mediumspringgreen":( 0, 250, 154),"mediumturquoise":( 72, 209, 204),"mediumvioletred":(199, 21, 133),
		"midnightblue":( 25, 25, 112),"mintcream":(245, 255, 250),"mistyrose":(255, 228, 225),
		"moccasin":(255, 228, 181),"navajowhite":(255, 222, 173),"navy":( 0, 0, 128),
		"oldlace":(253, 245, 230),"olive":(128, 128, 0),"olivedrab":(107, 142, 35),
		"orange":(255, 165, 0),"orangered":(255, 69, 0),"orchid":(218, 112, 214),
		"palegoldenrod":(238, 232, 170),"palegreen":(152, 251, 152),"paleturquoise":(175, 238, 238),
		"palevioletred":(219, 112, 147),"papayawhip":(255, 239, 213),"peachpuff":(255, 218, 185),
		"peru":(205, 133, 63),"pink":(255, 192, 203),"plum":(221, 160, 221),
		"powderblue":(176, 224, 230),"purple":(128, 0, 128),"red":(255, 0, 0),
		"rosybrown":(188, 143, 143),"royalblue":( 65, 105, 225),"saddlebrown":(139, 69, 19),
		"salmon":(250, 128, 114),"sandybrown":(244, 164, 96),"seagreen":( 46, 139, 87),
		"seashell":(255, 245, 238),"sienna":(160, 82, 45),"silver":(192, 192, 192),
		"skyblue":(135, 206, 235),"slateblue":(106, 90, 205),"slategray":(112, 128, 144),
		"slategrey":(112, 128, 144),"snow":(255, 250, 250),"springgreen":( 0, 255, 127),
		"steelblue":( 70, 130, 180),"tan":(210, 180, 140),"teal":( 0, 128, 128),
		"thistle":(216, 191, 216),"tomato":(255, 99, 71),"turquoise":( 64, 224, 208),
		"violet":(238, 130, 238),"wheat":(245, 222, 179),"white":(255, 255, 255),
		"whitesmoke":(245, 245, 245),"yellow":(255, 255, 0),"yellowgreen":(154, 205, 50)
	}

	def load(self, filepath):
	
		# parse XML DOM
		svg = mdom.parse(filepath).documentElement
		
		# handle svg element styles
		
		style = self._attribute("style", {}, svg, None, self._parse_svg_styles)

		width = self._attribute("width", None, svg, None, self._parse_svg_size, True)
		height = self._attribute("height", None, svg, None, self._parse_svg_size, True)
		
		strokecolour = self._attribute("stroke", None, svg, style, self._parse_svg_colour)
		strokealpha = self._attribute("stroke-opacity", 1.0, svg, style, float)
		
		strokewidth = self._attribute("stroke-width", 1.0, svg, style, self._parse_svg_size, True)
		
		fillcolour = self._attribute("fill", None, svg, style, self._parse_svg_colour)
		fillalpha = self._attribute("fill-opacity", 1.0, svg, style, float)
		
		v = Vector((width,height), [], strokecolour, strokealpha, strokewidth, fillcolour, fillalpha)
		
		# parse inner elements of svg, establishing dimensions of image
		minx, miny, maxx, maxy = 0,0,0,0
		for component,(ix,ax,iy,ay) in self._handle_svg_child_nodes(svg):
			v.components.append(component)
			if ix < minx: minx = ix
			if ax > maxx: maxx = ax
			if iy < miny: miny = iy
			if ay > maxy: maxy = ay
		
		if v.size[0] is None: v.size = (maxx-minx, v.size[1])
		if v.size[1] is None: v.size = (v.size[0], maxy-miny)
		
		return v

	def _parse_svg_colour(self, colourstring):
		colourstring = colourstring.strip()
		
		if colourstring == "none":
			return None
			
		m = re.match("^#([0-9a-fA-F]{3})$",colourstring)
		if not m is None:
			return [ int(x,16)/15.0 for x in m.group(1) ]
		
		m = re.match("^#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})$",colourstring)
		if not m is None:
			return [ int(x,16)/255.0 for x in m.groups() ]
			
		m = re.match("^rgb\(\s*([0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*\)$", colourstring)
		if not m is None:
			return [ int(x)/255.0 for x in m.groups() ]
			
		m = re.match("^rgb\(\s*([0-9]+)%\s*,\s*([0-9]+)%\s*,\s*([0-9]+)%\s*\)$", colourstring)
		if not m is None:
			return [ int(x)/100.0 for x in m.groups() ]
			
		if colourstring in SvgReader.COLOUR_KEYWORDS:
			return [ x/255.0 for x in SvgReader.COLOUR_KEYWORDS[colourstring] ]
					
		return None

	def _parse_svg_size(self, sizestr):
		m = re.match("(-?[0-9]+(?:\.[0-9]+)?)(?:px)?",sizestr.strip())
		if m is not None:
			return float(m.group(1))
		else:
			raise ValueError()

	def _parse_svg_styles(self, stylestring):
		d = {}
		for pair in stylestring.split(";"):
			name,val = pair.split(":")
			d[name] = val
		return d

	def _parse_svg_numbers(self,numstring):
		return map(float,filter(lambda x: len(x.strip())>0 ,re.split("(?:\s+,?\s*|,\s*)",numstring)))

	def _parse_svg_points(self,pointstring):
		nums = self._parse_svg_numbers(pointstring)
		return zip(nums[::2],nums[1::2])

	def _handle_svg_child_nodes(self,element):
		# return flattened result of handling each element child 
		retlist = []
		for c in element.childNodes:
			if c.nodeType == dom.Node.ELEMENT_NODE:
				retlist.extend(self._handle_svg_element(c))
		return retlist

	def _handle_svg_element(self,element):
		# dispatch to specific handler method
		hname = "_handle_svg_"+element.localName
		if hasattr(self,hname):
			return getattr(self,hname)(element)
		else:
			return []
		
	def _handle_svg_g(self,element):
		
		style = self._attribute("style", {}, element, None, self._parse_svg_styles)

		strokecolour = self._attribute("stroke", Inherited, element, style, self._parse_svg_colour)
		strokealpha = self._attribute("stroke-opacity", Inherited, element, style, float)
		
		strokewidth = self._attribute("stroke-width", Inherited, element, style, self._parse_svg_size, True)

		fillcolour = self._attribute("fill", Inherited, element, style, self._parse_svg_colour)
		fillalpha = self._attribute("fill-opacity", Inherited, element, style, float)
			
		transforms = self._attribute("transform", [], element, style, self._parse_svg_transforms)
			
		minx,maxx,miny,maxy = (0,0,0,0)
		components = []
		for component,(ix,ax,iy,ay) in self._handle_svg_child_nodes(element):
			components.append(component)
			if ix < minx: minx = ix
			if ax > maxx: maxx = ax
			if iy < miny: miny = iy
			if ay > maxy: maxy = ay
			
		return [(
			Group(components,strokecolour,strokealpha,strokewidth,fillcolour,fillalpha,transforms),
			(minx,maxx,miny,maxy)
		)]
		
	def _handle_svg_line(self,element):
	
		style = self._attribute("style", {}, element, None, self._parse_svg_styles)

		strokecolour = self._attribute("stroke", Inherited, element, style, self._parse_svg_colour)
		strokealpha = self._attribute("stroke-opacity", Inherited, element, style, float)
		
		strokewidth = self._attribute("stroke-width", Inherited, element, style, self._parse_svg_size, True)

		sx = self._attribute("x1", 0.0, element, None, float)
		sy = self._attribute("y1", 0.0, element, None, float)
		ex = self._attribute("x2", 0.0, element, None, float)
		ey = self._attribute("y2", 0.0, element, None, float)
		
		return [( 
			Line( (sx,sy), (ex,ey), strokecolour, strokealpha, strokewidth),
			( min(sx,ex), max(sx,ex), min(sy,ey), max(sy,ey) )
		)]
	
	def _handle_svg_polyline(self,element):
	
		style = self._attribute("style", {}, element, None, self._parse_svg_styles)

		strokecolour = self._attribute("stroke", Inherited, element, style, self._parse_svg_colour)
		strokealpha = self._attribute("stroke-opacity", Inherited, element, style, float)
		
		strokewidth = self._attribute("stroke-width", Inherited, element, style, self._parse_svg_size, True)

		fillcolour = self._attribute("fill", Inherited, element, style, self._parse_svg_colour)
		fillalpha = self._attribute("fill-opacity", Inherited, element, style, float)
		
		points = self._attribute("points", [], element, None, self._parse_svg_points)
		
		return [(
			Polyline(points, strokecolour, strokealpha, strokewidth, fillcolour, fillalpha) ,
			( min([p[0] for p in points]), max([p[0] for p in points]), 
				min([p[1] for p in points]), max([p[1] for p in points]) )
		)]

	def _handle_svg_polygon(self,element):
	
		style = self._attribute("style", {}, element, None, self._parse_svg_styles)
	
		strokecolour = self._attribute("stroke", Inherited, element, style, self._parse_svg_colour)	
		strokealpha = self._attribute("stroke-opacity", Inherited, element, style, float)
		
		strokewidth = self._attribute("stroke-width", Inherited, element, style, self._parse_svg_size, True)
		
		fillcolour = self._attribute("fill", Inherited, element, style, self._parse_svg_colour)		
		fillalpha = self._attribute("fill-opacity", Inherited, element, style, float)		
		
		points = self._attribute("points", [], element, None, self._parse_svg_points)
		
		return [(
			Polygon(points, strokecolour, strokealpha, strokewidth, fillcolour, fillalpha),
			( min([p[0] for p in points]), max([p[0] for p in points]),
				min([p[1] for p in points]), max([p[1] for p in points]) )
		)]

	def _handle_svg_rect(self,element):
	
		style = self._attribute("style", {}, element, None, self._parse_svg_styles)
		
		strokecolour = self._attribute("stroke", Inherited, element, style, self._parse_svg_colour)
		strokealpha = self._attribute("stroke-opacity", Inherited, element, style, float)
		
		strokewidth = self._attribute("stroke-width", Inherited, element, style, self._parse_svg_size, True)

		fillcolour = self._attribute("fill", Inherited, element, style, self._parse_svg_colour)
		fillalpha = self._attribute("fill-opacity", Inherited, element, style, float)		
		
		x = self._attribute("x", 0.0, element, None, float)
		y = self._attribute("y", 0.0, element, None, float)

		width = self._attribute("width", 1.0, element, None, float)
		height = self._attribute("height", 1.0, element, None, float)
		
		return [(
			 Rectangle((x,y),(width,height),strokecolour,strokealpha,strokewidth,fillcolour,fillalpha),
			 ( x, x+width, y, y+height )
		)]
	
	def _handle_svg_circle(self,element):
		
		style = self._attribute("style", {}, element, None, self._parse_svg_styles)

		strokecolour = self._attribute("stroke", Inherited, element, style, self._parse_svg_colour)		
		strokealpha = self._attribute("stroke-opacity", Inherited, element, style, float)
		
		strokewidth = self._attribute("stroke-width", Inherited, element, style, self._parse_svg_size, True)

		fillcolour = self._attribute("fill", Inherited, element, style, self._parse_svg_colour)
		fillalpha = self._attribute("fill-opacity", Inherited, element, style, float)
		
		cx = self._attribute("cx", 0.0, element, None, float)
		cy = self._attribute("cy", 0.0, element, None, float)
		
		radius = self._attribute("r", 1.0, element, None, float)
		
		return [(
			Circle((cx,cy),radius,strokecolour,strokealpha,strokewidth,fillcolour,fillalpha),
			( cx-radius, cx+radius, cy-radius, cy+radius ) 
		)]
	
	def _handle_svg_ellipse(self,element):
	
		style = self._attribute("style", {}, element, None, self._parse_svg_styles)
		
		strokecolour = self._attribute("stroke", Inherited, element, style, self._parse_svg_colour)
		strokealpha = self._attribute("stroke-opacity", Inherited, element, style, float)
		
		strokewidth = self._attribute("stroke-width", Inherited, element, style, self._parse_svg_size, True)
		
		fillcolour = self._attribute("fill", Inherited, element, style, self._parse_svg_colour)
		fillalpha = self._attribute("fill-opacity", Inherited, element, style, float)
		
		cx = self._attribute("cx", 0.0, element, None, float)
		cy = self._attribute("cy", 0.0, element, None, float)
		
		radx = self._attribute("rx", 1.0, element, None, float)
		rady = self._attribute("ry", 1.0, element, None, float)
		
		return [( 
			Ellipse((cx,cy),(radx,rady),strokecolour,strokealpha,strokewidth,fillcolour,fillalpha),
			( cx-radx, cx+radx, cy-rady, cy+rady )
		)]

	def _handle_svg_path(self, element):
	
		style = self._attribute("style", {}, element, None, self._parse_svg_styles)

		strokecolour = self._attribute("stroke", Inherited, element, style, self._parse_svg_colour)
		strokealpha = self._attribute("stroke-opacity", Inherited, element, style, float)
		
		strokewidth = self._attribute("stroke-width", Inherited, element, style, self._parse_svg_size, True)
		
		fillcolour = self._attribute("fill", Inherited, element, style, self._parse_svg_colour)
		fillalpha = self._attribute("fill-opacity", Inherited, element, style, float)
		
		segments,limits = self._attribute("d", ([],(0,0,0,0)), element, None, self._parse_svg_path)
		
		return [(
			Path(segments,strokecolour,strokealpha,strokewidth,fillcolour,fillalpha), 
			limits,
		)]

	def _chomp(self,list,size):
		return list[:size],list[size:]

	def _parse_svg_path(self,pathstring):
		
		segs = []
		limits = (None,None,None,None)
				
		for cstr,vstr in re.findall("([A-Za-z])([0-9., 	-]*)",pathstring):
		
			values = self._parse_svg_numbers(vstr)
			relative = cstr.islower()
			
			if cstr.lower() == 'm':
				points = []
				while len(values) > 0:
					p,values = self._chomp(values,2)
					points.append(p)
				segs.append(MoveSegment(relative,points))
				limits = self._adjust_limits(limits,points[::2],points[1::2])
							
			elif cstr.lower() == 'l':
				points = []
				while len(values) > 0:
					p,values = self._chomp(values,2)
					points.append(p)
				segs.append(LineSegment(relative,points))
				limits = self._adjust_limits(limits,points[::2],points[1::2])
				
			elif cstr.lower() == 'h':
				segs.append(HLineSegment(relative,values))
				limits = self._adjust_limits(limits,values,[])
				
			elif cstr.lower() == 'v':
				segs.append(VLineSegment(relative,values))
				limits = self._adjust_limits(limits,[],values)
				
			elif cstr.lower() == 'c':
				curves = []
				while len(values) > 0:
					(c1x,c1y,c2x,c2y,x,y),values = self._chomp(values,6)
					curves.append(Cubic((x,y),(c1x,c1y),(c2x,c2y)))
				segs.append(CubicSegment(relative,curves))
				# We'll include the control points in the limits 
				limits = self._adjust_limits(limits,[c.topoint[0] for c in curves],[c.topoint[1] for c in curves])
				limits = self._adjust_limits(limits,[c.ctlpoint1[0] for c in curves],[c.ctlpoint1[1] for c in curves])
				limits = self._adjust_limits(limits,[c.ctlpoint2[0] for c in curves],[c.ctlpoint2[1] for c in curves])
				
			elif cstr.lower() == 's':
				curves = []
				while len(values) > 0:
					(c2x,c2y,x,y),values = self._chomp(values,4)
					curves.append(Cubic((x,y),None,(c2x,c2y)))
				segs.append(CubicSegment(relative,curves))				
				# We'll include the (explicit) control points in the limits
				limits = self._adjust_limits(limits,[c.topoint[0] for c in curves],[c.topoint[1] for c in curves])
				limits = self._adjust_limits(limits,[c.ctlpoint2[0] for c in curves],[c.ctlpoint2[1] for c in curves])
				
			elif cstr.lower() == 'q':
				curves = []
				while len(values) > 0:
					(cx,cy,x,y),values = self._chomp(values,4)
					curves.append(Quadratic((x,y),(cx,cy)))
				segs.append(QuadraticSegment(relative,curves))
				# We'll include the control point in the limits
				limits = self._adjust_limits(limits,[c.topoint[0] for c in curves],[c.topoint[1] for c in curves])
				limits = self._adjust_limits(limits,[c.ctlpoint[0] for c in curves],[c.ctlpoint[1] for c in curves])
				
			elif cstr.lower() == 't':
				curves = []
				while len(values) > 0:
					(x,y),values = self._chomp(values,2)
					curves.append(Quadratic((x,y),None))
				segs.append(QuadraticSegment(relative,curves))
				# Won't include the implicit control point
				limits = self._adjust_limits(limits,[c.topoint[0] for c in curves],[c.topoint[1] for c in curves])
				
			elif cstr.lower() == 'a':
				arcs = []
				while len(values) > 0:
					(rx,ry,rot,long,cw,x,y),values = self._chomp(values,7)
					arcs.append(Arc((x,y),(rx,ry),rot,bool(long),bool(cw)))
				segs.append(ArcSegment(relative,arcs))
				# Just include the endpoints in limits
				limits = self._adjust_limits(limits,[a.topoint[0] for a in arcs],[a.topoint[1] for a in arcs])
				
			elif cstr.lower() == 'z':
				segs.append(CloseSegment())
				# no parameters, so no limit change
															
		return segs, limits

	def _parse_svg_transforms(self, tstr):
		tcommands = re.findall(
			"([a-zA-Z]+)\s*"					# transform name - captured
			+"\(\s*("							# parameter bracket - optional captured parameters
				+"-?[0-9]+(?:\.[0-9]+)?"		# first number
				+"(?:"
					+"(?:,|\s)+"				# comma/whitespace
					+"-?[0-9]+(?:\.[0-9]+)?"	# next number
				+")*"
			+")?\s*\)",tstr)
			
		tlist = []
		for name,paramstr in tcommands:
			name = name.lower()
			params = self._parse_svg_numbers(paramstr)
			
			if name == "translate":
				t = (
					params[0],
					params[1] if len(params)>1 else 0.0
				)
				tlist.append(TranslateTransform(t))
				
			elif name == "scale":
				s = (
					params[0],
					params[1] if len(params)>1 else params[0]
				)
				tlist.append(ScaleTransform(s))
				
			elif name == "rotate":
				if len(params) > 1:
					# rotating about point
					tlist.append(TranslateTransform((params[1],params[2])))
					tlist.append(RotateTransform(params[0]))
					tlist.append(TranslateTransform((-params[1],-params[2])))
				else:
					# rotating about origin
					tlist.append(RotateTransform(params[0]))
				
			elif name == "skewx":
				tlist.append(XSkewTransform(params[0]))
				
			elif name == "skewy":
				tlist.append(YSkewTransform(params[0]))
				
			elif name == "matrix":
				c = (
					( params[0], params[1] ),
					( params[2], params[3] ),
					( params[4], params[5] )
				)
				tlist.append(MatrixTransform(c))
				
		return tlist

	def _adjust_limits(self, limits, xlist, ylist):
		return (
			min(xlist + ([limits[0]] if limits[0] is not None else [])),
			max(xlist + ([limits[1]] if limits[1] is not None else [])),
			min(ylist + ([limits[2]] if limits[2] is not None else [])),
			max(ylist + ([limits[3]] if limits[3] is not None else []))
		)

	def _attribute(self, name, default, element=None, styles=None, converter=str, ignore_error=False):
	
		val = default
		
		if not element is None and element.hasAttribute(name):
			try:
				val = converter(element.getAttribute(name))
			except ValueError as e:
				if not ignore_error: raise e
				
		if not styles is None and name in styles:
			try:
				val = converter(styles[name])
			except ValueError as e:
				if not ignore_error: raise e
				
		return val


# Renderers

"""	
	Renderer interface:
		
	def render(self, target, img, pos, scale=1.0, rotation=0.0, stroke_colour=None, fill_colour=None)
	
		stroke_colour and fill_colour can be passed in to override the stroke and fill colours
		specified in the vector image itself.
		
	def cache(self, img)
	
		the render function caches images, but this can be used to pre-cache them 
		before the first invokation of render
				
"""

class PygamePolygon(object):
	
	stroke_width = 0
	stroke_colour = None
	fill_colour = None
	point_matrix = None
	closed = False
	
	def __init__(self,stroke_width,stroke_colour,fill_colour,closed,point_matrix):
		self.stroke_width = stroke_width
		self.stroke_colour = stroke_colour
		self.fill_colour = fill_colour
		self.closed = closed
		self.point_matrix = point_matrix
		
class PygameMatrixWrapper(object):
	"Wraps a matrix to behave as a point sequence"
	
	matrix = None
	
	def __init__(self,matrix):
		self.matrix = matrix
		
	def __len__(self):
		return self.matrix.cols
		
	def __getitem__(self,index):
		return ( int(self.matrix[0][index]), int(self.matrix[1][index]) )
	
	
class PathContext(object):
	"Object used to store status of pen while converting a path"
	def __init__(self):
		self.p = [0,0]
		self.closed = False
		self.points = []

class InheritContext(object):
	"Object used to store properties inherited from parent components when converting"
	def __init__(self,stroke_colour=None,stroke_alpha=1.0,stroke_width=1.0,
			fill_colour=None,fill_alpha=1.0,transforms=None):
		self.stroke_colour = stroke_colour
		self.stroke_alpha = stroke_alpha
		self.stroke_width = stroke_width
		self.fill_colour = fill_colour
		self.fill_alpha = fill_alpha
		self.transforms = [] if transforms is None else transforms

class PygameRenderer(object):
	"""	
	Vector renderer using Pygame's polygon drawing to render onto a surface object.
	Unimplemented capabilities:
		CAP_FILL_ALPHA, CAP_STROKE_ALPHA
	"""

	_cache = {}

	def __init__(self):
		# import pygame
		import pygame.draw
		# clear cache
		self._cache = {}

	def cache(self,img):
		self._cache[img] = self._convert(img)
						
	def render(self,target,img,pos,scale=1.0,rotation=0.0,stroke_colour=None,fill_colour=None):
		
		# fetch polygon list from cache
		if not img in self._cache:
			self.cache(img)
				
		# prepare transformation matrix
		tm = mu.Matrix([ #translation
			[	1.0,	0,		pos[0]	],
			[	0,		1.0,	pos[1]	],
			[	0,		0,		1.0		]
		]) * mu.Matrix([ #rotation
			[	math.cos(rotation),	-math.sin(rotation),	0	],
			[	math.sin(rotation),	math.cos(rotation),		0	],
			[	0,					0,						1.0	]
		]) * mu.Matrix([ #scale
			[	scale,	0,		0	],
			[	0,		scale,	0	],
			[	0,		0,		1.0	]
		])
				
		# draw polygons
		for poly in self._cache[img]:

			# transform points, get iterator		
			points = PygameMatrixWrapper(tm * poly.point_matrix)
		
			# fill
			if poly.fill_colour is not None:
				fill = poly.fill_colour if fill_colour is None else self._colour(fill_colour)
				pygame.draw.polygon(target, fill, points)
				
			# stroke
			if poly.stroke_colour is not None and poly.stroke_width > 0:
				stroke = poly.stroke_colour if stroke_colour is None else self._colour(stroke_colour)
				width = int(poly.stroke_width * scale)
				pygame.draw.lines(target, stroke, poly.closed, points, width)
	
	def _convert(self, img):
		"Convert a vector image to a more efficient list of polygon commands"
		clist = []
		
		# establish centre point
		centre = ( img.size[0]/2.0, img.size[1]/2.0 )
		
		# default inherited properties
		context = InheritContext((0,0,0,1), 1.0, None, [])
		
		# convert image background rectangle
		clist.extend(self._convert_Rectangle(Rectangle((0,0),img.size,img.strokecolour,img.strokealpha,
				img.strokewidth,img.fillcolour,img.fillalpha),centre,context))
		
		# convert image components
		clist.extend(self._convert_components(img.components,centre,context))
			
		return clist

	def _convert_components(self, components, centre, context):
		clist = []
		for c in components:
			hname = "_convert_"+type(c).__name__
			if hasattr(self,hname):
				clist.extend(getattr(self,hname)(c,centre,context))
			else:
				raise CapabilityError("Cannot render %s image component" % type(c).__name__)
		return clist

	def _convert_Group(self,group,centre,context):
		
		stroke_colour = context.stroke_colour if group.strokecolour==Inherited else group.strokecolour
		stroke_alpha = context.stroke_alpha if group.strokealpha==Inherited else group.strokealpha
		
		stroke_width = context.stroke_width if group.strokewidth==Inherited else group.strokewidth
		
		fill_colour = context.fill_colour if group.fillcolour==Inherited else group.fillcolour
		fill_alpha = context.fill_alpha if group.fillalpha==Inherited else group.fillalpha
					
		transforms = context.transforms + group.transforms
		
		# establish new inherited properties
		context = InheritContext(stroke_colour,stroke_alpha,stroke_width,fill_colour,fill_alpha,transforms)
		
		return self._convert_components(group.components,centre,context)
			
	def _convert_Line(self,line,centre,context):
		
		stroke_colour = context.stroke_colour if line.strokecolour==Inherited else line.strokecolour
		stroke_alpha = context.stroke_alpha if line.strokealpha==Inherited else line.strokealpha		
			
		stroke_width = context.stroke_width if line.strokewidth==Inherited else line.strokewidth
			
		matrix = self._transform(self._matrix(self._centre([line.start,line.end],centre)),context.transforms)
		
		stroke = self._colour(list(stroke_colour)+[stroke_alpha]) if stroke_colour is not None else None
		
		return [ PygamePolygon(stroke_width,stroke,None,False,matrix) ]
			
	def _convert_Polyline(self,polyline,centre,context):
		
		stroke_colour = context.stroke_colour if polyline.strokecolour==Inherited else polyline.strokecolour
		stroke_alpha = context.stroke_alpha if polyline.strokealpha==Inherited else polyline.strokealpha

		stroke_width = context.stroke_width if polyline.strokewidth==Inherited else polyline.strokewidth

		fill_colour = context.fill_colour if polyline.fillcolour==Inherited else polyline.fillcolour
		fill_alpha = context.fill_alpha if polyline.fillalpha==Inherited else polyline.fillalpha
		
		stroke = self._colour(list(stroke_colour)+[stroke_alpha]) if stroke_colour is not None else None
		fill = self._colour(list(fill_colour)+[fill_alpha]) if fill_colour is not None else None
		
		matrix = self._transform(self._matrix(self._centre(polyline.points,centre)),context.transforms)
		
		return [ PygamePolygon(stroke_width,stroke,fill,False,matrix) ]
			
	def _convert_Polygon(self,polygon,centre,context):

		stroke_colour = context.stroke_colour if polygon.strokecolour==Inherited else polygon.strokecolour
		stroke_alpha = context.stroke_alpha if polygon.strokealpha==Inherited else polygon.strokealpha

		stroke_width = context.stroke_width if polygon.strokewidth==Inherited else polygon.strokewidth

		fill_colour = context.fill_colour if polygon.fillcolour==Inherited else polygon.fillcolour
		fill_alpha = context.fill_alpha if polygon.fillalpha==Inherited else polygon.fillalpha

		stroke = self._colour(list(stroke_colour)+[stroke_alpha]) if stroke_colour is not None else None
		fill = self._colour(list(fill_colour)+[fill_alpha]) if fill_colour is not None else None
			
		matrix = self._transform(self._matrix(self._centre(polygon.points,centre)),context.transforms)
		
		return [ PygamePolygon(stroke_width,stroke,fill,True,matrix) ]
					
	def _convert_Rectangle(self,rectangle,centre,context):
	
		stroke_colour = context.stroke_colour if rectangle.strokecolour==Inherited else rectangle.strokecolour
		stroke_alpha = context.stroke_alpha if rectangle.strokealpha==Inherited else rectangle.strokealpha
		
		stroke_width = context.stroke_width if rectangle.strokewidth==Inherited else rectangle.strokewidth

		fill_colour = context.fill_colour if rectangle.fillcolour==Inherited else rectangle.fillcolour
		fill_alpha = context.fill_alpha if rectangle.fillalpha==Inherited else rectangle.fillalpha	

		stroke = self._colour(list(stroke_colour)+[stroke_alpha]) if stroke_colour is not None else None
		fill = self._colour(list(fill_colour)+[fill_alpha]) if fill_colour is not None else None
			
		t = rectangle.topleft
		s = rectangle.size
		matrix = self._transform(self._matrix(self._centre([
			(t[0],t[1]), (t[0]+s[0],t[1]), (t[0]+s[0],t[1]+s[1]), (t[0],t[1]+s[1])
		],centre)),context.transforms)
		
		return [ PygamePolygon(stroke_width,stroke,fill,True,matrix) ]
			
	def _convert_Circle(self,circle,centre,context):
	
		stroke_colour = context.stroke_colour if circle.strokecolour==Inherited else circle.strokecolour
		stroke_alpha = context.stroke_alpha if circle.strokealpha==Inherited else circle.strokealpha
		
		stroke_width = context.stroke_width if circle.strokewidth==Inherited else cicle.strokewidth

		fill_colour = context.stroke_colour	if circle.fillcolour==Inherited else circle.fillcolour
		fill_alpha = context.stroke_alpha if circle.fillalpha==Inherited else circle.fillalpha

		stroke = self._colour(list(stroke_colour)+[stroke_alpha]) if stroke_colour is not None else None
		fill = self._colour(list(fill_colour)+[fill_alpha]) if fill_colour is not None else None			
	
		# create a 32-sided polygon
		points = []
		for i in range(32):
			points.append((
				circle.centre[0] + circle.radius * math.cos(2.0*math.pi/32*i),
				circle.centre[1] + circle.radius * math.sin(2.0*math.pi/32*i)
			))
		matrix = self._transform(self._matrix(self._centre(points,centre)),context.transforms)
		
		return [ PygamePolygon(stroke_width,stroke,fill,True,matrix) ]
	
	def _convert_Ellipse(self,ellipse,centre,context):
	
		stroke_colour = context.stroke_colour if ellipse.strokecolour==Inherited else ellipse.strokecolour
		stroke_alpha = context.stroke_alpha if ellipse.strokealpha==Inherited else ellipse.strokealpha

		stroke_width = context.stroke_width if ellipse.strokewidth==Inherited else ellipse.strokewidth

		fill_colour = context.fill_colour if ellipse.fillcolour==Inherited else ellipse.fillcolour
		fill_alpha = context.fill_alpha if ellipse.fillalpha==Inherited else ellise.fillalpha	
			
		stroke = self._colour(list(stroke_colour)+[stroke_alpha]) if stroke_colour is not None else None
		fill = self._colour(list(fill_colour)+[fill_alpha]) if fill_colour is not None else None
	
		# create a 32-sided polygon
		points = []
		for i in range(32):
			points.append((
				ellipse.centre[0] + ellipse.radii[0] * math.cos(2.0*math.pi/32*i),
				ellipse.centre[1] + ellipse.radii[1] * math.sin(2.0*math.pi/32*i)
			))	
		matrix = self._transforms(self._matrix(self._centre(points,centre)),context.transforms)
			
		return [ PygamePolygon(stroke_width,stroke,fill,True,matrix) ]
	
	def _convert_Path(self,path,centre,context):
		
		stroke_colour = context.stroke_colour if path.strokecolour==Inherited else path.strokecolour
		stroke_alpha = context.stroke_alpha if path.strokealpha==Inherited else path.strokealpha
		
		stroke_width = context.stroke_width if path.strokewidth==Inherited else path.strokewidth
		
		fill_colour = context.fill_colour if path.fillcolour==Inherited else path.fillcolour
		fill_alpha = context.fill_alpha if path.fillalpha==Inherited else path.fillalpha
		
		stroke = self._colour(list(stroke_colour)+[stroke_alpha]) if stroke_colour is not None else None
		fill = self._colour(list(fill_colour)+[fill_alpha]) if fill_colour is not None else None
			
		# TODO: implement sub-paths properly i.e. donut shapes (wtf?)
		
		pcontext = PathContext()
		
		for seg in path.segments:
			hname = "_convert_"+type(seg).__name__
			getattr(self,hname)(seg, pcontext)
					
		matrix = self._transform(self._matrix(self._centre(pcontext.points,centre)),context.transforms)

		return [ PygamePolygon(stroke_width,stroke,fill,pcontext.closed,matrix) ]
			
	def _convert_MoveSegment(self,seg,context):
		for x,y in seg.points:
			if seg.relative and len(context.points)>0:
				context.p[0] += x
				context.p[1] += y					
			else:
				context.p[0] = x
				context.p[1] = y
			context.points.append(context.p[:])					
			
	def _convert_LineSegment(self,seg,context):
		for x,y in seg.points:
			if seg.relative:
				context.p[0] += x
				context.p[1] += y
			else:
				context.p[0] = x
				context.p[1] = y
			context.points.append(context.p[:])
	
	def _convert_HLineSegment(self,seg,context):
		for x in seg.coords:
			if seg.relative:
				context.p[0] += x
			else:
				context.p[0] = x
			context.points.append(context.p[:])
		
	def _convert_VLineSegment(self,seg,context):
		for y in seg.coords:
			if seg.relative:
				context.p[1] += y
			else:
				context.p[1] = y
			context.points.append(context.p[:])
			
	def _convert_CubicSegment(self,seg,context):
		# TODO: implement cubic bezier
		for c in seg.curves:
			x,y = c.topoint
			if seg.relative:
				context.p[0] += x
				context.p[1] += y
			else:
				context.p[0] = x
				context.p[1] = y
			context.points.append(context.p[:])
			
	def _convert_QuadraticSegment(self,seg,context):
		# TODO: implement quadratic bezier
		for c in seg.curves:
			x,y = c.topoint
			if seg.relative:
				context.p[0] += x
				context.p[1] += y
			else:
				context.p[0] = x
				context.p[1] = y
			context.points.append(context.p[:])
			
	def _convert_ArcSegment(self,seg,context):
		# TODO implement elliptical arc
		for a in seg.arcs:
			x,y = a.topoint
			if seg.relative:
				context.p[0] += x
				context.p[1] += y
			else:
				context.p[0] = x
				context.p[1] = y
			context.points.append(context.p[:])
			
	def _convert_CloseSegment(self,seg,context):
		context.closed = True
			
	def _matrix(self,pointlist):
		"Convert sequence of coordinate pairs to col-based homogenous coord matrix"
		return mu.Matrix([
			[ p[0] for p in pointlist ],
			[ p[1] for p in pointlist ],
			[1.0] * len(pointlist)
		])
			
	def _transform(self,pointmatrix,transforms):
		"Transform point matrix according to list of transform commands"	
		for t in transforms:
			hname = "_transform_"+type(t).__name__
			pointmatrix = getattr(self,hname)(pointmatrix,t)
		return pointmatrix
		
	def _transform_TranslateTransform(self,pointmatrix,translation):
		return mu.Matrix([
			[	1.0,	0.0,	translation.trans[0]	],
			[	0.0,	1.0,	translation.trans[1]	],
			[	0.0,	0.0,	1.0						]
		]) * pointmatrix
		
	def _transform_RotateTransform(self,pointmatrix,rotation):
		return mu.Matrix([
			[	math.cos(rotation.angle),	-math.sin(rotation.angle),	0.0	],
			[	math.sin(rotation.angle),	math.cos(rotation.angle),	0.0	],
			[	0.0,						0.0,						1.0	]
		]) * pointmatrix
		
	def _transform_ScaleTransform(self,pointmatrix,scale):
		return mu.Matrix([
			[	scale.scale[0],	0.0,			0.0	],
			[	0.0,			scale.scale[1],	0.0	],
			[	0.0,			0.0,			1.0	]
		]) * pointmatrix
		
	def _transform_XSkewTransform(self,pointmatrix,skew):
		return mu.Matrix([
			[	1.0,	math.tan(skew.angle),	0.0	],
			[	0.0,	1.0,					0.0	],
			[	0.0,	0.0,					1.0	]
		]) * pointmatrix
		
	def _transform_YSkewTransform(self,pointmatrix,skew):
		return mu.Matrix([
			[	1.0,					0.0,	0.0	],
			[	math.tan(skew.angle),	1.0,	0.0	],
			[	0.0,					0.0,	1.0	]
		]) * pointmatrix
		
	def _transform_MatrixTransform(self,pointmatrix,transform):
		return mu.Matrix([
			[	transform.cols[0][0],	transform.cols[1][0],	transform.cols[2][0]	],
			[	transform.cols[0][1],	transform.cols[1][1],	transform.cols[2][1]	],
			[	0.0,					0.0,					1.0						]
		]) * pointmatrix
		
	def _centre(self,points,centre):
		"convert from top-left origin to given origin"
		return [[v-centre[i] for i,v in enumerate(p)] for p in points]
			
	def _colour(self,val):
		"convert from (1.0,1.0,1.0) format colour to (255,255,255)"
		return [int(x*255) for x in val] if val is not None else None


class CapabilityError(Exception):
	"Raised if unsupported capability is requested of renderer"
	pass


def load(filepath):
	"""	
	Load a vector graphic from the given file path.
	Supports: .svg
	"""
	if filepath.endswith(".svg"):
		return SvgReader().load(filepath)
	else:
		raise ValueError("Cannot open %s" % filepath)


def make_renderer(type, capabilities=None):
	"""	
	Instantiate a renderer object for rendering vector graphics.
	Parameters:
		type			The renderer implementation to use. See RENDERER_X constants
		capabilities	Explicit set of capabilites desired from the renderer.
						See CAP_X constants. In some cases the renderer can make
						optimisations if certain capabilites are not required.
						Use None for all available capabilites for the given type.
	"""
	if type == RENDERER_PYGAME:
		if capabilities is not None and (
				capabilities & CAP_FILL_ALPHA != 0
				or capabilities & CAP_STROKE_ALPHA != 0 ):
			raise CapabilityError("CAP_FILL_ALPHA and CAP_STROKE_ALPHA not supported by RENDERER_PYGAME")
		return PygameRenderer()		
	else:
		raise ValueError("Unknown renderer type %s" % type)


if __name__ == "__main__":
	import sys
	import random
	import math
	import pygame
	import pygame.display
	import pygame.locals
	import pygame.time
	import pygame.event
	import pygame.font
	import mrf.trees as trees
	
	v = load(sys.argv[1])
	"""print v.size
	for c in v.components:
		print "\t"+str(c)"""
		
	def treedisplay(x):
		return type(x).__name__
	
	def treebranches(x):
		if type(x)==Vector:
			return x.components
		elif type(x)==Group:
			return [x.transforms,x.components]
		elif type(x)==list:
			return list
		elif type(x)==Path:
			return x.segments
		else:
			return []						
		
	print trees.draw_tree(v,branchstrategy=treebranches,displaystrategy=treedisplay)
	
	pygame.init()
	screen = pygame.display.set_mode((640,480))
	clock = pygame.time.Clock()
	renderer = make_renderer(RENDERER_PYGAME)
	font = pygame.font.Font(None,32)
	a = 0.0
	
	while True:
	
		for event in pygame.event.get():
			if event.type == pygame.locals.QUIT:
				sys.exit()
			elif event.type == pygame.locals.KEYDOWN and event.key == pygame.locals.K_ESCAPE:
				sys.exit()
	
		screen.fill((0,128,128))
		
		renderer.render(screen, v, (160,120), 0.25, 0.0)
		renderer.render(screen, v, (480,120), 0.5, 0.2, stroke_colour=(1,0,0,1))
		renderer.render(screen, v, (160,360), 1.0, 0.0, fill_colour=(0,1,1,1))
		renderer.render(screen, v, (480,360), 2.0, -0.2)
		
		a += 0.1
		scale = 0.3 + (math.sin(a)/2.0+0.5) * 10.0
		renderer.render(screen, v, (320,240), scale, a)
		
		fpstext = font.render("fps: %d" % clock.get_fps(), True, (255,255,255))
		screen.blit(fpstext,(10,10))
		
		pygame.display.flip()
		clock.tick(60)

