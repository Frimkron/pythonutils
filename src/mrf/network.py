import socket
import thread
import threading
import json
import sys
import time
import copy
from mrf.statemachine import StateMachineBase, statemethod
from mrf.structs import TagLookup

"""	
TODO: Use socket server framework in standard library instead?
TODO: Synchronisation for multiple threads accessing data simultanously
TODO: Should unregister player on server when client disconnects
TODO: Should notify players when player disconnects
TODO: GameClientHandler should similarly perform handshake - not add client to pool until negotiated.
	Do this by having server delegate handling of connect request to stateful client handler.
	Server should group clients in different ways - should have separate group for connected
	players, for purposes of counting players, etc.
TODO: GameServer/GameClient classes which throw these messages around
TODO: Refactor telnet module to use generic client/server classes
TODO: Unit tests for client/server

   Multiple inheritence:

                       Thread
                        ^  ^
   ,-----2--------------'  '---------.
   |         Node                 SkListener            SkListener:		
   |        ^ ^ ^                   ^ ^	                        send
   | ,---1--' | '--2----. ,----1----' |	                        received
 Server    GameNode    Client       ClHandler
    ^         ^  ^        ^ 	      ^	                Node:
    '--2----. |1 '--1---. |2          |	                        send
          GameServer   GameClient  GameClHandler                received

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

class Server(Node, threading.Thread):	
	"""	
	A socket server. After constructed, the "start" method should be invoked to begin
	the server in its own thread.
	"""
	
	SERVER = -1
	GROUP_ALL = "all"
	GROUP_CLIENTS = "clients"

	def __init__(self, client_class, port):
		"""	
		Initialises the server. "client_class" should be a class for handling clients.
		It should extend threading.Thread and accept the server, socket and client id as parameters.
		The client thread should invoke handle_client_arrival on startup and 
		handle_client_departure on termination. "port" is the port number to listen for 
		new clients on.
		"""
		Node.__init__(self)
		threading.Thread.__init__(self)
		self.client_class = client_class
		self.port = port
		
		self.next_id = 0
		self.handlers = {}		
		self.node_groups = TagLookup()
		

	def run(self):
		"""	
		Overridden from Thread - runs the server, listening on the specified port for 
		new clients connecting. For each new client a client handler of the specified 
		type is created in a new thread.
		"""
		
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			s.bind((socket.gethostname(),self.port))
			s.listen(1)
		
			self.next_id = 0
			self.handlers = {}
			self.node_groups = TagLookup()
			self.node_groups.tag_item(Server.SERVER, Server.GROUP_ALL)
		
			while True:
				conn,addr = s.accept()
				handler = self.client_class(self,conn,self.next_id)
				self.handlers[self.next_id] = handler
				handler.start()				
				self.next_id += 1
		finally:
			s.close()
	
	def handle_client_arrival(self, client_id):
		"""	
		Client with given id has connected
		"""
		# tag in appropriate groups
		self.node_groups.tag_item(client_id, Server.GROUP_ALL)
		self.node_groups.tag_item(client_id, Server.GROUP_CLIENTS)
		
	def handle_client_departure(self, client_id):
		"""	
		Client with given id has departed. Removes the associated
		handler.
		"""
		# remove from groups
		self.node_groups.remove_item(client_id)
		
		# remove handler
		# TODO: should stop thread?
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
		recips = self.resolve_message_recipients(message)

		if Server.SERVER in recips:
			recips.remove(Server.SERVER)
			self.received(message)

		for r in recips:
			if self.handlers.has_key(r):
				self.handlers[r].send(message)

	def resolve_message_recipients(self, message):
		exclude = set()
		for ex in message.get_excludes():
			if isinstance(ex, basestring):
				exclude = exclude.union(self.node_groups.get_tag_items(ex))
			else:
				exclude.add(ex)
		
		recips = set()
		for rec in message.get_recipients():
			if isinstance(rec, basestring):
				recips = recips.union(self.node_groups.get_tag_items(rec))
			else:
				recips.add(rec)
				
		return recips.difference(exclude)

	def get_node_id(self):
		return Server.SERVER

	def get_num_clients(self):
		return len(self.handlers)

class SocketListener(threading.Thread):
	"""	
	Base class for client socket listeners. Once constructed, "start" method should
	be invoked to start the SocketListener running in its own thread.
	"""

	def __init__(self, encoder, decoder):
		threading.Thread.__init__(self)
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

	def run(self):
		"""	
		Overidden from Thread. Just invokes listen_on_socket. Should be
		overidden in subclasses.
		"""
		self.listen_on_socket()

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
	on the server. After constructing, "start" method should be invoked
	to begin ClientHandler running in its own thread.
	"""

	def __init__(self, server, socket, id, encoder, decoder):
		SocketListener.__init__(self, encoder, decoder)
		self.server = server
		self.socket = socket
		self.id = id

	def get_socket(self):	
		return self.socket

	def run(self):
		"""	
		Overidden from SocketListener. Invoked when thread is started.	
		"""
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
	Socket client. After constructing, "start" method should be invoked in order
	to start the client running in its own thread.
	"""

	def __init__(self, host, port):
		self.host = host
		self.port  = port
		self.client_id = -1

	def run(self):
		"""	
		Overidden from SocketListener. Connects on socket then listens for
		messages. Invoked when thread is started.
		"""
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.connect((self.host, self.port))
		self.after_connect()
		self.listen_on_socket()

	def get_socket(self):
		return self.socket

	def get_node_id(self):
		return self.client_id

	def after_connect(self):
		"""	
		Invoked just after client connects to server and before client starts 
		listening to messages
		"""
		pass

class Message(object):
	"""	
	Base class for network messages
	"""

	def __init__(self, recipients, excludes, sender=Server.SERVER):
		"""	
		Initializes the message with the given recipient list and 
		sender id.
		"""
		self.recipients = recipients
		self.excludes = excludes
		self.sender = sender

	def get_recipients(self):
		"""	
		Returns the list of recipients, which may consist of a mixture of client
		id numbers and strings naming node groups.
		"""
		return self.recipients
	
	def get_excludes(self):
		"""
		Returns the list of excludes - clients which should be excluded from the 
		recipient list - which may consist of a mixture of client id numbers and 
		strings naming node groups.
		"""
		return self.excludes

	def get_sender(self):
		return self.sender
		
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
			"excludes" : message.get_excludes(),
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

		message = cls(dict["recipients"], dict["excludes"], dict["sender"])
		message.from_dict(dict["data"])
		return message


class MsgPlayerConnect(Message):
	"""	
	Sent by server to inform clients of a new player's arrival
	"""

	def __init__(self, recipients, excludes, sender=-1, player_id=-1, name=""):
		Message.__init__(self, recipients, excludes, sender)
		self.player_id = player_id
		self.name = name

	def to_dict(self):
		return self._get_attrs(("player_id","name"))
		

class MsgPlayerDisconnect(Message):
	"""		
	Sent by server to inform clients of a players' departure
	"""

	def __init__(self, recipients, excludes, sender=-1, player_id=-1, reason=""):
		Message.__init__(self, recipients, excludes, sender)
		self.player_id = player_id
		self.reason = reason

	def to_dict(self):
		return self._get_attrs(("player_id","reason"))
		

class MsgServerShutdown(Message):
	"""	
	Sent by server to inform clients that the server is about to stop
	"""

	def __init__(self, recipients, excludes, sender=-1):
		Message.__init__(self, recipients, excludes, sender)

	def to_dict(self):
		return self._get_attrs(())

class MsgRequestConnect(Message):
	"""	
	Sent from client to server when first connected to provide information
	about the player. Server should respond with either MsgAcceptConnect
	or MsgRejectConnect. 
	"""
	
	def __init__(self, recipients, excludes, sender=-1, player_info=None):
		Message.__init__(self, recipients, excludes, sender)
		self.player_info = player_info

	def to_dict(self):
		return self._get_attrs(("player_info",))

class MsgAcceptConnect(Message):
	"""	
	Sent from server to client to confirm their acceptence into the game,
	provide their client id and provide the player with information about
	the other players connected.
	"""

	def __init__(self, recipients, excludes, sender=-1, player_id=-1, player_infos=None):
		Message.__init__(self, recipients, excludes, sender)
		self.player_id = player_id
		self.players_info = players_info

	def to_dict(self):
		return self._get_attrs(("player_id","players_info"))

class MsgRejectConnect(Message):
	"""	
	Sent from server to client to indicate that connection to the game was
	unsuccessful.
	"""

	def __init__(self, recipients, excludes, sender=-1, reason=""):
		Message.__init__(self, recipients, excludes, sender)
		self.reason = reason

	def to_dict(self):
		return self._get_attrs(("reason",))

class MsgPing(Message):
	"""	
	Sent between client and server for calculaating network latency	
	"""

	def __init__(self, recipients, excludes, sender=-1, timestamp=0):
		Message.__init__(self, recipients, excludes, sender)
		self.timestamp = timestamp

	def to_dict(self):
		return self._get_attrs(("timestamp",))

class MsgPong(MsgPing):
	"""	
	Sent in response to MsgPing
	"""
	pass

class MsgChat(Message):
	"""	
	Sent between clients to allow players to communicate with each other	
	"""

	def __init__(self, recipients, excludes, sender=-1, message=""):
		Message.__init__(self, recipients, sender)
		self.message = message

	def to_dict(self):
		return self._get_attrs(("message",))

class GameFullError(Exception): pass

class NameTakenError(Exception): pass

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
		resp = MsgPong([message.sender], [], self.get_node_id(), self.get_timestamp())
		self.send(resp)

	def handle_MsgPong(self, message):
		pass

	def handle_MsgChat(self, message):
		pass

class GameClientHandler(ClientHandler, StateMachineBase):
	"""	
	ClientHandler used by GameServer. GameClientHandler is responsible for handling 
	client-specific logic on the server side and maintaining info about that player
	"""
	
	class StateConnecting(StateMachineBase.State):
		
		def handle_MsgRequestConnect(self, message):
			"""	
			The client has requested to enter the game
			"""
			try:
				info = message.get_player_info()

				# join the game
				self.machine.server.player_join(self.machine.id, info)
				
				# record player info
				self.machine.player_info = info

				# reply with client id and info about connected players
				other_players = self.machine.server.get_info_on_players()
				self.machine.server.send(MsgAcceptConnect([self.machine.id],[], 
					Server.SERVER, self.machine.id, other_players))
				
				# change state
				self.machine.change_state("StateInGame")
				
			except GameFullError:				
				self.machine.server.send(MsgRejectConnect([self.machine.id], [], 
					Server.SERVER, "The game is full"))
				
			except NameTakenError:
				self.machine.server.send(MsgRejectConnect([self.machine.id], [],
					Server.SERVER, "Your player name is already taken"))
				

	class StateInGame(StateMachineBase.State):
		pass

	def __init__(self, server, socket, id, encoder, decoder):
		ClientHandler.__init__(self, server, socket, id, encoder, decoder)
		StateMachineBase.__init__(self)
		self.player_info = {}
		self.change_state("StateConnecting")

	@statemethod
	def handle_MsgRequestConnect(self, message):
		pass

	def get_player_info(self):
		return self.player_info

class GameServer(GameNode, Server):
	"""	
	Basic game server for use with GameClient
	"""
	
	GROUP_PLAYERS = "players"
	
	def __init__(self, max_players=4, client_class=GameClientHandler, port=570810):
		"""	
		Initialises the server with default handler GameClientHandler and using
		port 570810
		"""
		GameNode.__init__(self)
		Server.__init__(self, client_class, port)
		self.max_players = max_players

	def send(self, message):
		Server.send(self.message)

	def received(self, message):
		GameNode.received(self, message)
	
	def handle_MsgRequestConnect(self, message):
		"""	
		Server receives this message from client when they are requesting to 
		enter the game. The client provides their chosen name. 	
		"""
		# delegate to client handler
		if self.handlers.has_key(message.get_sender()):
			self.handlers[message.get_sender()].handle_MsgRequestConnect(message)

	def handle_MsgPlayerDisconnect(self, message):
		"""	
		Server may receive player disconnect from a client, indicating that they 
		are intentionally leaving the game. On receipt, server removes player from
		the list and informs other clients.
		"""
		self.handle_client_departure(message.player_id)
		msg = MsgPlayerDisconnect([Server.GROUP_CLIENTS],[message.player_id],
			message.player_id,message.reason)
		self.send(msg)
		
	def get_num_players(self):
		return len(self.get_players())
		
	def get_players(self):
		return copy.copy(self.get_tag_items(GameServer.GROUP_PLAYERS))

	def player_join(self, id, info):
		"""	
		Attempt to receive the player into the game and notify others
		"""
		if self.get_num_players() >= self.max_players:
			raise GameFullError()
		elif info["name"] in [self.handlers[p].get_player_info["name"] for p in self.get_players()]:
			raise NameTakenError()
		else:			
			# add into group of connected players
			self.node_groups.tag_item(id, GameServer.GROUP_PLAYERS)
			# notify players
			self.send(MsgPlayerConnect([GameServer.GROUP_PLAYERS], [id], 
				GameServer.SERVER, id, info["name"]))
		
	def get_info_on_players(self):
		"""	
		Returns info on players in game, suitable for sending to newly connected 
		players
		"""
		return dict([(id,self.handlers[id].get_player_info()) for id in self.get_players()])
		

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
			# players_info field is a dictionary containing info about the 
			# players already connected
			for k in message.player_info:
				self.machine.register_player(k, message.players_info[k])

			self.machine.info_message("Connected to host")
			self.machine.change_state("StateInGame")

		def handle_MsgRejectConnect(self, message):
			"""	
			Client should receive MsgRejectConnect from the server to
			indicate that connection was unsuccessful
			"""
			# TODO: should probably throw exception here
			self.machine.info_message("Host rejected connection: %s" % message.reason)

	class StateInGame(StateMachineBase.State):

		pass

	def __init__(self, host, port, player_info):
		GameNode.__init__(self)
		Client.__init__(self, host, port)
		StateMachineBase.__init__(self)
		self.player_list = {}
		self.player_info = player_info
		self.change_state("StateConnecting")

	def run(self):
		Client.__run__(self)
		self.info_message("Disconnected from host")
	
	def after_connect(self):
		"""	
		Immediately after connecting to server, request entry into the game
		"""
		self.send(MsgRequestConnect([Server.SERVER],[],-1,self.player_info))

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
		
	@statemethod
	def handle_MsgAcceptConnect(self, message):
		pass
	
	@statemethod
	def handle_MsgRejectConnect(self, message):
		pass


# ----------------------------------------------------------------------------------
# Testing 
# ----------------------------------------------------------------------------------

if __name__ == "__main__":
	import unittest

	class TestMessage(Message):
		def __init__(self, recipients, excludes, sender=Server.SERVER, name="", age=0, weight=0.0):
			Message.__init__(self, recipients, excludes, sender)
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
			m = TestMessage([1,2,3],[],1,"Frank", 25, 123.5)
			j = self.encoder.encode(m)
			print j
			m2 = self.encoder.decode(j)
			self.assertEquals(TestMessage, m2.__class__)
			self.assertEquals([1,2,3],m2.get_recipients())
			self.assertEquals([],m2.get_excludes())
			self.assertEquals(1,m2.get_sender())
			self.assertEquals("Frank", m2.name)
			self.assertEquals(25, m2.age)
			self.assertEquals(123.5, m2.weight)

	class StubClientHandler(ClientHandler):
		def __init__(self, server, sock, id):
			self.server = server
			self.id = id
			self.stop = False
		def run(self):
			self.server.handle_client_arrival(id)
			while not self.stop:
				pass
			self.server.handle_client_departure(id)
		def disconnect(self):
			self.stop = True

	class TestClientServer(unittest.TestCase):

		def testServer(self):
			# create server
			server = Server(StubClientHandler,4444)
			server.start()

			# connect to server
			# TODO: how to test individual components?

	unittest.main()
