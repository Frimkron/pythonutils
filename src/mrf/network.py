import socket
import thread
import threading
import json
import sys
import time
from mrf.statemachine import StateMachineBase, statemethod

"""	
TODO:
 * GameClientHandler should similarly perform handshake - not add client to pool until negotiated.
	Do this by having server delegate handling of connect request to stateful client handler.
	Server should group clients in different ways - should have separate group for connected
	players, for purposes of counting players, etc.
 * GameServer/GameClient classes which throw these messages around
 * Refactor telnet module to use generic client/server classes
 * Unit tests for client/server

             Node                 SkListener		SkListener:		
            ^ ^ ^                   ^ ^				send
    ,-------' | '--2----. ,----1----' |				received
 Server    GameNode    Client       ClHandler		
    ^         ^  ^        ^ 	      ^			Node:
    '--2----. |1 '--1---. |2          |				send
          GameServer   GameClient  GameClHandler		received

"""

class Node(object):
	"""	
	Base class for all nodes in the network i.e. clients and server
	"""
	
	def send(self, message):
		pass

	def received(self, message):
		pass

	def get_node_id(self):
		pass

class Server(Node):	
	"""	
	A socket server
	"""

	def __init__(self, client_class, port):
		self.client_class = client_class
		self.port = port

	def run(self):
		"""	
		Runs the server, listening on the specified port for new clients connecting.
		For each new client a client handler of the specified type is created in a new
		thread.
		"""

		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			s.bind((socket.gethostname(),self.port))
			s.listen(1)
		
			self.next_id = 0
			self.handlers = {}
		
			while True:
				conn,addr = s.accept()
				handler = self.client_class(self,conn,self.next_id)
				self.handlers[self.next_id] = handler
				thread.start_new_thread(handler.handle_client,())
				self.next_id += 1
		finally:
			s.close()
	
	def handle_client_arrival(self, client_id):
		"""	
		Client with given id has connected
		"""
		pass
		
	def handle_client_departure(self, client_id):
		"""	
		Client with given id has departed. Removes the associated
		handler.
		"""
		del(self.handlers[client_id])

	def received(self, message):
		"""	
		Message to server received	
		"""
		pass

	def send(self, message):
		"""	
		Request appropriate handlers send message to their clients
		"""
		recips = message.get_recipients()

		if message.is_for_server():
			self.received(message)

		for c in message.get_client_recipients():
			if self.handlers.has_key(c):
				self.handlers[c].send(message)

	def get_node_id(self):
		return -1

	def get_num_clients(self):
		return len(self.handlers)

class SocketListener(object):
	"""	
	Base class for client socket listeners
	"""

	def __init__(self, encoder, decoder):
		self.encoder = encoder
		self.decoder = decoder
		self.send_lock = threading.Lock()		

	def get_socket(self):
		"""	
		Should return the socket
		"""
		pass

	def send(self, message):
		"""	
		Encodes the given message and sends it down the socket.
		Only one thread may enter at a time.
		"""
		with self.send_lock:
			data = self.encoder.encode(message)
			sent = 0
			while sent < len(data):
				sent += self.get_socket().send(data[sent:])

	def received(self, message):
		"""	
		Invoked when a message is received on the socket
		"""
		pass

	def listen_on_socket(self):
		"""	
		Blocks, waiting for messages on the socket
		"""
		try:
			while True:
				data = self.get_socket().recv(1024)
				if not data: break
				message = self.decoder.decode(data)
				self.received(message)
		finally:
			self.get_socket().close()


class ClientHandler(SocketListener):
	"""	
	A client handler which handles messages from a single client
	on the server.
	"""

	def __init__(self, server, socket, id, encoder, decoder):
		SocketListener.__init__(self, encoder, decoder)
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
		"""	
		When the client handler receives a message from its socket, it
		passes it on to the server for dispatching to its intended recipients.
		The handler ensures that the message's "sender" field is set correctly.
		"""
		message.sender = self.id
		self.server.send(message)


class Client(SocketListener, Node):
	"""	
	Socket client
	"""

	def __init__(self, host, port):
		self.host = host
		self.port  = port
		self.client_id = -1

	def run(self):
		
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.connect((self.host, self.port))
		self.listen_on_socket()

	def get_socket(self):
		return self.socket

	def get_node_id(self):
		return self.client_id

