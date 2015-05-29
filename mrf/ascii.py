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

Ascii Module

Utilities for handling ascii art
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



def visbar(frac,length=80,start='[',end=']',full='#',empty=' '):
    """    
    Returns a string visualising the given 0-1 value as an ascii bar.
    """
    s = ""
    s += start
    endslen = len(start)+len(end)
    midlen = length-endslen
    if length > endslen:
        for i in range(midlen):
            if float(i)/midlen <= frac:
                s += full
            else:
                s += empty
    s += end
    return s


def barchart(values,labels=None,length=80,vertical=False):
    c = Canvas()
    maxval = max(values)
    endchar = '-' if vertical else '|'
    if not labels is None:
        maxlab = max([len(x) for x in labels])
        barlen = length-maxlab
    else:
        maxlab = 0
        barlen = length

    for i,val in enumerate(values):
        if not labels is None:
            for j,char in enumerate(labels[i]):
                if vertical:
                    c.set(i*2,barlen+j,char)
                else:
                    c.set(j,i,char)
        bar = visbar(float(val)/maxval,length=barlen,start=endchar,end=endchar)
        for j,char in enumerate(bar):
            if vertical:
                c.set(i*2,barlen-j-1,char)
            else:
                c.set(maxlab+j,i,char)
        if vertical:
            for i in range(len(values)):
                c.set(i*2+1,0,endchar)
                c.set(i*2+1,barlen-1,endchar)
    return c.render()
