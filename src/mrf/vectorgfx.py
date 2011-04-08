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

# TODO: Change pygame renderer to implement rotation
# TODO: Change pygame renderer to implement ignore flags


import xml.dom.minidom as mdom
import xml.dom as dom
import re
import mrf.mathutil as mu


RENDERER_PYGAME = "pygame"
RENDERER_OPENGL = "opengl"

FLAG_IGNORE_STROKE = (1<<0)
FLAG_IGNORE_FILL = (1<<1)
FLAG_IGNORE_SCALE = (1<<2)
FLAG_IGNORE_ROTATION = (1<<3)


# Command objects:

class Vector(object):
	
	def __init__(self, size, components, strokecolour=(0,0,0,1), strokewidth=1.0, fillcolour=None):
		self.size = size
		self.components = components
		self.strokecolour = strokecolour
		self.strokewidth = strokewidth
		self.fillcolour = fillcolour
		
	def __repr__(self):
		return "Vector(size=%s,components=%s,strokecolour=%s,strokewidth=%s,fillcolour=%s)" % (
			self.size, self.components, self.strokecolour, self.strokewidth, self.fillcolour )

class Line(object):
	
	def __init__(self, start, end, strokecolour=(0,0,0,1), strokewidth=1.0):
		self.start = start
		self.end = end
		self.strokecolour = strokecolour
		self.strokewidth = strokewidth
		
	def __repr__(self):
		return "Line(start=%s,end=%s,strokecolour=%s,strokewidth=%s)" % (
			self.start, self.end, self.strokecolour, self.strokewidth )

class Polyline(object):
	
	def __init__(self, points, strokecolour=(0,0,0,1), strokewidth=1.0, fillcolour=None):
		self.points = points
		self.strokecolour = strokecolour
		self.strokewidth = strokewidth
		self.fillcolour = fillcolour
		
	def __repr__(self):
		return "Polyline(points=%s,strokecolour=%s,strokewidth=%s,fillcolour=%s)" % (
			self.points, self.strokecolour, self.strokewidth, self.fillcolour )

class Polygon(object):

	def __init__(self, points, strokecolour=(0,0,0,1), strokewidth=1.0, fillcolour=None):
		self.points = points
		self.strokecolour = strokecolour
		self.strokewidth = strokewidth
		self.fillcolour = fillcolour
		
	def __repr__(self):
		return "Polygon(points=%s,strokecolour=%s,strokewidth=%s,fillcolour=%s)" % (
			self.points, self.strokecolour, self.strokewidth, self.fillcolour )
		
class Rectangle(object):

	def __init__(self,topleft,size,strokecolour=(0,0,0,1), strokewidth=1.0, fillcolour=None):
		self.topleft = topleft
		self.size = size
		self.strokecolour = strokecolour
		self.strokewidth = strokewidth
		self.fillcolour = fillcolour
		
	def __repr__(self):
		return "Rectangle(topleft=%s,size=%s,strokecolour=%s,strokewidth=%s,fillcolour=%s)" % (
			self.topleft, self.size, self.strokecolour, self.strokewidth, self.fillcolour )
		
class Circle(object):

	def __init__(self,centre,radius,strokecolour=(0,0,0,1), strokewidth=1.0, fillcolour=None):
		self.centre = centre
		self.radius = radius
		self.strokecolour = strokecolour
		self.strokewidth = strokewidth
		self.fillcolour = fillcolour

	def __repr__(self):
		return "Circle(centre=%s,radius=%s,strokecolour=%s,strokewidth=%s,fillcolour=%s)" % (
			self.centre, self.radius, self.strokecolour, self.strokewidth, self.fillcolour )

