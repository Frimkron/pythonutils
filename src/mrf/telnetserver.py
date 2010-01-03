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

---------------------

Telnet Server Module

Extremely basic telnet server implementation
"""

import socket
import thread
from mrf.statemachine import StateMachine
			
# Commands			
CMD_SE = 240
CMD_NOP = 241
CMD_DM = 242
CMD_BRK = 243
CMD_IP = 244
CMD_AO = 245
CMD_AYT = 246
CMD_EC = 247
CMD_EL = 248
CMD_GA = 249
CMD_SB = 250
CMD_WILL = 251
CMD_WONT = 252
CMD_DO = 253
CMD_DONT = 254
CMD_IAC = 255

# Special chars
CHR_NOTHING = 0
CHR_BACKSPACE = 8
CHR_LINE_FEED = 10
CHR_CARR_RETURN = 13


class TelnetServer(object):
	
	def __init__(self, client_class, port=23):
		self.client_class = client_class
		self.port = port
		
	def run(self):
		
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.bind(('',self.port))
		s.listen(1)
		
		self.next_id = 0
		self.handlers = {}
		try:
			while True:
				conn,addr = s.accept()
				handler = self.client_class(self,conn,self.next_id)
				self.handlers[self.next_id] = handler
				thread.start_new_thread(handler.handle_client,())
				self.next_id += 1
		finally:
			conn.close()
		
	def handle_client_arrival(self, client_id):
		pass
		
	def handle_client_departure(self, client_id):
		del(self.handlers[client_id])
		

class TelnetClientHandler(StateMachine):
	
	class StateNormal(StateMachine.State):
		def handle_char(self, char):
			if ord(char) == CMD_IAC:
				self.machine.change_state("StateIac")
			elif 31 < ord(char) < 127:
				self.machine.message += char
				self.machine.change_state("StateMessage")
			elif ord(char) == CHR_LINE_FEED:
				self.machine.handle_message(self.machine.message)
				self.machine._reset()
			
	class StateIac(StateMachine.State):
		def handle_char(self,char):
			if ord(char) in [CMD_WILL,CMD_WONT,CMD_DO,CMD_DONT]:
				self.machine.command = ord(char)
				self.machine.change_state("StateOption")
			elif ord(char) == CMD_SB:
				self.machine.change_state("StateSubnegotiation")
			else:
				self.machine.handle_command(ord(char),"")
				self.machine._reset()
				
	class StateMessage(StateMachine.State):
		def handle_char(self,char):
			if ord(char) == CHR_LINE_FEED:
				self.machine.handle_message(self.machine.message)
				self.machine._reset()
			elif 31 < ord(char) < 127:
				self.machine.message += char
			
	class StateOption(StateMachine.State):
		def handle_char(self,char):
			self.machine.message = char
			self.machine.handle_command(self.machine.command,self.machine.message)
			self.machine._reset()
			
	class StateSubnegotiation(StateMachine.State):
		def handle_char(self,char):
			if ord(char) == CMD_IAC:
				self.machine.change_state("StateSubnegIac")
			else:
				self.machine.subneg_data += char
				
	class StateSubnegIac(StateMachine.State):
		def handle_char(self,char):
			if ord(char) == CMD_SE:
				self.machine.handle_command(CMD_SB,self.machine.subneg_data)
				self.machine._reset()
				self.machine.subneg_data = ""
			else:
				self.machine.handle_command(ord(char),"")
				self.machine._reset()
	
	def __init__(self, server, socket, id):
		StateMachine.__init__(self)
		self.change_state("StateNormal")
		self.message = ''
		self.command = None
		self.subneg_data = ''
		
		self.server = server
		self.socket = socket
		self.id = id
		
	def send(self, message):
		sent = 0
		while sent < len(message):
			sent += self.socket.send(message[sent:])
		
	def handle_message(self, message):
		pass
		
	def handle_command(self, command, data):
		pass
		
	def _reset(self):
		self.message = ""
		self.command = None
		self.change_state("StateNormal")
		
	def handle_client(self):
		self.server.handle_client_arrival(self.id)
		self._reset()
		self.subneg_data = ""
		while True:
			data = self.socket.recv(1024)
			if not data: break
			while len(data) > 0:
				c = data[0]
				data = data[1:]
				self.handle_char(c)
		self.server.handle_client_departure(self.id)
			

# -------------------- Testing ------------------------------------------

if __name__ == "__main__":

	class MudTest(TelnetServer):
		
		def __init__(self):
			TelnetServer.__init__(self, MudTestHandler)
		
		def handle_client_arrival(self, client_id):
			TelnetServer.handle_client_arrival(self, client_id)
			print "Client %d arrived" % client_id
			
		def handle_client_departure(self, client_id):
			TelnetServer.handle_client_departure(self, client_id)
			print "Client %d departed" % client_id
			
		def run(self):
			print "Running..."
			TelnetServer.run(self)
			print "...Finished"
			
		def send_to_all(self, message):
			for id in self.handlers:
				self.handlers[id].send(message)
			
	
	class MudTestHandler(TelnetClientHandler):
		
		def handle_command(self, command, data):
			print "client %d: COMMAND %d %s" % (self.id, command, data)
			
		def handle_message(self, message):
			print "client %d: %s" % (self.id, message) 
			self.server.send_to_all("%d says: %s\n" % (self.id,message))
				
	
	
	mud = MudTest()
	mud.run()	
		
