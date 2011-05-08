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

Tree Utils Module

"""

def _get_branches(node):
	# strings cause inf recursion
	if isinstance(node,basestring):
		return []
		
	# check if iterable
	try:
		i = iter(node)
	except TypeError:
		return []
	else:
		return [x for x in i]

def draw_tree(tree, branchstrategy=_get_branches, displaystrategy=str, nodestr="%s\n", indentstr="\t",
		branchstr="- ", linestr="|", halflinestr="'"):
	"""	
	Writes out the structure of a tree to a string. 
	Paraeters:
		tree - the tree to be displayed
		branchstrategy - one-parameter function to use for obtaining each node's children as a sequence 
		displaystrategy - one-parameter function to use for obtaining each node's string representation
		nodestr - string used for displaying each node. Use %s marker for node name
		indentstr - string used to indent branches
		branchstr - string used to prefix each branch
		linestr - string used to show vertical lines for branches
		halflinestr - string used to show half a vertical line for branches
	"""
	return _draw_tree(tree, branchstrategy, displaystrategy, 0, [], 
		nodestr, indentstr, branchstr, linestr, halflinestr)
	
def _draw_tree(tree, brstrat, dispstrat, depth, vlines, nodestr, indentstr, branchstr, linestr, halflinestr):
	
	s = nodestr % dispstrat(tree)
	
	branches = brstrat(tree)
	numbranches = len(branches)
	for i,c in enumerate(branches):
		
		for j in range(depth):
			s += indentstr
			if vlines[j]: s += linestr
		
		s += indentstr
		s += halflinestr if i==numbranches-1 else linestr
		s += branchstr
		s += _draw_tree(c, brstrat, dispstrat, depth+1, vlines+[i!=numbranches-1], nodestr, indentstr,
			branchstr, linestr, halflinestr)
	
	return s
	

if __name__ == "__main__":
	import unittest
	
	class TestDrawTree(unittest.TestCase):
	
		def test_basic(self):
			t = [[1,2],[[3,4],5],8,[6,[7]],9]
			s = draw_tree(t)
			self.assertEquals((
				 "[[1, 2], [[3, 4], 5], 8, [6, [7]], 9]\n"
				+"	|- [1, 2]\n"
				+"	|	|- 1\n"
				+"	|	'- 2\n"
				+"	|- [[3, 4], 5]\n"
				+"	|	|- [3, 4]\n"
				+"	|	|	|- 3\n"
				+"	|	|	'- 4\n"
				+"	|	'- 5\n"
				+"	|- 8\n"
				+"	|- [6, [7]]\n"
				+"	|	|- 6\n"
				+"	|	'- [7]\n"
				+"	|		'- 7\n"
				+"	'- 9\n" ), s)

		def test_string_recursion(self):
			t = "foo"
			s = draw_tree(t)
			self.assertEquals("foo\n", s)
	
		def test_display_strategy(self):
			t = (1,(2,3),4,(5,))
			s = draw_tree(t,displaystrategy=lambda x: "<%s>" % str(x))
			self.assertEquals((
				 "<(1, (2, 3), 4, (5,))>\n"
				+"	|- <1>\n"
				+"	|- <(2, 3)>\n"
				+"	|	|- <2>\n"
				+"	|	'- <3>\n"
				+"	|- <4>\n"
				+"	'- <(5,)>\n"
				+"		'- <5>\n"
			), s)
			
		def _branches(self, x):
			try:
				return list(x)[1:]
			except TypeError:
				return []
			
		def test_branch_strategy(self):
			t = (1,(2,3),4)
			s = draw_tree(t, branchstrategy=self._branches)
			self.assertEquals((
				 "(1, (2, 3), 4)\n"
				+"	|- (2, 3)\n"
				+"	|	'- 3\n"
				+"	'- 4\n"
			), s)
			
		def test_custom_formatting(self):
			t = (1,(2,3),4,(5,6))
			s = draw_tree(t, nodestr="[%s]\n\n", indentstr="  ", linestr=":", halflinestr="`", branchstr="--> ")
			self.assertEquals((
				 "[(1, (2, 3), 4, (5, 6))]\n\n"
				+"  :--> [1]\n\n"
				+"  :--> [(2, 3)]\n\n"
				+"  :  :--> [2]\n\n"
				+"  :  `--> [3]\n\n"
				+"  :--> [4]\n\n"
				+"  `--> [(5, 6)]\n\n"
				+"    :--> [5]\n\n"
				+"    `--> [6]\n\n"
			), s)
	unittest.main()
			
			
			