class Ellipse(object):
	
	def __init__(self,centre,radii,strokecolour=(0,0,0,1), strokewidth=1.0, fillcolour=None):
		self.centre = centre
		self.radii = radii
		self.strokecolour = strokecolour
		self.strokewidth = strokewidth
		self.fillcolour = fillcolour

	def __repr__(self):
		return "Ellipse(centre=%s,radii=%s,strokcolour=%s,strokewidth=%s,fillcolour=%s)" % (
			self.centre, self.radii, self.strokecolour, self.strokewidth, self.fillcolour )
	
	
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

		width = self._attribute("width", None, svg, None, float, True)
		height = self._attribute("height", None, svg, None, float, True)
		
		strokecolour = self._attribute("stroke", [0,0,0], svg, style, self._parse_svg_colour)
		if not strokecolour is None: strokecolour = strokecolour+[1.0]
		
		strokewidth = self._attribute("stroke-width", 1.0, svg, style, float)
		
		fillcolour = self._attribute("fill", None, svg, style, self._parse_svg_colour)
		fillalpha = self._attribute("fill-opacity", 1.0, svg, style, float)
		if not fillcolour is None: fillcolour = fillcolour+[fillalpha]
		
		v = Vector((width,height), [], strokecolour, strokewidth, fillcolour)
		
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
		
		centre = ( v.size[0]/2.0, v.size[1]/2.0 )
		
		# convert all draw commands to use centre-relative coordinates
		for component in v.components:
			hname = "_centre_"+type(component).__name__
			if hasattr(self,hname):
				getattr(self,hname)(centre, component)
			
		return v

	def _parse_svg_colour(self, colourstring):
		colourstring = colourstring.strip()
		
		if colourstring == "none":
			return None
			
		m = re.match("#([0-9a-fA-F]{3})",colourstring)
		if not m is None:
			return [ int(x,16)/15.0 for x in m.group(1) ]
		
		m = re.match("#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})",colourstring)
		if not m is None:
			return [ int(x,16)/255.0 for x in m.groups() ]
			
		m = re.match("rgb\(\s*([0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*\)", colourstring)
		if not m is None:
			return [ int(x)/255.0 for x in m.groups() ]
			
		m = re.match("rgb\(\s*([0-9]+)%\s*,\s*([0-9]+)%\s*,\s*([0-9]+)%\s*\)", colourstring)
		if not m is None:
			return [ int(x)/100.0 for x in m.groups() ]
			
		if colourstring in SvgReader.COLOUR_KEYWORDS:
			return [ x/255.0 for x in SvgReader.COLOUR_KEYWORDS[colourstring] ]
					
		return None

	def _parse_svg_styles(self, stylestring):
		d = {}
		for pair in stylestring.split(";"):
			name,val = pair.split(":")
			d[name] = val
		return d

	def _parse_svg_points(self,pointstring):
		nums = map(float,re.split("(?:\s+,?\s*|,\s*)",pointstring))
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
		return self._handle_svg_child_nodes(element)
		
	def _handle_svg_line(self,element):
	
		style = self._attribute("style", {}, element, None, self._parse_svg_styles)

		strokecolour = self._attribute("stroke", [0,0,0], element, style, self._parse_svg_colour)
		if not strokecolour is None: strokecolour = strokecolour+[1.0]
		
		strokewidth = self._attribute("stroke-width", 1.0, element, style, float)

		sx = self._attribute("x1", 0.0, element, None, float)
		sy = self._attribute("y1", 0.0, element, None, float)
		ex = self._attribute("x2", 0.0, element, None, float)
		ey = self._attribute("y2", 0.0, element, None, float)
		
		return [( 
			Line( (sx,sy), (ex,ey), strokecolour, strokewidth),
			( min(sx,ex), max(sx,ex), min(sy,ey), max(sy,ey) )
		)]
	
	def _handle_svg_polyline(self,element):
	
		style = self._attribute("style", {}, element, None, self._parse_svg_styles)

		strokecolour = self._attribute("stroke", [0,0,0], element, style, self._parse_svg_colour)
		if not strokecolour is None: strokecolour = strokecolour+[1.0]
		
		strokewidth = self._attribute("stroke-width", 1.0, element, style, float)

		fillcolour = self._attribute("fill", None, element, style, self._parse_svg_colour)
		fillalpha = self._attribute("fill-opacity", 1.0, element, style, float)
		if not fillcolour is None: fillcolour = fillcolour+[fillalpha]
		
		points = self._attribute("points", [], element, None, self._parse_svg_points)
		
		return [(
			Polyline(points, strokecolour, strokewidth, fillcolour) ,
			( min([p[0] for p in points]), max([p[0] for p in points]), 
				min([p[1] for p in points]), max([p[1] for p in points]) )
		)]

	def _handle_svg_polygon(self,element):
	
		style = self._attribute("style", {}, element, None, self._parse_svg_styles)
	
		strokecolour = self._attribute("stroke", [0,0,0], element, style, self._parse_svg_colour)	
		if not strokecolour is None: strokecolour = strokecolour+[1.0]
		
		strokewidth = self._attribute("stroke-width", 1.0, element, style, float)
		
		fillcolour = self._attribute("fill", None, element, style, self._parse_svg_colour)		
		fillalpha = self._attribute("fill-opacity", 1.0, element, style, float)		
		if not fillcolour is None: fillcolour = fillcolour+[fillalpha]
		
		points = self._attribute("points", [], element, None, self._parse_svg_points)
		
		return [(
			Polygon(points, strokecolour, strokewidth, fillcolour),
			( min([p[0] for p in points]), max([p[0] for p in points]),
				min([p[1] for p in points]), max([p[1] for p in points]) )
		)]

	def _handle_svg_rect(self,element):
	
		style = self._attribute("style", {}, element, None, self._parse_svg_styles)
		
		strokecolour = self._attribute("stroke", [0,0,0], element, style, self._parse_svg_colour)
		if not strokecolour is None: strokecolour = strokecolour+[1.0]
		
		strokewidth = self._attribute("stroke-width", 1.0, element, style, float)

		fillcolour = self._attribute("fill", None, element, style, self._parse_svg_colour)
		fillalpha = self._attribute("fill-opacity", 1.0, element, style, float)		
		if not fillcolour is None: fillcolour = fillcolour+[fillalpha]
		
		x = self._attribute("x", 0.0, element, None, float)
		y = self._attribute("y", 0.0, element, None, float)

		width = self._attribute("width", 1.0, element, None, float)
		height = self._attribute("height", 1.0, element, None, float)
		
		return [(
			 Rectangle((x,y),(width,height),strokecolour,strokewidth,fillcolour),
			 ( x, x+width, y, y+height )
		)]
	
	def _handle_svg_circle(self,element):
		
		style = self._attribute("style", {}, element, None, self._parse_svg_styles)

		strokecolour = self._attribute("stroke", [0,0,0], element, style, self._parse_svg_colour)		
		if not strokecolour is None: strokecolour = strokecolour+[1.0]
		
		strokewidth = self._attribute("stroke-width", 1.0, element, style, float)

		fillcolour = self._attribute("fill", None, element, style, self._parse_svg_colour)
		fillalpha = self._attribute("fill-opacity", 1.0, element, style, float)
		if not fillcolour is None: fillcolour = fillcolour+[fillalpha]
		
		cx = self._attribute("cx", 0.0, element, None, float)
		cy = self._attribute("cy", 0.0, element, None, float)
		
		radius = self._attribute("r", 1.0, element, None, float)
		
		return [(
			Circle((cx,cy),radius,strokecolour,strokewidth,fillcolour),
			( cx-radius, cx+radius, cy-radius, cy+radius ) 
		)]
	
	def _handle_svg_ellipse(self,element):
	
		style = self._attribute("style", {}, element, None, self._parse_svg_styles)
		
		strokecolour = self._attribute("stroke", [0,0,0], element, style, self._parse_svg_colour)
		if not strokecolour is None: strokecolour = strokecolour+[1.0]
		
		strokewidth = self._attribute("stroke-width", 1.0, element, style, float)
		
		fillcolour = self._attribute("fill", None, element, style, self._parse_svg_colour)
		fillalpha = self._attribute("fill-opacity", 1.0, element, style, float)
		if not fillcolour is None: fillcolour = fillcolour+[fillalpha]
		
		cx = self._attribute("cx", 0.0, element, None, float)
		cy = self._attribute("cy", 0.0, element, None, float)
		
		radx = self._attribute("rx", 1.0, element, None, float)
		rady = self._attribute("ry", 1.0, element, None, float)
		
		return [( 
			Ellipse((cx,cy),(radx,rady),strokecolour,strokewidth,fillcolour),
			( cx-radx, cx+radx, cy-rady, cy+rady )
		)]

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

	def _translate(self, point, offset):
		return ( point[0]+offset[0], point[1]+offset[1] )
		
	def _negate(self, point):
		return ( -point[0], -point[1] )

	def _centre_Line(self, centre, line):
		disp = self._negate(centre)
		line.start = self._translate(line.start,disp)
		line.end = self._translate(line.start,disp)

	def _centre_Polyline(self, centre, polyline):
		disp = self._negate(centre)
		for i,p in enumerate(polyline.points):
			polyline.points[i] = self._translate(p,disp)

	def _centre_Polygon(self, centre, polygon):
		disp = self._negate(centre)
		for i,p in enumerate(polygon.points):
			polygon.points[i] = self._translate(p,disp)
			
	def _centre_Rectangle(self, centre, rect):
		disp = self._negate(centre)
		rect.topleft = self._translate(rect.topleft,disp)
		
	def _centre_Circle(self, centre, circle):
		disp = self._negate(centre)
		circle.centre = self._translate(circle.centre,disp)
		
	def _centre_Ellipse(self, centre, ellipse):
		disp = self._negate(centre)
		ellipse.centre = self._translate(ellipse.centre,disp)


