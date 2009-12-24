import socket
import thread

class Server(object):

	def __init__(self, client_class, port):
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


class Node(object):

	def __init__(self, encoder, decoder):
		self.encoder = encoder
		self.decoder = decoder

	def get_socket(self):
		pass

	def send(self, message):
		sent = 0
		while sent < len(message):
			sent += self.get_socket().send(message[sent:])

	def received(self, message):
		pass

	def listen_on_socket(self):
		while True:
			data = self.get_socket().recv(1024)
			if not data: break
			message = self.decoder.decode(data)
			self.received(message)


class ClientHandler(Node):

	def __init__(self, server, socket, id, encoder, decoder):
		Node.__init__(self, encoder, decoder)
		self.server = server
		self.socket = socket
		self.id = id

	def get_socket(self):	
		return self.socket

	def handle_client(self):
		self.server.handle_client_arrival(self.id)		
		self.listen_on_socket()
		self.server.handle_client_departure(self.id)

	def received(self, message):
		recips = message.get_recipients()

		if message.is_for_server():
			# TODO message to server

		for c in message.get_client_recipients():
			self.server.handlers[c].send(message)


class Client(Node):

	def run(self):
		pass


class Message(object):

	RECIPIENT_SERVER = -1
	RECIPIENT_ALL_CLIENTS = -2
	RECIPIENT_ALL_OTHER_CLIENTS = -3
	RECIPIENT_ALL = -4

	def get_recipients(self):
		pass

	def is_for_server(self):
		recips = self.get_recipients()
		return ( Message.RECIPIENT_SERVER in recips
				or Message.RECIPIENT_ALL in recips )
		
	def get_client_recipients(self, clients, sender):
		recips = self.get_recipients()
		list = []
		for c in clients:
			if( c in recips
					or Message.RECIPIENT_ALL in recips
					or Message.RECIPIENT_ALL_CLIENTS in recips
					or (Message.RECIPIENT_ALL_OTHERS in recips and c!=sender) ):
				list.append(c)
		return list
