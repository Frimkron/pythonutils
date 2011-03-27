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


RENDERER_PYGAME = "pygame"
RENDERER_OPENGL = "opengl"


# Command objects:

class Vector(object):
	
	def __init__(self, size, components, fillcolour=None):
		self.size = size
		self.components = components
		self.fillcolour = fillcolour

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
		svg = mdom.parse(filepath).documentElement
		style = {}
		if svg.hasAttribute("style"): style = self._parse_svg_styles(svg.getAttribute("style"))
		width = None
		if svg.hasAttribute("width"): 
			try: width = float(svg.getAttribute("width")) 
			except ValueError: pass
		height = None
		if svg.hasAttribute("height"): 
			try: height = float(svg.getAttribute("height")) 
			except ValueError: pass
		fillcolour = None
		if svg.hasAttribute("fill"): fillcolour = self._parse_svg_colour(svg.getAttribute("fill"))
		if "fill" in style: fillcolour = self._parse_svg_colour(style["fill"])
		fillalpha = 1.0
		if svg.hasAttribute("fill-opacity"): fillalpha = float(svg.getAttribute("fill-opacity"))
		if "fill-opacity" in style: fillalpha = float(style["fill-opacity"])	
		if not fillcolour is None: fillcolour = fillcolour+[fillalpha]
		
		v = Vector((width,height), [], fillcolour)
		
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
		style = {}
		if element.hasAttribute("style"): style = self._parse_svg_styles(element.getAttribute("style"))
		strokecolour = [0,0,0]
		if element.hasAttribute("stroke"): strokecolour = self._parse_svg_colour(element.getAttribute("stroke"))
		if "stroke" in style: strokecolour = self._parse_svg_colour(style["stroke"])
		if not strokecolour is None: strokecolour = strokecolour+[1.0]
		strokewidth = 1.0
		if element.hasAttribute("stroke-width"): strokewidth = float(element.getAttribute("stroke-width"))
		if "stroke-width" in style: strokewidth = float(style["stroke-width"])
		start = ( float(element.getAttribute("x1")), float(element.getAttribute("y1")) )
		end = ( float(element.getAttribute("x2")), float(element.getAttribute("y2")) )
		return [( 
			Line(start,end,strokecolour,strokewidth),
			( min(start[0],end[0]), max(start[0],end[0]), min(start[1],end[1]), max(start[1],end[1]) )
		)]
	
	def _handle_svg_polyline(self,element):
		style = {}
		if element.hasAttribute("style"): style = self._parse_svg_styles(element.getAttribute("style"))
		strokecolour = [0,0,0]
		if element.hasAttribute("stroke"): strokecolour = self._parse_svg_colour(element.getAttribute("stroke"))
		if "stroke" in style: strokecolour = self._parse_svg_colour(style["stroke"])
		if not strokecolour is None: strokecolour = strokecolour+[1.0]
		strokewidth = 1.0
		if element.hasAttribute("stroke-width"): strokewidth = float(element.getAttribute("stroke-width"))
		if "stroke-width" in style: strokewidth = float(style["stroke-width"])
		fillcolour = None
		if element.hasAttribute("fill"): fillcolour = self._parse_svg_colour(element.getAttribute("fill"))
		if "fill" in style: fillcolour = self._parse_svg_colour(style["fill"])
		fillalpha = 1.0
		if element.hasAttribute("fill-opacity"): fillalpha = float(element.getAttribute("fill-opacity"))
		if "fill-opacity" in style: fillalpha = float(style["fill-opacity"])
		if not fillcolour is None: fillcolour = fillcolour+[fillalpha]
		points = self._parse_svg_points(element.getAttribute("points"))
		return [(
			Polyline(points, strokecolour, strokewidth, fillcolour) ,
			( min([p[0] for p in points]), max([p[0] for p in points]), 
				min([p[1] for p in points]), max([p[1] for p in points]) )
		)]

	def _handle_svg_polygon(self,element):
		style = {}
		if element.hasAttribute("style"): style = self._parse_svg_styles(element.getAttribute("style"))
		strokecolour = [0,0,0]
		if element.hasAttribute("stroke"): strokecolour = self._parse_svg_colour(element.getAttribute("stroke"))
		if "stroke" in style: strokecolour = self._parse_svg_colour(style["stroke"])
		if not strokecolour is None: strokecolour = strokecolour+[1.0]
		strokewidth = 1.0
		if element.hasAttribute("stroke-width"): strokewidth = float(element.getAttribute("stroke-width"))
		if "stroke-width" in style: strokewidth = float(style["stroke-width"])
		fillcolour = None
		if element.hasAttribute("fill"): fillcolour = self._parse_svg_colour(element.getAttribute("fill"))
		if "fill" in style: fillcolour = self._parse_svg_colour(style["fill"])
		fillalpha = 1.0
		if element.hasAttribute("fill-opacity"): fillalpha = float(element.getAttribute("fill-opacity"))
		if "fill-opacity" in style: fillalpha = float(style["fill-opacity"])
		if not fillcolour is None: fillcolour = fillcolour+[fillalpha]
		points = self._parse_svg_points(element.getAttribute("points"))
		return [(
			Polygon(points, strokecolour, strokewidth, fillcolour),
			( min([p[0] for p in points]), max([p[0] for p in points]),
				min([p[1] for p in points]), max([p[1] for p in points]) )
		)]

	def _handle_svg_rect(self,element):
		style = {}
		if element.hasAttribute("style"): style = self._parse_svg_styles(element.getAttribute("style"))
		strokecolour = [0,0,0]
		if element.hasAttribute("stroke"): strokecolour = self._parse_svg_colour(element.getAttribute("stroke"))
		if "stroke" in style: strokcolour = self._parse_svg_colour(style["stroke"])
		if not strokecolour is None: strokecolour = strokecolour+[1.0]
		strokewidth = 1.0
		if element.hasAttribute("stroke-width"): strokewidth = float(element.getAttribute("stroke-width"))
		if "stroke-width" in style: strokewidth = float(style["stroke-width"])
		fillcolour = None
		if element.hasAttribute("fill"): fillcolour = self._parse_svg_colour(element.getAttribute("fill"))
		if "fill" in style: fillcolour = self._parse_svg_colour(style["fill"])
		fillalpha = 1.0
		if element.hasAttribute("fill-opacity"): fillalpha = float(element.getAttribute("fill-opacity"))
		if "fill-opacity" in style: fillalpha = float(style["fill-opacity"])
		if not fillcolour is None: fillcolour = fillcolour+[fillalpha]
		x = 0.0
		if element.hasAttribute("x"): x = float(element.getAttribute("x"))
		y = 0.0
		if element.hasAttribute("y"): y = float(element.getAttribute("y"))
		width = float(element.getAttribute("width"))
		height = float(element.getAttribute("height"))
		return [(
			 Rectangle((x,y),(width,height),strokecolour,strokewidth,fillcolour),
			 ( x, x+width, y, y+height )
		)]
	
	def _handle_svg_circle(self,element):
		style = {}
		if element.hasAttribute("style"): style = self._parse_svg_styles(element.getAttribute("style"))
		strokecolour = [0,0,0]
		if element.hasAttribute("stroke"): strokecolour = self._parse_svg_colour(element.getAttribute("stroke"))
		if "stroke" in style: strokcolour = self._parse_svg_colour(style["stroke"])
		if not strokecolour is None: strokecolour = strokecolour+[1.0]
		strokewidth = 1.0
		if element.hasAttribute("stroke-width"): strokewidth = float(element.getAttribute("stroke-width"))
		if "stroke-width" in style: strokewidth = float(style["stroke-width"])
		fillcolour = None
		if element.hasAttribute("fill"): fillcolour = self._parse_svg_colour(element.getAttribute("fill"))
		if "fill" in style: fillcolour = self._parse_svg_colour(style["fill"])
		fillalpha = 1.0
		if element.hasAttribute("fill-opacity"): fillalpha = float(element.getAttribute("fill-opacity"))
		if "fill-opacity" in style: fillalpha = float(style["fill-opacity"])
		if not fillcolour is None: fillcolour = fillcolour+[fillalpha]
		cx = 0.0
		if element.hasAttribute("cx"): cx = float(element.getAttribute("cx"))
		cy = 0.0
		if element.hasAttribute("cy"): cy = float(element.getAttribute("cy"))
		radius = float(element.getAttribute("r"))
		return [(
			Circle((cx,cy),radius,strokecolour,strokewidth,fillcolour),
			( cx-radius, cx+radius, cy-radius, cy+radius ) 
		)]
	
	def _handle_svg_ellipse(self,element):
		style = {}
		if element.hasAttribute("style"): style = self._parse_svg_styles(element.getAttribute("style"))
		strokecolour = [0,0,0]
		if element.hasAttribute("stroke"): strokecolour = self._parse_svg_colour(element.getAttribute("stroke"))
		if "stroke" in style: strokcolour = self._parse_svg_colour(style["stroke"])
		if not strokecolour is None: strokecolour = strokecolour+[1.0]
		strokewidth = 1.0
		if element.hasAttribute("stroke-width"): strokewidth = float(element.getAttribute("stroke-width"))
		if "stroke-width" in style: strokewidth = float(style["stroke-width"])
		fillcolour = None
		if element.hasAttribute("fill"): fillcolour = self._parse_svg_colour(element.getAttribute("fill"))
		if "fill" in style: fillcolour = self._parse_svg_colour(style["fill"])
		fillalpha = 1.0
		if element.hasAttribute("fill-opacity"): fillalpha = float(element.getAttribute("fill-opacity"))
		if "fill-opacity" in style: fillalpha = float(style["fill-opacity"])
		if not fillcolour is None: fillcolour = fillcolour+[fillalpha]
		cx = 0.0
		if element.hasAttribute("cx"): cx = float(element.getAttribute("cx"))
		cy = 0.0
		if element.hasAttribute("cy"): cy = float(element.getAttribute("cy"))
		radx = float(element.getAttribute("rx"))
		rady = float(element.getAttribute("ry"))
		return [( 
			Ellipse((cx,cy),(radx,rady),strokecolour,strokewidth,fillcolour),
			( cx-radx, cx+radx, cy-rady, cy+rady )
		)]