# Renderers

"""	
	Renderer interface:
		
	def render(self, target, img, pos, scale=1.0, rotation=0.0, stroke_colour=None, fill_colour=None)
	
		stroke_colour and fill_colour can be passed in to override the stroke and fill colours
		specified in the vector image itself.
"""

class PygameRenderer(object):
			
	def __init__(self,flags):
		# This renderer implementation handles flags on the fly
		self.flags = flags
			
			
	def render(self,target,img,pos,scale=1.0,rotation=0.0,stroke_colour=None,fill_colour=None):
		
		if self.flags & FLAG_IGNORE_SCALE != 0: scale = 1.0
		if self.flags & FLAG_IGNORE_ROTATION != 0: rotation = 0.0
		
		# paint canvas rectangle
		if not img.strokecolour is None or not img.fillcolour is None:
			self._do_Rectangle(target,
				Rectangle(pos,img.size,img.strokecolour,img.strokewidth,img.fillcolour),
				pos, scale, rotation)
				
		# paint components
		for c in vector.components:
			getattr(self,"_do_"+type(c).__name__)(target,c,pos,scale,rotation,stroke_colour,fill_colour)
			
			
	def _do_Line(self,target,line,pos,scale,rotation,stroke_colour,fill_colour):
	
		# drawing unnecessary?
		if( line.strokecolour is None or line.strokewidth <= 0.0 or self.flags & FLAG_IGNORE_STROKE != 0 ):
			return
	
		# override colours
		scolour = line.strokecolour
		if not scolour is None and not stroke_colour is None: 
			scolour = stroke_colour
	
		self._polygon(target,[line.start,line.end],pos,scale,rotation,scolour,
			line.strokewidth,None,False)			
			
			
	def _do_Polyline(self,target,polyline,pos,scale,rotation,stroke_colour,fill_colour):
	
		# drawing unnecessary?
		if( polyline.strokecolour is None or poly.strokewidth <= 0.0 or self.flags & FLAG_IGNORE_STROKE != 0 ):
			return
			
		# override colours
		scolour = polyline.strokecolour
		if not scolour is None and not stroke_colour is None:
			scolour = stroke_colour
			
		self._polygon(target,polyline.points,pos,scale,rotation,scolour,
			polyline.strokewidth,None,False)	
			
			
	def _do_Polygon(self,target,polygon,pos,scale,rotation,stroke_colour,fill_colour):
	
		# drawing unnecessary?
		if( (polygon.strokecolour is None or polygon.strokewidth <= 0.0 or self.flags & FLAG_IGNORE_STROKE != 0)
				and (polygon.fillcolour is None or self.flags & FLAG_IGNORE_FILL != 0) ):
			return 
	
		# override colours
		scolour = polygon.scolour
		if not scolour is None and not stroke_colour is None:
			scolour = stroke_colour
		fcolour = polygon.fillcolour
		if not fcolour is None and not fill_colour is None:
			fcolour = fill_colour
	
		self._polygon(target,polygon.points,pos,scale,rotation,scolour,
			polygon.strokewidth,fcolour,True)
						
			
	def _do_Rectangle(self,target,rectangle,pos,scale,rotation,stroke_colour,fill_colour):
	
		# drawing necessary?
		if( (rectangle.strokecolour is None or rectangle.strokewidth <= 0.0 or self.flags & FLAG_IGNORE_STROKE != 0)
				and (rectangle.fillcolour is None or self.flags & FLAG_IGNORE_FILL != 0) ):
			return		
	
		# override colours
		scolour = rectangle.strokecolour
		if not scolour is None and not stroke_colour is None:
			scolour = stroke_colour
		fcolour = rectangle.fillcolour
		if not fcolour is None and not fill_colour is None:
			fcolour = fill_colour
	
		t = rectangle.topleft
		s = rectangle.size
		self._polygon(target, [ (t[0],t[1]), (t[0]+s[0],t[1]), (t[0]+s[0],t[1]+s[1]), (t[0],t[1]+s[1]) ],
			pos, scale, rotation, scolour, rectangle.strokewidth, fcolour, True)
	
			
	def _do_Circle(self,target,circle,pos,scale,rotation,stroke_colour,fill_colour):
	
		# drawing necessary?
		if( (circle.strokecolour is None or circle.strokewidth <= 0.0 or self.flags & FLAG_IGNORE_STROKE != 0)
				and (circle.fillcolour is None or self.flags & FLAG_IGNORE_FILL != 0) ):
			return

		# override colours
		scolour = circle.strokecolour
		if not scolour is None and not stroke_colour is None:
			scolour = stroke_colour
		fcolour = circle.fillcolour
		if not fcolour is None and not fill_colour is None:
			fcolour = fill_colour
	
		# create a 32-sided polygon
		points = []
		for i in range(32):
			points.append((
				circle.centre[0] + circle.radius * math.cos(2.0*math.pi/i),
				circle.centre[1] + circle.radius * math.sin(2.0*math.pi/i)
			))
		
		self._polygon(target, points, pos, scale, rotation, scolour, circle.strokewidth, fcolour, True)	
	
	
	def _do_Ellipse(self,target,ellipse,pos,scale,rotation,stroke_colour,fill_colour):
	
		# drawing necessary?
		if( (ellipse.strokecolour is None or ellipse.strokewidth <= 0.0 or self.flags & FLAG_IGNORE_STROKE != 0)
				and (ellipse.fillcolour is None or self.flags & FLAG_IGNORE_FILL != 0) ):
			return
	
		# override colours
		scolour = ellipse.strokecolour
		if not scolour is None and not stroke_colour is None:
			scolour = stroke_colour
		fcolour = ellipse.fillcolour
		if not fcolour is None and not fill_colour is None:
			fcolour = fill_colour
			
		# create a 32-sided polygon
		points = []
		for i in range(32):
			points.append((
				ellipse.centre[0] + ellipse.radii[0] * math.cos(2.0*math.pi/i),
				ellipse.centre[1] + ellipse.radii[1] * math.sin(2.0*math.pi/i)
			))	
			
		self._polygon(target, points, pos, scale, rotation, scolour, ellipse.strokewidth, fcolour, True)	
			
	
	def _polygon(self,target,points,pos,scale,rotation,stroke_colour,stroke_width,fill_colour,closed):
	
		# transform
		points = map(lambda p: (int(p[0]),int(p[1])), self._transform(points,pos,scale,rotation))
	
		# draw fill
		if not fill_colour is None:
			fcolour = self._colour(fill_colour)
			pygame.draw.polygon(target, fcolour, points, 0)
			
		# draw stroke
		if not stroke_colour is None and stroke_width > 0.0:
			scolour = self._colour(stroke_colour)
			swidth = int(stroke_width * scale)
			pygame.draw.lines(target, scolour, closed, points, swidth)
			
			
	def _transform(self,pointlist,pos,scale,rotation):
			
		# prepare point matrix using homogenous coords
		pm = mu.Matrix([ [p[0] for p in pointlist], [p[1] for p in pointlist], [1]*len(pointlist) ])
		
		# prepare transformation matrix
		tm = mu.Angle(rotation).matrix() * mu.Matrix([
			[	scale,	0.0, 	pos[0]	],
			[	0.0, 	scale, 	pos[1]	],
			[	0.0, 	0.0,	1.0		]
		])
		
		# transform
		rm = tm * pm
		
		# convert back to point list
		return zip(rm[0],rm[1])		
			
			
	def _colour(self,val):
		return [int(x*255) for x in val]


def load(filepath):
	if filepath.endswith(".xml"):
		return SvgReader().load(filepath)
	else:
		raise ValueError("Cannot open %s" % filepath)


def make_renderer(type, flags=0):
	if type == RENDERER_PYGAME:
		return PygameRenderer(flags)		
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
	
	v = load(sys.argv[1])
	print v.size
	for c in v.components:
		print "\t"+str(c)
	
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

