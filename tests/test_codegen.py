from mrf.codegen import *
from mrf.codegen import _FunctionBuilder, _BlockStatement, _FunctionBuilderInterface, _StatementBuilder
import unittest
import sys


class MockFunctionBuilder(object):

    def __init__(self,statement=None):
        self.statement = statement
        self.combined = []
        self.created = []
        
    def statement_combined(self,stmt):
        self.combined.append(stmt)
        
    def check_combined(self,testcase,vals):
        testcase.assertEquals(len(vals),len(self.combined))
        for i,c in enumerate(self.combined):
            testcase.assertIs(vals[i],c)

    def create_statement(self,name):
        self.created.append(name)
        return self.statement
        
    def start_if(self,val):
        self.created.append("if "+repr(val))
        
    def start_elif(self,val):
        self.created.append("elif "+repr(val))
        
    def start_else(self):
        self.created.append("else")
        
    def start_while(self,val):
        self.created.append("while "+repr(val))
        
    def start_for(self,tval,sval):
        self.created.append("for "+repr(tval)+" in "+repr(sval))
        
    def start_try(self):
        self.created.append("try")
        
    def start_except(self,eval,tval):
        self.created.append("except "+repr(eval)+" as "+repr(tval))    
    
    def start_finally(self):
        self.created.append("finally")
    
    def start_with(self, pairs):
        self.created.append("with "+repr(pairs))
    
    def end_block(self):
        self.created.append("end")
        
    def check_created(self,testcase,vals):
        testcase.assertEquals(len(vals),len(self.created))
        for i,c in enumerate(self.created):
            testcase.assertEquals(vals[i],c)


