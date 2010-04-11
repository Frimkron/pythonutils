"""	
Copyright (c) 2010 Mark Frimston

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

---------------------

Command Line Module

Utilities for command line apps.
"""

def yes_no_validator(string):
	if string.lower() in ("y","yes"):
		return True
	elif string.lower() in ("n","no"):
		return False
	else:
		raise ValueError()

def prompt(text,validator=str,invalid="Please enter a valid value"):
	"""	
	validator is a function which takes a string and returns the converted
	value, or raises ValueError if the value is invalid. For example, to
	require and integer value, the "int" function can be used.
	"""
	while True:
		string = raw_input(text).strip()
		try:
			value = validator(string)
			return value
		except ValueError:
			print invalid

def menu(items,prompt_text="Enter a selection: ",title="Menu\n----",option="%s) %s"):
	"""	
	Takes either a list/tuple or dictionary of menu options. For a list, 
	the options are numbered, requiring the user to enter a number. For
	a dictionary, the keys are used as the values the user should enter.	
	"""
	options = None
	values = None
	if isinstance(items,dict):		
		options = [str(k) for k in sorted(items.keys())]
		values = [items[k] for k in sorted(items.keys())]
	else:
		options = [str(i+1) for i in range(len(items))]
		values = items[:]
			
	print title
	for i in range(len(items)):
		print option % (options[i],str(values[i]))
		
	choice = prompt(prompt_text,lambda s: options.index(s),"Please enter a valid menu choice")
	return values[choice]


