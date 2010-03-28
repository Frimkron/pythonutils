import socket
import threading
import select
import json
import sys
import time
import copy
import Queue
from mrf.statemachine import StateMachineBase, statemethod
from mrf.structs import TagLookup
from mrf.mathutil import deviation, mean

"""	
TODO: client id generation has been changed in attempt to remedy json dict key problem
	but this messes up the distinction between direct client addressing and client group
	addressing. Needs to think of something better!
TODO: JSON format doesn't allow non-string dictionary keys. Must re-think encoding
	and/or use of int keys in message dictionaries.
TODO: recv doesn't necessarily return the entire message! Must redesign message
	format to include a content length somehow
TODO: Unit tests for client/server
TODO: Structure diagram
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
	
	def handle_network_error(self, error_info):
		"""	
		May be invoked to deal with errors raised by network communication in this
		thread. Should be overidden.
		"""
		pass
	
	def handle_unexpected_error(self, error_info):
		"""	
		May be invoked to deal with unexpected errors raised in this thread. 
		Should be overidden.
		"""
		pass


class NoEventHandlerError(Exception): pass	


class Event(object):
	"""	
	Base class for network events which are added to the event queue for game
	loop to process.
	"""
	pass


class EvtFatalError(Event):
	"""	
	Added to event queue when an unexpected error is raised
	"""
	
	def __init__(self, to_client, error):
		self.to_client = to_client
		self.error = error


class EvtConnectionError(Event):
	"""	
	Added to the event queue when an exception is raised by a socket
	"""
	
	def __init__(self, to_client, error):
		self.to_client = to_client	
		self.error = error

class EvtClientArrived(Event):
	"""	
	Added to the event queue when a client connects to the server
	"""
	
	def __init__(self, client_id):
		self.client_id = client_id
		
		
class EvtClientDeparted(Event):
	"""	
	Added to the event queue when a client disconnects from the server
	"""
	
	def __init__(self, client_id):
		self.client_id = client_id


class Node(object):
	"""	
	Base class for all nodes in the network i.e. clients and server
	"""
	
	def __init__(self):
		self.event_queue = Queue.Queue()

	def send(self, message):
		"""	
		Invoked when a message should be sent from this node. Should be overidden
		in subclasses
		"""
		pass

	def received(self, message):
		"""	
		Invoked when this node receives a message. 
		Attempts to locate interceptor method called "intercept_<messagetype>" 
		and if found, the message is handled by it. If no intercept method is 
		found, the message is simply added to the event queue to be picked up 
		by the game loop, which is how most messages should be handled.
		"""
		hname = "intercept_"+message.__class__.__name__
		if hasattr(self, hname):
			getattr(self, hname)(message)
		else:
			self.event_queue.put(message)

	def get_node_id(self):
		pass
	
	def take_events(self):
		"""	
		Removes and returns waiting events from the event queue.
		"""
		events = []
		num = self.event_queue.qsize()
		for i in range(num):
			try:
				events.append(self.event_queue.get(block=False))								
			except Queue.Empty:
				# qsize is not exact, so we might try to get one more items than 
				# exist in the queue. Can safely ignore exception
				pass
		return events
	
	def process_events(self, handler=None):
		"""	
		Takes waiting events from the queue and dispatches them to their handler
		methods. Should be invoked in the Node's game loop. A method named 
		"handle_<eventtype>" is executed in the Node itself if found, or by
		invoking "delegate_event" otherwise, and then again in the specified 
		"handler" object, if found. Thus events may be handled both internally
		and by the application. If an event is not handled after checking 
		internally and in the handler object, a NoEventHandlerError is raised.
		"""
		for event in self.take_events():
			handled = False
			hname = "handle_"+event.__class__.__name__
			
			# dispatch to internal handler method using naming convention			
			if hasattr(self, hname):
				getattr(self, hname)(event)
				handled = True
			else:
				handled = self.delegate_event(event, hname)				
			
			# dispatch to application handler method
			if handler!=None and hasattr(handler,hname):
				getattr(handler,hname)(event)
				handled = True
				
			if not handled:
				raise NoEventHandlerError(hname)			
	
	def delegate_event(self, event, handler_name):
		"""	
		Invoked if an event handler is not present in the current class. Should
		be overidden to check elsewhere for a handler return True if the event
		was handled.
		"""
		return False
	

def wait_for_data(socket, timeout):
	rlist,wlist,xlist = select.select([socket],[],[],timeout)
	return socket in rlist
	

class Server(Node, NetworkThread):	
	"""	
	A socket server. After constructed, the "start" method should be invoked to begin
	the server in its own thread.
	"""
	
	ACCEPT_POLL_INTERVAL = 0.5
	SERVER = -1
	GROUP_ALL = "all"
	GROUP_CLIENTS = "clients"

	def __init__(self, client_factory, port):
		"""	
		Initialises the server. "client_factory" should be a callable which creates
		new client handlers. The callable should take the server, socket and client_id
		as paramters. The client handler should extend threading.Thread and 
		invoke client_arrived on startup and client_departed on termination. 
		"port" is the port number to listen for new clients on.
		"""
		Node.__init__(self)
		NetworkThread.__init__(self)
		self.client_factory = client_factory
		self.port = port
		
		self.listen_socket = None
		self.next_id = 0
		lockable_attrs(self,				
			handlers = {},		
			node_groups = TagLookup()
		)

	def make_client_id(self):
		id = "c"+str(self.next_id)
		self.next_id += 1
		return id

	def run(self):
		"""	
		Overridden from Thread - runs the server, listening on the specified port for 
		new clients connecting. For each new client a client handler of the specified 
		type is created in a new thread.
		"""
			
		try:
			self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.listen_socket.setblocking(False)
			self.listen_socket.bind((socket.gethostname(),self.port))
			self.listen_socket.listen(1)
		
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
								
				if wait_for_data(self.listen_socket, Server.ACCEPT_POLL_INTERVAL):
					conn,addr = self.listen_socket.accept()
					new_id = make_client_id()
					handler = self.client_factory(self,conn,new_id)
					with self.handlers_lock:
						self.handlers[new_id] = handler
					handler.start()
				
		except socket.error as e:	
			# handle socket error		
			self.handle_network_error((Server.SERVER,e))
								
		except:
			# handle all other errors
			self.handle_unexpected_error((Server.SERVER,sys.exc_info()[1]))
		
		finally:
			# close socket
			if self.listen_socket != None:
				self.listen_socket.close()
			# stop client handler threads
			self.stop_handlers()
	
	def handle_network_error(self, error_info):
		# add event to queue to notify application
		self.event_queue.put(EvtConnectionError(*error_info))
		
	def handle_unexpected_error(self, error_info):
		# put in event queue to notify application
		self.event_queue.put(EvtFatalError(*error_info))	
	
	def handle_EvtConnectionError(self, event):
		pass
	
	def handle_EvtFatalError(self, event):
		pass
	
	def handle_EvtClientArrived(self, event):
		pass
	
	def handle_EvtClientDeparted(self, event):
		pass
	
	def stop(self):
		"""	
		Shuts down the server, closing all client connections and terminating 
		the thread.
		"""
		with self.stopping_lock:
			self.stopping = True
					
		# wait for thread to end
		self.join()
		
	def stop_handlers(self):
		"""	
		Invoked when the server is shutting down. Stops the client handler threads.
		"""
		with self.handlers_lock:
			for c in self.handlers:
				self.handlers[c].stop()			

	def client_arrived(self, client_id):
		"""	
		Client with given id has connected. Invoked by client handler on startup.
		"""
		with self.node_groups_lock:
			# tag in appropriate groups
			self.node_groups.tag_item(client_id, Server.GROUP_ALL)
			self.node_groups.tag_item(client_id, Server.GROUP_CLIENTS)
			
		# add event to queue
		self.event_queue.put(EvtClientArrived(client_id))
		
	def client_departed(self, client_id):
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
			
		# add event to queue
		self.event_queue.put(EvtClientDeparted(client_id))

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

	READ_POLL_INTERVAL = 0.5

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
	
	def get_connected_to(self):
		"""	
		Should return the client id the socket connection is to
		"""
		pass

	def send(self, message):
		"""	
		Encodes the given message and sends it down the socket.
		"""
		data = self.encoder.encode(message)
		sent = 0
		# need to acquire lock to write to socket
		with self.get_socket_lock():
			self.get_socket().sendall(data)

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
		Blocks, waiting for messages on the socket. Raises socket.error if there is a 
		problem reading from the socket.
		"""
		try:
			while True:
				# exit loop if shutting down
				with self.stopping_lock:
					if self.stopping:
						break				
				
				# dont need to lock read from socket
				# TODO: implement envelope to ensure entire message is read
				if wait_for_data(self.get_socket(), SocketListener.READ_POLL_INTERVAL):
					data = self.get_socket().recv(1024)
					if len(data) == 0:
						raise socket.error("Socket closed")
					message = self.decoder.decode(data)
					self.received(message)
				
		except socket.error as e:
			# catch socket errors			
			self.handle_network_error((self.get_connected_to(),e))
					
		except:
			# catch all other errors
			self.handle_unexpected_error((self.get_connected_to(),sys.exc_info()[1]))
					
		finally:
			# clean up
			with self.get_socket_lock():
				if self.get_socket() != None:
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
		socket.setblocking(False)

	def get_socket(self):	
		return self.socket
	
	def get_socket_lock(self):
		return self.socket_lock
	
	def get_connected_to(self):
		return self.id

	def run(self):
		"""	
		Overidden from SocketListener. Invoked when thread is started.	
		"""
		self.server.client_arrived(self.id)	
		try:	
			self.listen_on_socket()
		finally:
			self.server.client_departed(self.id)

	def received(self, message):
		"""	
		When the client handler receives a message from its socket, it
		passes it on to the server for dispatching to its intended recipients.
		The handler ensures that the message's "sender" field is set correctly.
		"""
		message.sender = self.id
		self.server.send(message)
		
	def handle_network_error(self, error_info):
		# add to server's event queue
		self.server.event_queue.put(EvtConnectionError(*error_info))
		
	def handle_unexpected_error(self, error_info):
		# add to server's event queue
		self.server.event_queue.put(EvtFatalError(*error_info))


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
		try:
			with self.socket_lock:
				self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				# connect using blocking call				
				self.socket.setblocking(True)				
				self.socket.connect((self.host, self.port))
				# then set to non-blocking ready for reads.
				self.socket.setblocking(False)
				
			self.after_connect()
			self.listen_on_socket()
		
		except socket.error as e:
			# catch socket errors and handle
			self.handle_network_error((Server.SERVER,e))
		
		except:
			# catch all other errors
			self.handle_unexpected_error((Server.SERVER,sys.exc_info()[1]))
		
		finally:
			# check socket is closed, in case there was an error connecting
			with self.socket_lock:
				if self.socket != None:
					self.socket.close()			
			

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

	def get_connected_to(self):
		return Server.SERVER

	def get_node_id(self):
		return self.client_id

	def after_connect(self):
		"""	
		Invoked just after client connects to server and before client starts 
		listening to messages
		"""
		pass
	
	def handle_network_error(self, error_info):
		# add to event queue
		self.event_queue.put(EvtConnectionError(*error_info))
		
	def handle_unexpected_error(self, error_info):
		# add to event queue
		self.event_queue.put(EvtFatalError(*error_info))
		

