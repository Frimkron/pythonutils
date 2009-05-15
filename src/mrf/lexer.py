"""
Copyright (c) 2009 Mark Frimston

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
"""

import sys
import ascii

"""
RE syntax:

expression -> term*
term -> (any_character|set|group|character)quantifier?
set -> (character|range_marker)* 
group -> expression+

Doesn't handle:
	Boundary markers e.g. ^, $, \A, \Z, \B
	Special constructs e.g. (?i), (?:), (?<=foo), etc
	Character groups e.g. \d, \s, etc.
	Character codes e.g. \o12, \x12, \u1212 etc
	Special characters OTHER THAN \n, \r, \t
	Character set unions or intersections e.g. [a-b[d-f]], [a-g&&[d-f]]
	POSIX character classes e.g. \p{Digit}
	Reluctant or possesive quantifiers e.g. a*?, a*+
	Capturing or backreferences e.g. \1, \2, $1, $2
	Quotation e.g. \Q, \E
"""

class ParseError(Exception):
	"""
	Error type thrown by the parser
	"""
	pass
	
class ReSymbol(object):
	"""
	A node in the regular expression parse tree
	"""
	def __str__(self):
		return str(self.type) + ("("+str(self.data)+")" if hasattr(self,"data") else "()")

class ReParser(object):
	"""
	Class for parsing a regular expression into a parse tree.
	"""
	
	def parse_re(self, input):
		"""
		Parses a regular expression string and returns a tree of ReSymbol objects
		"""
		self.input = input
		self.pos = 0
		
		exp = self._parse_expression()
		if self._current_char() != None:
			raise ParseError("Expected end of input at char %d" % self.pos)		
			
		return exp
		
	def _current_char(self):
		if self.pos >= len(self.input):
			return None
		else:
			return self.input[self.pos]
			
	def _parse_expression(self):
		retval = ReSymbol()
		retval.type = "expression"
		retval.children = []
		while self._current_char() != None and not self._current_char() in [')','|']:
			retval.children.append(self._parse_term())
		return retval
			
	def _parse_term(self):
		if self._current_char() in ['+','*',']','?','}',')','|']:
			raise ParseError("Unexpected start of term '%s' at char %d" % (self._current_char(),self.pos))		
		elif self._current_char() == '.':
			item = ReSymbol()
			item.type = "any_character"
			self.pos+=1
		elif self._current_char() == '[':
			item = self._parse_set()
		elif self._current_char() == '(':
			item = self._parse_group()
		else:
			item = self._parse_character()
			
		retval = ReSymbol()
		retval.type = "term"
		retval.children = [item]
		
		if self._current_char() != None:
			if self._current_char() == '?':
				mod = ReSymbol()
				mod.type = "quantifier"
				mod.data = (0,1)
				retval.children.append(mod)
				self.pos+=1
			elif self._current_char() == '*':
				mod = ReSymbol()
				mod.type = "quantifier"
				mod.data = (0,-1)
				retval.children.append(mod)
				self.pos+=1
			elif self._current_char() == '+':
				mod = ReSymbol()
				mod.type = "quantifier"
				mod.data = (1,-1)
				retval.children.append(mod)
				self.pos+=1
			elif self._current_char() == '{':
				mod = self._parse_quant()
				retval.children.append(mod)
				
		return retval
		
	def _parse_quant(self):
		self.pos+=1
		min = ""
		max = ""
		if self._current_char() == None:
				raise ParseError("Unexpected end of input at char %d" % self.pos)
		if not( ord('0') <= ord(self._current_char()) <= ord('9') ):
			raise ParseError("Expected value in quantifier at char %d" % self.pos)	 
		while not self._current_char() in [',','}']:
			if self._current_char() == None:
				raise ParseError("Unexpected end of input at char %d" % self.pos)
			if not( ord('0') <= ord(self._current_char()) <= ord('9') ):
				raise ParseError("Expected value in quantifier at char %d" % self.pos)
			min += self._current_char()
			self.pos+=1
		min = int(min)
		if self._current_char() == ',':
			self.pos+=1
			if self._current_char() != '}':
				while not self._current_char()=='}':
					if self._current_char() == None:
						raise ParseError("Unexpected end of input at char %d" % self.pos)
					if not( ord('0') <= ord(self._current_char()) <= ord('9') ):
						raise ParseError("Expected value in quantifier at char %d" % self.pos)
					max += self._current_char()
					self.pos+=1
				max = int(max)
			else:
				max = -1
		else:
			max = min
		self.pos+=1
		
		retval = ReSymbol()
		retval.type = "quantifier"
		retval.data = (min,max)
		return retval
		
			
	def _parse_character(self):
		if self._current_char() == '\\':
			return self._parse_escape()
		else:
			retval = ReSymbol()
			retval.type = "character"
			retval.data = self._current_char()
			self.pos+=1
			return retval
			
	def _parse_escape(self):
		self.pos+=1
		if self._current_char() == None:
			raise ParseError("Unexpected end of input at char %d" % self.pos)
		elif self._current_char() == 'n':
			retval = ReSymbol()
			retval.type = "character"
			retval.data = "\n"
			self.pos+=1
			return retval
		elif self._current_char() == 'r':
			retval = ReSymbol()
			retval.type = "character"
			retval.data = "\r"
			self.pos+=1
			return retval
		elif self._current_char() == 't':
			retval = ReSymbol()
			retval.type = "character"
			retval.data = "\t"
			self.pos+=1
			return retval
		else:
			retval = ReSymbol()
			retval.type = "character"
			retval.data = self._current_char()
			self.pos+=1
			return retval
			
	def _parse_set(self):
		self.pos+=1
		if self._current_char() == '^':
			negate = True
			self.pos+=1
		else:
			negate = False
		
		retval = ReSymbol()
		retval.type = "set"
		retval.negate = negate
		retval.children = []
		while self._current_char() != ']':
			if self._current_char() == None:
				raise ParseError("Unexpected end of input at char %d" % self.pos)
			if self._current_char() == '-':
				item = ReSymbol()
				item.type = "range_marker"
				retval.children.append(item)
				self.pos+=1
			else:
				retval.children.append(self._parse_character())
			
		if self._current_char() == None:
			raise ParseError("Unexpected end of input at char %d" % self.pos)
		
		self.pos+=1
		return retval
		
	def _parse_group(self):
		self.pos+=1
		retval = ReSymbol()
		retval.type = "group"
		retval.children = []
		
		if self._current_char() != ')':
			if self._current_char() == None:
				raise ParseError("Unexpected end of input at char %d" % self.pos)
			retval.children.append(self._parse_expression())
		
		while self._current_char() != ')':
			if self._current_char() == None:
				raise ParseError("Unexpected end of input at char %d" % self.pos)
			elif self._current_char() != '|':
				raise ParseError("Expected '|' at char %d" % self.pos)
			self.pos+=1
			retval.children.append(self._parse_expression())				
				
		self.pos+=1
		return retval
		
		
