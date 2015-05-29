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
        
        
if __name__ == "__main__":    
    import unittest
    import sys
    import doctest
    
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


    doctest.testmod()        
    unittest.main()
