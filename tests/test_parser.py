from mrf.parser import *
import unittest

def delve(item, path):
    curr = item
    for n in path.split("/"):
        if n[0] in "0123456789":
            curr = curr.children[int(n)]
        else:
            curr = getattr(curr,n)
    return curr


class TestReParser(unittest.TestCase):
    
    def setUp(self):
        self.parser = ReParser()
    
    def testChars(self):
        tree = self.parser.parse_re("a")
        self.assertEquals("expression()",str(tree))
        self.assertEquals("term()",str(delve(tree,"0")))
        self.assertEquals("character(a)",str(delve(tree,"0/0")))
        tree = self.parser.parse_re("\+")
        self.assertEquals("character(+)",str(delve(tree,"0/0")))
    
    def testQuantifiers(self):
        tree = self.parser.parse_re("a?")
        self.assertEquals("character(a)",str(delve(tree,"0/0")))
        self.assertEquals("quantifier((0, 1))",str(delve(tree,"0/1")))
        tree = self.parser.parse_re("a+")
        self.assertEquals("quantifier((1, -1))",str(delve(tree,"0/1")))
        tree = self.parser.parse_re("a*")
        self.assertEquals("quantifier((0, -1))",str(delve(tree,"0/1")))
        tree = self.parser.parse_re("a{2}")
        self.assertEquals("quantifier((2, 2))",str(delve(tree,"0/1")))
        tree = self.parser.parse_re("a{2,3}")
        self.assertEquals("quantifier((2, 3))",str(delve(tree,"0/1")))
        tree = self.parser.parse_re("a{2,}")
        self.assertEquals("quantifier((2, -1))",str(delve(tree,"0/1")))
        self.assertRaises(ParseError, self.parser.parse_re, "+")

        
    def testSets(self):
        tree = self.parser.parse_re("[ab]")
        self.assertEquals("set()",str(delve(tree,"0/0")))
        self.assertEquals("character(a)",str(delve(tree,"0/0/0")))
        self.assertEquals("character(b)",str(delve(tree,"0/0/1")))
        tree = self.parser.parse_re("[^a]")
        self.assertEquals("character(a)",str(delve(tree,"0/0/0")))
        self.assertEquals(True, delve(tree,"0/0/negate"))
        self.assertRaises(ParseError, self.parser.parse_re, "[a")
        
    def testGroups(self):
        tree = self.parser.parse_re("(a|b)")
        self.assertEquals("group()",str(delve(tree,"0/0")))
        self.assertEquals("expression()",str(delve(tree,"0/0/0")))
        self.assertEquals("term()",str(delve(tree,"0/0/0/0")))
        self.assertEquals("character(a)",str(delve(tree,"0/0/0/0/0")))
        self.assertEquals("character(b)",str(delve(tree,"0/0/1/0/0")))
        self.assertRaises(ParseError, self.parser.parse_re, "(")


class TestNfa(unittest.TestCase):

    def testConstruction(self):
        nfa = NfAutomaton()
        self.assertEquals(0, len(nfa.get_states()))
        nfa.add_state("one")
        self.assert_("one" in nfa.get_states() and len(nfa.get_states())==1)
        nfa.set_start_state("one")
        self.assertEquals("one", nfa.get_start_state())
        nfa.add_end_state("two")
        self.assert_("two" in nfa.get_states() and len(nfa.get_states())==2)
        self.assert_("two" in nfa.end_states and len(nfa.end_states)==1)
        nfa.add_trans("one", "two", ["a","b"])
        self.assertEquals(2, len(nfa.get_transitions()))
        self.assert_(("one","two","a") in nfa.get_transitions())
        self.assert_(("one","two","b") in nfa.get_transitions())
        
    def testMakeDfa(self):
        nfa = NfAutomaton()
        nfa.add_state("one")
        nfa.add_state("two")
        nfa.add_end_state("three")
        nfa.set_start_state("one")
        nfa.add_trans("one","two",[NfAutomaton.EMPTY])
        nfa.add_trans("two","three",["a"])
        nfa.add_trans("two","one",["a"])
        dfa = nfa.make_dfa()
        self.assertEquals(2, len(dfa.get_states()))

        