def print_re_tree(re, indent=0):
	"""
	Prints out a parse tree obtained from ReParser, RuleParser or LrParser
	"""
	s = "\t"*indent	
	s += re.type
	if hasattr(re,"data"):
		s += '('+str(re.data)+')'
	else:
		s += '()'
	print s
	if hasattr(re,"children"):
		for c in re.children:
			print_re_tree(c, indent+1)
			

class StateError(Exception):
	"""
	Error type thrown by finite state automata classes
	"""
	pass

class NfAutomaton(object):
	"""
	A non-deterministic finite state automaton.
	"""

	class empty(object):
		def __str__(self):
			return "E"
	EMPTY = empty()
	
	def __init__(self):
		self.states = {}		
		self.start_state = None
		self.end_states = set([])
		self.state_data = {}
		
	def set_start_state(self,name):
		"""
		Makes the state with the given name the starting state.
		"""
		self.start_state = name
		
	def add_end_state(self, name, label_only=False):
		"""
		Adds a new state with the given name as an end state. If label_only is true,
		a new state is not created, and instead an existing state can be named as an
		end state
		"""
		if not label_only:
			self.states[name] = {}
		self.end_states.add(name)
		
	def add_state(self, name):
		"""
		Adds a new state to the automaton with the given name
		"""
		self.states[name] = {}
		
	def add_trans(self, fr, to, vals):
		"""
		Adds a new transition or transitions between fr and to, on each of the items 
		in the sequence vals.
		"""
		for v in vals:
			if not self.states[fr].has_key(v):
				self.states[fr][v] = []
			self.states[fr][v].append(to)
	
	def add_state_data(self, state, data):
		"""
		Adds additional data to accompany the named state.
		"""
		self.state_data[state] = data
		
	def make_dfa(self):
		"""
		Generates a deterministic state automaton from this nfa. Returns a 
		DfAutomaton object
		"""
		if self.start_state == None:
			raise StateError("No start state")
		dfa = DfAutomaton()		
		new_start = self._make_dfa_state(dfa, [self.start_state])
		dfa.set_start_state(new_start)
		return dfa
		
	def _make_dfa_state(self, dfa, states):
		closure = set([])
		self._make_closure(closure, states)
		state_name = ""
		combined_trans = {}
		combined_data = []
		is_end = False
		for s in closure:
			if s in self.end_states:
				is_end = True
			state_name += s
			if self.state_data.has_key(s):
				combined_data.append(self.state_data[s])
			for t in self.states[s]:
				if not combined_trans.has_key(t):
					combined_trans[t] = []
				combined_trans[t].extend(self.states[s][t])
		if not state_name in dfa.states:
			if is_end:
				dfa.add_end_state(state_name)
			else:
				dfa.add_state(state_name)
			dfa.add_state_data(state_name, combined_data)
			for t in combined_trans:
				if not t == NfAutomaton.EMPTY:
					new_state_name = self._make_dfa_state(dfa, combined_trans[t])
					dfa.add_trans(state_name, new_state_name, [t])
			
		return state_name
		
	def _make_closure(self, state_set, states):
		for s in states:
			state_set.add(s)
			for t in self.states[s]:
				if t == NfAutomaton.EMPTY:
					for s2 in self.states[s][t]:
						if not s2 in state_set:
							self._make_closure(state_set, [s2])
		
	def get_start_state(self):
		"""
		Returns the name of the start state
		"""
		return self.start_state
							
	def get_states(self):
		"""
		Returns the list of state names
		"""
		return self.states.keys()
		
	def get_transitions(self):
		"""
		Returns the list of transitions. Each item is a three-item tuple consisting 
		of the 'from' state, the 'to' state and the transition symbol  
		"""
		out = []
		for s in self.states:
			for t in self.states[s]:
				for ts in self.states[s][t]:
					out.append((s,ts,t))
		return out
	
		
class DfAutomaton(NfAutomaton):
	"""
	A deterministic finite state automaton.
	"""
		
	def __init__(self):
		NfAutomaton.__init__(self)
		self.current_state = None
		self.reset()
		
	def add_trans(self, fr, to, vals):
		"""
		Adds a new transition from 'fr' to 'to' for each of the items in the squence
		'vals' 
		"""
		for v in vals:
			if v == NfAutomaton.EMPTY:
				raise StateError("deterministic automata may not use empty transitions")
			self.states[fr][v] = to
		
	def reset(self):
		"""
		Resets the automaton to the starting state
		"""
		self.current_state = self.start_state
			
	def move(self, value):
		"""
		Attempts to change state via an available transition with the given symbol. 
		If no such transition exists from the current state or the current state is
		invalid, a StateError is thrown.
		"""
		if self.current_state == None:
			raise StateError("Not in state")
		if not self.states[self.current_state].has_key(value):
			raise StateError("No transition on \"%s\" in state \"%s\"" % (value,self.current_state))
		new_state = self.states[self.current_state][value]
		if not self.states.has_key(new_state):
			raise StateError("State \"%s\" does not exist" % new_state)
		self.current_state = new_state
		
	def is_at_end(self):
		"""
		Returns true if the current state is an end state.
		"""
		return self.current_state in self.end_states
		
	def get_state(self):
		"""
		Returns the name of the current state
		"""
		return self.current_state
		
	def get_transitions(self):
		"""
		Returns the list of transitions. Each item consists of a three-item tuple
		containing the 'from' state, the 'to' state and the transition symbol
		"""
		out = []
		for s in self.states:
			for t in self.states[s]:				
				out.append((s,self.states[s][t],t))
		return out
		

