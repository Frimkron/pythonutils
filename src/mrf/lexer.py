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

class Parse_error(Exception):
	pass
	
class Re_symbol(object):
	pass

class Re_parser(object):
	
	def parse_re(self, input):
		self.input = input
		self.pos = 0
		
		exp = self._parse_expression()
		if self._current_char() != None:
			raise Parse_error("Expected end of input at char %d" % self.pos)		
			
		return exp
		
	def _current_char(self):
		if self.pos >= len(self.input):
			return None
		else:
			return self.input[self.pos]
			
	def _parse_expression(self):
		retval = Re_symbol()
		retval.type = "expression"
		retval.children = []
		while self._current_char() != None and not self._current_char() in [')','|']:
			retval.children.append(self._parse_term())
		return retval
			
	def _parse_term(self):
		if self._current_char() in ['+','*',']','?','}',')','|']:
			raise Parse_error("Unexpected start of term '%s' at char %d" % (self._current_char(),self.pos))		
		elif self._current_char() == '.':
			item = Re_symbol()
			item.type = "any_character"
			self.pos+=1
		elif self._current_char() == '[':
			item = self._parse_set()
		elif self._current_char() == '(':
			item = self._parse_group()
		else:
			item = self._parse_character()
			
		retval = Re_symbol()
		retval.type = "term"
		retval.children = [item]
		
		if self._current_char() != None:
			if self._current_char() == '?':
				mod = Re_symbol()
				mod.type = "quantifier"
				mod.data = (0,1)
				retval.children.append(mod)
				self.pos+=1
			elif self._current_char() == '*':
				mod = Re_symbol()
				mod.type = "quantifier"
				mod.data = (0,-1)
				retval.children.append(mod)
				self.pos+=1
			elif self._current_char() == '+':
				mod = Re_symbol()
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
				raise Parse_error("Unexpected end of input at char %d" % self.pos)
		if not( ord('0') <= ord(self._current_char()) <= ord('9') ):
			raise Parse_error("Expected value in quantifier at char %d" % self.pos)	 
		while not self._current_char() in [',','}']:
			if self._current_char() == None:
				raise Parse_error("Unexpected end of input at char %d" % self.pos)
			if not( ord('0') <= ord(self._current_char()) <= ord('9') ):
				raise Parse_error("Expected value in quantifier at char %d" % self.pos)
			min += self._current_char()
			self.pos+=1
		min = int(min)
		if self._current_char() == ',':
			self.pos+=1
			if self._current_char() != '}':
				while not self._current_char()=='}':
					if self._current_char() == None:
						raise Parse_error("Unexpected end of input at char %d" % self.pos)
					if not( ord('0') <= ord(self._current_char()) <= ord('9') ):
						raise Parse_error("Expected value in quantifier at char %d" % self.pos)
					max += self._current_char()
					self.pos+=1
				max = int(max)
			else:
				max = -1
		else:
			max = min
		self.pos+=1
		
		retval = Re_symbol()
		retval.type = "quantifier"
		retval.data = (min,max)
		return retval
		
			
	def _parse_character(self):
		if self._current_char() == '\\':
			return self._parse_escape()
		else:
			retval = Re_symbol()
			retval.type = "character"
			retval.data = self._current_char()
			self.pos+=1
			return retval
			
	def _parse_escape(self):
		self.pos+=1
		if self._current_char() == None:
			raise Parse_error("Unexpected end of input at char %d" % self.pos)
		elif self._current_char() == 'n':
			retval = Re_symbol()
			retval.type = "character"
			retval.data = "\n"
			self.pos+=1
			return retval
		elif self._current_char() == 'r':
			retval = Re_symbol()
			retval.type = "character"
			retval.data = "\r"
			self.pos+=1
			return retval
		elif self._current_char() == 't':
			retval = Re_symbol()
			retval.type = "character"
			retval.data = "\t"
			self.pos+=1
			return retval
		else:
			retval = Re_symbol()
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
		
		retval = Re_symbol()
		retval.type = "set"
		retval.negate = negate
		retval.children = []
		while self._current_char() != ']':
			if self._current_char() == None:
				raise Parse_error("Unexpected end of input at char %d" % self.pos)
			if self._current_char() == '-':
				item = Re_symbol()
				item.type = "range_marker"
				retval.children.append(item)
				self.pos+=1
			else:
				retval.children.append(self._parse_character())
			
		if self._current_char() == None:
			raise Parse_error("Unexpected end of input at char %d" % self.pos)
		
		self.pos+=1
		return retval
		
	def _parse_group(self):
		self.pos+=1
		retval = Re_symbol()
		retval.type = "group"
		retval.children = []
		
		if self._current_char() != ')':
			if self._current_char() == None:
				raise Parse_error("Unexpected end of input at char %d" % self.pos)
			retval.children.append(self._parse_expression())
		
		while self._current_char() != ')':
			if self._current_char() == None:
				raise Parse_error("Unexpected end of input at char %d" % self.pos)
			elif self._current_char() != '|':
				raise Parse_error("Expected '|' at char %d" % self.pos)
			self.pos+=1
			retval.children.append(self._parse_expression())				
				
		self.pos+=1
		return retval
		
		
