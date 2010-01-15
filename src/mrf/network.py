import socket
import threading
import json
import sys
import time
import copy
import Queue
from mrf.statemachine import StateMachineBase, statemethod
from mrf.structs import TagLookup
from mrf.mathutil import deviation, mean

"""	
TODO: Informing user of client/server shutdown.
TODO: Unit tests for client/server
TODO: Structure diagram
TODO: GameServer/GameClient classes which throw these messages around
TODO: Refactor telnet module to use generic client/server classes


   Multiple inheritence:

                    NetworkThread
                        ^  ^
   ,-----2--------------'  '---------.                  TODO: out of date:
   |         Node                 SkListener            SkListener:		
   |        ^ ^ ^                   ^ ^	                        send
   | ,---1--' | '--2----. ,----1----' |	                        received
 Server    GameNode    Client       ClHandler
    ^         ^  ^        ^ 	      ^	                Node:
    '--2----. |1 '--1---. |2          |	                        send
          GameServer   GameClient  GameClHandler                received

"""
	
def lockable_attrs(obj, **kargs):
	for k in kargs:
		setattr(obj, k, kargs[k])
		setattr(obj, k+"_lock", threading.RLock())		

class NetworkThread(threading.Thread):
	
	def __init__(self):
		threading.Thread.__init__(self)
		lockable_attrs(self,
			stopping = False
		)

	def stop(self):
		"""	
		May be used to stop this network thread. Blocks until the thread has stopped
		running. Should be overidden to perform any other cleanup tasks required 
		to shut down the thread.
		"""
		with self.stopping_lock:
			self.stopping = True
		self.join()

class Node(object):
	"""	
	Base class for all nodes in the network i.e. clients and server
	"""
	
	def __init__(self):
		pass

	def send(self, message):
		"""	
		Invoked when a message should be sent from this node. Should be overidden
		in subclasses
		"""
		pass

	def received(self, message):
		"""	
		Invoked when a message is received by this node. Should be overidden in 
		subclasses.
		"""
		pass

	def get_node_id(self):
		pass

class Server(Node, NetworkThread):	
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
		NetworkThread.__init__(self)
		self.client_class = client_class
		self.port = port
		
		self.next_id = 0
		lockable_attrs(self,
			listen_socket = None,		
			handlers = {},		
			node_groups = TagLookup()
		)

	def run(self):
		"""	
		Overridden from Thread - runs the server, listening on the specified port for 
		new clients connecting. For each new client a client handler of the specified 
		type is created in a new thread.
		"""
		
		with self.listen_socket_lock:
			self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			with self.listen_socket_lock:
				self.listen_socket().bind((socket.gethostname(),self.port))
				self.listen_socket().listen(1)
		
			self.next_id = 0
			with self.handlers_lock:
				self.handlers = {}
			with self.node_groups_lock:
				self.node_groups = TagLookup()
				self.node_groups.tag_item(Server.SERVER, Server.GROUP_ALL)
		
			while True:				
				# exit loop if shutting down
				with self.stopping_lock:
					if self.stopping:
						break
				
				# can't lock here, because other threads need to be able to close socket
				conn,addr = self.listen_socket().accept()
				handler = self.client_class(self,conn,self.next_id)
				with self.handlers_lock:
					self.handlers[self.next_id] = handler
				handler.start()				
				self.next_id += 1	
				
		except socket.error as e:
			# do not raise exception if user explicitly shut down the server
			with self.stopping_lock:
				if not self.stopping:
					# TODO: can't just raise the exception - who will catch it?					
					raise e
		finally:
			# close socket
			with self.listen_socket_lock:
				self.listen_socket.close()
			# stop client handler threads
			self.stop_handlers()
	
	def stop(self):
		"""	
		Shuts down the server, closing all client connections and terminating 
		the thread.
		"""
		with self.stopping_lock:
			self.stopping = True
		# close the listen socket to interrupt blocking call
		with self.listen_socket_lock:
			self.listen_socket.close()
		# wait for thread to end
		self.join()
		
	def stop_handlers(self):
		"""	
		Invoked when the server is shutting down. Stops the client handler threads.
		"""
		with self.handlers_lock:
			for c in self.handlers():
				self.handlers[c].stop()			

	def handle_client_arrival(self, client_id):
		"""	
		Client with given id has connected
		"""
		with self.node_groups_lock:
			# tag in appropriate groups
			self.node_groups.tag_item(client_id, Server.GROUP_ALL)
			self.node_groups.tag_item(client_id, Server.GROUP_CLIENTS)
		
	def handle_client_departure(self, client_id):
		"""	
		Invoked by client handler when handler shuts down. Removes client from 
		groups and removes the associated handler.
		"""
		# remove from groups
		with self.node_groups_lock:
			self.node_groups.remove_item(client_id)
			
		# remove the stopped handler from the dictionary
		with self.handlers_lock:		
			del(self.handlers[client_id])

	def send(self, message):
		"""	
		Request appropriate handlers send message to their clients
		"""
		recips = self.resolve_message_recipients(message)

		if Server.SERVER in recips:
			recips.remove(Server.SERVER)
			self.received(message)

		for r in recips:
			with self.handlers_lock:
				if self.handlers.has_key(r):
					self.handlers[r].send(message)

	def resolve_message_recipients(self, message):
		with self.node_groups_lock:
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
		with self.handlers_lock:
			return len(self.handlers)