class Message(object):
	"""	
	Base class for network messages
	"""

	RECIPIENT_SERVER = -1
	RECIPIENT_ALL_CLIENTS = -2
	RECIPIENT_ALL_OTHER_CLIENTS = -3
	RECIPIENT_ALL = -4

	SENDER_SERVER = -1

	def __init__(self, recipients, sender=-1):
		"""	
		Initializes the message with the given recipient list and 
		sender id.
		"""
		self.recipients = recipients
		self.sender = sender

	def get_recipients(self):
		"""	
		Returns the list of recipients, which may include special constants
		to represent groups of recipients such as Message.RECIPIENT_ALL_CLIENTS
		"""
		return self.recipients

	def get_sender(self):
		return self.sender

	def is_for_server(self):
		"""	
		Returns True if the server is included in the recipients for this message
		"""
		recips = self.get_recipients()
		return ( Message.RECIPIENT_SERVER in recips
				or Message.RECIPIENT_ALL in recips )
		
	def get_client_recipients(self, clients, sender):
		"""	
		Returns an explicit list of client ids obtained from the message recipients.
		Constants such as Message.RECIPIENT_ALL_CLIENTS are expanded.
		"""
		recips = self.get_recipients()
		list = []
		for c in clients:
			if( c in recips
					or Message.RECIPIENT_ALL in recips
					or Message.RECIPIENT_ALL_CLIENTS in recips
					or (Message.RECIPIENT_ALL_OTHERS in recips and c!=sender) ):
				list.append(c)
		return list

	def _get_attrs(self, names):
		"""	
		Helper method to extract named attributes as dictionary
		"""
		d = {}
		for k in names:
			d[k] = getattr(self, k)
		return d

	def to_dict(self):
		"""	
		Should be implemented to convert the message data to a dictionary for subsequent
		serialisation for transport. Need not include the message type, recipients or sender.
		"""
		return self._get_attrs(())
	

	def from_dict(self, dict):
		"""	
		Should be implemented to populate the message instance with the data from the 
		given dictionary.
		"""
		for k in dict:
			setattr(self, k, dict[k])

class MessageError(Exception):
	pass

class JsonEncoder(object):

	def encode(self, message):
		data = message.to_dict()
		dict = {
			"type" : message.__module__+"."+message.__class__.__name__,
			"recipients" : message.get_recipients(),
			"sender" : message.get_sender(),
			"data" : data
		}
		return json.dumps(dict)

	def decode(self, data):
		dict = json.loads(data)
		
		typename = dict["type"]
		classname = typename.split(".")[-1]
		modname = ".".join(typename.split(".")[:-1])

		if not sys.modules.has_key(modname):
			raise MessageError("Module for message type %s not loaded" % typename)
		mod = sys.modules[modname]
		if not hasattr(mod, classname):
			raise MessageError("Message class %s not found" % typename)
		cls = getattr(mod, classname)
		if not issubclass(cls,Message):
			raise MessageError("Message type %s is not a Message" % typename)

		message = cls(dict["recipients"], dict["sender"])
		message.from_dict(dict["data"])
		return message


class MsgPlayerConnect(Message):
	"""	
	Sent by server to inform clients of a new player's arrival
	"""

	def __init__(self, recipients, sender=-1, player_id=-1, name=""):
		Message.__init__(self, recipients, sender)
		self.player_id = player_id
		self.name = name

	def to_dict(self):
		return self._get_attrs(("player_id","name"))
		

class MsgPlayerDisconnect(Message):
	"""		
	Sent by server to inform clients of a players' departure
	"""

	def __init__(self, recipients, sender=-1, player_id=-1, reason=""):
		Message.__init__(self, recipients, sender)
		self.player_id = player_id
		self.reason = reason

	def to_dict(self):
		return self._get_attrs(("player_id","reason"))
		

class MsgServerShutdown(Message):
	"""	
	Sent by server to inform clients that the server is about to stop
	"""

	def __init__(self, recipients, sender=-1):
		Message.__init__(self, recipients, sender)

	def to_dict(self):
		return self._get_attrs(())

