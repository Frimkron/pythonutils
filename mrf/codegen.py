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

---------------------------

Code Generation Module


FunctionDefiner
---------------

Facilitates the dynamic generation of functions using an intuitive syntax.
Example:

    >>> d = FunctionDefiner()
    >>> with d.def_("myfunction") as f:
    ...     with f.for_( f.i, f.range(3) ):
    ...         f.print_("Hi")
    ...
    print('Hi')
    >>> myfunction = d.get()
    >>> myfunction()
    Hi
    Hi
    Hi

Def

To define a new function, construct a FunctionDefiner and invoke 'def_' in a
'with' context block. The block delimits the function definition. The context
target variable can then be used to add statements to the function definition.
Finally, the new function can be retrieved by invoking 'get' on the definer.

For example, the following defines a function called 'foo' with a single 'pass' 
statement. The context target 'f' is used to add the statement to the function:

    >>> d = FunctionDefiner()
    >>> with d.def_("foo") as f:
    ...     f.pass_
    ...
    pass
    >>> foo = d.get()

Statements

The context target allows any statement to be added to the function definition.
To begin a statement with a name, simply use the dot operator to request it as 
an attribute. Most unary and binary operators, slicing, indexing, calling etc
can then be performed in the statement and added to the definition.

For example, the following defines a function which returns the sum of the first
two indexes of a list named 'mylist':

    >>> d = FunctionDefiner()
    >>> with d.def_("foo") as f:
    ...     f.mylist = [1,2,3]
    ...     f.return_( f.mylist[0] + f.mylist[1] )
    ... 
    return(mylist[0] + mylist[1])
    >>> foo = d.get()
    >>> foo()
    3
    
Literals
    
Literals can be used in the middle of statements as one might expect, but to
begin a statement with a literal, the 'lit_' function must be used.

For example, the following defines a function which returns the concatenation of
the string 'foo' with string variable 'bar'

    >>> d = FunctionDefiner()
    >>> with d.def_("foo") as f:
    ...     f.bar = "bagh"
    ...     f.return_( f.lit_("foo") + f.bar )
    ...
    return('foo' + bar)
    >>> foo = d.get()
    >>> foo()
    'foobagh'
    
Parameters 

Function parameters can be specified in the 'def_' call. It takes the function name
followed by an optional list of standard argument names, and an optional dictionary
for keyword argument names and default values.

For example, for following function returns the sum of arguments 'a', 'b' and 'c'. 
The last of which has a default value of 5:

    >>> d = FunctionDefiner()
    >>> with d.def_("foo", ["a","b"], {"c": 5}) as f:
    ...     f.return_( f.a + f.b + f.c )
    ...
    return(a + b + c)
    >>> foo = d.get()
    >>> foo(2, 5)
    12
    
Special Functions

Certain operations require a special function to be acheived, including 'return' and
'pass' statements and their ilk, logical 'and' and 'or', 'is' and others. The following
table describes these functions:

    Operation        Function to use
    ---------       ---------------
    logical and     and_
    logical or      or_
    logical not     not_
    is              is_
    is not          is_not_
    parentheses     b_
    assert          assert_
    pass            pass_
    del             del_
    print           print_
    return          return_
    yield           yield_
    raise           raise_
    break           break_
    continue        continue_
    import          import_
    global          global_
    exec            exec_
    
Compound Statements

Flow control statements such as 'if' and 'while' are acheived by using the appropriate
function in a 'with' context block. The block delimits the scope of the statement. 

For example, the following definition includes an 'if-else' statement which returns a 
different value depending on the value of parameter 'x':

    >>> d = FunctionDefiner()
    >>> with d.def_("foo",["x"]) as f:
    ...     with f.if_( f.x ):
    ...         f.return_( True )
    ...     with f.else_():
    ...         f.return_( False )
    ...
    return(True)
    return(False)
    >>> foo = d.get()
    >>> foo(True)
    True
    >>> foo(False)
    False
    
The flow control statement functions and their parameters are described below:

    Statement    Function    Parameters
    ---------    --------    ----------
    if           if_         The statement to branch on
    elif         elif_       The statement to branch on
    else         else_       None
    while        while_      The statement to check
    for          for_        Target statement, sequence statement
    try          try_        None
    except       except_     Exception type statement (optional), target statement (optional)
    finally      finally_    None
    with         with_       Variable list of params of the form A, B, A, B where A is
                             a context object statement and B is a target statement.

Scope