class Test_StatementBuilder(unittest.TestCase):

    if sys.version_info < (2,7):
        def assertIs(self, a,b):
            self.assertTrue(a is b)

    def setUp(self):
        self.o = MockFunctionBuilder()
        self.s = _StatementBuilder(self.o,"foobar")
        self.t = _StatementBuilder(MockFunctionBuilder(),"blah")

    def test_repr(self):
        self.assertEquals("foobar",repr(self.s))
        
    def test_get_attribute(self):
        a = self.s.yadda
        self.assertIs(self.s, a)
        self.assertEquals("foobar.yadda",repr(self.s))
        
    def test_get_existing_attribute(self):
        a = self.s._owner
        self.assertIs(self.o,a)
        self.assertEquals("foobar",repr(self.s))
        
    def test_set_attribute(self):
        self.s.yadda = 5
        self.assertEquals("foobar.yadda = 5", repr(self.s))
        
    def test_set_existing_attribute(self):
        self.s._owner = None
        self.assertEquals(None, self.s._owner)
        self.assertEquals("foobar", repr(self.s))
        
    def test_set_attribute_statement(self):
        self.s.yadda = self.t
        self.assertEquals("foobar.yadda = blah", repr(self.s))
        self.o.check_combined(self,[self.t])
        
    def test_is(self):
        self.s.is_("blah")
        self.assertEquals("foobar is 'blah'", repr(self.s))
        
    def test_is_statement(self):
        self.s.is_(self.t)
        self.assertEquals("foobar is blah", repr(self.s))
        self.o.check_combined(self,[self.t])
        
    def test_is_not(self):
        self.s.is_not_(False)
        self.assertEquals("foobar is not False", repr(self.s))
    
    def test_is_not_statement(self):
        self.s.is_not_(self.t)
        self.assertEquals("foobar is not blah",repr(self.s))
        self.o.check_combined(self,[self.t])
        
    def test_and(self):
        self.s.and_(5.0)
        self.assertEquals("foobar and 5.0", repr(self.s))
        
    def test_and_statement(self):
        self.s.and_(self.t)
        self.assertEquals("foobar and blah", repr(self.s))
        self.o.check_combined(self,[self.t])
        
    def test_or(self):
        self.s.or_([42])
        self.assertEquals("foobar or [42]", repr(self.s))
        
    def test_or_statement(self):
        self.s.or_(self.t)
        self.assertEquals("foobar or blah", repr(self.s))
        self.o.check_combined(self,[self.t])

    def test_attr(self):
        self.s.attr_("_owner")
        self.assertEquals("foobar._owner", repr(self.s))
            
    def test_call(self):
        self.s(42,69,foo="bar")
        self.assertEquals("foobar(42,69,foo='bar')", repr(self.s))
        
    def test_call_statement(self):
        self.s(weh=self.t)
        self.assertEquals("foobar(weh=blah)", repr(self.s))
        self.o.check_combined(self,[self.t])
        
    def test_less_than(self):
        self.s < 99
        self.assertEquals("foobar < 99",repr(self.s))
        
    def test_less_than_statement(self):
        self.s < self.t
        self.assertEquals("foobar < blah", repr(self.s))
        self.o.check_combined(self,[self.t])
        
    def test_less_equal(self):
        self.s <= 69
        self.assertEquals("foobar <= 69", repr(self.s))
        
    def test_less_equal_statement(self):
        self.s <= self.t
        self.assertEquals("foobar <= blah", repr(self.s))
        self.o.check_combined(self,[self.t])
        
    def test_greater_than(self):
        self.s > "lol"
        self.assertEquals("foobar > 'lol'",repr(self.s))
        
    def test_greater_than_statement(self):
        self.s >= self.t
        self.assertEquals("foobar >= blah",repr(self.s))
        self.o.check_combined(self,[self.t])
        
    def test_greater_equal(self):
        self.s >= 777
        self.assertEquals("foobar >= 777", repr(self.s))
        
    def test_greater_equal_statement(self):
        self.s >= self.t
        self.assertEquals("foobar >= blah", repr(self.s))
        self.o.check_combined(self,[self.t])
        
    def test_get_item(self):
        v = self.s["cake"]
        self.assertIs(self.s, v)
        self.assertEquals("foobar['cake']", repr(self.s))
        
    def test_get_item_slice(self):
        v = self.s[1:2:3]
        self.assertIs(self.s, v)
        self.assertEquals("foobar[1:2:3]", repr(self.s))
        
    def test_get_item_slice_blanks(self):
        v = self.s[::]
        self.assertIs(self.s, v)
        self.assertEquals("foobar[::]", repr(self.s))
        
    def test_get_item_statement(self):
        v = self.s[self.t]
        self.assertIs(self.s,v)
        self.assertEquals("foobar[blah]", repr(self.s))
        self.o.check_combined(self,[self.t])
        
    def test_set_item(self):
        self.s[999] = ":D"
        self.assertEquals("foobar[999] = ':D'", repr(self.s))
        
    def test_set_item_slice(self):
        self.s[1:2:3] = "XD"
        self.assertEquals("foobar[1:2:3] = 'XD'", repr(self.s))
        
    def test_set_item_slice_blanks(self):
        self.s[::] = ":|"
        self.assertEquals("foobar[::] = ':|'", repr(self.s))
        
    def test_set_item_statement(self):
        u = _StatementBuilder(MockFunctionBuilder(),"yadda")
        self.s[self.t] = u
        self.assertEquals("foobar[blah] = yadda",repr(self.s))
        self.o.check_combined(self,[u,self.t])

    def test_contains(self):
        42 in self.s
        self.assertEquals("42 in foobar", repr(self.s))
        
    def test_contains_statement(self):
        self.t in self.s
        self.assertEquals("blah in foobar", repr(self.s))
        self.o.check_combined(self,[self.t])

    def test_add(self):
        self.s + 0xFF
        self.assertEquals("foobar + 255", repr(self.s))
        
    def test_add_statement(self):
        self.s + self.t
        self.assertEquals("foobar + blah", repr(self.s))
        self.o.check_combined(self,[self.t])
            
    def test_sub(self):
        self.s - ";)"
        self.assertEquals("foobar - ';)'", repr(self.s))
    
    def test_sub_statement(self):
        self.s - self.t
        self.assertEquals("foobar - blah", repr(self.s))
        self.o.check_combined(self,[self.t])

    def test_mul(self):
        self.s * 0.5
        self.assertEquals("foobar * 0.5", repr(self.s))
        
    def test_mul_statement(self):
        self.s * self.t
        self.assertEquals("foobar * blah", repr(self.s))
        self.o.check_combined(self,[self.t])
    
    def test_floordiv(self):
        self.s // 7
        self.assertEquals("foobar // 7", repr(self.s))
        
    def test_floordiv_statement(self):
        self.s // self.t
        self.assertEquals("foobar // blah", repr(self.s))
        self.o.check_combined(self,[self.t])
    
    def test_div(self):
        self.s / 1337
        self.assertEquals("foobar / 1337", repr(self.s))
        
    def test_div_statement(self):
        self.s / self.t
        self.assertEquals("foobar / blah", repr(self.s))
        self.o.check_combined(self,[self.t])

    def test_mod(self):
        self.s % {}
        self.assertEquals("foobar % {}", repr(self.s))
        
    def test_mod_statement(self):
        self.s % self.t
        self.assertEquals("foobar % blah", repr(self.s))
        self.o.check_combined(self,[self.t])
        
    def test_pow(self):
        self.s ** 6
        self.assertEquals("foobar ** 6", repr(self.s))
        
    def test_pow_statement(self):
        self.s ** self.t
        self.assertEquals("foobar ** blah", repr(self.s))
        self.o.check_combined(self,[self.t])

    def test_left_shift(self):
        self.s << 16
        self.assertEquals("foobar << 16", repr(self.s))

    def test_left_shift_statement(self):
        self.s << self.t
        self.assertEquals("foobar << blah", repr(self.s))
        self.o.check_combined(self,[self.t])

    def test_right_shift(self):
        self.s >> 50
        self.assertEquals("foobar >> 50", repr(self.s))
        
    def test_right_shift_statement(self):
        self.s >> self.t
        self.assertEquals("foobar >> blah", repr(self.s))
        self.o.check_combined(self,[self.t])
        
    def test_bit_and(self):
        self.s & 9
        self.assertEquals("foobar & 9", repr(self.s))
    
    def test_bit_and_statement(self):
        self.s & self.t
        self.assertEquals("foobar & blah",repr(self.s))
        self.o.check_combined(self,[self.t])
        
    def test_bit_or(self):
        self.s | "!"
        self.assertEquals("foobar | '!'", repr(self.s))
        
    def test_bit_or_statement(self):
        self.s | self.t
        self.assertEquals("foobar | blah", repr(self.s))
        self.o.check_combined(self,[self.t])

    def test_bit_xor(self):
        self.s ^ 666
        self.assertEquals("foobar ^ 666", repr(self.s))
        
    def test_bit_xor_statement(self):
        self.s ^ self.t
        self.assertEquals("foobar ^ blah", repr(self.s))
        self.o.check_combined(self,[self.t])

    def test_iadd(self):
        ss = self.s
        self.s += 7
        self.assertEquals("foobar += 7", repr(ss))
        
    def test_iadd_statement(self):
        ss = self.s
        self.s += self.t
        self.assertEquals("foobar += blah", repr(ss))
        self.o.check_combined(self,[self.t])
        
    def test_isub(self):
        ss = self.s
        self.s -= 8
        self.assertEquals("foobar -= 8", repr(ss))
        
    def test_isub_statement(self):
        ss = self.s
        self.s -= self.t
        self.assertEquals("foobar -= blah", repr(ss))
        self.o.check_combined(self,[self.t])

    def test_imul(self):
        ss = self.s
        self.s *= 8.0
        self.assertEquals("foobar *= 8.0", repr(ss))
        
    def test_imul_statement(self):
        ss = self.s
        self.s *= self.t
        self.assertEquals("foobar *= blah", repr(ss))
        self.o.check_combined(self,[self.t])

    def test_ifloordiv(self):
        ss = self.s
        self.s //= 9
        self.assertEquals("foobar //= 9", repr(ss))
        
    def test_ifloordiv_statement(self):
        ss = self.s
        self.s //= self.t
        self.assertEquals("foobar //= blah", repr(ss))
        self.o.check_combined(self,[self.t])

    def test_idiv(self):
        ss = self.s
        self.s / 4
        self.assertEquals("foobar / 4", repr(ss))
        
    def test_idiv_statement(self):
        ss = self.s
        self.s / self.t
        self.assertEquals("foobar / blah", repr(ss))
        self.o.check_combined(self,[self.t])

    def test_imod(self):
        ss = self.s
        self.s %= 2
        self.assertEquals("foobar %= 2", repr(ss))
        
    def test_imod_statement(self):
        ss = self.s
        self.s %= self.t
        self.assertEquals("foobar %= blah", repr(ss))
        self.o.check_combined(self,[self.t])
        
    def test_ipow(self):
        ss = self.s
        self.s **= 10
        self.assertEquals("foobar **= 10", repr(ss))

    def test_ipow_statement(self):
        ss = self.s
        self.s **= self.t
        self.assertEquals("foobar **= blah", repr(ss))
        self.o.check_combined(self,[self.t])

    def test_ileft(self):
        ss = self.s
        self.s <<= 5
        self.assertEquals("foobar <<= 5", repr(ss))
        
    def test_ileft_statement(self):
        ss = self.s
        self.s <<= self.t
        self.assertEquals("foobar <<= blah", repr(ss))
        self.o.check_combined(self,[self.t])
        
    def test_iright(self):
        ss = self.s
        self.s >>= 77
        self.assertEquals("foobar >>= 77", repr(ss))
        
    def test_iright_statement(self):
        ss = self.s
        self.s >>= self.t
        self.assertEquals("foobar >>= blah", repr(ss))
        self.o.check_combined(self,[self.t])
        
    def test_ibitand(self):
        ss = self.s
        self.s &= 43
        self.assertEquals("foobar &= 43", repr(ss))
        
    def test_ibitand_statement(self):
        ss = self.s
        self.s &= self.t
        self.assertEquals("foobar &= blah", repr(ss))
        self.o.check_combined(self,[self.t])
        
    def test_ibitor(self):
        ss = self.s
        self.s |= 3
        self.assertEquals("foobar |= 3", repr(ss))

    def test_ibitor_statement(self):
        ss = self.s
        self.s |= self.t
        self.assertEquals("foobar |= blah", repr(ss))
        self.o.check_combined(self,[self.t])

    def test_ibitxor(self):
        ss = self.s
        self.s ^= 7
        self.assertEquals("foobar ^= 7", repr(ss))

    def test_ibitxor_statement(self):
        ss = self.s
        self.s ^= self.t
        self.assertEquals("foobar ^= blah", repr(ss))
        self.o.check_combined(self,[self.t])

    def test_neg(self):
        -self.s
        self.assertEquals("-foobar", repr(self.s))
        
    def test_pos(self):
        +self.s
        self.assertEquals("+foobar", repr(self.s))
        
    def test_invert(self):
        ~self.s
        self.assertEquals("~foobar", repr(self.s))