class SocketListener(NetworkThread):
	"""	
	Base class for client socket listeners. Once constructed, "start" method should
	be invoked to start the SocketListener running in its own thread.
	"""

	def __init__(self, encoder, decoder):
		NetworkThread.__init__(self)
		self.encoder = encoder
		self.decoder = decoder

	def get_socket(self):
		"""	
		Should return the socket
		"""
		pass
	
	def get_socket_lock(self):
		"""
		Should return the socket lock
		"""
		pass

	def send(self, message):
		"""	
		Encodes the given message and sends it down the socket.
		Only one thread may enter at a time.
		"""
		data = self.encoder.encode(message)
		sent = 0
		with self.get_socket_lock():
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

	def stop(self):
		"""	
		May be used to stop the SocketListener, closing the port and terminating
		the thread
		"""
		with self.stopping_lock:
			self.stopping = True
		# close socket to interrupt blocking call
		with self.get_socket_lock():
			self.get_socket().close()
		# wait for thread to finish
		self.join()

	def listen_on_socket(self):
		"""	
		Blocks, waiting for messages on the socket. Raises socket.error if there is a 
		problem reading from the socket.
		"""
		try:
			while True:
				# exit loop if shutting down
				with self.stopping_lock:
					if self.stopping:
						break				
				
				# can't lock here, because other threads must be able to forcefully
				# close the socket.
				data = self.get_socket().recv(1024)
				if not data: 
					raise socket.error
				message = self.decoder.decode(data)
				self.received(message)
				
		except socket.error as e:
			# if user explicitly shut down SocketListener, do not raise exception
			with self.stopping_lock:
				if not self.stopping:
					# TODO: Nope - who will catch this exception?
					raise e
		finally:
			# clean up
			with self.get_socket_lock():
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
		self.id = id
		lockable_attrs(self,
			socket = socket
		)

	def get_socket(self):	
		return self.socket
	
	def get_socket_lock(self):
		return self.socket_lock

	def run(self):
		"""	
		Overidden from SocketListener. Invoked when thread is started.	
		"""
		self.server.handle_client_arrival(self.id)	
		try:	
			self.listen_on_socket()
			# TODO: exception could be thrown here. How to inform user?
		finally:
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

	def __init__(self, host, port, encoder, decoder):
		SocketListener.__init__(self, encoder, decoder)
		Node.__init__(self)
		self.host = host
		self.port  = port
		
		# client doesn't know its id yet
		self.client_id = -1
		lockable_attrs(self,
			socket = None
		)

	def run(self):
		"""	
		Overidden from SocketListener. Connects on socket then listens for
		messages. Invoked when thread is started.
		"""
		with self.socket_lock:
			self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.socket.connect((self.host, self.port))
		self.after_connect()
		self.listen_on_socket()

	def send(self, message):
		"""	
		Both SocketListener and Node have a "send" method! Here we override 
		Node's version, passing the message to SocketListener's version for 
		sending down the socket.
		"""
		SocketListener.send(self, message)

	def received(self, message):
		"""	
		Both SocketListener and Node have a "received" method! Here we override
		SocketListener's version, passing the message on to Node's version for
		adding to the message queue.
		"""
		Node.received(self, message)

	def get_socket(self):
		return self.socket

	def get_socket_lock(self):
		return self.socket_lock

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
	Base class for network messages. Subclasses should implement "to_dict" to
	allow the message to be encoded for transport.
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
	"""
	Encodes Message objects in JSON format. Will not handle subclasses of Message
	which are nested classes - they must be in module scope.	
	"""

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

	def __init__(self, recipients, excludes, sender=-1, player_id=-1, players_info=None):
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

	def __init__(self, recipients, excludes, sender=-1, ping_timestamp=0):
		Message.__init__(self, recipients, excludes, sender)
		self.ping_timestamp = ping_timestamp

	def to_dict(self):
		return self._get_attrs(("ping_timestamp",))