class TestDfa(unittest.TestCase):

    def testConstruction(self):
        dfa = DfAutomaton()
        dfa.add_state("one")
        dfa.add_state("two")
        dfa.add_state("three")
        dfa.add_trans("one","two",["a"])
        dfa.add_trans("one","three",["a"])
        self.assertEquals(1, len(dfa.get_transitions()))
        
    def testMove(self):
        dfa = DfAutomaton()            
        dfa.add_state("one")
        dfa.set_start_state("one")
        dfa.add_end_state("two")
        dfa.add_trans("one","two",["a"])
        self.assertRaises(StateError,dfa.move,"a")
        dfa.reset()
        self.assertRaises(StateError,dfa.move,"b")
        self.assertEquals(False,dfa.is_at_end())
        dfa.move("a")
        self.assertEquals(True,dfa.is_at_end())

        
class TestReCompiler(unittest.TestCase):

    def setUp(self):
        self.parser = ReParser()
        self.compiler = ReCompiler()
        
    def testCharacter(self):
        dfa = self.compiler.make_dfa(self.parser.parse_re("a"))
        self.assertEquals(2,len(dfa.get_states()))
        self.assertEquals(1,len(dfa.get_transitions()))
        states = dfa.get_states()
        self.assert_((states[0],states[1],"a") in dfa.get_transitions())
        dfa.reset()
        self.assertEquals(False,dfa.is_at_end())
        self.assertRaises(StateError,dfa.move,"b")
        dfa.move("a")
        self.assertEquals(True,dfa.is_at_end())
        
    def testAnyCharacter(self):
        dfa = self.compiler.make_dfa(self.parser.parse_re("."))
        self.assertEquals(2, len(dfa.get_states()))
        states = dfa.get_states()
        self.assert_(len(dfa.get_transitions()) > 1)
        self.assert_((states[0],states[1],"!") in dfa.get_transitions())
        dfa.reset()
        self.assertEquals(False,dfa.is_at_end())
        dfa.move("~")
        self.assertEquals(True,dfa.is_at_end())
        
    def testSet(self):
        dfa = self.compiler.make_dfa(self.parser.parse_re("[ab]"))
        self.assertEquals(2,len(dfa.get_states()))
        self.assertEquals(2,len(dfa.get_transitions()))
        dfa.reset()
        self.assertEquals(False,dfa.is_at_end())
        self.assertRaises(StateError,dfa.move,"c")
        dfa.move("a")
        self.assertEquals(True,dfa.is_at_end())
        dfa.reset()
        dfa.move("b")
        self.assertEquals(True,dfa.is_at_end())
        
    def testGroup(self):
        dfa = self.compiler.make_dfa(self.parser.parse_re("(ab|c)"))
        self.assertEquals(4,len(dfa.get_states()))
        self.assertEquals(3,len(dfa.get_transitions()))
        dfa.reset()
        self.assertEquals(False,dfa.is_at_end())
        self.assertRaises(StateError,dfa.move,"b")
        dfa.move("a")
        self.assertEquals(False,dfa.is_at_end())
        dfa.move("b")
        self.assertEquals(True,dfa.is_at_end())
        dfa.reset()
        dfa.move("c")
        self.assertEquals(True,dfa.is_at_end())
        
    def testTerm(self):
        dfa = self.compiler.make_dfa(self.parser.parse_re("a?"))
        self.assertEquals(2,len(dfa.get_states()))
        self.assertEquals(1,len(dfa.get_transitions()))
        dfa.reset()
        self.assertEquals(True, dfa.is_at_end())
        self.assertRaises(StateError,dfa.move,"b")
        dfa.move("a")
        self.assertEquals(True, dfa.is_at_end())
        self.assertRaises(StateError,dfa.move,"a")
        
        dfa = self.compiler.make_dfa(self.parser.parse_re("a+"))
        self.assertEquals(2, len(dfa.get_states()))
        self.assertEquals(2, len(dfa.get_transitions()))
        dfa.reset()
        self.assertEquals(False, dfa.is_at_end())
        self.assertRaises(StateError, dfa.move, "b")
        dfa.move("a")
        self.assertEquals(True, dfa.is_at_end())
        dfa.move("a")
        self.assertEquals(True, dfa.is_at_end())
        
        dfa = self.compiler.make_dfa(self.parser.parse_re("a*"))
        self.assertEquals(2, len(dfa.get_states()))
        self.assertEquals(2, len(dfa.get_transitions()))
        dfa.reset()
        self.assertEquals(True, dfa.is_at_end())
        self.assertRaises(StateError, dfa.move, "b")
        dfa.move("a")
        self.assertEquals(True, dfa.is_at_end())
        dfa.move("a")
        self.assertEquals(True, dfa.is_at_end())
        
        dfa = self.compiler.make_dfa(self.parser.parse_re("a{2}"))
        self.assertEquals(3, len(dfa.get_states()))
        self.assertEquals(2, len(dfa.get_transitions()))
        dfa.reset()
        self.assertEquals(False, dfa.is_at_end())
        self.assertRaises(StateError, dfa.move, "b")
        dfa.move("a")
        self.assertEquals(False, dfa.is_at_end())
        dfa.move("a")
        self.assertEquals(True, dfa.is_at_end())
        self.assertRaises(StateError, dfa.move, "a")
        
        dfa = self.compiler.make_dfa(self.parser.parse_re("a{2,3}"))
        self.assertEquals(4, len(dfa.get_states()))
        self.assertEquals(3, len(dfa.get_transitions()))
        dfa.reset()
        self.assertEquals(False, dfa.is_at_end())
        self.assertRaises(StateError, dfa.move, "b")
        dfa.move("a")
        self.assertEquals(False, dfa.is_at_end())
        dfa.move("a")
        self.assertEquals(True, dfa.is_at_end())
        dfa.move("a")
        self.assertEquals(True, dfa.is_at_end())
        self.assertRaises(StateError, dfa.move, "a")
        
        dfa = self.compiler.make_dfa(self.parser.parse_re("a{2,}"))
        self.assertEquals(3, len(dfa.get_states()))
        self.assertEquals(3, len(dfa.get_transitions()))
        dfa.reset()
        self.assertEquals(False, dfa.is_at_end())
        self.assertRaises(StateError, dfa.move, "b")
        dfa.move("a")
        self.assertEquals(False, dfa.is_at_end())
        dfa.move("a")
        self.assertEquals(True, dfa.is_at_end())
        dfa.move("a")
        self.assertEquals(True, dfa.is_at_end())
        
    def testCombination(self):
        dfa = self.compiler.make_dfa(self.parser.parse_re("([ab]+|c{2})*"))
        dfa.reset()
        self.assertEquals(True,dfa.is_at_end())
        dfa.move("a")            
        self.assertEquals(True, dfa.is_at_end())
        dfa.move("b")
        self.assertEquals(True, dfa.is_at_end())
        dfa.move("a")
        self.assertEquals(True,dfa.is_at_end())
        dfa.reset()
        dfa.move("c")
        self.assertEquals(False, dfa.is_at_end())
        self.assertRaises(StateError, dfa.move, "a")
        dfa.move("c")
        self.assertEquals(True, dfa.is_at_end())
        dfa.move("c")
        self.assertEquals(False, dfa.is_at_end())

        