def print_re_tree(re, indent=0):
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
			

class State_error(Exception):
	pass

class Nf_automaton(object):

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
		self.start_state = name
		
	def add_end_state(self, name, label_only=False):
		if not label_only:
			self.states[name] = {}
		self.end_states.add(name)
		
	def add_state(self, name):
		self.states[name] = {}
		
	def add_trans(self, fr, to, vals):
		for v in vals:
			if not self.states[fr].has_key(v):
				self.states[fr][v] = []
			self.states[fr][v].append(to)
	
	def add_state_data(self, state, data):
		self.state_data[state] = data
		
	def make_dfa(self):
		if self.start_state == None:
			raise State_error("No start state")
		dfa = Df_automaton()		
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
				if not t == Nf_automaton.EMPTY:
					new_state_name = self._make_dfa_state(dfa, combined_trans[t])
					dfa.add_trans(state_name, new_state_name, [t])
			
		return state_name
		
	def _make_closure(self, state_set, states):
		for s in states:
			state_set.add(s)
			for t in self.states[s]:
				if t == Nf_automaton.EMPTY:
					for s2 in self.states[s][t]:
						if not s2 in state_set:
							self._make_closure(state_set, [s2])
		
	def get_start_state(self):
		return self.start_state
							
	def get_states(self):
		return self.states.keys()
		
	def get_transitions(self):
		out = []
		for s in self.states:
			for t in self.states[s]:
				for ts in self.states[s][t]:
					out.append((s,ts,t))
		return out
	
		
class Df_automaton(Nf_automaton):
	
	def __init__(self):
		Nf_automaton.__init__(self)
		self.current_state = None
		self.reset()
		
	def add_trans(self, fr, to, vals):
		for v in vals:
			if v == Nf_automaton.EMPTY:
				raise State_error("deterministic automata may not use empty transitions")
			self.states[fr][v] = to
		
	def reset(self):
		self.current_state = self.start_state
			
	def move(self, value):
		if self.current_state == None:
			raise State_error("Not in state")
		if not self.states[self.current_state].has_key(value):
			raise State_error("No transition on \"%s\" in state \"%s\"" % (value,self.current_state))
		new_state = self.states[self.current_state][value]
		if not self.states.has_key(new_state):
			raise State_error("State \"%s\" does not exist" % new_state)
		self.current_state = new_state
		
	def is_at_end(self):
		return self.current_state in self.end_states
		
	def get_state(self):
		return self.current_state
		
	def get_transitions(self):
		out = []
		for s in self.states:
			for t in self.states[s]:				
				out.append((s,self.states[s][t],t))
		return out
		