class ReCompiler(object):
	"""
	Class for compiling a regular expression parse tree into a deterministic 
	finite state automaton.
	"""
	
	ALL_CHARS = []
	for c in range(1,128):
		ALL_CHARS.append(chr(c))

	def __init__(self):
		self.tree = None
		self.next_state = 0
		self.handlers = {
			"expression" : self._build_expression,
			"term" : self._build_term,
			"character" : self._build_character,
			"any_character" : self._build_any_character,
			"set" : self._build_set,
			"group" : self._build_group
		}
		
	def make_nfa(self, tree):
		"""
		Compiles a given re parse tree into a non-deterministic finite state automaton.
		Returns a NfAutomaton object.
		"""
		
		self.tree = tree
		nfa = NfAutomaton()
		
		state_name = self._gen_state_name()
		nfa.add_state(state_name)
		nfa.set_start_state(state_name)
		
		start_state,end_state = self._build_symbol(tree, nfa, state_name)		
		nfa.add_end_state(end_state, True)
		return nfa	
		
	def make_dfa(self, tree):
		"""
		Compiles a given re parse tree into a deterministic finite state automaton.
		Returns a DfAutomaton object.
		"""
		nfa = self.make_nfa(tree)
		dfa = nfa.make_dfa()
		return dfa
		
	def _build_symbol(self, symbol, nfa, trans_from):
		if self.handlers.has_key(symbol.type):
			return self.handlers[symbol.type](symbol, nfa, trans_from)
		else:
			return trans_from, trans_from
		
	def _build_expression(self, symbol, nfa, trans_from):
		exp_start = trans_from
		exp_end = trans_from
		for term in symbol.children:
			term_start,term_end = self._build_symbol(term, nfa, trans_from)
			if exp_end == trans_from:
				exp_end = term_end
			trans_from = term_end
		return exp_start, exp_end
		
	def _build_term(self, symbol, nfa, trans_from):
		term_start = trans_from
		term_end = trans_from
		min_times = 1
		max_times = 1
		if len(symbol.children)>1:
			quant = symbol.children[1]
			min_times = quant.data[0]
			max_times = quant.data[1]
			if max_times!=-1 and max_times<min_times:
				raise StateError("max quantity less than min quantity")
		num_times = max_times
		if max_times == -1:
			if min_times > 0:
				num_times = min_times
			else:
				num_times = 1
		link_trans_from = trans_from
		for i in range(num_times):
			front_name = self._build_link_state(nfa, link_trans_from)
			if term_start == trans_from:
				term_start = front_name
			link_trans_from = front_name
			ti_start,ti_end = self._build_symbol(symbol.children[0],nfa,link_trans_from)			
			if i >= min_times:
				nfa.add_trans(ti_start,ti_end,[NfAutomaton.EMPTY])
			if i==num_times-1 and max_times==-1:
				nfa.add_trans(ti_end,ti_start,[NfAutomaton.EMPTY])
			link_trans_from = ti_end
			back_name = self._build_link_state(nfa, link_trans_from)			
			term_end = back_name
			link_trans_from = term_end		
		return term_start,term_end
		
	def _build_character(self, symbol, nfa, trans_from):
		term_start = trans_from
		term_end = trans_from
		trans_from = self._build_link_state(nfa, trans_from)
		state_name = self._gen_state_name()
		nfa.add_state(state_name)
		nfa.add_trans(trans_from,state_name,[symbol.data])
		trans_from = state_name
		trans_from = self._build_link_state(nfa, trans_from)		
		term_end = trans_from
		return term_start,term_end
		
	def _build_any_character(self, symbol, nfa, trans_from):
		term_start = trans_from
		term_end = trans_from
		trans_from = self._build_link_state(nfa, trans_from)
		state_name = self._gen_state_name()
		nfa.add_state(state_name)
		nfa.add_trans(trans_from,state_name,ReCompiler.ALL_CHARS)
		trans_from = state_name
		trans_from = self._build_link_state(nfa, trans_from)
		term_end = trans_from
		return term_start,term_end
		
	def _build_set(self, symbol, nfa, trans_from):
		term_start = trans_from
		term_end = trans_from
		trans_from = self._build_link_state(nfa, trans_from)
		chars = set([])
		i=0
		while i<len(symbol.children):
			if( i+1 < len(symbol.children) and symbol.children[i+1].type == "range_marker"
						and i+2 < len(symbol.children) ):
				if ord(symbol.children[i].data) > ord(symbol.children[i+2].data):
					raise ParseError("Incorrect character order for character range in set")
				for c in range(ord(symbol.children[i].data),ord(symbol.children[i+2].data)+1):
					chars.add(chr(c))
				i+=3
			else:
				if symbol.children[i].type == "range_marker":
					chars.add("-")
				else:
					chars.add(symbol.children[i].data)
				i+=1
		if symbol.negate:
			new_chars = set([])
			for c in ReCompiler.ALL_CHARS:
				if not c in chars:
					new_chars.add(c)
			chars = new_chars
		state_name = self._gen_state_name()
		nfa.add_state(state_name)
		nfa.add_trans(trans_from,state_name,chars)
		trans_from = state_name
		trans_from = self._build_link_state(nfa, trans_from)
		term_end = trans_from
		return term_start,term_end
		
	def _build_group(self, symbol, nfa, trans_from):
		term_start = trans_from
		term_end = trans_from
		trans_from = self._build_link_state(nfa, trans_from)
		back_state = self._gen_state_name()
		nfa.add_state(back_state)
		term_end = back_state
		for e in symbol.children:
			e_start,e_end = self._build_expression(e,nfa,trans_from)
			nfa.add_trans(e_end,back_state,[NfAutomaton.EMPTY])
		return term_start,term_end
		
	def _build_link_state(self, nfa, trans_from):
		state = self._gen_state_name()
		nfa.add_state(state)
		nfa.add_trans(trans_from,state,[NfAutomaton.EMPTY])
		return state
		
	def _gen_state_name(self):
		state_name = str(self.next_state)
		self.next_state+=1
		return state_name
		
		