By default, the new function is declared in an empty scope. But the global and local variables
to be made available to the function can be specified using the 'globals' and 'locals' 
parameters of 'def_'. 

For example, the following function adds together the global variables 'alpha' and 'beta':

    >>> alpha = 10
    >>> beta = 6
    >>> d = FunctionDefiner()
    >>> with d.def_("foo",globals=globals()) as f:
    ...     f.return_( f.alpha + f.beta )
    ...
    return(alpha + beta)
    >>> foo = d.get()
    >>> foo()
    16
    
"""

from mrf.structs import iscollection


class FunctionDefiner(object):
    """    
    Wrapper for function builder. 'def_' method can be used to define a new dynamically 
    declared function, and 'get' method can be used to retreive it.
    """

    def __init__(self):
        self.builder = None

    def def_(self,name,args=[],kargs={},globals={},locals={}):
        """    
        Begins the definition of a new dynamically declared function. This should be used 
        in a 'with' statement to delimit the function to define.
        Parameters:
            name    The name of the new function
            args    List of names for standard arguments
            kargs    Dictionary of names and default values for keyword arguments
            globals    The global variable dictionary to give the function access to
            locals    The local variable dictionary to give the function access to
        """
        self.builder = _FunctionBuilder(name,args,kargs,globals,locals)
        return self.builder
        
    def get(self):
        """    
        Returns the last function defined
        """
        return self.builder.get_function()


class FunctionBuilderError(Exception):
    """    
    Raised if the function builder encounters a problem
    """
    pass


class _FunctionBuilder(object):
    """    
    Main class responsible for building a function dynamically. Consists of a list of statements
    at different indentation levels which is added to by _StatementBuilder instances. Should be used
    in a context block - when doing so, a _FunctionBuilderInterface instance is exposed providing 
    the user with a nice interface to declare the function's contents. _FunctionBuilder maintains 
    state and an instance may be used once only to define a single function.
    """
    
    STATE_BEFORE = 0
    STATE_DURING = 1
    STATE_AFTER = 2
    
    def __init__(self, name, args, kargs, globals, locals,
            stmt_tester=lambda s: isinstance(s,_StatementBuilder),
            stmt_factory=lambda s,n: _StatementBuilder(s,n),
            blkstmt_factory=lambda p,s: _BlockStatement(p,s),
            iface_factory=lambda s: _FunctionBuilderInterface(s) ):
        """    
        Initialises the _FunctionBuilder
        Parameters:
            name            The name of the function to define
            args            List of names for standard arguments
            kargs            Dictionary of names and default values for keyword arguments
            globals            Global scope in which to define function
            locals            Local scope in which to define function
            stmt_tester        One-arg function for determining whether a value is a statement builder or not
            stmt_factory    Two-arg function for constructing statement builders. Takes owner and name
            blkstmt_factory    Two-arg function for constructing block statements. Takes pattern and statements
            iface_factory    One-arg function for constructing builder interface
        """
        self.name = name
        self.args = args
        self.kargs = kargs
        self.globals = globals
        self.locals = locals
        self.stmt_tester = stmt_tester
        self.stmt_factory = stmt_factory
        self.blkstmt_factory = blkstmt_factory
        self.iface_factory = iface_factory
        self.indent = 1
        self.state = _FunctionBuilder.STATE_BEFORE
        self.statements = []
        self.function = None
        
    def __enter__(self):
        """    
        Invoked when context entered. Exposes a _FunctionBuilderInterface providing the
        user with a nice interface with which to define the function contents
        """
        if self.state != _FunctionBuilder.STATE_BEFORE:
            raise FunctionBuilderError("Should be no more than one 'with' block")
        self.state = _FunctionBuilder.STATE_DURING
        return self.iface_factory(self)
            
    def create_statement(self,name):
        """    
        Returns a new _StatementBuilder which is appended to the internal statement list.
        This statement is assumed to be on its own line in the function, at the current 
        indentation, until the statement is used as an operand with another _StatementBuilder 
        at which point the statements are merged.
        """
        if self.state != _FunctionBuilder.STATE_DURING:
            raise FunctionBuilderError("Cannot invoke outside of 'with' block")
        sb = self.stmt_factory(self,name)
        self.statements.append((self.indent,sb))
        return sb
        
    def statement_combined(self,statement):
        """    
        Invoked when a _StatementBuilder is used as an operand for another statement. The 
        given statement is no longer assumed to be on its own line in the function definition
        and is removed from the internal statement list. It should have already been
        incorporated into the other statement.
        """
        if self.state != _FunctionBuilder.STATE_DURING:
            raise FunctionBuilderError("Cannot invoke outside of 'with' block")            
        for i,(d,s) in enumerate(self.statements):
            if s is statement:
                del(self.statements[i])
                return
        assert False, "Statement to combine was not found"
                
    def start_if(self,stmt):
        """    
        Begins an "if" block definition, using the given value as the condition expression.
        This may be a _StatementBuilder or any other value with an appropriate "repr" representation.
        The "if" start is added as a statement line and the indentation increased. Subsequent
        statements will be included inside the "if" block until a corresponding "end_block" is 
        invoked.
        """
        if self.state != _FunctionBuilder.STATE_DURING:
            raise FunctionBuilderError("Cannot invoke outside of 'with' block")
        if self.stmt_tester(stmt):
            self.statement_combined(stmt)
        self.statements.append((self.indent,self.blkstmt_factory("if %s :",[stmt])))
        self.indent += 1
        
    def start_elif(self,stmt):
        """    
        Begins an "elif" block definition, using the given value as the condition expression.
        This may be a _StatementBuilder or any other value with an appropriate "repr" representation.
        The "elif" start is added as a statement line and the indentation increased. Subsequent
        statements will be included inside the "elif" block until a corresponding "end_block" is
        invoked.
        """
        if self.state != _FunctionBuilder.STATE_DURING:
            raise FunctionBuilderError("Cannot invoke outside of 'with' block")
        if self.stmt_tester(stmt):
            self.statement_combined(stmt)
        self.statements.append((self.indent,self.blkstmt_factory("elif %s :",[stmt])))
        self.indent += 1
        
    def start_else(self):
        """    
        Begins an "else" block definition. The "else" start is added as a statement line and the
        indentation increased. Subsequent statements will be included inside the "else" block 
        until a corresponding "end_block" is invoked.
        """
        if self.state != _FunctionBuilder.STATE_DURING:
            raise FunctionBuilderError("Cannot invoke outside of 'with' block")            
        self.statements.append((self.indent,self.blkstmt_factory("else :",[])))
        self.indent += 1
        
    def start_while(self,stmt):
        """    
        Begins a "while" block definition, using the given value as the condition expression.
        This may be a _StatementBuilder or any other value with an appropriate "repr" representation.
        The "while" start is added as a statement line and the indentation increased. Subsequent
        statements will be included inside the "while" block until a corresponding "end_block" is
        invoked.
        """
        if self.state != _FunctionBuilder.STATE_DURING:
            raise FunctionBuilderError("Cannot invoke outside of 'with' block")
        if self.stmt_tester(stmt):
            self.statement_combined(stmt)
        self.statements.append((self.indent,self.blkstmt_factory("while %s :",[stmt])))
        self.indent += 1
        
    def start_for(self,varstmt,seqstmt):
        """    
        Begins a "for" block definition, using varstmt as the target expression and seqstmt as 
        the iterable expression. Each may be a _StatementBuilder or any other value with an appropriate 
        "repr" representation. The "for" start is added as a statement line and the indentation increased. 
        Subsequent statements will be included inside the "for" block until a corresponding "end_block" is
        invoked.
        """
        if self.state != _FunctionBuilder.STATE_DURING:
            raise FunctionBuilderError("Cannot invoke outside of 'with' block")
        if self.stmt_tester(varstmt):
            self.statement_combined(varstmt)
        if self.stmt_tester(seqstmt):
            self.statement_combined(seqstmt)
        self.statements.append((self.indent,self.blkstmt_factory("for %s in %s :",[varstmt,seqstmt])))
        self.indent += 1
        
    def start_try(self):
        """    
        Begins an "try" block definition. The "try" start is added as a statement line and the indentation 
        increased. Subsequent statements will be included inside the "try" block until a corresponding 
        "end_block" is invoked.
        """
        if self.state != _FunctionBuilder.STATE_DURING:
            raise FunctionBuilderError("Cannot invoke outside of 'with' block")
        self.statements.append((self.indent,self.blkstmt_factory("try :",[])))
        self.indent += 1
        
    def start_except(self,exstmts,varstmt):
        """    
        Begins an "except" block definition, using exstmt as the exception expression list and varstmt
        as the target expression. Each may be a _StatementBuilder or any other value with an appropriate 
        "repr" representation. They may be emitted by passing as None. The "except" start is added as a 
        statement line and the indentation increased. Subsequent statements will be included inside the 
        "except" block until a corresponding "end_block" is invoked.
        """
        if self.state != _FunctionBuilder.STATE_DURING:
            raise FunctionBuilderError("Cannot invoke outside of 'with' block")
        for ex in exstmts:
            if self.stmt_tester(ex):
                self.statement_combined(ex)
        if varstmt is not None and self.stmt_tester(varstmt):
            self.statement_combined(varstmt)
        if len(exstmts) > 0:
            if varstmt is not None:
                pattern,statements = "except %s as %s :",[tuple(exstmts),varstmt]
            else:
                pattern,statements = "except %s :",[tuple(exstmts)]
        else:
            pattern,statements = "except :",[]
        self.statements.append((self.indent,self.blkstmt_factory(pattern,statements)))
        self.indent += 1
        
    def start_finally(self):
        """    
        Begins a "finally" block definition. The "finally" start is added as a statement line 
        and the indentation increased. Subsequent statements will be included inside the "finally" 
        block until a corresponding "end_block" is invoked.    
        """
        if self.state != _FunctionBuilder.STATE_DURING:
            raise FunctionBuilderError("Cannot invoke outside of 'with' block")
        self.statements.append((self.indent,self.blkstmt_factory("finally :",[])))
        self.indent += 1
        
    def start_with(self,pairs):
        """    
        Begins a "with" block definition, using the given pairs of values as the pairs of context
        object expression and target expression, for the context objects to be entered. None may
        be passed to omit a target expression. Each may be a _StatementBuilder or any other value 
        with an appropriate "repr" representation. The "with" start is added as a statement line 
        and the indentation increased. Subsequent statements will be included inside the "with" 
        block until a corresponding "end_block" is invoked.
        """
        if self.state != _FunctionBuilder.STATE_DURING:
            raise FunctionBuilderError("Cannot invoke outside of 'with' block")
        for o,v in pairs:
            if o is not None and self.stmt_tester(o):
                self.statement_combined(o)
            if v is not None and self.stmt_tester(v):
                self.statement_combined(v)
        patterns = []
        statements = []
        for objstmt,varstmt in pairs:
            if varstmt is not None:
                patterns.append("%s as %s")
                statements.append(objstmt)
                statements.append(varstmt)
            else:
                patterns.append("%s")
                statements.append(objstmt)
        pattern = "with %s :" % ", ".join(patterns)
        self.statements.append((self.indent,self.blkstmt_factory(pattern,statements)))
        self.indent += 1
        
    def end_block(self):
        """    
        Invoked to end the current block definition. The current indentation is decreased and 
        subsequent statements will be added outside of the block.
        """
        if self.state != _FunctionBuilder.STATE_DURING:
            raise FunctionBuilderError("Cannot invoke outside of 'with' block")
        self.indent -= 1
        
    def __exit__(self,extype,exvalue,traceback):
        """    
        Invoked when context is exited. The function is automatically built.
        """
        self.state = _FunctionBuilder.STATE_AFTER
        if extype is None:
            # dont build if there was an exception
            self.function = self.build()
        
    def build(self):
        """    
        Builds the internal statement list into a function definition and attempts to execute
        as python code, creating a new function. Returns the new function.
        """
        if self.state != _FunctionBuilder.STATE_AFTER:
            raise FunctionBuilderError("Must complete 'with' block before building")
        arglist = self.args
        arglist.extend(["%s=%s" % (k,repr(self.kargs[k])) for k in self.kargs])        
        buffer = "def %s (%s):\n" % (self.name, ",".join(arglist))
        for d,s in self.statements:
            buffer += "%s%s\n" % ("\t"*d,repr(s))
        exec buffer in self.globals, self.locals
        return self.locals[self.name]
        
    def get_function(self):
        """    
        Returns the newly-built function
        """
        if self.state != _FunctionBuilder.STATE_AFTER:
            raise FunctionBuilderError("Must complete 'with' block before function can be returned")
        return self.function
    
        
class _BlockStatement(object):
    """    
    Used by _FunctionBuilder to represnt a line beginning a block, such as an "if" line or "while"
    line.
    """
    
    def __init__(self,pattern,statements):
        """    
        Initialisesd the _BlockStatement
        Parameters:
            pattern        a string representing the statement, with %s markers to be filled in
            statements    list of repr-able values to be combined with the pattern. 
        """
        self.pattern = pattern
        self.statements = statements
        
    def __repr__(self):
        return self.pattern % tuple(map(repr,self.statements))
        
                
class _FunctionBuilderInterface(object):
    """    
    Used by _FunctionBuilder to expose a nice interface to the user for definition the function
    statements.
    """

    def __init__(self,owner):
        """    
        Initialises the _FunctionBuilderInterface to serve the given _FunctionBuilder
        """
        self._owner = owner
        
    def __getattr__(self,name):
        """    
        Invoked when an attribute is requested on the object. A new statement is started and its
        _StatementBuilder object is returned, allowing further operators to be chained to build up
        the statement.
        """
        # Functions with trailing underscores are defined to allow special statements to be used
        # even though they are reserved words.
        if name in ("assert_","pass_","del_","print_","return_","yield_","raise_","break_",
                "continue_","import_","global_","exec_"):
            # begin new statement, starting with special statement
            return self._owner.create_statement(name[:-1])
        else:
            # begin new statement, starting with requested name
            return self._owner.create_statement(name)

    def __setattr__(self,name,value):        
        """    
        Invoked when an attribute is assigne to on the object. A new statement is started and its
        _StatementBuilder object is returned, allowing further operators to be chained to build up
        the statement.
        """
        # If the assigned value is a statement, combine it with current statement to remove it from
        # function body.
        if isinstance(value,_StatementBuilder):
            self._owner.statement_combined(value)
    
        # Dummy object is used as workaround for assignment behaviour
        if value is _StatementBuilder.DUMMY:
            pass    
        # special case for existing object attributes
        elif name in ("_owner",):
            super(_FunctionBuilderInterface,self).__setattr__(name,value)
        else:
            # begin new statement, starting with assignment
            return self._owner.create_statement("%s = %s" % (name,repr(value)))
            
        return self    
            
    def b_(self,statement):
        """    
        Defines a pair of parentheses, using the given value as the contents. This may be
        a _StatementBuilder or any other repr-able object. A new statement is started and its
        _StatementBuilder object is returned, allowing further operators to be chained to
        build up the statement.
        """
        if isinstance(statement,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(statement)
        # begin new statement, starting with bracket
        return self._owner.create_statement("( %s )" % repr(statement))
            
    def lit_(self,value):
        """    
        Defines a literal value using the given value which may be any repr-able object. The
        representation of the object is used in the function code as is. This is useful for
        beginning statements with string or int literals, for example, which cannot be accessed
        as attributes. A new statement is started and its _StatementBuilder object is returned,
        allowing further operators to be chained to build up the statement.
        """
        # begin new statement, starting with literal value
        return self._owner.create_statement(repr(value))

    def not_(self,statement):
        """    
        Defines the logical negation of the given value, i.e. "not X" where X is the value.
        This may be a _StatementBuilder or any other repr-able object. A new statement is 
        started and its _StatementBuilder object is returned, allowing further operators to be
        chained to build up the statement.
        """
        if isinstance(statement,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(statement)
        # begin new statement, starting with the statement negation
        return self._owner.create_statement("not %s" % repr(statement))
            
    def if_(self,statement):
        """    
        Begins an "if" block definition, using the given value as the condition expression. 
        This may be a _StatementBuilder or any other repr-able object. Should be used in a 
        "with" context block to delimit the block.
        """
        self._owner.start_if(statement)
        return self

    def elif_(self,statement):
        """    
        Begins an "elif" definition, using the given value as the condition expression. This
        may be a _StatementBuilder or any other repr-able object.  Should be used in a "with" 
        context block to delimit the block.
        """
        self._owner.start_elif(statement)
        return self
        
    def else_(self):
        """    
        Begins an "else" definition. Should be used in a "with" context block to delimit the block.
        """
        self._owner.start_else()
        return self
        
    def while_(self,statement):
        """    
        Begins a "while" definition, using the given value as the condition expression. This
        may be a _StatementBuilder or any other repr-able object. Should be used in a "with"
        context block to delimit the block.    
        """
        self._owner.start_while(statement)
        return self
        
    def for_(self,var,seq):
        """    
        Begins a "for" definition, using the given values as the target expression and sequence
        expressions repectively. Each may be a _StatementBuilder or any other repr-able object.
        Should be used in a "with" context block to delimit the block.
        """
        self._owner.start_for(var,seq)
        return self
        
    def try_(self):
        """    
        Begins a "try" definition. Should be used in a "with" context block to delimit the block.
        """
        self._owner.start_try()
        return self
        
    def except_(self,exceptions=None,var=None):
        """    
        Begins an "except" definition, using the given values as the exception expression(s) and 
        target expression respectively. Each is optional and may be a _StatementBuilder or any 
        other repr-able object. Should be used in a "with" context block to delimit the block.
        To specify multiple exception types, pass a sequence as the first parameter.
        """
        if exceptions is None:
            exceptions = []
        elif not iscollection(exceptions):
            exceptions = [exceptions]
        exceptions = list(exceptions)
        self._owner.start_except(exceptions,var)
        return self
        
    def finally_(self):
        """    
        Begins a "finally" definition. Should be used in a "with" context block to delimit the 
        block.
        """
        self._owner.start_finally()
        return self
        
    def with_(self,*args):
        """    
        Begins a "with" definition. Takes zero or more arguments, pairs of which are used for
        the context object expression and target expression for each context object respectively.
        Each value may be a _StatementBuilder or any other repr-able object. Should be used in a
        "with" context block to delimit the block.
        """
        args = list(args)
        if len(args) % 2 != 0:
            args.append(None)
        self._owner.start_with(zip(args[::2],args[1::2]))
        return self

    def __enter__(self):
        """    
        Invoked when object is entered in "with" context.
        """
        return self
        
    def __exit__(self,extype,exvalue,traceback):
        """    
        Invoked when object is exited in "with" context. This ends the current block definition.
        """
        self._owner.end_block()
        

class _StatementBuilder(object):
    """    
    Used by _FunctionBuilder to construct statements within the function. The object serves as an
    interface to the user for building up the statement.
    """

    class DUMMY(object): pass

    def __init__(self,owner,propname):
        """    
        Initialises the _StatementBuilder with the given owning _FunctionBuilder and the name
        starting the statement.
        """
        self._owner = owner
        self._buffer = propname
        
    def is_(self,other):
        """    
        Defines an "is" expression as part of the statement being built, using the given value 
        as the right hand side. This may be another _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " is %s" % repr(other)
        return self
        
    def is_not_(self,other):
        """    
        Defines an "is not" expressio as part of the statement being built, using the given value
        as the right hand side. This may be another _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " is not %s" % repr(other)
        return self
        
    def and_(self,other):
        """    
        Defines an "and" comparison as part of the statement being built, using the given value
        as the right hand side. This may be another _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " and %s" % repr(other)
        return self
        
    def or_(self,other):
        """    
        Defines an "or" compariso as part of the statement being built, using the given value
        as the right hand side. This may be another _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " or %s" % repr(other)
        return self
        
    def attr_(self,name):
        """    
        Defines an access of the named attribute as part of the statement being built. For use 
        where an attribute already exists, e.g. "is_"
        """
        return self.__getattr__(name)
        
    def __getattr__(self,name):
        """    
        Invoked when an attribute is accessed (if it cannot be found). Allows arbitrary attribute 
        access as part of the statement being built.
        """
        self._buffer += "."+name
        return self

    def __setattr__(self,name,value):
        """    
        Invoked when an attribute is assigned to. Allows arbitrary attribute setting as part
        of the statement being built.
        """
        if isinstance(value,_StatementBuilder):
            # combine the statement, remove from main list
            self._owner.statement_combined(value)
        
        # workaround for behaviour of += and the like
        if value is _StatementBuilder.DUMMY:
            pass    
        # special case for existing attributes
        elif name in ("_owner","_buffer"):
            super(_StatementBuilder,self).__setattr__(name,value)
        else:    
            self._buffer += ".%s = %s" % (name,repr(value))
            
        return self
        
    def __call__(self,*args,**kargs):
        """    
        Invoked when the object is called as a function. Allows method invokation as part
        of the statement being built. Arguments may be other _StatementBuilders or any other
        repr-able objects.
        """
        # combine statements, removing from main list
        for a in args:
            if isinstance(a,_StatementBuilder):
                self._owner.statement_combined(a)
        for k in kargs:
            if isinstance(kargs[k],_StatementBuilder):
                self._owner.statement_combined(kargs[k])
    
        arglist = []
        arglist.extend(map(repr,args))
        arglist.extend(["%s=%s" % (k,repr(kargs[k])) for k in kargs])
        self._buffer += "(%s)" % ",".join(arglist)
        
        return self        
        
    def __repr__(self):
        """    
        Returns the representation of the statement. This is the buffered code as a string.
        """
        return self._buffer    
    
    def __lt__(self, other):
        """    
        Invoked for < comparisons. Allows such comparisons in the statement being built.
        Right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine the statment, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " < %s" % repr(other)
        return self
        
    def __le__(self, other):
        """    
        Invoked for <= comparisons. Allows such comparisons in the statement being built.
        Right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine the statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " <= %s" % repr(other)
        return self
        
    def __eq__(self, other):
        """    
        Invoked for == comparisons. Allows such comparisons in the statement being built.
        Right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine the statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " == %s" % repr(other)
        return self
        
    def __ne__(self, other):
        """    
        Invoked for != comparisons. Allows such comparisons in the statement being built.
        Right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine the statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " != %s" % repr(other)
        return self
        
    def __gt__(self, other):
        """    
        Invoked for > comparisons. Allows such comparisons in the statement being built.
        Right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine the statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " > %s" % repr(other)
        return self
        
    def __ge__(self, other):
        """    
        Invoked for >= comparisons. Allows such comparisons in the statement being built.
        Right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine the statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " >= %s" % repr(other)
        return self
    
    def __getitem__(self,key):
        """    
        Invoked for [] value access or slicing, allowing such accesses as part of the statement 
        being built. The key may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(key,slice):
            # may be a slice object, if slicing
            self._buffer += "[%s:%s:%s]" % (
                repr(key.start) if key.start is not None else "",
                repr(key.stop) if key.stop is not None else "",
                repr(key.step) if key.step is not None else "" )
        else:
            if isinstance(key,_StatementBuilder):
                self._owner.statement_combined(key)
            self._buffer += "[%s]" % repr(key)
        return self
        
    def __setitem__(self,key,value):
        """    
        Invoked for [] value or slice assignment, allowing such assignments as part of the
        statement being built. The key may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(value,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(value)
            
        # workaround for += behaviour and the like
        if value is _StatementBuilder.DUMMY:
            pass
        # may be a slice object, if slicing
        elif isinstance(key,slice):
            self._buffer += "[%s:%s:%s] = %s" % (
                repr(key.start) if key.start is not None else "",
                repr(key.stop) if key.stop is not None else "",
                repr(key.step) if key.step is not None else "",
                repr(value) )            
        else:
            if isinstance(key,_StatementBuilder):
                self._owner.statement_combined(key)
            self._buffer += "[%s] = %s" % (repr(key),repr(value))
            
        return self
        
    def __contains__(self,item):
        """    
        Invoked for "in" comparisons, allowing such comparisons in the statement being built.
        The item being checked for containment within this object may be a _StatementBuilder
        or any other repr-able object.
        """
        if isinstance(item,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(item)            
        self._buffer = "%s in %s" % (repr(item),self._buffer)
        return self

    def __add__(self, other):
        """    
        Invoked for + operations, allowing such operations as part of the statement being built.
        The right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " + %s" % repr(other)
        return self
    
    def __sub__(self, other):
        """    
        Invoked for - operations, allowing such operations as part of the statement being built.
        The right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " - %s" % repr(other)
        return self
        
    def __mul__(self, other):
        """    
        Invoked for * operations, allowing such operations as part of the statement being built.
        The right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " * %s" % repr(other)
        return self
    
    def __floordiv__(self, other):
        """    
        Invoked for // operations, allowing such operations as part of the statement being built.
        The right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " // %s" % repr(other)
        return self
    
    def __mod__(self, other):
        """    
        Invoked for % operations, allowing such operations as part of the statement being built.
        The right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " %% %s" % repr(other)
        return self
        
    def __pow__(self, other):
        """    
        Invoked for ** operations, allowing such operations as part of the statement being built.
        The right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " ** %s" % repr(other)
        return self
        
    def __lshift__(self, other):
        """    
        Invoked for << operations, allowing such operations as part of the statement being built.
        The right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " << %s" % repr(other)
        return self
        
    def __rshift__(self, other):
        """    
        Invoked for >> operations, allowing such operations as part of the statement being built.
        The right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " >> %s" % repr(other)
        return self
        
    def __and__(self, other):
        """    
        Invoked for & operations, allowing such operations as part of the statement being built.
        The right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " & %s" % repr(other)
        return self
        
    def __xor__(self, other):
        """    
        Invoked for ^ operations, allowing such operations as part of the statement being built.
        The right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " ^ %s" % repr(other)
        return self
        
    def __or__(self, other):
        """    
        Invoked for | operations, allowing such operations as part of the statement being built.
        The right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " | %s" % repr(other)
        return self

    def __div__(self, other):
        """    
        Invoked for / operations, allowing such operations as part of the statement being built.
        The right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " / %s" % repr(other)
        return self
        
    def __truediv__(self, other):
        """    
        Invoked for (true) / operations, allowing such operations as part of the statement being
        built. The right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " / %s" % repr(other)
        return self
        
    def __iadd__(self, other):
        """    
        Invoked for += operations, allowing such operations as part of the statement being built.
        The right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " += %s" % repr(other)
        # workaround for re-assignment behaviour
        return _StatementBuilder.DUMMY
        
    def __isub__(self, other):
        """    
        Invoked for -= operations, allowing such operations as part of the statement being built.
        The right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " -= %s" % repr(other)
        # workaround for re-assignment behaviour
        return _StatementBuilder.DUMMY
        
    def __imul__(self, other):
        """    
        Invoked for *= operations, allowing such operations as part of the statement being built.
        The right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " *= %s" % repr(other)
        # workaround for re-assignment behaviour
        return _StatementBuilder.DUMMY
        
    def __idiv__(self, other):
        """    
        Invoked for /= operations, allowing such operations as part of the statement being built.
        The right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " /= %s" % repr(other)
        # workaround for re-assignment behaviour
        return _StatementBuilder.DUMMY
        
    def __itruediv__(self, other):
        """    
        Invoked for (true) /= operations, allowing such operations as part of the statement being built.
        The right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from list
            self._owner.statement_combined(other)
        self._buffer += " /= %s" % repr(other)    
        # workaround for re-assignment behaviour    
        return _StatementBuilder.DUMMY
        
    def __ifloordiv__(self, other):
        """    
        Invoked for //= operations, allowing such operations as part of the statement being built.
        The right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from list
            self._owner.statement_combined(other)
        self._buffer += " //= %s" % repr(other)
        # workaround for re-assignment behaviour
        return _StatementBuilder.DUMMY
        
    def __imod__(self, other):
        """    
        Invoked for %= operations, allowing such operations as part of the statement being built.
        The right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from list
            self._owner.statement_combined(other)
        self._buffer += " %%= %s" % repr(other)
        # workaround for re-assignment behaviour
        return _StatementBuilder.DUMMY
        
    def __ipow__(self, other):
        """    
        Invoked for **= operations, allowing such operations as part of the statement being built.
        The right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from list
            self._owner.statement_combined(other)
        self._buffer += " **= %s" % repr(other)
        # workaround for re-assignment behaviour
        return _StatementBuilder.DUMMY
        
    def __ilshift__(self, other):
        """    
        Invoked for <<= operations, allowing such operations as part of the statement being built.
        The right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " <<= %s" % repr(other)
        # workaround for re-assignment behaviour
        return _StatementBuilder.DUMMY
        
    def __irshift__(self, other):
        """    
        Invoked for >>= operations, allowing such operations as part of the statement being built.
        The right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " >>= %s" % repr(other)
        # workaround for re-assignment behaviour
        return _StatementBuilder.DUMMY
        
    def __iand__(self, other):
        """    
        Invoked for &= operations, allowing such operations as part of the statement being built.
        The right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " &= %s" % repr(other)
        # workaround for re-assignment behaviour
        return _StatementBuilder.DUMMY
        
    def __ixor__(self, other):
        """    
        Invoked for ^= operations, allowing such operations as part of the statement being built.
        The right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statmeent, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " ^= %s" % repr(other)
        # workaround for re-assignment behaviour
        return _StatementBuilder.DUMMY
        
    def __ior__(self, other):
        """    
        Invoked for |= operations, allowing such operations as part of the statement being built.
        The right hand side may be a _StatementBuilder or any other repr-able object.
        """
        if isinstance(other,_StatementBuilder):
            # combine statement, remove from main list
            self._owner.statement_combined(other)
        self._buffer += " |= %s" % repr(other)
        # workaround for re-assignment behaviour
        return _StatementBuilder.DUMMY
        
    def __neg__(self):
        """    
        Invoked when object negated, allowing negations as part of the statement being built.
        """
        self._buffer = "-" + self._buffer
        return self
        
    def __pos__(self):
        """    
        Invoked when object is unary +'d, allowing this as part of the statement being built.
        """
        self._buffer = "+" + self._buffer
        return self
        
    def __invert__(self):
        """    
        Invoked when object is bitwise negated, allowing this as part of the statement being built.
        """
        self._buffer = "~" + self._buffer
        return self
        
        
