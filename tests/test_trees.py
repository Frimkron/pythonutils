from mrf.trees import *
import unittest
    
    
class TestDrawTree(unittest.TestCase):

    def test_basic(self):
        t = [[1,2],[[3,4],5],8,[6,[7]],9]
        s = draw_tree(t)
        self.assertEqual((
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
        self.assertEqual("foo\n", s)

    def test_display_strategy(self):
        t = (1,(2,3),4,(5,))
        s = draw_tree(t,displaystrategy=lambda x: "<%s>" % str(x))
        self.assertEqual((
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
        self.assertEqual((
             "(1, (2, 3), 4)\n"
            +"	|- (2, 3)\n"
            +"	|	'- 3\n"
            +"	'- 4\n"
        ), s)
        
    def test_custom_formatting(self):
        t = (1,(2,3),4,(5,6))
        s = draw_tree(t, nodestr="[%s]\n\n", indentstr="  ", linestr=":", halflinestr="`", branchstr="--> ")
        self.assertEqual((
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
        
            
            