class ReMatcher(object):		
		"""
		Class for testing if a string matches a given regular expression.
		"""
		
		def __init__(self, re):			
			"""
			Constructs the object from the given regular expression string
			"""				
			p = ReParser()
			tree = p.parse_re(re)
			#print_re_tree(tree)
			#print "---------------------------"
			
			c = ReCompiler()
			nfa = c.make_nfa(tree)
			#pr = SaPrinter()
			#pr.print_automaton(nfa)
			#print "---------------------------"
			
			self.dfa = nfa.make_dfa()
			#pr.print_automaton(self.dfa)

		def matches(self, input):
			"""
			Returns true if the input string matches the regular expression this object
			was initialised with.
			"""
			self.dfa.reset()
			try:
				for c in input:
					self.dfa.move(c)	
			except StateError:
				return False
			if not self.dfa.is_at_end():
				return False
			return True
		

class SaPrinter(ascii.Canvas):
	"""
	Class for representing a finite state automaton in ascii art
	"""

	def __init__(self):
		self.arrowed = set([])
		self.state_order = {}
		
	def render_automaton(self, automaton):
		"""
		Renders the given NfAutomaton or DfAutomaton object to a string as ascii 
		art. Returns the string representation.
		"""
		self.arrowed = set([])
		self.state_order = {}
		self.clear()
		i = 0
		for s in automaton.get_states():
			self.state_order[s] = i
			i+=1
		for s in automaton.get_states():
			pos = self.state_order[s]
			y = pos*4
			self.set(1,y,'/')
			self.set(8,y,'\\')
			self.set(0,y+1,'|')
			self.set(9,y+1,'|')
			self.set(1,y+2,'\\')
			self.set(8,y+2,'/')
			self.write(2,y+1,s,6)
			if s == automaton.get_start_state():
				self.write(3,y,"START")
			if s in automaton.end_states:
				self.write(3,y+2,"END")
		for t in automaton.get_transitions():
			fr,to,on = t[0],t[1],t[2]
			fr_pos = self.state_order[fr]
			to_pos = self.state_order[to]
			if to_pos!=fr_pos:
				inc = (to_pos-fr_pos)/abs(to_pos-fr_pos)
			else:
				inc = -1	
			fr_y = fr_pos*4 + 2 
			to_y = to_pos*4
			check_x = 0
			x_found = False
			range_fr = (fr_pos*2 -(1 if inc<0 else 0) 
				+ (1 if fr_pos>to_pos or (fr_pos==to_pos and inc<0) else 0))
			range_to = (to_pos*2	-(1 if inc<0 else 0) 
				+ (1 if to_pos>fr_pos or (fr_pos==to_pos and inc>0) else 0))
			while not x_found:	
				blocked = False									
				for i in range(range_fr, range_to, inc):
					check_pos = i
					if (check_x,check_pos) in self.arrowed:
						blocked = True
						break
				if not blocked:
					x_found = True
					break
				check_x+=1
			for i in range(range_fr, range_to, inc):
				self.arrowed.add((check_x,i))
			for i in range(check_x):
				for j in range(3):
					if self.get(10+i*3+j,fr_y) in ['|','.','\'',':','+']:
						self.set(10+i*3+j,fr_y,'+')
					else:
						self.set(10+i*3+j,fr_y,'-')
			self.set(10+check_x*3,fr_y,'-')
			self.set(10+check_x*3+1,fr_y,'-')
			if self.get(10+check_x*3+2,fr_y) in ['.','\'',':']:
				self.set(10+check_x*3+2,fr_y, ':')
			else:
				self.set(10+check_x*3+2,fr_y, '.' if inc>0 else '\'')
			for i in range(fr_y+inc, to_y, inc):
				if self.get(10+check_x*3+2,i) in ['-','+']:
					self.set(10+check_x*3+2,i,'+')
				else:
					self.set(10+check_x*3+2,i,'|')
			if self.get(10+check_x*3+2,to_y) in ['.','\'',':']:
				self.set(10+check_x*3+2,to_y,':')
			else:
				self.set(10+check_x*3+2,to_y,'\'' if inc>0 else '.')
			self.set(10+check_x*3+1,to_y,'-')
			self.set(10+check_x*3,to_y,'-')
			for i in range(check_x):
				for j in range(3):
					if self.get(10+i*3+j,to_y) in ['|','.','\'',':','+']:
						self.set(10+i*3+j,to_y,'+')
					else:
						self.set(10+i*3+j,to_y,'-')
			self.set(10,to_y,'<')
			self.set(10+check_x*3+3,fr_y+inc,str(on)[0])
		return self.render()
		
	def print_automaton(self, automaton):
		"""
		Prints out an ascii art representation of the given NfAutomaton or 
		DfAutomaton object.
		"""
		print self.render_automaton(automaton)		
		

class SyntaxError(Exception):
	"""
	Error type thrown by Lexer class
	"""
	pass


class ParserSymbol(object):
	"""
	Item in parse tree
	"""
	type = ""
	data = ""
	children = None
	
	def __init__(self, type, data):
		self.type = type
		self.data = data
		self.children = []
	
	def __str__(self):
		return str(self.type)+"("+str(self.data)+")"

	def __repr__(self):
		return self.__str__()	
		

class Token(ParserSymbol):
	"""
	Class representing the default token type output from Lexer
	"""
	pass
	

