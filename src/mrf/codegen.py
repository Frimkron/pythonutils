# TODO: comment properly
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
			
	# TODO: describe parameters!
	def if_(self,statement):
		"""	
		Begins an "if" block definition. Should be used in a context block to delimit the block.
		"""
		self._owner.start_if(statement)
		return self

	def elif_(self,statement):
		"""	
		Begins an "elif" definition. Should be used in a context block to delimit the block.
		"""
		self._owner.start_elif(statement)
		return self
		
	def else_(self):
		"""	
		Begins an "else" definition. Should be used in a context block to delimit the block.
		"""
		self._owner.start_else()
		return self
		
	def while_(self,statement):
		"""	
		Begins a "while" definition. Should be used in a context block to delimit the block.	
		"""
		self._owner.start_while(statement)
		return self
		
	def for_(self,var,seq):
		"""	
		Begins a "for" definition. Should be used in a contet block to delimit the block.
		"""
		self._owner.start_for(var,seq)
		return self
		
	def try_(self):
		self._owner.start_try()
		return self
		
	def except_(self,exception=None,var=None):
		self._owner.start_except(exception,var)
		return self
		
	def finally_(self):
		self._owner.start_finally()
		return self
		
	def with_(self,*args):
		args = list(args)
		if len(args) % 2 != 0:
			args.append(None)
		self._owner.start_with(zip(args[::2],args[1::2]))
		return self

	def __enter__(self):
		return self
		
	def __exit__(self,extype,exvalue,traceback):
		self._owner.end_block()
		

class StatementBuilder(object):

	class DUMMY(object): pass

	def __init__(self,owner,propname):
		self._owner = owner
		self._buffer = propname
		
	def is_(self,other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(value)
		self._buffer += " is %s" % repr(other)
		return self
		
	def prop(self,name):
		return self.__getattr__(name)
		
	def __getattr__(self,name):
		#print "get[%s]" % name
		self._buffer += "."+name
		#print "\t=>%s" % repr(self)
		return self

	def __setattr__(self,name,value):
		#print "set[%s][%s]" % (name,repr(value))
		if isinstance(value,StatementBuilder):
			self._owner.statement_combined(value)
		
		if value is StatementBuilder.DUMMY:
			pass	
		elif name in ("_owner","_buffer"):
			super(StatementBuilder,self).__setattr__(name,value)
		else:	
			self._buffer += ".%s = %s" % (name,repr(value))
			
		return self
		
	def __call__(self,*args,**kargs):
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
		return self._buffer	
	
	def __lt__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " < %s" % repr(other)
		return self
		
	def __le__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " <= %s" % repr(other)
		return self
		
	def __eq__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " == %s" % repr(other)
		return self
		
	def __ne__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " != %s" % repr(other)
		return self
		
	def __gt__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " > %s" % repr(other)
		return self
		
	def __ge__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " >= %s" % repr(other)
		return self
	
	def __getitem__(self,key):
		#print "getitem[%s]" % key
		if isinstance(key,slice):
			self._buffer += "[%s:%s:%s]" % (
				repr(key.start) if key.start is not None else "",
				repr(key.stop) if key.stop is not None else "",
				repr(key.step) if key.step is not None else "" )
		else:
			self._buffer += "[%s]" % repr(key)
		return self
		
	def __setitem__(self,key,value):
		#print "setitem[%s][%s]" % (key,repr(value))
		if isinstance(value,StatementBuilder):
			self._owner.statement_combined(value)
			
		if value is StatementBuilder.DUMMY:
			pass
		elif isinstance(key,slice):
			self._buffer += "[%s:%s:%s] = %s" % (
				repr(key.start) if key.start is not None else "",
				repr(key.stop) if key.stop is not None else "",
				repr(key.step) if key.step is not None else "",
				repr(value) )			
		else:
			self._buffer += "[%s] = %s" % (repr(key),repr(value))
			
		return self
		
	def __contains__(self,item):
		if isinstance(item,StatementBuilder):
			self._owner.statement_combined(item)			
		self._buffer += "%s in " % repr(item)
		return self

	def __add__(self, other):
		#print "add [%s]" % repr(other)
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " + %s" % repr(other)
		return self
	
	def __sub__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " - %s" % repr(other)
		return self
		
	def __mul__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " * %s" % repr(other)
		return self
	
	def __floordiv__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " // %s" % repr(other)
		return self
	
	def __mod__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " %% %s" % repr(other)
		return self
		
	def __pow__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " ** %s" % repr(other)
		return self
		
	def __lshift__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " << %s" % repr(other)
		return self
		
	def __rshift__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " >> %s" % repr(other)
		return self
		
	def __and__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " & %s" % repr(other)
		return self
		
	def __xor__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " ^ %s" % repr(other)
		return self
		
	def __or__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " | %s" % repr(other)
		return self

	def __div__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " / %s" % repr(other)
		return self
		
	def __truediv__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " / %s" % repr(other)
		return self
		
	def __iadd__(self, other):
		#print "iadd [%s]" % repr(other)
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " += %s" % repr(other)
		return StatementBuilder.DUMMY
		
	def __isub__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " -= %s" % repr(other)
		return StatementBuilder.DUMMY
		
	def __imul__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " *= %s" % repr(other)
		return StatementBuilder.DUMMY
		
	def __idiv__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " /= %s" % repr(other)
		return StatementBuilder.DUMMY
		
	def __itruediv__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " /= %s" % repr(other)		
		return StatementBuilder.DUMMY
		
	def __ifloordiv__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " //= %s" % repr(other)
		return StatementBuilder.DUMMY
		
	def __imod__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " %%= %s" % repr(other)
		return StatementBuilder.DUMMY
		
	def __ipow__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " **= %s" % repr(other)
		return StatementBuilder.DUMMY
		
	def __ilshift__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " <<= %s" % repr(other)
		return StatementBuilder.DUMMY
		
	def __irshift__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " >>= %s" % repr(other)
		return StatementBuilder.DUMMY
		
	def __iand__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " &= %s" % repr(other)
		return StatementBuilder.DUMMY
		
	def __ixor__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " ^= %s" % repr(other)
		return StatementBuilder.DUMMY
		
	def __ior__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer += " |= %s" % repr(other)
		return StatementBuilder.DUMMY
		
	def __neg__(self):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer = "-" + self._buffer
		return self
		
	def __pos__(self):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer = "+" + self._buffer
		return self
		
	def __invert__(self):
		if isinstance(other,StatementBuilder):
			self._owner.statement_combined(other)
		self._buffer = "~" + self._buffer
		return self
		

	