class Re_compiler(object):

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
		self.tree = tree
		nfa = Nf_automaton()
		
		state_name = self._gen_state_name()
		nfa.add_state(state_name)
		nfa.set_start_state(state_name)
		
		start_state,end_state = self._build_symbol(tree, nfa, state_name)		
		nfa.add_end_state(end_state, True)
		return nfa	
		
	def make_dfa(self, tree):
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
				raise State_error("max quantity less than min quantity")
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
				nfa.add_trans(ti_start,ti_end,[Nf_automaton.EMPTY])
			if i==num_times-1 and max_times==-1:
				nfa.add_trans(ti_end,ti_start,[Nf_automaton.EMPTY])
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
		nfa.add_trans(trans_from,state_name,Re_compiler.ALL_CHARS)
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
					raise Parse_error("Incorrect character order for character range in set")
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
			for c in Re_compiler.ALL_CHARS:
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
			nfa.add_trans(e_end,back_state,[Nf_automaton.EMPTY])
		return term_start,term_end
		
	def _build_link_state(self, nfa, trans_from):
		state = self._gen_state_name()
		nfa.add_state(state)
		nfa.add_trans(trans_from,state,[Nf_automaton.EMPTY])
		return state
		
	def _gen_state_name(self):
		state_name = str(self.next_state)
		self.next_state+=1
		return state_name
		
		
class Re_matcher(object):		
		
		def __init__(self, re):								
			p = Re_parser()
			tree = p.parse_re(re)
			#print_re_tree(tree)
			#print "---------------------------"
			
			c = Re_compiler()
			nfa = c.make_nfa(tree)
			#pr = Sa_printer()
			#pr.print_automaton(nfa)
			#print "---------------------------"
			
			self.dfa = nfa.make_dfa()
			#pr.print_automaton(self.dfa)

		def matches(self, input):
			self.dfa.reset()
			try:
				for c in input:
					self.dfa.move(c)	
			except State_error:
				return False
			if not self.dfa.is_at_end():
				return False
			return True
		

class Ascii_canvas(object):
	
	def __init__(self):
		self.clear()
		
	def clear(self):
		self.grid = {}
		self.width = 0
		self.height = 0
		
	def set(self, x, y, char):
		self.grid[(x,y)] = char
		if x >= self.width:
			self.width = x+1
		if y >= self.height:
			self.height = y+1
	
	def get(self, x, y):
		if self.grid.has_key((x,y)):
			return self.grid[(x,y)]
		else:
			return ' '
			
	def write(self, x,y, text, maxlength=-1):
		i = 0
		for c in text:
			if maxlength!=-1 and i>=maxlength:
				break
			self.set(x,y,c)
			x+=1
			i+=1
	
	def render(self):
		str = ""
		for j in range(self.height):
			for i in range(self.width):		
				str += self.get(i,j)
			str += "\n"
		return str
			
	def print_out(self):
		print self.render()

class Sa_printer(Ascii_canvas):

	def __init__(self):
		self.arrowed = set([])
		self.state_order = {}
		
	def render_automaton(self, automaton):
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
		print self.render_automaton(automaton)		
		

class Syntax_error(Exception):
	pass

class Lexer(object):

	END_OF_INPUT = 0

	def __init__(self, token_defs):
		"""
		token_defs = [("myToken","a+"),("myOtherToken",[0-9]{0,3})]
		"""
		self.next_state=0
		self.prepare("")
		
		self.dfa = self.make_dfa(token_defs)
		
	def prepare(self, input):
		self.input = input
		self.pos = 0
		
	def make_dfa(self, token_defs):
	
		self.next_state=0
		parser = Re_parser()
		compiler = Re_compiler()
		
		nfa = Nf_automaton()
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
					nfa.add_trans(start_state,state_mapping[s],[Nf_automaton.EMPTY])
					
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
		t = self.next_token()
		if t == None:
			raise StopIteration
		return t
		
	def next_token(self):
		if self._current_char() == Lexer.END_OF_INPUT:
			return None
		self.dfa.reset()
		buffer = ""
		try:
			while True:
				self.dfa.move(self._current_char())
				buffer += self._current_char()
				self._advance()
		except State_error:
			if self.dfa.is_at_end():
				return (self.dfa.state_data[self.dfa.current_state][0], buffer)	
			else:
				raise Syntax_error("Syntax error at \"%s\"" % self._current_char())

"""
Rule syntax:
	Ru -> Lhs separator Rhs
	Lhs -> nonterminal
	Rhs -> T ("|" T)*
	T -> (terminal|nonterminal)+
"""