class Lexer(object):
	"""
	A simple lexical analyser which compiles a state machine from a number of 
	token patterns. Can be used as an iterator.
	"""
	
	END_OF_INPUT = 0

	def __init__(self, token_defs):
		"""
		Initialises the object from the given list of token definitions. Each item
		in the list should be a token definition consisting of a tuple containing the 
		token name followed by a regular expression describing its pattern, and 
		optionally a token class to use in place of the default Token.
		"""
		"""
		token_defs = [("myToken","a+"),("myOtherToken",[0-9]{0,3})]
		"""
		self.next_state=0
		self.prepare("")
		
		# Store hash of token classes
		self.token_classes = {}
		for tdef in token_defs:
			if len(tdef) > 2:
				self.token_classes[tdef[0]] = tdef[2]
		
		self.dfa = self.make_dfa(token_defs)
		
	def prepare(self, input):
		"""
		Prepares the lexer to tokenise the given input string.
		"""
		self.input = input
		self.pos = 0
		
	def make_dfa(self, token_defs):
		"""
		Returns a DfAutomaton object representing the deterministic finite state
		automaton compiled by combining the regular expressions in the token 
		definitions. Each end state in the automaton will have a token name in its
		accompanying data.
		"""
	
		self.next_state=0
		parser = ReParser()
		compiler = ReCompiler()
		
		nfa = NfAutomaton()
		start_state = self._make_state_name()
		nfa.add_state(start_state)
		nfa.set_start_state(start_state)
		
		for tdef in token_defs:
			token_name = tdef[0]
			token_re = tdef[1]
			tree = parser.parse_re(token_re)
			#print token_re
			#print_re_tree(tree)
			sub_nfa = compiler.make_nfa(tree)
			
			state_mapping = {}
			for s in sub_nfa.get_states():
				new_name = self._make_state_name()
				state_mapping[s] = new_name
				if s in sub_nfa.end_states:
					nfa.add_end_state(new_name)	
					nfa.add_state_data(new_name, token_name)				
				else:
					nfa.add_state(new_name)
				if s == sub_nfa.get_start_state():
					nfa.add_trans(start_state,state_mapping[s],[NfAutomaton.EMPTY])
					
			for t in sub_nfa.get_transitions():
				nfa.add_trans(state_mapping[t[0]], state_mapping[t[1]], [t[2]])
			
		dfa = nfa.make_dfa()
		
		return dfa
		
	def _make_state_name(self):
		name = str(self.next_state)
		self.next_state+=1
		return name
		
	def _current_char(self):
		if self.pos < len(self.input):
			return self.input[self.pos]
		else:
			return Lexer.END_OF_INPUT
			
	def _advance(self):
		self.pos += 1
		
	def __iter__(self):
		return self
		
	def next(self):
		"""
		Advances the lexer by one token and returns the next token. Throws 
		StopIteration if no more tokens are available
		"""
		t = self.next_token()
		if t == None:
			raise StopIteration
		return t
		
	def next_token(self):
		"""
		Advances the lexer by one token and returns the next token, or None, of no
		more tokens are available
		"""
		if self._current_char() == Lexer.END_OF_INPUT:
			return None
		self.dfa.reset()
		buffer = ""
		try:
			while True:
				self.dfa.move(self._current_char())
				buffer += self._current_char()
				self._advance()
		except StateError:
			if self.dfa.is_at_end():
				ttype = self.dfa.state_data[self.dfa.current_state][0]
				tclass = self.token_classes[ttype] if self.token_classes.has_key(ttype) else Token
				return tclass(ttype, buffer)
			else:
				raise SyntaxError("Syntax error at \"%s\"" % self._current_char())

"""
Rule syntax:
	Ru -> Lhs separator Rhs
	Lhs -> nonterminal
	Rhs -> T ("|" T)*
	T -> (terminal|nonterminal)+
"""

class RuleParser(object):
	"""
	Class for parsing grammar rules using a simple syntax
	"""

	def __init__(self):
		self.lexer = Lexer([
			("whitespace", "[ \t\n\r]+"),
			("terminal","[a-z][a-zA-Z0-9_-]*"),
			("nonterminal", "[A-Z][a-zA-Z0-9_-]*"),
			("separator", "->"),
			("or", "\|")
		])	

	def parse_rule(self, rule):
		"""
		Parses the given rule string, returning a parse tree of Rule_symbol objects
		"""
		self.lexer.prepare(rule)
		self._advance()
		
		out = ParserSymbol("rule","")
		
		if self._current_token_type() != "nonterminal":
			raise ParseError("Expected Non-terminal, found %s" % self._current_token_type())
		lhs = ParserSymbol("lhs","")
		lhs.children.append(self._current_token())
		out.children.append(lhs)
		self._advance()	
		
		if self._current_token_type() != "separator":
			raise ParseError("Expected separator, found %s" % self._current_token_type())
		self._advance()
		
		rhs = self._parse_rhs()
		out.children.append(rhs)
		self._advance()
		
		if self._current_token() != None:
			raise ParseError("Expected end of input ,found %s" % self._current_token_type())
			
		return out
		
	def _parse_rhs(self):
		out = ParserSymbol("rhs","")
		
		while(True):
			term = self._parse_term()
			out.children.append(term)
			
			if self._current_token_type() != "or":
				break
			else:
				self._advance()
				
		return out
		
	def _parse_term(self):
		out = ParserSymbol("term","")
		
		if not self._current_token_type() in ["terminal","nonterminal"]:
			raise ParseError("Expected Terminal or Non-terminal, found %s" % self._current_token_type())
		
		while True:
			out.children.append(self._current_token())
			self._advance()
			
			if not self._current_token_type() in ["terminal", "nonterminal"]:
				break
				
		return out
		
	def _current_token(self):
		return self.current_token
		
	def _current_token_type(self):
		if self.current_token == None:
			return None
		else:
			return self.current_token.type
	
	def _advance(self):
		# skip over whitespace 
		while True:
			self.current_token = self.lexer.next_token()
			if self.current_token==None or self.current_token.type != "whitespace":
				break
	
	
