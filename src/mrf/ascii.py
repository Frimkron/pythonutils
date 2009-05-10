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
"""

class Canvas(object):
	"""
	Class facilitating ascii art by allowing characters at arbitrary coordinates to
	be set and then the full character space be printed out line by line.
	"""
	
	def __init__(self):
		self.clear()
		
	def clear(self):
		"""
		Clears the canvas
		"""
		self.grid = {}
		self.width = 0
		self.height = 0
		
	def set(self, x, y, char):
		"""
		Sets the position at x,y to the given character
		"""
		self.grid[(x,y)] = char
		if x >= self.width:
			self.width = x+1
		if y >= self.height:
			self.height = y+1
	
	def get(self, x, y):
		"""
		Returns the character at position x,y
		"""
		if self.grid.has_key((x,y)):
			return self.grid[(x,y)]
		else:
			return ' '
			
	def write(self, x,y, text, maxlength=-1):
		"""
		Writes a sequence of characters into the space, starting at x,y and writing 
		left to right. maxlength can be specified to cut short the text at a maximum
		length
		"""
		i = 0
		for c in text:
			if maxlength!=-1 and i>=maxlength:
				break
			self.set(x,y,c)
			x+=1
			i+=1
	
	def render(self):
		"""
		Returns a string representation of the full canvas
		"""
		str = ""
		for j in range(self.height):
			for i in range(self.width):		
				str += self.get(i,j)
			str += "\n"
		return str
			
	def print_out(self):
		"""
		Prints the full canvas
		"""
		print self.render()