class Rule_symbol(object):
	pass

class Rule_parser(object):

	def __init__(self):
		self.lexer = Lexer([
			("whitespace", "[ \t\n\r]+"),
			("terminal","[a-z][a-zA-Z0-9_-]*"),
			("nonterminal", "[A-Z][a-zA-Z0-9_-]*"),
			("separator", "->"),
			("or", "\|")
		])	

	def parse_rule(self, rule):
		self.lexer.prepare(rule)
		self._advance()
		
		out = Rule_symbol()
		out.type = "rule"
		out.children = []
		
		if self._current_token_type() != "nonterminal":
			raise Parse_error("Expected Non-terminal, found %s" % self._current_token_type())
		lhs = Rule_symbol()
		lhs.type="lhs"
		lhs.data = self._current_token()
		out.children.append(lhs)
		self._advance()	
		
		if self._current_token_type() != "separator":
			raise Parse_error("Expected separator, found %s" % self._current_token_type())
		self._advance()
		
		rhs = self._parse_rhs()
		out.children.append(rhs)
		self._advance()
		
		if self._current_token() != None:
			raise Parse_error("Expected end of input ,found %s" % self._current_token_type())
			
		return out
		
	def _parse_rhs(self):
		out = Rule_symbol()
		out.type = "rhs"
		out.children = []
		
		while(True):
			term = self._parse_term()
			out.children.append(term)
			
			if self._current_token_type() != "or":
				break
			else:
				self._advance()
				
		return out
		
	def _parse_term(self):
		out = Rule_symbol()
		out.type = "term"
		out.data = []
		
		if not self._current_token_type() in ["terminal","nonterminal"]:
			raise Parse_error("Expected Terminal or Non-terminal, found %s" % self._current_token_type())
		
		while True:
			out.data.append(self._current_token())
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
			return self.current_token[0]	
	
	def _advance(self):
		# skip over whitespace 
		while True:
			self.current_token = self.lexer.next_token()
			if self.current_token==None or self.current_token[0] != "whitespace":
				break


class Parser_symbol(object):
	pass	
	
class Parser_item(object):

	def __init__(self, rules, rulename, position):
		self.rules = rules
		self.rulename = rulename
		self.position = position
		
	def get_next_symbol(self):
		if self.position < len(self.rules[self.rulename][1]):
			return self.rules[self.rulename][1][self.position]
		else:
			return None
			
	def make_next_item(self):
		if self.position < len(self.rules[self.rulename][1]):
			next_pos = self.position + 1
			return Parser_item(self.rules, self.rulename, next_pos)
		else:
			return None
			
	def __eq__(self, other):
		return( self.rules==other.rules and self.rulename==other.rulename 
				and self.position==other.position )			
		
	def __ne__(self, other):
		return( self.rules!=other.rules or self.rulename!=other.rulename
				or self.position!=other.position )
	