# Renderers

class PygameRenderer(object):
			
	def render(self,target,vector,pos,scale):
		# calculate origin
		topleft = ( int(pos[0]-vector.size[0]*scale/2), int(pos[1]-vector.size[1]*scale/2) )
		
		# paint canvas rectangle
		if not vector.fillcolour is None:
			pygame.draw.rect(target, self._colour(vector.fillcolour),
				( topleft, (int(vector.size[0]*scale),int(vector.size[1]*scale)) ))
				
		# paint components
		for c in vector.components:
			getattr(self,"_do_"+type(c).__name__)(target,c,topleft,scale)
			
	def _do_Line(self,target,line,topleft,scale):
		pygame.draw.line(target, self._colour(line.strokecolour),
			( int(topleft[0]+line.start[0]*scale), int(topleft[1]+line.start[1]*scale) ),
			( int(topleft[0]+line.end[0]*scale), int(topleft[1]+line.end[1]*scale) ), 
			int(line.strokewidth*scale) )
			
	def _do_Polyline(self,target,polyline,topleft,scale):
		pygame.draw.lines(target, self._colour(polyline.strokecolour), False,
			map(lambda p: ( int(topleft[0]+p[0]*scale), int(topleft[1]+p[1]*scale) ), polyline.points), 
			int(polyline.strokewidth*scale))
			
	def _do_Polygon(self,target,polygon,topleft,scale):
		points = map(lambda p: ( int(topleft[0]+p[0]*scale), int(topleft[1]+p[1]*scale) ), polygon.points)
		if not polygon.fillcolour is None:
			pygame.draw.polygon(target, self._colour(polygon.fillcolour),points, 0)
		if not polygon.strokecolour is None and polygon.strokewidth > 0:
			pygame.draw.polygon(target, self._colour(polygon.strokecolour),points,int(polygon.strokewidth*scale))
			
	def _do_Rectangle(self,target,rectangle,topleft,scale):
		rect = ( ( int(topleft[0]+rectangle.topleft[0]*scale), int(topleft[1]+rectangle.topleft[1]*scale) ),
			(int(rectangle.size[0]*scale),int(rectangle.size[1]*scale)) )
		if not rectangle.fillcolour is None:
			pygame.draw.rect(target, self._colour(rectangle.fillcolour), rect, 0)
		if not rectangle.strokecolour is None and rectangle.strokewidth > 0:
			pygame.draw.rect(target, self._colour(rectangle.strokecolour), rect, int(rectangle.strokewidth*scale))
			
	def _do_Circle(self,target,circle,topleft,scale):
		centre = ( int(topleft[0]+circle.centre[0]*scale), int(topleft[1]+circle.centre[1]*scale) )
		radius = int(circle.radius*scale)
		if not circle.fillcolour is None:
			pygame.draw.circle(target, self._colour(circle.fillcolour), centre, radius, 0)
		if not circle.strokecolour is None and circle.strokewidth > 0:
			pygame.draw.circle(target, self._colour(circle.strokecolour), centre, radius, int(circle.strokewidth*scale))
	
	def _do_Ellipse(self,target,ellipse,topleft,scale):
		topleft = ( int(topleft[0]+ellipse.centre[0]*scale-ellipse.radii[0]*scale),
			int(topleft[1]+ellipse.centre[1]*scale-ellipse.radii[1]*scale) )
		size = ( int(ellipse.radii[0]*2*scale), int(ellipse.radii[1]*2*scale) )
		rect = ( topleft, size )
		if not ellipse.fillcolour is None:
			pygame.draw.ellipse(target, self._colour(ellipse.fillcolour), rect, 0)
		if not ellipse.strokecolour is None and ellipse.strokewidth > 0:
			pygame.draw.ellipse(target, self._colour(ellipse.strokecolour), rect, int(ellipse.strokewidth*scale))
			
	def _colour(self,val):
		return [int(x*255) for x in val]


def load(filepath):
	if filepath.endswith(".xml"):
		return SvgReader().load(filepath)
	else:
		raise ValueError("Cannot open %s" % filepath)


def make_renderer(type):
	if type == RENDERER_PYGAME:
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
		
		renderer.render(screen, v, (160,120), 0.25)
		renderer.render(screen, v, (480,120), 0.5)
		renderer.render(screen, v, (160,360), 1.0)
		renderer.render(screen, v, (480,360), 2.0)
		
		a += 0.1
		scale = 0.3 + (math.sin(a)/2.0+0.5) * 10.0
		renderer.render(screen, v, (320,240), scale )
		
		fpstext = font.render("fps: %d" % clock.get_fps(), True, (255,255,255))
		screen.blit(fpstext,(10,10))
		
		pygame.display.flip()
		clock.tick(60)