class ParserItem(object):
	"""
	Used internally by LrParser to represent an item e.g. E -> E . plus B
	"""

	def __init__(self, rules, rulename, position):
		self.rules = rules
		self.rulename = rulename
		self.position = position
		
	def get_next_symbol(self):
		"""
		Returns the symbol following the dot or None if dot is at the end
		"""
		if self.position < len(self.rules[self.rulename][1]):
			return self.rules[self.rulename][1][self.position]
		else:
			return None
			
	def make_next_item(self):
		"""
		Returns another item where the dot has been advanced past the next symbol
		"""
		if self.position < len(self.rules[self.rulename][1]):
			next_pos = self.position + 1
			return ParserItem(self.rules, self.rulename, next_pos)
		else:
			return None
			
	def is_end(self):
		"""
		Returns true if the dot is at the end
		"""
		return self.position >= len(self.rules[self.rulename][1])
			
	def __eq__(self, other):
		return( other!=None 
				and self.rules==other.rules 
				and self.rulename==other.rulename 
				and self.position==other.position )			
		
	def __ne__(self, other):
		return( other==None
				or self.rules!=other.rules 
				or self.rulename!=other.rulename
				or self.position!=other.position )
				
	def __str__(self):
		rhs_with_dot = list(self.rules[self.rulename][1][:])
		rhs_with_dot.insert(self.position,".")
		return self.rules[self.rulename][0]+" -> " + " ".join(rhs_with_dot)
	
	def __repr__(self):
		return self.__str__()
		
	def __hash__(self):
		return hash(str(id(self.rules))+str(hash(self.rulename))+str(hash(self.position)))
	
class ItemSet(object):
	"""
	Used internally by LrParser to represent a set of items. Contains a set of 
	ParserItem objects.
	"""
	
	def __init__(self):
		self.items = set([])
		self.lookup = {}
		self.end_rules = []
		
	def add(self, item):
		"""
		Adds a new ParserItem object to the set
		"""
		if not item in self.items:
			self.items.add(item)
			if item.get_next_symbol() != None:
				if not self.lookup.has_key(item.get_next_symbol()):
					self.lookup[item.get_next_symbol()] = []
				self.lookup[item.get_next_symbol()].append(item)
			if item.is_end():
				if not item.rulename in self.end_rules:
					self.end_rules.append(item.rulename)
	
	def __eq__(self,other):
		return other!=None and self.items==other.items
		
	def __ne__(self,other):
		return other==None or self.items!=other.items
		
	def __str__(self):
		return str(self.items)
		
	def __repr__(self):
		return self.__str__()
		
	def __hash__(self):
		set_hash = 0
		for i in self.items:
			set_hash ^= hash(i)
		return set_hash
		
	