class Lr_parser(object):

	def __init__(self, ruledefs):
	
		self.action_handlers = {
			"shift" : self._do_shift,
			"goto" : self._do_goto,
			"reduce" : self._do_reduce,
			"accept" : self._do_accept
		}
	
		self.rules = self._make_rules(ruledefs)
		
		# Find start rule
		self.start_rule = None
		for r in self.rules:
			if self.rules[r][0] ==  "S":
				self.start_rule = r
				break
		if self.start_rule == None:
			raise Parse_error("Must specify start rule with lhs 'S'")
		
		self.table = self._make_table()
		
		self._reset()
	
		# temporary
		self.table = {
			("0","zero") 	: ("shift","1"),
			("0","one")		: ("shift","2"),
			("0","E")			: ("goto","3"),
			("0","B")			: ("goto","4"),
			("1","times")	: ("reduce","4"),
			("1","plus")	: ("reduce","4"),
			("1","zero")	: ("reduce","4"),
			("1","one")		: ("reduce","4"),
			("1",None)		: ("reduce","4"),
			("2","times")	: ("reduce","5"),
			("2","plus")	: ("reduce","5"),
			("2","zero")	: ("reduce","5"),
			("2","one")		: ("reduce","5"),
			("2",None)		: ("reduce","5"),
			("3","times")	: ("shift","5"),
			("3","plus")	: ("shift","6"),
			("3",None)		: ("accept",None),
			("4","times")	: ("reduce","3"),
			("4","plus")	: ("reduce","3"),
			("4","zero")	: ("reduce","3"),
			("4","one")		: ("reduce","3"),
			("4",None)		: ("reduce","3"),
			("5","zero")	: ("shift","1"),
			("5","one")		: ("shift","2"),
			("5","B")			: ("goto","7"),
			("6","zero")	: ("shift","1"),
			("6","one")		: ("shift","2"),
			("6","B")			: ("goto","8"),
			("7","times") : ("reduce","1"),
			("7","plus")	: ("reduce","1"),
			("7","zero")	: ("reduce","1"),
			("7","one")		: ("reduce","1"),
			("7",None)		: ("reduce","1"),
			("8","times")	: ("reduce","2"),
			("8","plus")	: ("reduce","2"),
			("8","zero")	: ("reduce","2"),
			("8","one")		: ("reduce","2"),
			("8",None)		: ("reduce","2")
		}
	
	def _make_rules(self, ruledefs):
		rules = {}
		ruleparser = Rule_parser()
		rulenum = 1
		for ruledef in ruledefs:
			ruletree = ruleparser.parse_rule(ruledef)
			for rhs in ruletree.children[1].children:
				ruletuple = tuple([
						ruletree.children[0].data[1],
						tuple([x[1] for x in rhs.data])
				])							
				rules[str(rulenum)] = ruletuple 
				rulenum += 1		
		return rules
	
	def _make_table(self):
		
		item_sets = []
		
		# make first item set		
		first_item = Parser_item(self.rules, self.start_rule, 0)
		first_set = self._make_item_closure(first_item)
		item_sets.append(first_set)
		
		""" TODO: need to make note of symbol being moved over in order
			to build table correctly""" 
		
		# derive remaining sets
		next_sets = [first_set]
		while True:
			next_sets = self._make_next_item_sets(next_sets, item_sets)
			if len(next_sets) == 0:
				break
			for s in next_sets:
				item_sets.append(s)
				
		
		
	def _make_next_item_sets(self, item_sets, set_list):
		new_sets = []
		for item_set in item_sets:
			for item in item_set:
				new_item = item.make_next_item()
				new_set = self._make_item_closure(new_item)
				if not new_set in set_list:
					new_sets.append(new_set)			
		return new_sets	
		
	def _make_item_closure(self, item):
		closure = set([])
		if item.get_next_symbol() != None:
			more_rules = self._find_rules(item.get_next_symbol())
			for r in more_rules:
				new_item = Parser_item(self.rules,r,0)
				closure = closure.union(self._make_item_closure(new_item))
				closure.add(new_item)
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
		next_token = self.token_itr.next_token()
		if next_token != None:
			self.current_token = Parser_symbol()
			self.current_token.type = next_token[0]
			self.current_token.data = next_token[1]
		else:
			self.current_token = None
	
	def parse(self, token_itr):

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
					raise Parse_error("Unexpected end of input")
				else:
					raise Parse_error("Unexpected %s token \"%s\""
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
		new_symb = Parser_symbol()
		new_symb.type = ruledata[0]
		new_symb.children = children
		self.input_stack.append(new_symb)
		
		try:
			goto = self.table[(self._current_state(),ruledata[0])]
		except KeyError:
			raise Parse_error("No goto found for state %s, symbol %s" 
				% (self._current_state(),ruledata[0]))
		self.action_handlers[goto[0]](goto[1])
		
	def _do_goto(self, to_state):
		#print "goto %s" % to_state
		self.state_stack.append(to_state)
		
	def _do_accept(self, dummy):
		#print "accept"
		self.accepted = True
		

l = Lexer([
	("times","\*"),
	("plus","\+"),
	("one","1"),
	("zero","0")
])			
l.prepare(sys.argv[1])
p = Lr_parser([
	"E -> E times B",
	"E -> E plus B",
	"E -> B",
	"B -> one",
	"B -> zero"
])
tree = p.parse(l)
print_re_tree(tree)