class MockStatement(object):
    def __init__(self,val=""):
        self.val = val
    def __repr__(self):
        return self.val


class TestFunctionBuilderInterface(unittest.TestCase):

    if sys.version_info < (2,7):
        def assertIs(self,a,b):
            self.assertTrue(a is b)

    def setUp(self):
        self.s = MockStatement()
        self.o = MockFunctionBuilder(self.s)
        self.i = _FunctionBuilderInterface(self.o)

    def test_get_attribute(self):
        s = self.i.foo
        self.assertIs(self.s,s)
        self.o.check_created(self,["foo"])
        
    def test_get_attribute_special(self):
        for n in ("assert","pass","del","print","return","yield","raise","break",
                "continue","import","global","exec"):
            self.s = MockStatement()
            self.o = MockFunctionBuilder(self.s)
            self.i = _FunctionBuilderInterface(self.o)
            s = getattr(self.i, n+"_")
            self.assertIs(self.s,s)
            self.o.check_created(self,[n])
    
    def test_set_attribute(self):
        self.i.foo = "bar"    
        self.o.check_created(self,["foo = 'bar'"])

    def test_set_existing_attribute(self):
        self.i._owner = "bar"
        self.o.check_created(self,[])
        
    def test_brackets(self):
        s = self.i.b_(77)
        self.assertIs(self.s, s)
        self.o.check_created(self,["( 77 )"])
        
    def test_brackets_statement(self):
        t = _StatementBuilder(self.o,"foo")
        s = self.i.b_(t)
        self.assertIs(self.s, s)
        self.o.check_created(self,["( foo )"])
        self.o.check_combined(self,[t])
            
    def test_lit(self):
        s = self.i.lit_("hi")
        self.assertIs(self.s, s)
        self.o.check_created(self,["'hi'"])
            
    def test_not(self):
        s = self.i.not_(20)
        self.assertIs(self.s, s)
        self.o.check_created(self,["not 20"])
            
    def test_not_statement(self):
        t = _StatementBuilder(self.o,"foo")
        s = self.i.not_(t)
        self.assertIs(self.s,s)
        self.o.check_created(self,["not foo"])
        self.o.check_combined(self,[t])

    def test_if(self):
        with self.i.if_(5):
            pass
        self.o.check_created(self,["if 5","end"])
    
    def test_elif(self):
        with self.i.elif_(5.0):
            pass
        self.o.check_created(self,["elif 5.0","end"])
        
    def test_else(self):
        with self.i.else_():
            pass
        self.o.check_created(self,["else","end"])
        
    def test_while(self):
        with self.i.while_(99):
            pass
        self.o.check_created(self,["while 99","end"])
        
    def test_for(self):
        with self.i.for_(4, "foo"):
            pass
        self.o.check_created(self,["for 4 in 'foo'","end"])
        
    def test_try(self):
        with self.i.try_():
            pass
        self.o.check_created(self,["try","end"])
        
    def test_except(self):
        with self.i.except_(69,":|"):
            pass
        self.o.check_created(self,["except [69] as ':|'","end"])
        
    def test_except_no_args(self):
        with self.i.except_():
            pass
        self.o.check_created(self,["except [] as None","end"])
        
    def test_except_no_target(self):
        with self.i.except_(8008135):
            pass
        self.o.check_created(self,["except [8008135] as None","end"])

    def test_except_two_exceptions(self):
        with self.i.except_((123,456),789):
            pass
        self.o.check_created(self,["except [123, 456] as 789","end"])

    def test_finally(self):
        with self.i.finally_():
            pass
        self.o.check_created(self,["finally","end"])

    def test_with(self):
        with self.i.with_(1,"2",3.0,[1,1,1,1]):
            pass
        self.o.check_created(self,["with [(1, '2'), (3.0, [1, 1, 1, 1])]","end"])
        
    def test_with_one_pair(self):
        with self.i.with_("a","b"):
            pass
        self.o.check_created(self,["with [('a', 'b')]","end"])
        
    def test_with_no_target(self):
        with self.i.with_(42):
            pass
        self.o.check_created(self,["with [(42, None)]","end"])
        
    def test_with_pair_no_target(self):
        with self.i.with_(42,None,"foo"):
            pass
        self.o.check_created(self,["with [(42, None), ('foo', None)]","end"])
        
        