class MsgPong(Message):
	"""	
	Sent in response to MsgPing
	"""
	
	def __init__(self, recipients, excludes, sender=-1, ping_timestamp=0, pong_timestamp=0):
		Message.__init__(self, recipients, excludes, sender)
		self.ping_timestamp = ping_timestamp
		self.pong_timestamp = pong_timestamp
		
	def to_dict(self):
		return self._get_attrs(("ping_timestamp","pong_timestamp"))

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

class NoMessageHandlerError(Exception): pass	

class GameNode(Node):
	"""	
	Base class for all nodes (clients & server) in the game network
	"""
	
	def __init__(self):
		Node.__init__(self)
		self.message_queue = Queue.Queue()
	
	def take_messages(self):
		"""	
		Removes and returns waiting messages from the message queue.
		"""
		msgs = []
		num = self.message_queue.qsize()
		for i in range(num):
			try:
				msgs.append(self.message_queue.get(block=False))								
			except Queue.Empty:
				# qsize is not exact, so we might try to get one more items than 
				# exist in the queue. Can safely ignore exception
				pass
		return msgs
	
	def process_messages(self, handler=None):
		"""	
		Takes waiting messages from the queue and dispatches them to their handler
		methods. Should be invoked in the GameNode's game loop. A method named 
		"handle_<messagetype>" is looked for first in the "handler" object, if 
		provided, then in the GameNode object itself.
		"""
		for msg in self.take_messages():
			# dispatch to handler method using naming convention
			hname = "handle_"+msg.__class__.__name__
			if handler!=None and hasattr(handler,hname):
				getattr(handler,hname)(msg)
			elif hasattr(self, hname):
				getattr(self, hname)(msg)
			else:
				self.delegate_message(msg, hname)			
	
	def delegate_message(self, message, handler_name):
		"""	
		Invoked if a message handler is not present in the current class. Should
		be overidden to check elsewhere for a handler and raise 
		NoMessageHandlerError if one is not found.
		"""
		raise NoMessageHandlerError(handler_name)
	
	def get_timestamp(self):
		return int(time.time()*1000)

	def received(self, message):
		"""	
		Overidden from Node. Invoked when this node receives a message. 
		Attempts to locate interceptor method called "intercept_<messagetype>" 
		and if found, the message is handled by it. If no intercept method is 
		found, the message is simply added to the message queue to be picked up 
		by the game loop, which is how most messages should be handled.
		"""
		hname = "intercept_"+message.__class__.__name__
		if hasattr(self, hname):
			getattr(self, hname)(message)
		else:
			self.message_queue.put(message)

	def intercept_MsgPing(self, message):
		"""
		Respond with MsgPong as soon as MsgPing is received. Don't wait for
		game loop.
		"""
		resp = MsgPong([message.sender], [], self.get_node_id(), 
			message.ping_timestamp, self.get_timestamp())
		self.send(resp)

	def handle_MsgPlayerConnect(self, message): pass

	def handle_MsgPlayerDisconnect(self, message): pass

	def handle_MsgServerShutdown(self, message): pass
	
	def handle_MsgRequestConnect(self, message): pass

	def handle_MsgAcceptConnect(self, message): pass

	def handle_MsgRejectConnect(self, message): pass
	
	def handle_MsgPong(self, message): pass

	def handle_MsgChat(self, message): pass