class Message(Event):
	"""	
	Base class for network messages. Subclasses should implement "to_dict" to
	allow the message to be encoded for transport.
	"""

	def __init__(self, recipients, excludes, sender=Server.SERVER):
		"""	
		Initializes the message with the given recipient list and 
		sender id.
		"""
		Event.__init__(self)
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
		if message.__class__.__name__ == "MsgAcceptConnect":
			print "Encode before: %s" % str(dict)
			foo = json.dumps(dict)
			print "Encode after: %s" % foo
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

	def __init__(self, recipients, excludes, sender=-1, player_id=-1, player_info={}):
		Message.__init__(self, recipients, excludes, sender)
		self.player_id = player_id
		self.player_info = player_info

	def to_dict(self):
		return self._get_attrs(("player_id","player_info"))
		

class MsgPlayerDisconnect(Message):
	"""		
	Sent by server to inform clients of a players' departure
	"""

	def __init__(self, recipients, excludes, sender=-1, player_id=-1, reason=""):
		Message.__init__(self, recipients, excludes, sender)
		print "MsgPlayerDisconnect set player_id to %s %s" % (str(type(player_id)),str(player_id))
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
		print "players_info: %s" % str(players_info)

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
		Message.__init__(self, recipients, excludes, sender)
		self.message = message

	def to_dict(self):
		return self._get_attrs(("message",))