class TestLexer(unittest.TestCase):

    def testConstruction(self):
        l = Lexer([
            ("ex","x"),
            ("number","[0-9]"),
            ("hex","0x[0-9A-F]+")
        ])
        l.prepare("1x90x0x0")
        tokens = [x for x in l]
        self.assertEquals(6,len(tokens))
        self.assertEquals(["number","ex","number","hex","ex","number"],
                [x.type for x in tokens])
        self.assertEquals(["1","x","9","0x0","x","0"],
                [x.data for x in tokens])
        l.prepare("0x99q")
        l.next()
        self.assertRaises(SyntaxError,l.next)
                
    def testCustomClass(self):
    
        class Foo(Token):
            def __str__(self):
                return "{%s}" % Token.__str__(self)
    
        l = Lexer([
            ("ex","x"),
            ("number","[0-9]"),
            ("hex","0x[0-9A-F]+",Foo)
        ])            
        l.prepare("x00xFF")
        tokens = [x for x in l]
        self.assertEquals("ex(x)",str(tokens[0]))
        self.assertEquals("number(0)",str(tokens[1]))
        self.assertEquals("{hex(0xFF)}",str(tokens[2]))
        
    def testCallbacks(self):
        
        def cb(state_info, type, data, clazz):
            return clazz(type,data[1:-1])
            
        l = Lexer([
            ("whitespace","( +|\t+)",None,Lexer.cb_ignore),
            ("indent","\n\t*",None,Lexer.cb_indent),
            ("node","n"),
            ("name","\"[a-zA-Z0-9]*\"",None,cb)
        ])
        l.prepare("""n "foo"
	n "bar"     
	n "wah"
		n "fah"  
			n "nah"
	n "gah"                
"""
        )
        tokens = [x.type for x in l]
        self.assertEquals(["node","name",
            "indent","node","name","node","name",
            "indent","node","name",
            "indent","node","name",
            "unindent","unindent","node","name",
            "unindent"], tokens)

        
