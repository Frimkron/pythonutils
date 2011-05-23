# TODO: brackets?
# TODO: unit tests
# TODO: documentation
# TODO: way of capturing global and local scope


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
		Invoked when context is exited. Invokes "build" to compile the function definition
		"""
		self.state = FunctionBuilder.STATE_AFTER
		self.build()
		
	def build(self):
		"""	
		Builds the internal statement list into a function definition and attempts to execute
		as python code, creating a new function
		"""
		if self.state != FunctionBuilder.STATE_AFTER:
			raise FunctionBuilderError("Must complete 'with' block before building")
		arglist = self.args
		arglist.extend(["%s=%s" % (k,repr(self.kargs[k])) for k in self.kargs])		
		buffer = "def %s (%s):\n" % (self.name, ",".join(arglist))
		for d,s in self.statements:
			buffer += "%s%s\n" % ("\t"*d,repr(s))
		print buffer
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
			self._owner.statement_combined(value)
		self._buffer += " is %s" % repr(other)
		return self
		
	def and_(self,other):
		"""	
		Defines an "and" comparison as part of the statement being built, using the given value
		as the right hand side. This may be another StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(value)
		self._buffer += " and %s" % repr(other)
		return self
		
	def or_(self,other):
		"""	
		Defines an "or" compariso as part of the statement being built, using the given value
		as the right hand side. This may be another StatementBuilder or any other repr-able object.
		"""
		if isinstance(other,StatementBuilder):
			# combine statement, remove from main list
			self._owner.statement_combined(value)
		self._buffer += " or %s" % repr(other)
		return self
		
	def not_(self):
		"""	
		Defines a logical negation as part of the statement being built.
		"""
		self._buffer = "not "+self._buffer
		return self
		
	def attr(self,name):
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
			# TODO: combine key statement here!
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
			# TODO: combine key statement here!
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
		self._buffer += "%s in " % repr(item)
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
		
	