class MockInterface(object):
    pass
    
class MockContext(object):
    def __init__(self):
        self.log = []
    def __enter__(self):
        self.log.append("entered")
        return self
    def __exit__(self,a,b,c):
        self.log.append("exited")

class TestFunctionBuilder(unittest.TestCase):

    def is_statement(self,s):
        return isinstance(s,MockStatement)
        
    def make_statement(self,owner,name):
        return MockStatement(name)
        
    def make_block(self,pattern,statements):
        return MockStatement(pattern % tuple(map(repr,statements)))
        
    def make_interface(self,owner):
        return MockInterface()

    def setUp(self):
        self.fb = _FunctionBuilder("foo",[],{},{},{},self.is_statement,
                self.make_statement, self.make_block, self.make_interface)

    def test_basic_build(self):            
        with self.fb:
            self.fb.create_statement("pass")
        self.fb.get_function()()
        
    def test_create(self):
        with self.fb:
            s = self.fb.create_statement("pass")
            self.assertEquals("pass", s.val)
        
    def test_early_create(self):
        with self.assertRaises(FunctionBuilderError):
            self.fb.create_statement("print 5")
        
    def test_late_create(self):
        with self.fb:
            self.fb.create_statement("pass")
        with self.assertRaises(FunctionBuilderError):
            self.fb.create_statement("print 5")
        
    def test_second_with(self):
        with self.fb:
            self.fb.create_statement("pass")
        with self.assertRaises(FunctionBuilderError):
            with self.fb:
                self.fb.create_statement("pass")
                
    def test_early_get(self):    
        with self.assertRaises(FunctionBuilderError):        
            self.fb.get_function()

    def test_statement_combined(self):
        with self.fb:
            self.fb.create_statement("a = [1,2,3]")
            s = self.fb.create_statement("a = 'lol'")
            self.fb.statement_combined(s)
            self.fb.create_statement("return a")
        f = self.fb.get_function()
        self.assertEquals([1,2,3], f())
        
    def test_early_statement_combined(self):
        with self.assertRaises(FunctionBuilderError):
            self.fb.statement_combined(MockStatement("foo"))
    
    def test_late_statement_combined(self):
        with self.fb:
            self.fb.create_statement("pass")
        with self.assertRaises(FunctionBuilderError):
            self.fb.statement_combined(MockStatement("foo"))
            
    def test_args(self):
        self.fb = _FunctionBuilder("foo",["alpha","beta"],{},{},{},self.is_statement,
                self.make_statement, self.make_block, self.make_interface)
        with self.fb:
            self.fb.create_statement("return alpha + beta")
        f = self.fb.get_function()
        self.assertEquals(3, f(1,2))
        self.assertEquals("XD", f("X","D"))
        
    def test_keyword_args(self):
        self.fb = _FunctionBuilder("foo",[],{"alpha":1,"beta":2},{},{},self.is_statement,
                self.make_statement, self.make_block, self.make_interface)
        with self.fb:
            self.fb.create_statement("return alpha + beta")
        f = self.fb.get_function()
        self.assertEquals(3, f())
        self.assertEquals(6, f(4))
        self.assertEquals(9, f(5,4))
        self.assertEquals(5, f(beta=3,alpha=2))
        
    def test_scope(self):
        glob = { "alpha": 7, "gamma": 9 }
        self.fb = _FunctionBuilder("foo",[],{},glob,{},self.is_statement,
                self.make_statement, self.make_block, self.make_interface)
        with self.fb:
            self.fb.create_statement("return alpha + gamma")
        f = self.fb.get_function()
        self.assertEquals(16, f())
        
    def test_compile_error(self):
        with self.assertRaises(SyntaxError):
            with self.fb:
                self.fb.create_statement("return 'unclosed ")
            self.fb.get_function()()
            
    def test_interface(self):
        with self.fb as f:
            self.fb.create_statement("pass")
            self.assertEquals(MockInterface, type(f))
            
    def test_start_if(self):            
        self.fb = _FunctionBuilder("foo",[],{},{},{},self.is_statement,
                self.make_statement, self.make_block, self.make_interface)
        with self.fb:
            self.fb.start_if(True)
            self.fb.create_statement("return True")
        self.assertEquals(True, self.fb.get_function()())
        
        self.fb = _FunctionBuilder("foo",[],{},{},{},self.is_statement,
                self.make_statement, self.make_block, self.make_interface)
        with self.fb:
            self.fb.start_if(False)
            self.fb.create_statement("return True")
        self.assertEquals(None, self.fb.get_function()())

    def test_start_if_statement(self):
        self.fb = _FunctionBuilder("foo",["val"],{},{},{},self.is_statement,
            self.make_statement, self.make_block, self.make_interface)
        with self.fb:
            self.fb.start_if(self.fb.create_statement("val"))
            self.fb.create_statement("return True")
        f = self.fb.get_function()
        self.assertEquals(True, f(True))
        self.assertEquals(None, f(False))
        
    def test_early_start_if(self):
        with self.assertRaises(FunctionBuilderError):
            self.fb.start_if("blah")
            
    def test_late_start_if(self):
        with self.fb:
            self.fb.create_statement("pass")
        with self.assertRaises(FunctionBuilderError):
            self.fb.start_if("blah")
            
    def test_end_block(self):
        with self.fb:
            self.fb.start_if(False)
            self.fb.create_statement("return False")
            self.fb.end_block()
            self.fb.create_statement("return True")
        self.assertEquals(True, self.fb.get_function()())
            
    def test_early_end_block(self):
        with self.assertRaises(FunctionBuilderError):
            self.fb.end_block()
            
    def test_late_end_block(self):
        with self.fb:
            self.fb.create_statement("pass")
        with self.assertRaises(FunctionBuilderError):
            self.fb.end_block()
            
    def test_start_else(self):
        self.fb = _FunctionBuilder("foo",["val"],{},{},{},self.is_statement,
                self.make_statement, self.make_block, self.make_interface)
        with self.fb:
            self.fb.start_if(self.fb.create_statement("val"))
            self.fb.create_statement("return True")
            self.fb.end_block()
            self.fb.start_else()
            self.fb.create_statement("return False")
        f = self.fb.get_function()
        self.assertEquals(True, f(True))
        self.assertEquals(False, f(False))
        
    def test_early_start_else(self):
        with self.assertRaises(FunctionBuilderError):
            self.fb.start_else()
            
    def test_late_start_else(self):
        with self.fb:
            self.fb.create_statement("pass")
        with self.assertRaises(FunctionBuilderError):
            self.fb.start_else()
            
    def test_start_elif(self):
        with self.fb:
            self.fb.start_if(False)
            self.fb.create_statement("return True")
            self.fb.end_block()
            self.fb.start_elif(True)
            self.fb.create_statement("return False")
        self.assertEquals(False, self.fb.get_function()())
        
    def test_start_elif_statement(self):
        self.fb = _FunctionBuilder("foo",["val"],{},{},{},self.is_statement,
                self.make_statement, self.make_block, self.make_interface)
        with self.fb:
            self.fb.start_if(self.fb.create_statement("val == 1"))
            self.fb.create_statement("return True")
            self.fb.end_block()
            self.fb.start_elif(self.fb.create_statement("val == 2"))
            self.fb.create_statement("return False")
            self.fb.end_block()
        f = self.fb.get_function()
        self.assertEquals(True, f(1))
        self.assertEquals(False, f(2))
        self.assertEquals(None, f(3))
        
    def test_early_start_elif(self):
        with self.assertRaises(FunctionBuilderError):
            self.fb.start_elif(True)
            
    def test_late_start_elif(self):
        with self.fb:
            self.fb.create_statement("pass")
        with self.assertRaises(FunctionBuilderError):
            self.fb.start_elif(True)

    def test_start_while(self):
        with self.fb:
            self.fb.start_while(True)
            self.fb.create_statement("return True")
        self.assertEquals(True, self.fb.get_function()())
        
    def test_start_while_statement(self):
        with self.fb:
            self.fb.create_statement("i=0")
            self.fb.start_while(self.fb.create_statement("i<3"))
            self.fb.create_statement("i+=1")
            self.fb.end_block()
            self.fb.create_statement("return i")
        self.assertEquals(3, self.fb.get_function()())
        
    def test_early_start_while(self):
        with self.assertRaises(FunctionBuilderError):
            self.fb.start_while(True)
            
    def test_late_start_while(self):
        with self.fb:
            self.fb.create_statement("pass")
        with self.assertRaises(FunctionBuilderError):
            self.fb.start_while(True)

    def test_start_for(self):
        with self.fb:
            self.fb.create_statement("a = 0")
            self.fb.start_for(self.fb.create_statement("i"),(1,2,3))
            self.fb.create_statement("a += 1")
            self.fb.end_block()
            self.fb.create_statement("return a")
        self.assertEquals(3, self.fb.get_function()())
        
    def test_start_for_statement(self):
        with self.fb:
            self.fb.create_statement("a = 0")
            self.fb.start_for(self.fb.create_statement("i"),self.fb.create_statement("list((1,2,3,4))"))
            self.fb.create_statement("a += 1")
            self.fb.end_block()
            self.fb.create_statement("return a")
        self.assertEquals(4, self.fb.get_function()())
        
    def test_early_start_for(self):
        with self.assertRaises(FunctionBuilderError):
            self.fb.start_for(None,None)
    
    def test_late_start_for(self):
        with self.fb:
            self.fb.create_statement("pass")
        with self.assertRaises(FunctionBuilderError):
            self.fb.start_for(None,None)

    def test_start_try_start_except(self):
        with self.fb:
            self.fb.start_try()
            self.fb.create_statement("[][1]")
            self.fb.end_block()
            self.fb.start_except([],None)
            self.fb.create_statement("return True")
        self.assertEquals(True, self.fb.get_function()())
        
    def test_early_start_try(self):
        with self.assertRaises(FunctionBuilderError):
            self.fb.start_try()
            
    def test_late_start_try(self):
        with self.fb:
            self.fb.create_statement("pass")
        with self.assertRaises(FunctionBuilderError):
            self.fb.start_try()

    def test_start_except_both_args(self):
        with self.fb:
            self.fb.start_try()
            self.fb.create_statement("[][1]")
            self.fb.end_block()
            self.fb.start_except([self.fb.create_statement("IndexError")],
                    self.fb.create_statement("e"))
            self.fb.create_statement("return e")
            self.fb.end_block()
        self.assertEquals(IndexError, type(self.fb.get_function()()))
        
    def test_start_except_both_args_type(self):
        with self.fb:
            self.fb.start_try()
            self.fb.create_statement("[][1]")
            self.fb.end_block()
            self.fb.start_except([self.fb.create_statement("ValueError")],
                    self.fb.create_statement("e"))
            self.fb.create_statement("return e")
            self.fb.end_block()
        with self.assertRaises(IndexError):
            self.fb.get_function()()
            
    def test_start_except_one_arg(self):
        with self.fb:
            self.fb.start_try()
            self.fb.create_statement("[][1]")
            self.fb.end_block()
            self.fb.start_except([self.fb.create_statement("IndexError")],None)
            self.fb.create_statement("return True")
        self.assertEquals(True, self.fb.get_function()())
    
    def test_start_except_two_exceptions(self):
        with self.fb:
            self.fb.start_try()
            self.fb.create_statement("[]['a']")
            self.fb.end_block()
            self.fb.start_except([self.fb.create_statement("IndexError"),self.fb.create_statement("Exception")],
                    self.fb.create_statement("e"))
            self.fb.create_statement("return True")
        self.assertEquals(True, self.fb.get_function()())            
        
    def test_early_start_except(self):
        with self.assertRaises(FunctionBuilderError):
            self.fb.start_except([],None)
            
    def test_late_start_except(self):
        with self.fb:
            self.fb.create_statement("pass")
        with self.assertRaises(FunctionBuilderError):
            self.fb.start_except([],None)

    def test_start_finally(self):
        self.fb = _FunctionBuilder("foo",[],{},{},{},self.is_statement,
                self.make_statement, self.make_block, self.make_interface)
        with self.fb:
            self.fb.start_try()
            self.fb.create_statement("pass")
            self.fb.end_block()
            self.fb.start_finally()
            self.fb.create_statement("return True")
            self.fb.end_block()    
        self.assertEquals(True, self.fb.get_function()())
        
        self.fb = _FunctionBuilder("foo",[],{},{},{},self.is_statement,
                self.make_statement, self.make_block, self.make_interface)
        with self.fb:
            self.fb.start_try()
            self.fb.create_statement("[][1]")
            self.fb.end_block()
            self.fb.start_finally()
            self.fb.create_statement("return True")
            self.fb.end_block()    
        self.assertEquals(True, self.fb.get_function()())
        
    def test_early_start_finally(self):
        with self.assertRaises(FunctionBuilderError):
            self.fb.start_finally()
            
    def test_late_start_finally(self):
        with self.fb:
            self.fb.create_statement("pass")
        with self.assertRaises(FunctionBuilderError):
            self.fb.start_finally()

    def test_start_with(self):
        self.fb = _FunctionBuilder("foo",["context"],{},{},{},self.is_statement,
                self.make_statement, self.make_block, self.make_interface)
        with self.fb:
            self.fb.start_with([[self.fb.create_statement("context"),None]])
            self.fb.create_statement("pass")
        c = MockContext()
        self.fb.get_function()(c)
        self.assertEquals(["entered","exited"], c.log)
        
    def test_start_with_both_args(self):
        self.fb = _FunctionBuilder("foo",["context"],{},{},{},self.is_statement,
                self.make_statement, self.make_block, self.make_interface)
        with self.fb:
            self.fb.start_with([[self.fb.create_statement("context"),self.fb.create_statement("c")]])
            self.fb.create_statement("return c")
        c = MockContext()
        self.assertEquals(c, self.fb.get_function()(c))
        self.assertEquals(["entered","exited"], c.log)

    def test_start_with_two_contexts(self):
        self.fb = _FunctionBuilder("foo",["context1","context2"],{},{},{},self.is_statement,
                self.make_statement, self.make_block, self.make_interface)
        with self.fb:
            self.fb.start_with([[self.fb.create_statement("context1"),None],
                    [self.fb.create_statement("context2"),self.fb.create_statement("c")]])
            self.fb.create_statement("return c")
        c1 = MockContext()
        c2 = MockContext()
        self.assertEquals(c2, self.fb.get_function()(c1,c2))
        self.assertEquals(["entered","exited"], c1.log)
        self.assertEquals(["entered","exited"], c2.log)
        
    def test_early_start_with(self):
        with self.assertRaises(FunctionBuilderError):
            self.fb.start_with([[None,None]])
            
    def test_late_start_with(self):
        with self.fb:
            self.fb.create_statement("pass")
        with self.assertRaises(FunctionBuilderError):
            self.fb.start_with([[None,None]])