class LrParser(object):
	"""
	An LR(0) parser implementation.
	"""

	def __init__(self, ruledefs):
		"""
		Initialises the parser with the given symbol definitions. ruledefs should be
		a list of symbol definitions. Each definition should be a string describing 
		a rule for a nonterminal symbol, as parsed by RuleParser. Or optionally a 
		definition may be a tuple consisting of the rule string and an alternative 
		symbol class to use in place of the default ParserSymbol class. The 
		definitions must include a start rule with right hand side "S".
		"""
	
		self.action_handlers = {
			"shift" : self._do_shift,
			"goto" : self._do_goto,
			"reduce" : self._do_reduce,
			"accept" : self._do_accept
		}
	
		self.rules, self.symbol_classes, terminals, nonterminals = self._make_rules(ruledefs)
		
		#for r in self.rules:
		#	print "rule %s: %s" % (r,self.rules[r])
		#print ""
		
		# Find start rule
		self.start_rule = None
		for r in self.rules:
			if self.rules[r][0] ==  "S":
				self.start_rule = r
				break
		if self.start_rule == None:
			raise ParseError("Must specify start rule with lhs 'S'")
		
		self.table = self._make_table(self.rules, self.start_rule, terminals)
		
		#p = LrTablePrinter()
		#p.print_lr_table(self.table)
		
		self._reset()
	
	def _make_rules(self, ruledefs):
		"""
		Returns 4 items tuple containing the new rule dict, a dict of symbol 
			classes, the set of terminal symbols and the set of nonterminal symbols
		"""
		rules = {}
		symbol_classes = {}
		terminals = set([])
		nonterminals = set([])
		ruleparser = RuleParser()
		rulenum = 0
		for ruledef in ruledefs:
			if type(ruledef)==tuple:
				ruleclass = ruledef[1]
				ruledef = ruledef[0]
			else:
				ruleclass = None
			ruletree = ruleparser.parse_rule(ruledef)
			nonterminals.add(ruletree.children[0].children[0].data)
			if ruleclass != None:
				symbol_classes[ruletree.children[0].children[0].data] = ruleclass
			for rhs in ruletree.children[1].children:
				rhs_items = []
				for rhs_item in rhs.children:
					rhs_items.append(rhs_item.data)
					if self._is_nonterminal(rhs_item.data):
						nonterminals.add(rhs_item.data)
					else:
						terminals.add(rhs_item.data)
				ruletuple = (ruletree.children[0].children[0].data, tuple(rhs_items))							
				rules[str(rulenum)] = ruletuple 
				rulenum += 1		
		return (rules,symbol_classes,terminals,nonterminals)
	
	def _make_table(self, rules, start_rule, terminals):
		
		table = {}
		item_sets = {}
		
		# make first item set: "0"		
		first_item = ParserItem(rules, start_rule, 0)
		first_closure = self._make_item_closure(first_item)
		self._make_item_set(first_closure, item_sets)
		
		"""derive remaining sets, populating shifts and gotos in table"""
		next_set_names = ["0"]
		while True:
			next_set_names = self._make_next_item_sets(next_set_names, item_sets, 
					table, rules, start_rule, terminals)
			if len(next_set_names) == 0:
				break
		
		#print "item sets:"
		#for i in item_sets:					
		#	print "%s: %s {%s}" % (i,str(item_sets[i]),str(item_sets[i].lookup))
				
		return table
								
	def _make_item_set(self, closure, item_sets):
		"""Make an item set from set of items and add to dict under next available 
			name. Returns a tuple containing the name of the new item set (or the name 
			of an existing equivalent item set) and whether the item set is new or not."""
		new_set = ItemSet()
		for i in closure:
			new_set.add(i)
		if not new_set in item_sets.values():
			set_name = str(len(item_sets))
			item_sets[set_name] = new_set
			return (set_name,True)
		else:
			for t in item_sets.items():
				if t[1] == new_set:
					return (t[0],False)
											
	def _make_next_item_sets(self, item_set_names, item_sets, table, rules, 
			start_rule, terminals):
		"""For each item set given, follow all available symbol transitions, creating
			and adding new item sets to the dictionary as they are found, and recording
			transitions as actions in table. Returns a list containing the keys of the 
			newly created item sets"""
		new_set_names = []
		for item_set_name in item_set_names:
			item_set = item_sets[item_set_name]
			# for each symbol, find item set reached by transitioning on it
			for symbol in item_set.lookup:
				closure = set([])
				for item in item_set.lookup[symbol]:
					next_item = item.make_next_item()
					if next_item != None:
						closure = closure.union(self._make_item_closure(next_item))
				dest_item_set_name,is_new = self._make_item_set(closure, item_sets)
				# record terminal transition as shift, nonterminal as goto
				new_action = (
						"goto" if symbol!=None and self._is_nonterminal(symbol) else "shift",
						dest_item_set_name
					)
				if table.has_key((item_set_name,symbol)):
					conflicting = new_action[0]+" "+dest_item_set_name
					existing = table[(item_set_name,symbol)]
					existing = str(existing[0])+" "+str(existing[1])
					raise (ParseError("Conflict on symbol \"%s\" in state %s: %s (Cannot add \"%s\" because \"%s\" already exists)"
							% (symbol, item_set_name, str(item_set), conflicting, existing)))
				table[(item_set_name,symbol)] = new_action			
				if is_new:
					new_set_names.append(dest_item_set_name)
					# for end item set, add reduce action or accept for final rule					
					for end_rule in item_sets[dest_item_set_name].end_rules:
						if end_rule == start_rule:
							#print "add accept for %s" % dest_item_set_name
							table[(dest_item_set_name,None)] = ("accept",None)
						else:
							#print terminals
							#print terminals.union([None])
							for terminal in terminals.union([None]):
								if table.has_key((dest_item_set_name,terminal)):									
									conflicting = "reduce "+str(end_rule)
									existing = table[(dest_item_set_name,terminal)]
									existing = str(existing[0])+" "+str(existing[1])
									raise (ParseError("Conflict on symbol \"%s\" in state %s: %s (Cannot add \"%s\" because \"%s\" already exists)"
											% (terminal, dest_item_set_name, str(item_sets[dest_item_set_name]),conflicting,existing)))
								#print "add reduce for %s, %s" % (dest_item_set_name,terminal)
								table[(dest_item_set_name,terminal)] = ("reduce",end_rule)
						
		return new_set_names	
		
	def _is_nonterminal(self, symbol):
		return symbol[0].isupper()
		
	def _make_item_closure(self, item, visited_rules=set([])):	
		#print "make item closure %s" % item
		visited_rules = visited_rules.copy()
		visited_rules.add(item.rulename)
		closure = set([item])
		#print "\tget next symbol %s" % item.get_next_symbol()
		if item.get_next_symbol() != None:
			more_rules = self._find_rules(item.get_next_symbol())
			#print "\tmore rules %s" % more_rules
			for r in more_rules:
				# dont get into left recursion
				if not r in visited_rules:
					new_item = ParserItem(self.rules,r,0)
					closure = closure.union(self._make_item_closure(new_item, visited_rules))
					closure.add(new_item)	
				#else:
				#	print "\t%r in visited rules" % r
		#print "closure: %s" % closure	
		return closure
	
	def _find_rules(self, lhs):
		return [x for x in self.rules if self.rules[x][0]==lhs]
	
	def _reset(self):
		self.token_itr = None
		self.current_token = None
		self.state_stack = []
		self.input_stack = []
		self.tree = None
		self.accepted = False
	
	def _current_token(self):
		return self.current_token
		
	def _current_token_type(self):
		if self.current_token != None:
			return self.current_token.type
		else:
			return None
	
	def _current_token_value(self):
		if self.current_token != None:
			return self.current_token.data
		else:
			return None
	
	def _current_state(self):
		if len(self.state_stack) > 0:
			return self.state_stack[len(self.state_stack)-1]
		else:
			return None
			
	def _advance(self):
		self.current_token = self.token_itr.next_token()
	
	def parse(self, token_itr):
		"""
		Parses the given token iterator into a parse tree of ParserSymbol objects.
		"""

		self._reset()
		self.token_itr = token_itr
		
		self.state_stack.append("0")
		self._advance()
		
		while True:
		
			#print "state stack %s" % str(self.state_stack)
			#print "input stack %s" % str(self.input_stack)
		
			try:
				action = self.table[(self._current_state(),self._current_token_type())]
			except KeyError:
				if self._current_token_type() == None:
					raise ParseError("Unexpected end of input")
				else:
					raise ParseError("Unexpected %s token \"%s\""
							% (self._current_token_type(), self._current_token_value()))
	
			self.action_handlers[action[0]](action[1])
			
			if self.accepted:
				break
				
		# return final symbol now at top of input stack
		return self.input_stack.pop()
				
	def _do_shift(self, to_state):
		#print "shift %s" % to_state
		self.input_stack.append(self._current_token())
		self.state_stack.append(to_state)
		self._advance()		
		
	def _do_reduce(self, rule):
		#print "reduce %s" % rule
		ruledata = self.rules[rule]
		children = []
		for i in range(len(ruledata[1])):
			children.insert(0,self.input_stack.pop())
			self.state_stack.pop()
		if self.symbol_classes.has_key(ruledata[0]):
			symbclass = self.symbol_classes[ruledata[0]]
		else:
			symbclass = ParserSymbol
		new_symb = symbclass(ruledata[0],"")
		new_symb.children = children
		self.input_stack.append(new_symb)
		
		try:
			goto = self.table[(self._current_state(),ruledata[0])]
		except KeyError:
			raise ParseError("No goto found for state %s, symbol %s" 
				% (self._current_state(),ruledata[0]))
		self.action_handlers[goto[0]](goto[1])
		
	def _do_goto(self, to_state):
		#print "goto %s" % to_state
		self.state_stack.append(to_state)
		
	def _do_accept(self, dummy):
		#print "accept"
		self.accepted = True
		
		