class TestRuleParser(unittest.TestCase):

    def testConstruction(self):
        p = RuleParser()
        t = p.parse_rule("S -> A b | c")
        self.assertEquals(("nonterminal","S"), (delve(t,"0/0/type"),delve(t,"0/0/data")))
        self.assertEquals(("nonterminal","A"), (delve(t,"1/0/0/type"),delve(t,"1/0/0/data")))
        self.assertEquals(("terminal","b"), (delve(t,"1/0/1/type"),delve(t,"1/0/1/data")))
        self.assertEquals(("terminal","c"), (delve(t,"1/1/0/type"),delve(t,"1/1/0/data")))


class TestParserItem(unittest.TestCase):
    
    def testConstructon(self):
        rules = {
            "0" : ("S",("A","b"))
        }
        i = ParserItem(rules, "0", 0)
        self.assertEquals("A",i.get_next_symbol())
        i2 = i.make_next_item()
        self.assertEquals("b",i2.get_next_symbol())
        i3 = i2.make_next_item()
        self.assertEquals(True, i3.is_end())


class TestItemSet(unittest.TestCase):

    def setUp(self):
    
        self.rules = {
            "0": ("S",("A","b"))
        }
        self.i = ParserItem(self.rules,"0",0)
        self.i2 = ParserItem(self.rules,"0",2)
        self.i3 = ParserItem(self.rules,"0",2)
        self.s = ItemSet()

    def testAdding(self):
        self.s.add(self.i)
        self.s.add(self.i2)
        self.assertEquals(2,len(self.s.items))            
        self.s.add(self.i3)
        self.assertEquals(2,len(self.s.items))
    
    def testLookup(self):
        self.s.add(self.i)
        self.s.add(self.i2)
        self.assertEquals(1,len(self.s.lookup["A"]))
        self.assertEquals("A",self.s.lookup["A"][0].get_next_symbol())
        
    def testEndItems(self):
        self.s.add(self.i)
        self.assertEquals(0,len(self.s.end_rules))
        self.s.add(self.i2)
        self.assertEquals(1,len(self.s.end_rules))


class TestLRParser(unittest.TestCase):

    def setUp(self):
    
        self.l = Lexer([
            ("one","1"),
            ("plus","\+")
        ])
        self.p = LrParser([
            "S -> E",
            "E -> E plus B | B",
            "B -> one"
        ])
        
    def testParsing(self):
        self.l.prepare("1+1+1")
        t = self.p.parse(self.l)
        self.assertEquals("one",delve(t,"0/0/0/0/type"))
        self.assertEquals("plus",delve(t,"0/1/type"))
        self.assertEquals("one",delve(t,"0/2/0/type"))
        self.assertEquals("plus",delve(t,"1/type"))
        self.assertEquals("one",delve(t,"2/0/type"))
        
    def testCustomClasses(self):
    
        class Foo(ParserSymbol):
            def __str__(self):
                return "{%s}" % ParserSymbol.__str__(self)
     
        self.p = LrParser([
            "S -> E",
            "E -> E plus B | B",
            ("B -> one", Foo)
        ])
        self.l.prepare("1+1+1")
        t = self.p.parse(self.l)
        self.assertEquals("E()",str(delve(t,"0")))
        self.assertEquals("{B()}",str(delve(t,"0/2")))


""" 
class One(Token):
    def eval(self):
        return 1
class Zero(Token):
    def eval(self):
        return 0
class Plus(Token):
    def eval(self,a,b):
        return a + b
class Times(Token):
    def eval(self,a,b):
        return a * b
class Bee(ParserSymbol):
    def eval(self):
        return self.children[0].eval()
class Eee(ParserSymbol):
    def eval(self):
        if len(self.children)>1:
            return self.children[1].eval(
                    self.children[0].eval(),self.children[2].eval())
        else:
            return self.children[0].eval()
class Ess(ParserSymbol):
    def eval(self):
        return self.children[0].eval()

l = Lexer([
    ("times","\*", Times),
    ("plus","\+", Plus),
    ("one","1", One),
    ("zero","0", Zero)
])

l.prepare(sys.argv[1])

p = LrParser([
    ("S -> E", Ess),
    ("E -> E times B | E plus B | B", Eee),
    ("B -> one | zero", Bee)
])

tree = p.parse(l)
print_re_tree(tree)

print "result: %d" % tree.eval()
"""