class MsgRequestConnect(Message):
	"""	
	Sent from client to server when first connected to provide information
	about the player. Server should respond with either MsgAcceptConnect
	or MsgRejectConnect. 
	"""
	
	def __init__(self, recipients, sender=-1, name=""):
		Message.__init__(self, recipients, sender)
		self.name = name

	def to_dict(self):
		return self._get_attrs(("name",))

class MsgAcceptConnect(Message):
	"""	
	Sent from server to client to confirm their acceptence into the game,
	provide their client id and provide the player with information about
	the other players connected.
	"""

	def __init__(self, recipients, sender=-1, player_id=-1, player_info=None):
		Message.__init__(self, recipients, sender)
		self.player_id = player_id
		self.player_info = player_info

	def to_dict(self):
		return self._get_attrs(("player_id","player_info"))

class MsgRejectConnect(Message):
	"""	
	Sent from server to client to indicate that connection to the game was
	unsuccessful.
	"""

	def __init__(self, recipients, sender=-1, reason=""):
		Message.__init__(self, recipients, sender)
		self.reason = reason

	def to_dict(self):
		return self._get_attrs(("reason",))

class MsgPing(Message):
	"""	
	Sent between client and server for calculaating network latency	
	"""

	def __init__(self, recipients, sender=-1, timestamp=0):
		Message.__init__(self, recipients, sender)
		self.timestamp = timestamp

	def to_dict(self):
		return self._get_attrs(("timestamp",))

class MsgPong(MsgPing):
	"""	
	Sent in response to MsgPing
	"""

class MsgChat(Message):
	"""	
	Sent between clients to allow players to communicate with each other	
	"""

	def __init__(self, recipients, sender=-1, message=""):
		Message.__init__(self, recipients, sender)
		self.message = message

	def to_dict(self):
		return self._get_attrs(("message",))


class GameNode(Node):
	"""	
	Base class for all nodes (clients & server) in the game network
	"""
	
	def get_timestamp(self):
		return int(time.time()*1000)

	def received(self, message):
		"""	
		Dispatches message to appropriate handler method using naming convention
		"""
		typename = message.__class__.__name__
		methname = "handle_"+typename
		if hasattr(self, methname):
			meth = getattr(self, methname)
			meth(message)
		else:
			raise MessageError("No handler method for message type %s" % typename)

	def handle_MsgPlayerConnect(self, message):
		pass

	def handle_MsgPlayerDisconnect(self, message):
		pass

	def handle_MsgServerShutdown(self, message):
		pass
	
	def handle_MsgRequestConnect(self, message):
		pass

	def handle_MsgAcceptConnect(self, message):
		pass

	def handle_MsgRejectConnect(self, message):
		pass

	def handle_MsgPing(self, message):
		# respond with pong
		resp = MsgPong([message.sender], self.get_node_id(), self.get_timestamp())
		self.send(resp)

	def handle_MsgPong(self, message):
		pass

	def handle_MsgChat(self, message):
		pass

class GameClientHandler(ClientHandler, StateMachineBase):
	"""	
	ClientHandler used by GameServer
	"""
	
	class StateConnecting(StateMachineBase.State):
		
		def connect_request(self, message):
			#TODO
			pass

	class StateInGame(StateMachineBase.State):
		pass

	def __init__(self, server, socket, id, encoder, decoder):
		ClientHandler.__init__(self, server, socket, id, encoder, decoder)
		StateMachineBase.__init__(self)
		self.change_state("StateConnecting")

	@statemethod
	def connect_request(self, message):
		pass

