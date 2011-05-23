class FunctionBuilderError(Exception):
	pass


class FunctionBuilder(object):
	
	STATE_BEFORE = 0
	STATE_DURING = 1
	STATE_AFTER = 2
	
	def __init__(self,name,args,kargs,globals,locals):
		self.name = name
		self.args = args
		self.kargs = kargs
		self.globals = globals
		self.locals = locals
		self.indent = 1
		self.state = FunctionBuilder.STATE_BEFORE
		self.statements = []
		
	def __enter__(self):
		if self.state != FunctionBuilder.STATE_BEFORE:
			raise FunctionBuilderError("Should be no more than one 'with' block")
		self.state = FunctionBuilder.STATE_DURING
		return FunctionBuilderInterface(self)
			
	def create_statement(self,name):
		if self.state != FunctionBuilder.STATE_DURING:
			raise FunctionBuilderError("Cannot invoke outside of 'with' block")
		sb = StatementBuilder(self,name)
		self.statements.append((self.indent,sb))
		return sb
		
	def statement_combined(self,statement):
		if self.state != FunctionBuilder.STATE_DURING:
			raise FunctionBuilderError("Cannot invoke outside of 'with' block")
		for i,(d,s) in enumerate(self.statements):
			if s is statement:
				del(self.statements[i])
				break
				
	def start_if(self,stmt):
		if self.state != FunctionBuilder.STATE_DURING:
			raise FunctionBuilderError("Cannot invoke outside of 'with' block")
		if isinstance(stmt,StatementBuilder):
			self.statement_combined(stmt)
		self.statements.append((self.indent,BlockStatement("if %s :",[stmt])))
		self.indent += 1
		
	def start_elif(self,stmt):
		if self.state != FunctionBuilder.STATE_DURING:
			raise FunctionBuilderError("Cannot invoke outside of 'with' block")
		if isinstance(stmt,StatementBuilder):
			self.statement_combined(stmt)
		self.statements.append((self.indent,BlockStatement("elif %s :",[stmt])))
		self.indent += 1
		
	def start_else(self):
		if self.state != FunctionBuilder.STATE_DURING:
			raise FunctionBuilderError("Cannot invoke outside of 'with' block")			
		self.statements.append((self.indent,BlockStatement("else :",[])))
		self.indent += 1
		
	def start_while(self,stmt):
		if self.state != FunctionBuilder.STATE_DURING:
			raise FunctionBuilderError("Cannot invoke outside of 'with' block")
		if isinstance(stmt,StatementBuilder):
			self.statement_combined(stmt)
		self.statements.append((self.indent,BlockStatement("while %s :",[stmt])))
		self.indent += 1
		
	def start_for(self,varstmt,seqstmt):
		if self.state != FunctionBuilder.STATE_DURING:
			raise FunctionBuilderError("Cannot invoke outside of 'with' block")
		if isinstance(varstmt,StatementBuilder):
			self.statement_combined(varstmt)
		if isinstance(seqstmt,StatementBuilder):
			self.statement_combined(seqstmt)
		self.statements.append((self.indent,BlockStatement("for %s in %s :",[varstmt,seqstmt])))
		self.indent += 1
		
	def start_try(self):
		if self.state != FunctionBuilder.STATE_DURING:
			raise FunctionBuilderError("Cannot invoke outside of 'with' block")
		self.statements.append((self.indent,BlockStatement("try :",[])))
		self.indent += 1
		
	def start_except(self,exstmt,varstmt):
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
		if self.state != FunctionBuilder.STATE_DURING:
			raise FunctionBuilderError("Cannot invoke outside of 'with' block")
		self.statements.append((self.indent,BlockStatement("finally :",[])))
		self.indent += 1
		
	def start_with(self,pairs):
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
		if self.state != FunctionBuilder.STATE_DURING:
			raise FunctionBuilderError("Cannot invoke outside of 'with' block")
		self.indent -= 1
		
	def __exit__(self,extype,exvalue,traceback):
		self.state = FunctionBuilder.STATE_AFTER
		
	def build(self):
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
	
	def __init__(self,pattern,statements):
		self.pattern = pattern
		self.statements = statements
		
	def __repr__(self):
		return self.pattern % tuple(map(repr,self.statements))
		
				
class FunctionBuilderInterface(object):

	def __init__(self,owner):
		self._owner = owner
		
	def __getattr__(self,name):
		if name in ("assert_","pass_","del_","print_","return_","yield_","raise_","break_",
				"continue_","import_","global_","exec_"):
			return self._owner.create_statement(name[:-1])
		else:
			return self._owner.create_statement(name)

	def if_(self,statement):
		self._owner.start_if(statement)
		return self

	def elif_(self,statement):
		self._owner.start_elif(statement)
		return self
		
	def else_(self):
		self._owner.start_else()
		return self
		
	def while_(self,statement):
		self._owner.start_while(statement)
		return self
		
	def for_(self,var,seq):
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
		print "get[%s]" % name
		self._buffer += "."+name
		print "\t=>%s" % repr(self)
		return self

	def __setattr__(self,name,value):
		print "set[%s][%s]" % (name,repr(value))
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
		print "getitem[%s]" % key
		if isinstance(key,slice):
			self._buffer += "[%s:%s:%s]" % (
				repr(key.start) if key.start is not None else "",
				repr(key.stop) if key.stop is not None else "",
				repr(key.step) if key.step is not None else "" )
		else:
			self._buffer += "[%s]" % repr(key)
		return self
		
	def __setitem__(self,key,value):
		print "setitem[%s][%s]" % (key,repr(value))
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
		print "add [%s]" % repr(other)
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
		print "iadd [%s]" % repr(other)
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
		

	