class GameClientHandler(ClientHandler, StateMachineBase):
	"""	
	ClientHandler used by GameServer. GameClientHandler is responsible for handling 
	client-specific logic on the server side and maintaining info about that player.
	GameClientHandler's "handle_" messages are invoked by GameServer for any messages
	which aren't handled by the server itself.
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
	
	def __init__(self, max_players=4, client_class=GameClientHandler, port=57810):
		"""	
		Initialises the server with default handler GameClientHandler and using
		port 57810
		"""
		GameNode.__init__(self)
		Server.__init__(self, client_class, port)
		self.max_players = max_players

	def send(self, message):
		"""
		Explicitly send message as Server does	
		"""
		Server.send(self, message)

	def received(self, message):
		"""
		Explicitly receive message as GameNode does - dispatching to any 
		interceptor methods or placing in the message queue.	
		"""
		GameNode.received(self, message)
	
	def delegate_message(self, message, handler_name):
		"""
		Overidden from GameNode. Invoked if server doesn't have an appropriate 
		handler method for a message. Checks appropriate client handler for handler
		method instead.
		"""
		id = message.get_sender()
		ch = None
		with self.handlers_lock:
			if self.handlers.has_key(id):
				ch = self.handlers[id]
		if ch != None:
			if hasattr(ch, handler_name):
				getattr(ch, handler_name)(message)
			else:
				raise NoMessageHandlerError(handler_name)
	
	def handle_MsgPlayerDisconnect(self, message):
		"""	
		Server may receive player disconnect from a client, indicating that they 
		are intentionally leaving the game. On receipt, server stops client handler
		"""
		self.disconnect_client(message.player_id)
		
	def disconnect_client(self, client_id):
		"""
		May be invoked to "kick" a player from the server
		"""
		with self.handlers_lock:
			if self.handlers.has_key(client_id):
				# stop the handler. handle_client_departure will later be invoked
				# to clean up handler.
				self.handlers[client_id].stop()
		
	def handle_client_departure(self, client_id):
		"""
		Overidden from Server. Invoked by client handler when a handler shuts 
		down. Removes the client from groups and removes the handler then, if the
		client was a player in the game, informs other players of their departure.
		"""
		# Client exists and had entered the game?
		send_msg = False
		with self.handlers_lock:
			if self.handlers.has_key(client_id):
				with self.node_groups_lock:			
					if GameServer.GROUP_PLAYERS in self.node_groups.get_item_tags(client_id):
						send_msg = True
				
		# remove client from groups and remove handler
		Server.handle_client_departure(self, client_id)
						
		# inform other players
		if send_msg:
			# TODO: Reason parameter should tell players whether client left or was kicked
			self.send(MsgPlayerDisconnect([GameServer.GROUP_PLAYERS],[client_id],
					GameServer.SERVER, client_id, ""))
			
	def get_num_players(self):
		return len(self.get_players())
		
	def get_players(self):
		with self.node_groups_lock:
			return copy.copy(self.node_groups.get_tag_items(GameServer.GROUP_PLAYERS))

	def get_player_names(self):
		with self.handlers_lock:
			return [self.handlers[p].get_player_info["name"] for p in self.get_players()]

	def player_join(self, id, info):
		"""	
		Attempt to receive the player into the game and notify others
		"""
		joined = False
		with self.node_groups_lock:
			if self.get_num_players() >= self.max_players:
				raise GameFullError()
			elif info["name"] in self.get_player_names():
				raise NameTakenError()
			else:			
				# add into group of connected players
				self.node_groups.tag_item(id, GameServer.GROUP_PLAYERS)
				joined = True
		if joined:
			# notify players
			self.send(MsgPlayerConnect([GameServer.GROUP_PLAYERS], [id], 
				GameServer.SERVER, id, info["name"]))
		
	def get_info_on_players(self):
		"""	
		Returns info on players in game, suitable for sending to newly connected 
		players
		"""
		with self.handlers_lock:
			return dict([(id,self.handlers[id].get_player_info()) for id in self.get_players()])
		
	def stop(self):
		"""
		Overidden from Server. Informs clients of imminent shutdown then shuts 
		down the server and all client handlers.
		"""
		# send shutdown message to clients
		self.send(MsgServerShutdown([GameServer.GROUP_CLIENTS],[],GameServer.SERVER))
		# close listener socket and stop client handlers
		Server.stop(self)
	
# TODO: Should probably throw this if server rejects clients join request
#		Are exceptions the best way to do this?

class JoinRefusedError(Exception): pass	

class GameClient(GameNode, Client, StateMachineBase):
	"""	
	Basic game client for use with GameServer. Clients inform one another of 
	their arrival, maintaining their own player lists. They also maintain a 
	synchronised clock.
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

			# TODO: how to inform user of successful connection?
			self.machine.change_state("StateInGame")

		def handle_MsgRejectConnect(self, message):
			"""	
			Client should receive MsgRejectConnect from the server to
			indicate that connection was unsuccessful
			"""
			# TODO: how to inform user?
			# not allowed to enter game - shut down the client
			self.machine.stop()

	class StateInGame(StateMachineBase.State):

		pass

	def __init__(self, host, port, player_info):
		GameNode.__init__(self)
		Client.__init__(self, host, port)
		StateMachineBase.__init__(self)
		self.player_list = {}
		self.player_info = player_info
		self.latencies = [],
		lockable_attrs(self,
			latency = 0,
			time_delta = 0
		)
		self.pinger_thread = None
		self.change_state("StateConnecting")

	def run(self):
		Client.run(self)
		# TODO: raise exception?
	
	def run_ping_sender(self):		
		while True:
			# break if client has been stopped
			with self.stopping_lock:
				if self.stopping:
					break						
			time.sleep(3.0)
			self.send(MsgPing([Server.SERVER],[],-1,self.get_timestamp()))			
	
	def after_connect(self):
		"""	
		Immediately after connecting to server, request entry into the game
		and start pinging
		"""
		self.send(MsgRequestConnect([Server.SERVER],[],-1,self.player_info))
		self.pinger_thread = threading.Thread(target=self.run_ping_sender)
		self.pinger_thread.start()
	
	def stop(self):
		"""
		Overidden from Client. Sends disconnect message to server before closing
		the socket.
		"""
		# send disconnect message
		self.send(MsgPlayerDisconnect([Server.SERVER],[],self.client_id,""))
		# shut down client
		Client.stop(self)
	
	def get_latency(self):
		"""	
		Returns the average one-way time between client and server, in milliseconds 
		"""
		with self.latency_lock:
			return self.latency
		
	def get_time_delta(self):
		"""	
		Returns an estimate of the difference between the client's clock and the
		server's clock, in milliseconds
		"""
		with self.time_delta_lock:
			return self.time_delta
	
	def get_server_time(self):
		"""	
		Returns an estimate of the time on the server, in milliseconds
		"""
		return self.get_timestamp() - self.get_time_delta()

	def register_player(self, id, info):
		self.player_list[id] = info

	def deregister_player(self, id):
		del(self.player_list[id])

	def _player_connected(self, message):
		self.register_player(message.player_id, {
			"name" : message.name
		})		

	def _player_disconnectd(self, message):
		if self.player_list.has_key(message.player_id):
			name = self.player_list(message.player_id)
			self.deregister_player(message.player_id)

	def intercept_MsgPong(self, message):
		"""
		Invoked in socket listener thread when MsgPong received. Uses timing 
		information from server ping response to update synchronised clock and 
		latency information	
		"""
		recv_time = self.get_timestamp()
		round_time = recv_time - message.ping_timestamp
		latn = round_time/2		
		
		# ignore the latency value if more than 1 sd from mean
		if deviation(self.latencies, latn) < 1.0:
			
			self.latencies.append(latn)			
			# keep the last 5 latency values
			if len(self.latencies) > 5:
				self.latencies.pop(0)
				
		# get the current average latency
		av_latn = mean(self.latencies)	
				
		# find difference between local clock and server clock
		server_time = message.pong_timestamp + av_latn
		delta = recv_time - server_time
		
		# update values
		with self.latency_lock:
			self.latency = av_latn
		with self.time_delta_lock:
			self.time_delta = delta

	@statemethod
	def handle_MsgPlayerConnect(self, message):
		self._player_connected(message)

	@statemethod
	def handle_MsgPlayerDisconnect(self, message):
		self._player_disconnected(message)
	
	@statemethod
	def handle_MsgServerShutdown(self, message):
		# TODO: how to inform user?
		# stop client
		self.stop()

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
			#server = Server(StubClientHandler,4444)
			#server.start()

			# connect to server
			# TODO: how to test individual components?
			pass

	unittest.main()
