class FunctionBuilder(object):
	
	def __init__(self,name,args,kargs):
		self.name = name
		self.args = args
		self.kargs = kargs
		self.statements = []
		
	def __getattr__(self,name):
		sb = StatementBuilder(self,name)
		self.statements.append(sb)		
		return sb
		
	# TODO: this name prevents calls to properties with same name
	def build(self):
		arglist = self.args
		arglist.extend(["%s=%s" % (k,repr(self.kargs[k])) for k in self.kargs])		
		buffer = "def %s (%s):\n" % self.name, arglist
		for s in self.statements:
			buffer += "\t%s\n" % repr(s)
		exec buffer
		
	def combined(self,statement):
		self.statements.remove(statement)


class StatementBuilder(object):

	class DUMMY(object): pass

	def __init__(self,owner,propname):
		self._owner = owner
		self._buffer = propname
		
	def iz(self,other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(value)
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
			self._owner.combined(value)
		
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
				self._owner.combined(a)
		for k in kargs:
			if isinstance(kargs[k],StatementBuilder):
				self._owner.combined(kargs[k])
	
		arglist = []
		arglist.extend(map(repr,args))
		arglist.extend(["%s=%s" % (k,repr(kargs[k])) for k in kargs])
		self._buffer += "(%s)" % ",".join(arglist)
		
		return self		
		
	def __repr__(self):
		return self._buffer	
	
	def __lt__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " < %s" % repr(other)
		return self
		
	def __le__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " <= %s" % repr(other)
		return self
		
	def __eq__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " == %s" % repr(other)
		return self
		
	def __ne__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " != %s" % repr(other)
		return self
		
	def __gt__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " > %s" % repr(other)
		return self
		
	def __ge__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
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
			self._owner.combined(value)
			
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
			self._owner.combined(item)			
		self._buffer += "%s in " % repr(item)
		return self

	def __add__(self, other):
		print "add [%s]" % repr(other)
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " + %s" % repr(other)
		return self
	
	def __sub__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " - %s" % repr(other)
		return self
		
	def __mul__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " * %s" % repr(other)
		return self
	
	def __floordiv__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " // %s" % repr(other)
		return self
	
	def __mod__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " %% %s" % repr(other)
		return self
		
	def __pow__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " ** %s" % repr(other)
		return self
		
	def __lshift__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " << %s" % repr(other)
		return self
		
	def __rshift__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " >> %s" % repr(other)
		return self
		
	def __and__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " & %s" % repr(other)
		return self
		
	def __xor__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " ^ %s" % repr(other)
		return self
		
	def __or__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " | %s" % repr(other)
		return self

	def __div__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " / %s" % repr(other)
		return self
		
	def __truediv__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " / %s" % repr(other)
		return self
		
	def __iadd__(self, other):
		print "iadd [%s]" % repr(other)
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " += %s" % repr(other)
		return StatementBuilder.DUMMY
		
	def __isub__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " -= %s" % repr(other)
		return StatementBuilder.DUMMY
		
	def __imul__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " *= %s" % repr(other)
		return StatementBuilder.DUMMY
		
	def __idiv__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " /= %s" % repr(other)
		return StatementBuilder.DUMMY
		
	def __itruediv__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " /= %s" % repr(other)		
		return StatementBuilder.DUMMY
		
	def __ifloordiv__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " //= %s" % repr(other)
		return StatementBuilder.DUMMY
		
	def __imod__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " %%= %s" % repr(other)
		return StatementBuilder.DUMMY
		
	def __ipow__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " **= %s" % repr(other)
		return StatementBuilder.DUMMY
		
	def __ilshift__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " <<= %s" % repr(other)
		return StatementBuilder.DUMMY
		
	def __irshift__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " >>= %s" % repr(other)
		return StatementBuilder.DUMMY
		
	def __iand__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " &= %s" % repr(other)
		return StatementBuilder.DUMMY
		
	def __ixor__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " ^= %s" % repr(other)
		return StatementBuilder.DUMMY
		
	def __ior__(self, other):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer += " |= %s" % repr(other)
		return StatementBuilder.DUMMY
		
	def __neg__(self):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer = "-" + self._buffer
		return self
		
	def __pos__(self):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer = "+" + self._buffer
		return self
		
	def __invert__(self):
		if isinstance(other,StatementBuilder):
			self._owner.combined(other)
		self._buffer = "~" + self._buffer
		return self
		

	