class LrTablePrinter(ascii.Canvas):
	"""
	Class for printing out an ascii art representation of an LrParser object's 
	parsing table.
	"""
	
	def __init__(self):
		ascii.Canvas.__init__(self)
		self.state_order = []
		self.symbol_order = []
		
	def _is_nonterminal(self, symbol):
		return symbol!=None and symbol[0].isupper()
		
	def render_lr_table(self, table):
		"""
		Renders the given parse table to a string as ascii art. returns the string.
		"""
		states = set([])
		terminals = set([])
		nonterminals = set([])
		for key in table:
			states.add(key[0])
			if self._is_nonterminal(key[1]):
				nonterminals.add(key[1])
			else:
				terminals.add(key[1])
		self.state_order = [str(x) for x in sorted([int(x) for x in states])]
		self.symbol_order = sorted(terminals) + sorted(nonterminals)
		self.clear()
		
		for st in range(len(self.state_order)):
			for sy in range(len(self.symbol_order)):
				for i in range(2):
					self.set(1+(sy+1)*7+6,1+(st+1)*3+i, "|")
				for i in range(6):
						self.set(1+(sy+1)*7+i,1+(st+1)*3+2, "-")
				self.set(1+(sy+1)*7+6,1+(st+1)*3+2,"+")
				if table.has_key((self.state_order[st],self.symbol_order[sy])):
					content = table[(self.state_order[st],self.symbol_order[sy])]
					self.write(1+(sy+1)*7,1+(st+1)*3, content[0], 6)					
					self.write(1+(sy+1)*7,1+(st+1)*3+1, str(content[1]), 6)
					
		self.set(0,3,"+")
		for i in range(6):
			self.set(1+i,3,"-")
		for st in range(len(self.state_order)):
			for i in range(2):				
				self.set(0,1+(st+1)*3+i,"|")
				self.set(1+6,1+(st+1)*3+i,"|")
			self.set(0,1+(st+1)*3+2,"+")
			self.write(1,1+(st+1)*3,self.state_order[st],6)
			for i in range(6):
				self.set(1+i,1+(st+1)*3+2,"-")
			self.set(1+6,1+(st+1)*3+2,"+")
			
		self.set(1+6,0,"+")
		for i in range(2):
			self.set(1+6,1+i,"|")
		self.set(1+6,1+2,"+")
		for sy in range(len(self.symbol_order)):
			for i in range(6):
				self.set(1+(1+sy)*7+i,0,"-")
				self.set(1+(1+sy)*7+i,1+2,"-")
			self.set(1+(1+sy)*7+6,0,"+")
			self.write(1+(1+sy)*7,1,str(self.symbol_order[sy]),6)
			for i in range(2):
				self.set(1+(1+sy)*7+6,1+i,"|")
			self.set(1+(1+sy)*7+6,1+2,"+")

		return self.render()
		
	def print_lr_table(self, table):	
		"""
		Prints out the ascii representation of the given parse table
		"""
		print self.render_lr_table(table)


# ----- Testing ----------------------------------------------------------------
if __name__ == "__main__":
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
			self.assertRaises(Parse_error, self.parser.parse_re, "+")

			
		def testSets(self):
			tree = self.parser.parse_re("[ab]")
			self.assertEquals("set()",str(delve(tree,"0/0")))
			self.assertEquals("character(a)",str(delve(tree,"0/0/0")))
			self.assertEquals("character(b)",str(delve(tree,"0/0/1")))
			tree = self.parser.parse_re("[^a]")
			self.assertEquals("character(a)",str(delve(tree,"0/0/0")))
			self.assertEquals(True, delve(tree,"0/0/negate"))
			self.assertRaises(Parse_error, self.parser.parse_re, "[a")
			
		def testGroups(self):
			tree = self.parser.parse_re("(a|b)")
			self.assertEquals("group()",str(delve(tree,"0/0")))
			self.assertEquals("expression()",str(delve(tree,"0/0/0")))
			self.assertEquals("term()",str(delve(tree,"0/0/0/0")))
			self.assertEquals("character(a)",str(delve(tree,"0/0/0/0/0")))
			self.assertEquals("character(b)",str(delve(tree,"0/0/1/0/0")))
			self.assertRaises(Parse_error, self.parser.parse_re, "(")

	
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
			self.assertRaises(State_error, dfa.move, "b")
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
			self.assertRaises(State_error, dfa.move, "a")
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
			self.assertRaises(Syntax_error,l.next)
					
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
			
	class TestRuleParser(unittest.TestCase):
	
		def testConstruction(self):
			p = Rule_parser()
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
			i = Parser_item(rules, "0", 0)
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
			self.i = Parser_item(self.rules,"0",0)
			self.i2 = Parser_item(self.rules,"0",2)
			self.i3 = Parser_item(self.rules,"0",2)
			self.s = Item_set()
	
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
			self.p = Lr_parser([
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
		
			class Foo(Parser_symbol):
				def __str__(self):
					return "{%s}" % Parser_symbol.__str__(self)
 		
			self.p = Lr_parser([
				"S -> E",
				"E -> E plus B | B",
				("B -> one", Foo)
			])
			self.l.prepare("1+1+1")
			t = self.p.parse(self.l)
			self.assertEquals("E()",str(delve(t,"0")))
			self.assertEquals("{B()}",str(delve(t,"0/2")))
	
	unittest.main()

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
	
	"""
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