class GameServer(GameNode, Server):
	"""	
	Basic game server for use with GameClient
	"""
	
	def __init__(self, max_players=4, client_class=GameClientHandler, port=570810):
		"""	
		Initialises the server with default handler GameClientHandler and using
		port 570810 (sto-blo)
		"""
		GameNode.__init__(self)
		Server.__init__(self, client_class, port)
		self.max_players = max_players

	def send(self, message):
		Server.send(self.message)

	def received(self, message):
		GameNode.received(self, message)
	
	def handle_MsgPlayerConnect(self, message):
		"""	
		Server should receive player connect from client on arrival, indicating
		their chosen name. Server relays this to all clients, thereby providing
		the new client with their allocated id.	
		"""
		# TODO - above is untrue and finish this method
		pass

	def handle_MsgPlayerDisconnect(self, message):
		"""	
		Server may receive player disconnect from a client, indicating that they 
		are intentionally leaving the game. On receipt, server removes player from
		the list and informs other clients.
		"""
		self.handle_client_departure(message.player_id)
		msg = MsgPlayerDisconnect([Message.RECIPIENT_ALL_CLIENTS],message.player_id,message.reason)
		self.send(msg)

class GameClient(GameNode, Client, StateMachineBase):
	"""	
	Basic game client for use with GameServer. Clients inform one another of 
	their arrival, maintaining their own player lists. They also maintain a 
	synchornized clock.
	"""
	
	class StateConnecting(StateMachineBase.State):

		def handle_MsgPlayerConnect(self, message): pass
		def handle_MsgPlayerDisconnect(self, message): pass

		def handle_MsgAcceptConnect(self, message):
			"""	
			Client should receive MsgAcceptConnect from the server to 
			acknowledge the player's entry into the game
			"""
			# player_id field provides the client with their designated id
			self.machine.client_id = message.player_id
			# player_info field is a dictionary containing info about the 
			# players already connected
			for k in message.player_info:
				self.machine.register_player(k, message.player_info[k])

			self.machine.info_message("Connected to host")
			self.machine.change_state("StateInGame")

		def handle_MsgRejectConnect(self, message):
			"""	
			Client should receive MsgRejectConnect from the server to
			indicate that connection was unsuccessful
			"""
			self.machine.info_message("Host rejected connection: %s" % message.reason)

	class StateInGame(StateMachineBase.State):

		pass

	def __init__(self, host, port):
		GameNode.__init__(self)
		Client.__init__(self, host, port)
		StateMachineBase.__init__(self)
		self.player_list = {}
		self.change_state("StateConnecting")
	
	def run(self):
		Client.__run__(self)
		self.info_message("Disconnected from host")

	def register_player(self, id, info):
		self.player_list[id] = info

	def deregister_player(self, id):
		del(self.player_list[id])

	def info_message(self, message):
		"""	
		Invoked to display an information message about the game state
		"""
		pass

	def chat_message(self, message):
		"""	
		Invoked on receipt of a chat message to display it
		"""
		pass

	def _player_connected(self, message):
		self.register_player(message.player_id, {
			"name" : message.name
		})		
		self.info_message("%s has joined the game" % message.name)

	def _player_disconnectd(self, message):
		if self.player_list.has_key(message.player_id):
			name = self.player_list(message.player_id)
			self.deregister_player(message.player_id)
			self.info_message("%s has left the game" % name)

	@statemethod
	def handle_MsgPlayerConnect(self, message):
		self._player_connectd(message)

	@statemethod
	def handle_MsgPlayerDisconnect(self, message):
		self._player_disconnected(message)
	
	@statemethod
	def handle_MsgServerShutdown(self, message):
		self.info_message("The host has ended the game")


# ----------------------------------------------------------------------------------
# Testing 
# ----------------------------------------------------------------------------------

if __name__ == "__main__":
	import unittest

	class TestMessage(Message):
		def __init__(self, recipients, name="", age=0, weight=0.0):
			self.recipients = recipients
			self.name = name
			self.age = age
			self.weight = weight

		def to_dict(self):
			d = {}
			for k in ("name", "age", "weight"):
				d[k] = getattr(self, k)
			return d

	class JsonTest(unittest.TestCase):

		def setUp(self):
			self.encoder = JsonEncoder()

		def testEncodeDecode(self):
			m = TestMessage([1,2,3],"Frank", 25, 123.5)
			j = self.encoder.encode(m)
			print j
			m2 = self.encoder.decode(j)
			self.assertEquals(TestMessage, m2.__class__)
			self.assertEquals([1,2,3],m2.get_recipients())
			self.assertEquals("Frank", m2.name)
			self.assertEquals(25, m2.age)
			self.assertEquals(123.5, m2.weight)

	unittest.main()
