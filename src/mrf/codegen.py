# TODO: unit tests
# TODO: documentation


def def_(name,args=[],kargs={},globals={},locals={}):
	"""	
	Begins the definition of a new dynamically declared function. This should be used 
	in a 'with' statement to delimit the function to define.
	Parameters:
		name	The name of the new function
		args	List of names for standard arguments
		kargs	Dictionary of names and default values for keyword arguments
		globals	The global scope in which to define the function
		locals	The local scope in which to define the function
	"""
	return FunctionBuilder(name,args,kargs,globals,locals)


class FunctionBuilderError(Exception):
	"""	
	Raised if the function builder encounters a problem
	"""
	pass


class FunctionBuilder(object):
	"""	
	Main class responsible for building a function dynamically. Consists of a list of statements
	at different indentation levels which is added to by StatementBuilder instances. Should be used
	in a context block - when doing so, a FunctionBuilderInterface instance is exposed providing 
	the user with a nice interface to declare the function's contents. FunctionBuilder maintains 
	state and an instance may be used once only to define a single function.
	"""
	
	STATE_BEFORE = 0
	STATE_DURING = 1
	STATE_AFTER = 2
	
	def __init__(self,name,args,kargs,globals,locals):
		"""	
		Initialises the FunctionBuilder
		Parameters:
			name	The name of the function to define
			args	List of names for standard arguments
			kargs	Dictionary of names and default values for keyword arguments
			globals	Global scope in which to define function
			locals	Local scope in which to define function
		"""
		self.name = name
		self.args = args
		self.kargs = kargs
		self.globals = globals
		self.locals = locals
		self.indent = 1
		self.state = FunctionBuilder.STATE_BEFORE
		self.statements = []
		
	def __enter__(self):
		"""	
		Invoked when context entered. Exposes a FunctionBuilderInterface providing the
		user with a nice interface with which to define the function contents
		"""
		if self.state != FunctionBuilder.STATE_BEFORE:
			raise FunctionBuilderError("Should be no more than one 'with' block")
		self.state = FunctionBuilder.STATE_DURING
		return FunctionBuilderInterface(self)
			
	def create_statement(self,name):
		"""	
		Returns a new StatementBuilder which is appended to the internal statement list.
		This statement is assumed to be on its own line in the function, at the current 
		indentation, until the statement is used as an operand with another StatementBuilder 
		at which point the statements are merged.
		"""
		if self.state != FunctionBuilder.STATE_DURING:
			raise FunctionBuilderError("Cannot invoke outside of 'with' block")
		sb = StatementBuilder(self,name)
		self.statements.append((self.indent,sb))
		return sb
		
	def statement_combined(self,statement):
		"""	
		Invoked when a StatementBuilder is used as an operand for another statement. The 
		given statement is no longer assumed to be on its own line in the function definition
		and is removed from the internal statement list. It should have already been
		incorporated into the other statement.
		"""
		if self.state != FunctionBuilder.STATE_DURING:
			raise FunctionBuilderError("Cannot invoke outside of 'with' block")
		for i,(d,s) in enumerate(self.statements):
			if s is statement:
				del(self.statements[i])
				break
				
	def start_if(self,stmt):
		"""	
		Begins an "if" block definition, using the given value as the condition expression.
		This may be a StatementBuilder or any other value with an appropriate "repr" representation.
		The "if" start is added as a statement line and the indentation increased. Subsequent
		statements will be included inside the "if" block until a corresponding "end_block" is 
		invoked.
		"""
		if self.state != FunctionBuilder.STATE_DURING:
			raise FunctionBuilderError("Cannot invoke outside of 'with' block")
		if isinstance(stmt,StatementBuilder):
			self.statement_combined(stmt)
		self.statements.append((self.indent,BlockStatement("if %s :",[stmt])))
		self.indent += 1
		
	def start_elif(self,stmt):
		"""	
		Begins an "elif" block definition, using the given value as the condition expression.
		This may be a StatementBuilder or any other value with an appropriate "repr" representation.
		The "elif" start is added as a statement line and the indentation increased. Subsequent
		statements will be included inside the "elif" block until a corresponding "end_block" is
		invoked.
		"""
		if self.state != FunctionBuilder.STATE_DURING:
			raise FunctionBuilderError("Cannot invoke outside of 'with' block")
		if isinstance(stmt,StatementBuilder):
			self.statement_combined(stmt)
		self.statements.append((self.indent,BlockStatement("elif %s :",[stmt])))
		self.indent += 1
		
	def start_else(self):
		"""	
		Begins an "else" block definition. The "else" start is added as a statement line and the
		indentation increased. Subsequent statements will be included inside the "else" block 
		until a corresponding "end_block" is invoked.
		"""
		if self.state != FunctionBuilder.STATE_DURING:
			raise FunctionBuilderError("Cannot invoke outside of 'with' block")			
		self.statements.append((self.indent,BlockStatement("else :",[])))
		self.indent += 1
		
	def start_while(self,stmt):
		"""	
		Begins a "while" block definition, using the given value as the condition expression.
		This may be a StatementBuilder or any other value with an appropriate "repr" representation.
		The "while" start is added as a statement line and the indentation increased. Subsequent
		statements will be included inside the "while" block until a corresponding "end_block" is
		invoked.
		"""
		if self.state != FunctionBuilder.STATE_DURING:
			raise FunctionBuilderError("Cannot invoke outside of 'with' block")
		if isinstance(stmt,StatementBuilder):
			self.statement_combined(stmt)
		self.statements.append((self.indent,BlockStatement("while %s :",[stmt])))
		self.indent += 1
		
	def start_for(self,varstmt,seqstmt):
		"""	
		Begins a "for" block definition, using varstmt as the target expression and seqstmt as 
		the iterable expression. Each may be a StatementBuilder or any other value with an appropriate 
		"repr" representation. The "for" start is added as a statement line and the indentation increased. 
		Subsequent statements will be included inside the "for" block until a corresponding "end_block" is
		invoked.
		"""
		if self.state != FunctionBuilder.STATE_DURING:
			raise FunctionBuilderError("Cannot invoke outside of 'with' block")
		if isinstance(varstmt,StatementBuilder):
			self.statement_combined(varstmt)
		if isinstance(seqstmt,StatementBuilder):
			self.statement_combined(seqstmt)
		self.statements.append((self.indent,BlockStatement("for %s in %s :",[varstmt,seqstmt])))
		self.indent += 1
		
	def start_try(self):
		"""	
		Begins an "try" block definition. The "try" start is added as a statement line and the indentation 
		increased. Subsequent statements will be included inside the "try" block until a corresponding 
		"end_block" is invoked.
		"""
		if self.state != FunctionBuilder.STATE_DURING:
			raise FunctionBuilderError("Cannot invoke outside of 'with' block")
		self.statements.append((self.indent,BlockStatement("try :",[])))
		self.indent += 1
		
	def start_except(self,exstmt,varstmt):
		"""	
		Begins an "except" block definition, using exstmt as the exception expression and varstmt
		as the target expression. Each may be a StatementBuilder or any other value with an appropriate 
		"repr" representation. They may be emitted by passing as None. The "except" start is added as a 
		statement line and the indentation increased. Subsequent statements will be included inside the 
		"except" block until a corresponding "end_block" is invoked.
		"""
		if self.state != FunctionBuilder.STATE_DURING:
			raise FunctionBuilderError("Cannot invoke outside of 'with' block")
		if isinstance(exstmt,StatementBuilder):			
			self.statement_combined(exstmt)
		if varstmt is not None and isinstance(varstmt,StatementBuilder):
			self.statement_combined(varstmt)
		if exstmt is not None:
			if varstmt is not None:
				pattern,statements = "except %s as %s :",[exstmt,varstmt]
			else:
				pattern,statements = "except %s :",[exstmt]
		else:
			pattern,statements = "except :",[]			
		self.statements.append((self.indent,BlockStatement(pattern,statements)))
		self.indent += 1
		
	def start_finally(self):
		"""	
		Begins a "finally" block definition. The "finally" start is added as a statement line 
		and the indentation increased. Subsequent statements will be included inside the "finally" 
		block until a corresponding "end_block" is invoked.	
		"""
		if self.state != FunctionBuilder.STATE_DURING:
			raise FunctionBuilderError("Cannot invoke outside of 'with' block")
		self.statements.append((self.indent,BlockStatement("finally :",[])))
		self.indent += 1
		
	def start_with(self,pairs):
		"""	
		Begins a "with" block definition, using the given pairs of values as the pairs of context
		object expression and target expression, for the context objects to be entered. None may
		be passed to omit a target expression. Each may be a StatementBuilder or any other value 
		with an appropriate "repr" representation. The "with" start is added as a statement line 
		and the indentation increased. Subsequent statements will be included inside the "with" 
		block until a corresponding "end_block" is invoked.
		"""
		if self.state != FunctionBuilder.STATE_DURING:
			raise FunctionBuilderError("Cannot invoke outside of 'with' block")
		for o,v in pairs:
			if o is not None and isinstance(o,StatementBuilder):
				self.statement_combined(o)
			if v is not None and isinstance(v,StatementBuilder):
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
		self.statements.append((self.indent,BlockStatement(pattern,statements)))
		self.indent += 1
		
	def end_block(self):
		"""	
		Invoked to end the current block definition. The current indentation is decreased and 
		subsequent statements will be added outside of the block.
		"""
		if self.state != FunctionBuilder.STATE_DURING:
			raise FunctionBuilderError("Cannot invoke outside of 'with' block")
		self.indent -= 1
		
	def __exit__(self,extype,exvalue,traceback):
		"""	
		Invoked when context is exited
		"""
		self.state = FunctionBuilder.STATE_AFTER
		
	def build(self):
		"""	
		Builds the internal statement list into a function definition and attempts to execute
		as python code, creating a new function. Returns the new function.
		"""
		if self.state != FunctionBuilder.STATE_AFTER:
			raise FunctionBuilderError("Must complete 'with' block before building")
		arglist = self.args
		arglist.extend(["%s=%s" % (k,repr(self.kargs[k])) for k in self.kargs])		
		buffer = "def %s (%s):\n" % (self.name, ",".join(arglist))
		for d,s in self.statements:
			buffer += "%s%s\n" % ("\t"*d,repr(s))
		exec buffer in self.globals, self.locals
		return self.locals[self.name]
	
		