class GameFullError(Exception): pass


class NameTakenError(Exception): pass


class EvtPlayerRejected(Event):
	"""	
	Added to server's event queue when a client's request to enter the game is 
	rejected 
	"""
	
	def __init__(self, client_id, reason):
		Event.__init__(self)
		self.client_id = client_id
		self.reason = reason
	
	
class EvtPlayerAccepted(Event):
	"""	
	Added to server's event queue when a client's request to enter the game is 
	accepted
	"""
	
	def __init__(self, client_id):
		Event.__init__(self)
		self.client_id = client_id
	

class GameNode(Node):
	"""	
	Base class for all nodes (clients & server) in the game network
	"""
	
	def __init__(self):
		Node.__init__(self)
	
	def get_timestamp(self):
		return int(time.time()*1000)

	def intercept_MsgPing(self, message):
		"""	
		Respond with MsgPong as soon as MsgPing is received. Don't wait for
		game loop.
		"""
		resp = MsgPong([message.sender], [], self.get_node_id(), 
			message.ping_timestamp, self.get_timestamp())
		self.send(resp)


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
				info = message.player_info

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
	
	def __init__(self, max_players=4, 
			client_factory=lambda server,socket,client_id: GameClientHandler(server,socket,client_id,JsonEncoder(),JsonEncoder()), 
			port=57810):
		"""	
		Initialises the server with default handler GameClientHandler and using
		port 57810
		"""
		GameNode.__init__(self)
		Server.__init__(self, client_factory, port)
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
	
	def delegate_event(self, event, handler_name):
		"""	
		Overidden from GameNode. Invoked if server doesn't have an appropriate 
		handler method for an event. Checks appropriate client handler for handler
		method instead.
		"""
		# can only delegate messages, by checking who the message is for
		if not isinstance(event, Message):
			return False
		
		id = event.get_sender()
		ch = None
		with self.handlers_lock:
			if self.handlers.has_key(id):
				ch = self.handlers[id]
		if ch != None:
			if hasattr(ch, handler_name):
				getattr(ch, handler_name)(event)
				return True
		
		return False
	
	def handle_MsgPlayerDisconnect(self, message):
		"""	
		Server may receive player disconnect from a client, indicating that they 
		are intentionally leaving the game. On receipt, server stops client handler
		"""
		self.disconnect_client(message.player_id)

	def handle_EvtPlayerAccepted(self, event):
		pass
		
	def handle_EvtPlayerRejected(self, event):
		pass
		
	def disconnect_client(self, client_id):
		"""	
		May be invoked to "kick" a player from the server
		"""
		with self.handlers_lock:
			if self.handlers.has_key(client_id):
				# stop the handler. client_departed will later be invoked
				# to clean up handler.
				self.handlers[client_id].stop()
		
	def client_departed(self, client_id):
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
		Server.client_departed(self, client_id)
						
		# inform other players
		if send_msg:
			# TODO: Reason parameter should tell players whether client left or was kicked
			print "sending MsgPlayerDisconnect, id type is %s" % str(type(client_id))
			self.send(MsgPlayerDisconnect([GameServer.GROUP_PLAYERS],[client_id],
					GameServer.SERVER, client_id, ""))
			
	def get_num_players(self):
		return len(self.get_players())
		
	def get_players(self):
		with self.node_groups_lock:
			return copy.copy(self.node_groups.get_tag_items(GameServer.GROUP_PLAYERS))

	def get_player_names(self):
		with self.handlers_lock:
			return [self.handlers[p].player_info["name"] for p in self.get_players()]

	def player_join(self, id, info):
		"""	
		Attempt to receive the player into the game and notify others
		"""
		joined = False
		with self.node_groups_lock:
			if self.get_num_players() >= self.max_players:
				
				# add event as application hook
				self.event_queue.put(EvtPlayerRejected(id,"The game is full"))
				
				# raise exception
				raise GameFullError()
			
			elif info["name"] in self.get_player_names():
				
				# add event as application hook
				self.event_queue.put(EvtPlayerRejected(id, "The player name is taken"))
				
				# raise exception
				raise NameTakenError()
			
			else:			
				# add event as application hook
				self.event_queue.put(EvtPlayerAccepted(id))
			
				# add into group of connected players
				self.node_groups.tag_item(id, GameServer.GROUP_PLAYERS)
				joined = True
				
		if joined:
			# notify players
			print "sending MsgPlayerConnect, id type is %s" % str(type(id))
			self.send(MsgPlayerConnect([GameServer.GROUP_PLAYERS], [id], 
				GameServer.SERVER, id, info))
		
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
		with self.stopping_lock:
			should_send = not self.stopping
		if should_send:
			self.send(MsgServerShutdown([GameServer.GROUP_CLIENTS],[],GameServer.SERVER))
		# close listener socket and stop client handlers
		Server.stop(self)
		

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
			for k in message.players_info:
				self.machine.register_player(k, message.players_info[k])

			self.machine.change_state("StateInGame")

		def handle_MsgRejectConnect(self, message):
			"""	
			Client should receive MsgRejectConnect from the server to
			indicate that connection was unsuccessful
			"""
			print "Got reject message"
			# not allowed to enter game - shut down the client
			self.machine.stop()

	class StateInGame(StateMachineBase.State):

		pass

	def __init__(self, host, port, player_info, encoder=JsonEncoder(), decoder=JsonEncoder()):
		GameNode.__init__(self)
		Client.__init__(self, host, port, encoder, decoder)
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
	
	def is_in_game(self):
		return self.get_state() == "StateInGame"
	
	def stop(self):
		"""	
		Overidden from Client. Sends disconnect message to server before closing
		the socket.
		"""
		if self.is_in_game():
			with self.stopping_lock:
				should_send = not self.stopping
			if should_send:
				# send disconnect message
				print "(client) sending MsgPlayerDisconnect, id type is %s" % str(type(self.client_id))
				self.send(MsgPlayerDisconnect([Server.SERVER],[],self.client_id,self.client_id,""))
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
		self.register_player(message.player_id, message.player_info)		

	def _player_disconnectd(self, message):
		if self.player_list.has_key(message.player_id):
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
			m = TestMessage(["c1","c2","c3"],[],"c1","Frank", 25, 123.5)
			j = self.encoder.encode(m)
			print j
			m2 = self.encoder.decode(j)
			self.assertEquals(TestMessage, m2.__class__)
			self.assertEquals(["c1","c2","c3"],m2.get_recipients())
			self.assertEquals([],m2.get_excludes())
			self.assertEquals("c1",m2.get_sender())
			self.assertEquals("Frank", m2.name)
			self.assertEquals(25, m2.age)
			self.assertEquals(123.5, m2.weight)

	class TestMessages(unittest.TestCase):
		
		encoder = JsonEncoder()

		def doTestMessage(self, message_class, **params):
			m1 = message_class(**params)
			for k in params:
				self.assertEquals(params[k], getattr(m1, k))
			data = self.encoder.encode(m1)
			m2 = self.encoder.decode(data)
			for k in params:
				self.assertEquals(params[k], getattr(m2, k))
		
		def testMessages(self):
			self.doTestMessage(MsgPlayerConnect, 
				recipients=["players",1], excludes=[2], sender=2, player_id=1, player_info={"name":"dave","age":21})
			self.doTestMessage(MsgPlayerDisconnect,
				recipients=[2,"players"], excludes=[3], sender=5, player_id=9, reason="test")
			self.doTestMessage(MsgServerShutdown,
				recipients=[3,"players"], excludes=[2,4], sender=6)
			self.doTestMessage(MsgRequestConnect,
				recipients=[4,5], excludes=["players"], sender=7, player_info={"name":"dave","age":21})
			self.doTestMessage(MsgAcceptConnect,
				recipients=[1], excludes=[99,98], sender=4, player_id=3, 
				players_info={"dave":{"age":31},"sue":{"age":24}})
			self.doTestMessage(MsgRejectConnect,
				recipients=[4,5], excludes=[9], sender=2, reason="test")
			self.doTestMessage(MsgPing,
				recipients=[2,3], excludes=[5], sender=7, ping_timestamp=123456789)
			self.doTestMessage(MsgPong,
				recipients=[9,9], excludes=[6,7], sender=2, ping_timestamp=123456789, 
				pong_timestamp=987654321)
			self.doTestMessage(MsgChat,
				recipients=[7,7], excludes=[5], sender=3, message="hi thar")
	
	class EventHandler(object):
	
		messages = []
		
		def __init__(self):
			self.messages = []
		
		def handle_EvtClientArrived(self, event):
			print "Client %d arrived" % event.client_id
			
		def handle_EvtClientDeparted(self, event):
			print "Client %d departed" % event.client_id

		def handle_EvtFatalError(self, event):
			print "Fatal error: %s" % str(event.error.args)			
		
		def handle_EvtConnectionError(self, event):
			print "Connection error: %s" % str(event.error.args)

		def handle_MsgChat(self, event):
			print "Chat message: %s" % str(event.message)
			self.messages.append(event)
			
		def handle_MsgAcceptConnect(self, event):
			print "Connect accepted"
			self.messages.append(event)
			
		def handle_MsgRejectConnect(self, event):
			print "Connect rejected: %s" % str(event.reason)
			self.messages.append(event)

		def handle_EvtPlayerAccepted(self, event):
			print "Player accepted: %d" % event.client_id
			self.messages.append(event)
			
		def handle_EvtPlayerRejected(self, event):
			print "Player rejected: %d" % event.client_id
			self.messages.append(event)
			
		def handle_MsgPlayerConnect(self, event):
			print "Handling MsgPlayerConnect, id type is %s" % str(type(event.player_id))
			print "Player connected: %d, %s" % (event.player_id, event.player_info["name"])
			self.messages.append(event)
			
		def handle_MsgPlayerDisconnect(self, event):
			print "Handling MsgPlayerDisconnect, id type is %s" % str(type(event.player_id))
			print "Player disconnect: %d" % event.player_id
			self.messages.append(event)
			
	
	class TestClientServer(unittest.TestCase):

		def make_client_handler(self,server,socket,client_id):
			return ClientHandler(server,socket,client_id,JsonEncoder(),JsonEncoder())

		def testServerNumClients(self):
			"""	
			Test that Server maintains client handler set as expected 
			"""
			# create server
			handler = EventHandler()
			server = Server(self.make_client_handler,4444)
			server.start()
			time.sleep(0.1)			
			server.process_events(handler)

			self.assertEquals(0, server.get_num_clients())

			# connect to server
			sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock1.connect(("localhost",4444))
			time.sleep(0.1)
			server.process_events(handler)
			
			self.assertEquals(1, server.get_num_clients())
			
			# connect second client
			sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock2.connect(("localhost",4444))
			time.sleep(0.1)
			server.process_events(handler)
			
			self.assertEquals(2, server.get_num_clients())
			
			# disconnect second
			sock2.close()
			time.sleep(0.1)
			server.process_events(self)
			
			self.assertEquals(1, server.get_num_clients())
			
			# disconnect first
			sock1.close()
			time.sleep(0.1)
			server.process_events(handler)
			
			self.assertEquals(0, server.get_num_clients())
			
			server.stop()
			
		def testClientConnection(self):
			"""	
			Test that the client can connect and communicate with the server 
			"""
			server_handler = EventHandler()
			server = Server(self.make_client_handler,4445)	
			server.start()
			time.sleep(0.1)
			
			encoder = JsonEncoder()
			client_handler = EventHandler()
			client = Client("localhost", 4445, encoder, encoder)
			client.start()
			time.sleep(0.1)
			
			server.process_events(server_handler)
			client.process_events(client_handler)
			
			self.assertEquals(1, server.get_num_clients())

			client.send(MsgChat([Server.SERVER],[], None, "Hi server!"))
			time.sleep(0.1)
			
			server.process_events(server_handler)
			client.process_events(client_handler)
			
			self.assertEquals(1, len(server_handler.messages))
			self.assertEquals("Hi server!", server_handler.messages[-1].message)
			self.assertEquals(0, server_handler.messages[-1].sender)
			
			server.send(MsgChat([0],[],Server.SERVER,"Hello client!"))
			time.sleep(0.1)
			
			server.process_events(server_handler)
			client.process_events(client_handler)
			
			self.assertEquals(1, len(client_handler.messages))
			self.assertEquals("Hello client!", client_handler.messages[-1].message)
			self.assertEquals(Server.SERVER, client_handler.messages[-1].sender)
			
			client.stop()		
			server.stop()
			
		def testMessageDelivery(self):
			"""	
			Test that messages are send to correct recipients
			"""
			server_handler = EventHandler()
			server = Server(self.make_client_handler,4446)
			server.start()
			time.sleep(0.1)			
				
			encoder = JsonEncoder()
			clientA_handler = EventHandler()
			clientA = Client("localhost", 4446, encoder, encoder)
			clientA.start()
			time.sleep(0.1)
			
			clientB_handler = EventHandler()
			clientB = Client("localhost", 4446, encoder, encoder)
			clientB.start()
			time.sleep(0.1)

			# send from client A to client B
			clientA.send(MsgChat([1],[],None,"Hi client B"))
			time.sleep(0.1)
			
			server.process_events(server_handler)
			clientA.process_events(clientA_handler)
			clientB.process_events(clientB_handler)

			self.assertEquals(1, len(clientB_handler.messages))
			self.assertEquals("Hi client B", clientB_handler.messages[-1].message)
			self.assertEquals(0, clientB_handler.messages[-1].sender)

			# send from client B to client A
			clientB.send(MsgChat([0],[],None,"Hi client A"))
			time.sleep(0.1)
			
			server.process_events(server_handler)
			clientA.process_events(clientA_handler)
			clientB.process_events(clientB_handler)

			self.assertEquals(1, len(clientA_handler.messages))
			self.assertEquals("Hi client A", clientA_handler.messages[-1].message)
			self.assertEquals(1, clientA_handler.messages[-1].sender)

			# send from server to all clients
			server.send(MsgChat([Server.GROUP_CLIENTS],[],Server.SERVER,"Hi all clients"))
			time.sleep(0.1)
			
			server.process_events(server_handler)
			clientA.process_events(clientA_handler)
			clientB.process_events(clientB_handler)

			self.assertEquals(0, len(server_handler.messages))
			self.assertEquals(2, len(clientA_handler.messages))
			self.assertEquals("Hi all clients", clientA_handler.messages[-1].message)
			self.assertEquals(Server.SERVER, clientA_handler.messages[-1].sender)
			self.assertEquals(2, len(clientB_handler.messages))
			self.assertEquals("Hi all clients", clientB_handler.messages[-1].message)
			self.assertEquals(Server.SERVER, clientB_handler.messages[-1].sender)
		
			# send from client A to everyone
			clientA.send(MsgChat([Server.GROUP_ALL],[],None,"Hi everyone"))
			time.sleep(0.1)
			
			server.process_events(server_handler)
			clientA.process_events(clientA_handler)
			clientB.process_events(clientB_handler)
			
			self.assertEquals(1, len(server_handler.messages))
			self.assertEquals("Hi everyone", server_handler.messages[-1].message)
			self.assertEquals(0, server_handler.messages[-1].sender)
			self.assertEquals(3, len(clientA_handler.messages))
			self.assertEquals("Hi everyone", clientA_handler.messages[-1].message)
			self.assertEquals(0, clientA_handler.messages[-1].sender)
			self.assertEquals(3, len(clientB_handler.messages))
			self.assertEquals("Hi everyone", clientB_handler.messages[-1].message)
			self.assertEquals(0, clientB_handler.messages[-1].sender)
			
			# send from client A to everyone excluding client B
			clientA.send(MsgChat([Server.GROUP_ALL],[1],None,"Client B sucks"))
			time.sleep(0.1)
			
			server.process_events(server_handler)
			clientA.process_events(clientA_handler)
			clientB.process_events(clientB_handler)
			
			self.assertEquals(2, len(server_handler.messages))
			self.assertEquals("Client B sucks", server_handler.messages[-1].message)
			self.assertEquals(0, server_handler.messages[-1].sender)
			self.assertEquals(4, len(clientA_handler.messages))
			self.assertEquals("Client B sucks", clientA_handler.messages[-1].message)
			self.assertEquals(0, clientA_handler.messages[-1].sender)
			self.assertEquals(3, len(clientB_handler.messages))
			
			# send from client A to everyone excluding client A and server
			clientA.send(MsgChat([Server.GROUP_ALL],[0,Server.SERVER],None,"Two excludes"))
			time.sleep(0.1)
			
			server.process_events(server_handler)
			clientA.process_events(clientA_handler)
			clientB.process_events(clientB_handler)
			
			self.assertEquals(2, len(server_handler.messages))
			self.assertEquals(4, len(clientA_handler.messages))
			self.assertEquals(4, len(clientB_handler.messages))
			self.assertEquals("Two excludes", clientB_handler.messages[-1].message)
			self.assertEquals(0, clientB_handler.messages[-1].sender)

			clientA.stop()
			clientB.stop()
			server.stop()

	class TestGameClientServer(unittest.TestCase):
	
		def make_client_handler(self,server,socket,client_id):
			return GameClientHandler(server,socket,client_id,JsonEncoder(),JsonEncoder())

		def test_client_connection(self):
			"""	
			Test that GameClient can (or cant) connect to the game accordingly
			"""
			server_handler = EventHandler()
			server = GameServer(2,self.make_client_handler,4447)	
			server.start()
			time.sleep(0.1)
			
			encoder = JsonEncoder()
			clientA_handler = EventHandler()
			clientA = GameClient("localhost", 4447, {"name":"testerA"}, encoder, encoder)
			clientA.start()
			time.sleep(0.1)
			
			for i in range(2):
				server.process_events(server_handler)
				clientA.process_events(clientA_handler)
				time.sleep(0.1)
			
			self.assertEquals(1, server.get_num_clients())
			self.assertEquals(1, server.get_num_players())
			self.assertEquals("testerA", server.get_player_names()[0])
			self.assertEquals(1, len(server_handler.messages))
			self.assertEquals(EvtPlayerAccepted, server_handler.messages[-1].__class__)
			
			# add second player with taken name
			clientB1_handler = EventHandler()
			clientB1 = GameClient("localhost", 4447, {"name":"testerA"}, encoder, encoder)
			clientB1.start()
			time.sleep(0.1)
			
			for i in range(3):
				server.process_events(server_handler)
				clientA.process_events(clientA_handler)
				clientB1.process_events(clientB1_handler)
				time.sleep(0.1)
			
			# second player should have been rejected because name is taken
			self.assertEquals(1, server.get_num_players())
			self.assertEquals(1, len(clientB1_handler.messages))
			self.assertEquals(MsgRejectConnect,clientB1_handler.messages[-1].__class__)
			self.assertEquals(2, len(server_handler.messages))
			self.assertEquals(EvtPlayerRejected, server_handler.messages[-1].__class__)
			
			# add second player with unique name
			clientB2_handler = EventHandler()
			clientB2 = GameClient("localhost", 4447, {"name":"testerB"}, encoder, encoder)
			clientB2.start()
			time.sleep(0.1)
			
			for i in range(3):
				server.process_events(server_handler)
				clientA.process_events(clientA_handler)
				clientB2.process_events(clientB2_handler)
				time.sleep(0.1)
			
			self.assertEquals(2, server.get_num_players())
			self.assertEquals(3, len(server_handler.messages))
			self.assertEquals(EvtPlayerAccepted, server_handler.messages[-1].__class__)
			self.assertEquals(2, len(clientA_handler.messages))
			self.assertEquals(MsgPlayerConnect, clientA_handler.messages[-1].__class__)
			self.assertEquals(2, clientA_handler.messages[-1].player_id)
			self.assertEquals("testerB", clientA_handler.messages[-1].player_info["name"])
			self.assertEquals(1, len(clientB2_handler.messages))
			self.assertEquals(MsgAcceptConnect, clientB2_handler.messages[-1].__class__)
			print clientB2_handler.messages[-1].players_info
			self.assertTrue(clientB2_handler.messages[-1].players_info.has_key(0))
			self.assertEquals("testerA", clientB2_handler.messages[-1].players_info[0]["name"])
			
			# add third player
			clientC_handler = EventHandler()
			clientC = GameClient("localhost", 4447, {"name":"testerC"}, encoder, encoder)
			clientC.start()
			time.sleep(0.1)
			
			server.process_events(server_handler)
			clientA.process_events(clientA_handler)
			clientB2.process_events(clientB2_handler)
			clientC.process_events(clientC_handler)
			time.sleep(0.1)
			
			server.process_events(server_handler)
			clientA.process_events(clientA_handler)
			clientB2.process_events(clientB2_handler)
			clientC.process_events(clientC_handler)
			time.sleep(0.1)
			
			# third player should have been rejected because max is 2
			self.assertEquals(1, len(clientC_handler.messages))
			self.assertEquals(MsgRejectConnect,clientC_handler.messages[-1].__class__)
			self.assertEquals(4, len(server_handler.messages))
			self.assertEquals(EvtPlayerRejected, server_handler.messages[-1].__class__)
			
			clientA.stop()
			clientB1.stop()
			clientB2.stop()
			clientC.stop()
			server.stop()
			
			
	def print_queue(queue):
		print "queue:"
		try:
			print "\t%s" % str(queue.get_nowait())
		except Empty:
			pass
		
	unittest.main()
	
	
	
	
	
	
	
