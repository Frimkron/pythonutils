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

class StateMachine(object):

    class State(object):
        
        def __init__(self, mach):
            self.machine = mach
       
    def __init__(self):
        #initialise state member to no state
        self.state = None
        #find States defined in class and store new instance of each in states dict
        self.states = {}
        for membkey in self.__class__.__dict__:
            memb = self.__class__.__dict__[membkey]
            if type(memb) == type and issubclass(memb, StateMachine.State):                
                self.states[membkey] = memb(self)                
       
    def __getattribute__(self, attr):
        if attr != "state" and hasattr(self, "state") and self.state != None:
            try:
                return self.state.__getattribute__(attr)
            except AttributeError, error:
                return object.__getattribute__(self, attr)
        else:
            return object.__getattribute__(self, attr)
        
    def change_state(self, statename):
        self.state = self.states[statename]
        


        
            