class BlockStatement(object):
	"""	
	Used by FunctionBuilder to represnt a line beginning a block, such as an "if" line or "while"
	line.
	"""
	
	def __init__(self,pattern,statements):
		"""	
		Initialisesd the BlockStatement
		Parameters:
			pattern		a string representing the statement, with %s markers to be filled in
			statements	list of repr-able values to be combined with the pattern. 
		"""
		self.pattern = pattern
		self.statements = statements
		
	def __repr__(self):
		return self.pattern % tuple(map(repr,self.statements))
		
				
class FunctionBuilderInterface(object):
	"""	
	Used by FunctionBuilder to expose a nice interface to the user for definition the function
	statements.
	"""

	def __init__(self,owner):
		"""	
		Initialises the FunctionBuilderInterface to serve the given FunctionBuilder
		"""
		self._owner = owner
		
	def __getattr__(self,name):
		"""	
		Invoked when an attribute is requested on the object. A new statement is started and its
		StatementBuilder object is returned, allowing further operators to be chained to build up
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
		StatementBuilder object is returned, allowing further operators to be chained to build up
		the statement.
		"""
		# If the assigned value is a statement, combine it with current statement to remove it from
		# function body.
		if isinstance(value,StatementBuilder):
			self._owner.statement_combined(value)
	
		# Dummy object is used as workaround for assignment behaviour
		if value is StatementBuilder.DUMMY:
			pass	
		# special case for existing object attributes
		elif name in ("_owner",):
			super(FunctionBuilderInterface,self).__setattr__(name,value)
		else:
			# begin new statement, starting with assignment
			return self._owner.create_statement("%s = %s" % (name,repr(value)))
			
		return self	
			
	def b_(self,statement):
		"""	
		Defines a pair of parentheses, using the given value as the contents. This may be
		a StatementBuilder or any other repr-able object. A new statement is started and its
		StatementBuilder object is returned, allowing further operators to be chained to
		build up the statement.
		"""
		if isinstance(statement,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(statement)
		# begin new statement, starting with bracket
		return self._owner.create_statement("( %s )" % repr(statement))
			
	def lit_(self,value):
		"""	
		Defines a literal value using the given value which may be any repr-able object. The
		representation of the object is used in the function code as is. This is useful for
		beginning statements with string or int literals, for example, which cannot be accessed
		as attributes. A new statement is started and its StatementBuilder object is returned,
		allowing further operators to be chained to build up the statement.
		"""
		# begin new statement, starting with literal value
		return self._owner.create_statement(repr(value))

	def not_(self,statement):
		"""	
		Defines the logical negation of the given value, i.e. "not X" where X is the value.
		This may be a StatementBuilder or any other repr-able object. A new statement is 
		started and its StatementBuilder object is returned, allowing further operators to be
		chained to build up the statement.
		"""
		if isinstance(statement,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(statement)
		# begin new statement, starting with the statement negation
		return self._owner.create_statement("not %s" % repr(statement))
			
	def if_(self,statement):
		"""	
		Begins an "if" block definition, using the given value as the condition expression. 
		This may be a StatementBuilder or any other repr-able object. Should be used in a 
		"with" context block to delimit the block.
		"""
		self._owner.start_if(statement)
		return self

	def elif_(self,statement):
		"""	
		Begins an "elif" definition, using the given value as the condition expression. This
		may be a StatementBuilder or any other repr-able object.  Should be used in a "with" 
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
		may be a StatementBuilder or any other repr-able object. Should be used in a "with"
		context block to delimit the block.	
		"""
		self._owner.start_while(statement)
		return self
		
	def for_(self,var,seq):
		"""	
		Begins a "for" definition, using the given values as the target expression and sequence
		expressions repectively. Each may be a StatementBuilder or any other repr-able object.
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
		
	def except_(self,exception=None,var=None):
		"""	
		Begins an "except" definition, using the given values as the exception expression and 
		target expression respectively. Each is optional and may be a StatementBuilder or any 
		other repr-able object. Should be used in a "with" context block to delimit the block.
		"""
		self._owner.start_except(exception,var)
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
		Each value may be a StatementBuilder or any other repr-able object. Should be used in a
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
		

class StatementBuilder(object):
	"""	
	Used by FunctionBuilder to construct statements within the function. The object serves as an
	interface to the user for building up the statement.
	"""

	class DUMMY(object): pass

	def __init__(self,owner,propname):
		"""	
		Initialises the StatementBuilder with the given owning FunctionBuilder and the name
		starting the statement.
		"""
		self._owner = owner
		self._buffer = propname
		
	def is_(self,other):
		"""	
		Defines an "is" expression as part of the statement being built, using the given value 
		as the right hand side. This may be another StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " is %s" % repr(other)
		return self
		
	def is_not_(self,other):
		"""	
		Defines an "is not" expressio as part of the statement being built, using the given value
		as the right hand side. This may be another StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " is not %s" % repr(other)
		return self
		
	def and_(self,other):
		"""	
		Defines an "and" comparison as part of the statement being built, using the given value
		as the right hand side. This may be another StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " and %s" % repr(other)
		return self
		
	def or_(self,other):
		"""	
		Defines an "or" compariso as part of the statement being built, using the given value
		as the right hand side. This may be another StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
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
		if isinstance(value,StatementBuilder):
			# combine the statement, remove from main list
			self._owner.statement_combined(value)
		
		# workaround for behaviour of += and the like
		if value is StatementBuilder.DUMMY:
			pass	
		# special case for existing attributes
		elif name in ("_owner","_buffer"):
			super(StatementBuilder,self).__setattr__(name,value)
		else:	
			self._buffer += ".%s = %s" % (name,repr(value))
			
		return self
		
	def __call__(self,*args,**kargs):
		"""	
		Invoked when the object is called as a function. Allows method invokation as part
		of the statement being built. Arguments may be other StatementBuilders or any other
		repr-able objects.
		"""
		# combine statements, removing from main list
		for a in args:
			if isinstance(a,StatementBuilder):
				self._owner.statement_combined(a)
		for k in kargs:
			if isinstance(kargs[k],StatementBuilder):
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
		Right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine the statment, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " < %s" % repr(other)
		return self
		
	def __le__(self, other):
		"""	
		Invoked for <= comparisons. Allows such comparisons in the statement being built.
		Right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine the statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " <= %s" % repr(other)
		return self
		
	def __eq__(self, other):
		"""	
		Invoked for == comparisons. Allows such comparisons in the statement being built.
		Right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine the statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " == %s" % repr(other)
		return self
		
	def __ne__(self, other):
		"""	
		Invoked for != comparisons. Allows such comparisons in the statement being built.
		Right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine the statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " != %s" % repr(other)
		return self
		
	def __gt__(self, other):
		"""	
		Invoked for > comparisons. Allows such comparisons in the statement being built.
		Right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine the statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " > %s" % repr(other)
		return self
		
	def __ge__(self, other):
		"""	
		Invoked for >= comparisons. Allows such comparisons in the statement being built.
		Right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine the statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " >= %s" % repr(other)
		return self
	
	def __getitem__(self,key):
		"""	
		Invoked for [] value access or slicing, allowing such accesses as part of the statement 
		being built. The key may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(key,slice):
			# may be a slice object, if slicing
			self._buffer += "[%s:%s:%s]" % (
				repr(key.start) if key.start is not None else "",
				repr(key.stop) if key.stop is not None else "",
				repr(key.step) if key.step is not None else "" )
		else:
			if isinstance(key,StatementBuilder):
				self._owner.statement_combined(key)
			self._buffer += "[%s]" % repr(key)
		return self
		
	def __setitem__(self,key,value):
		"""	
		Invoked for [] value or slice assignment, allowing such assignments as part of the
		statement being built. The key may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(value,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(value)
			
		# workaround for += behaviour and the like
		if value is StatementBuilder.DUMMY:
			pass
		# may be a slice object, if slicing
		elif isinstance(key,slice):
			self._buffer += "[%s:%s:%s] = %s" % (
				repr(key.start) if key.start is not None else "",
				repr(key.stop) if key.stop is not None else "",
				repr(key.step) if key.step is not None else "",
				repr(value) )			
		else:
			if isinstance(key,StatementBuilder):
				self._owner.statement_combined(key)
			self._buffer += "[%s] = %s" % (repr(key),repr(value))
			
		return self
		
	def __contains__(self,item):
		"""	
		Invoked for "in" comparisons, allowing such comparisons in the statement being built.
		The item being checked for containment within this object may be a StatementBuilder
		or any other repr-able object.
		"""
		if isinstance(item,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(item)			
		self._buffer = "%s in %s" % (repr(item),self._buffer)
		return self

	def __add__(self, other):
		"""	
		Invoked for + operations, allowing such operations as part of the statement being built.
		The right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " + %s" % repr(other)
		return self
	
	def __sub__(self, other):
		"""	
		Invoked for - operations, allowing such operations as part of the statement being built.
		The right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " - %s" % repr(other)
		return self
		
	def __mul__(self, other):
		"""	
		Invoked for * operations, allowing such operations as part of the statement being built.
		The right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " * %s" % repr(other)
		return self
	
	def __floordiv__(self, other):
		"""	
		Invoked for // operations, allowing such operations as part of the statement being built.
		The right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " // %s" % repr(other)
		return self
	
	def __mod__(self, other):
		"""	
		Invoked for % operations, allowing such operations as part of the statement being built.
		The right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " %% %s" % repr(other)
		return self
		
	def __pow__(self, other):
		"""	
		Invoked for ** operations, allowing such operations as part of the statement being built.
		The right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " ** %s" % repr(other)
		return self
		
	def __lshift__(self, other):
		"""	
		Invoked for << operations, allowing such operations as part of the statement being built.
		The right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " << %s" % repr(other)
		return self
		
	def __rshift__(self, other):
		"""	
		Invoked for >> operations, allowing such operations as part of the statement being built.
		The right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " >> %s" % repr(other)
		return self
		
	def __and__(self, other):
		"""	
		Invoked for & operations, allowing such operations as part of the statement being built.
		The right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " & %s" % repr(other)
		return self
		
	def __xor__(self, other):
		"""	
		Invoked for ^ operations, allowing such operations as part of the statement being built.
		The right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " ^ %s" % repr(other)
		return self
		
	def __or__(self, other):
		"""	
		Invoked for | operations, allowing such operations as part of the statement being built.
		The right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " | %s" % repr(other)
		return self

	def __div__(self, other):
		"""	
		Invoked for / operations, allowing such operations as part of the statement being built.
		The right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " / %s" % repr(other)
		return self
		
	def __truediv__(self, other):
		"""	
		Invoked for (true) / operations, allowing such operations as part of the statement being
		built. The right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " / %s" % repr(other)
		return self
		
	def __iadd__(self, other):
		"""	
		Invoked for += operations, allowing such operations as part of the statement being built.
		The right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " += %s" % repr(other)
		# workaround for re-assignment behaviour
		return StatementBuilder.DUMMY
		
	def __isub__(self, other):
		"""	
		Invoked for -= operations, allowing such operations as part of the statement being built.
		The right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " -= %s" % repr(other)
		# workaround for re-assignment behaviour
		return StatementBuilder.DUMMY
		
	def __imul__(self, other):
		"""	
		Invoked for *= operations, allowing such operations as part of the statement being built.
		The right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " *= %s" % repr(other)
		# workaround for re-assignment behaviour
		return StatementBuilder.DUMMY
		
	def __idiv__(self, other):
		"""	
		Invoked for /= operations, allowing such operations as part of the statement being built.
		The right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " /= %s" % repr(other)
		# workaround for re-assignment behaviour
		return StatementBuilder.DUMMY
		
	def __itruediv__(self, other):
		"""	
		Invoked for (true) /= operations, allowing such operations as part of the statement being built.
		The right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from list
			self._owner.statement_combined(other)
		self._buffer += " /= %s" % repr(other)	
		# workaround for re-assignment behaviour	
		return StatementBuilder.DUMMY
		
	def __ifloordiv__(self, other):
		"""	
		Invoked for //= operations, allowing such operations as part of the statement being built.
		The right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from list
			self._owner.statement_combined(other)
		self._buffer += " //= %s" % repr(other)
		# workaround for re-assignment behaviour
		return StatementBuilder.DUMMY
		
	def __imod__(self, other):
		"""	
		Invoked for %= operations, allowing such operations as part of the statement being built.
		The right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from list
			self._owner.statement_combined(other)
		self._buffer += " %%= %s" % repr(other)
		# workaround for re-assignment behaviour
		return StatementBuilder.DUMMY
		
	def __ipow__(self, other):
		"""	
		Invoked for **= operations, allowing such operations as part of the statement being built.
		The right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from list
			self._owner.statement_combined(other)
		self._buffer += " **= %s" % repr(other)
		# workaround for re-assignment behaviour
		return StatementBuilder.DUMMY
		
	def __ilshift__(self, other):
		"""	
		Invoked for <<= operations, allowing such operations as part of the statement being built.
		The right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " <<= %s" % repr(other)
		# workaround for re-assignment behaviour
		return StatementBuilder.DUMMY
		
	def __irshift__(self, other):
		"""	
		Invoked for >>= operations, allowing such operations as part of the statement being built.
		The right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " >>= %s" % repr(other)
		# workaround for re-assignment behaviour
		return StatementBuilder.DUMMY
		
	def __iand__(self, other):
		"""	
		Invoked for &= operations, allowing such operations as part of the statement being built.
		The right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " &= %s" % repr(other)
		# workaround for re-assignment behaviour
		return StatementBuilder.DUMMY
		
	def __ixor__(self, other):
		"""	
		Invoked for ^= operations, allowing such operations as part of the statement being built.
		The right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statmeent, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " ^= %s" % repr(other)
		# workaround for re-assignment behaviour
		return StatementBuilder.DUMMY
		
	def __ior__(self, other):
		"""	
		Invoked for |= operations, allowing such operations as part of the statement being built.
		The right hand side may be a StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(other)
		self._buffer += " |= %s" % repr(other)
		# workaround for re-assignment behaviour
		return StatementBuilder.DUMMY
		
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
			
		def check_created(self,testcase,vals):
			testcase.assertEquals(len(vals),len(self.created))
			for i,c in enumerate(self.created):
				testcase.assertEquals(vals[i],c)
	
	
	class TestStatementBuilder(unittest.TestCase):

		if sys.version_info < (2,7):
			def assertIs(self, a,b):
				self.assertTrue(a is b)
	
		def setUp(self):
			self.o = MockFunctionBuilder()
			self.s = StatementBuilder(self.o,"foobar")
			self.t = StatementBuilder(MockFunctionBuilder(),"blah")
	
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
			u = StatementBuilder(MockFunctionBuilder(),"yadda")
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
		pass


	class TestFunctionBuilderInterface(unittest.TestCase):
	
		if sys.version_info < (2,7):
			def assertIs(self,a,b):
				self.assertTrue(a is b)
	
		def setUp(self):
			self.s = MockStatement()
			self.o = MockFunctionBuilder(self.s)
			self.i = FunctionBuilderInterface(self.o)
	
		def test_get_attribute(self):
			s = self.i.foo
			self.assertIs(self.s,s)
			self.o.check_created(self,["foo"])
			
		def test_get_attribute_special(self):
			for n in ("assert","pass","del","print","return","yield","raise","break",
					"continue","import","global","exec"):
				self.s = MockStatement()
				self.o = MockFunctionBuilder(self.s)
				self.i = FunctionBuilderInterface(self.o)
				s = getattr(self.i, n+"_")
				self.assertIs(self.s,s)
				self.o.check_created(self,[n])

			
	unittest.main()
