from mrf.network import *
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
        print(j)
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
        print("Client %d arrived" % event.client_id)
        
    def handle_EvtClientDeparted(self, event):
        print("Client %d departed" % event.client_id)

    def handle_EvtFatalError(self, event):
        print("Fatal error: %s" % str(event.error.args))
    
    def handle_EvtConnectionError(self, event):
        print("Connection error to %d: %s" % (event.to_client,str(event.error.args)))

    def handle_MsgChat(self, event):
        print("Chat message: %s" % str(event.message))
        self.messages.append(event)
        
    def handle_MsgAcceptConnect(self, event):
        print("Connect accepted")
        self.messages.append(event)
        
    def handle_MsgRejectConnect(self, event):
        print("Connect rejected: %s" % str(event.reason))
        self.messages.append(event)

    def handle_EvtPlayerAccepted(self, event):
        print("Player accepted: %d" % event.client_id)
        self.messages.append(event)
        
    def handle_EvtPlayerRejected(self, event):
        print("Player rejected: %d" % event.client_id)
        self.messages.append(event)
        
    def handle_MsgPlayerConnect(self, event):
        print("Player connected: %d, %s" % (event.player_id, event.player_info["name"]))
        self.messages.append(event)
        
    def handle_MsgPlayerDisconnect(self, event):
        print("Player disconnect: %d" % event.player_id)
        self.messages.append(event)
        
    def handle_MsgServerShutdown(self, event):
        print("Server shutdown")
        self.messages.append(event)
        

class TestClientServer(unittest.TestCase):

    def make_client_handler(self,server,socket,client_id):
        return ClientHandler(server,socket,client_id,JsonEncoder())

    def testServerNumClients(self):
        """    
        Test that Server maintains client handler set as expected 
        """
        
        server = None
        try:
        
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
        
        finally:
            if server:
                server.stop()
        
    def testClientConnection(self):
        """    
        Test that the client can connect and communicate with the server 
        """
        
        server = None
        client = None
        try:
        
            server_handler = EventHandler()
            server = Server(self.make_client_handler,4445)    
            server.start()
            time.sleep(0.1)
        
            encoder = JsonEncoder()
            client_handler = EventHandler()
            client = Client("localhost", 4445, encoder)
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
        
        finally:
            if client:
                client.stop()        
            if server:
                server.stop()
        
    def testMessageDelivery(self):
        """    
        Test that messages are send to correct recipients
        """
        
        server = None
        clientA = None
        clientB = None
        try:
        
            server_handler = EventHandler()
            server = Server(self.make_client_handler,4446)
            server.start()
            time.sleep(0.1)            
            
            encoder = JsonEncoder()
            clientA_handler = EventHandler()
            clientA = Client("localhost", 4446, encoder)
            clientA.start()
            time.sleep(0.1)
        
            clientB_handler = EventHandler()
            clientB = Client("localhost", 4446, encoder)
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

        finally:
            if clientA:
                clientA.stop()
            if clientB:
                clientB.stop()
            if server:
                server.stop()


class TestGameClientServer(unittest.TestCase):

    def pong_test(self,round_trips,offset,expected_latency,expected_delta):
        encoder = JsonEncoder()
        client = GameClient({"name":"tester"},"localhost", 4447,encoder)
        for rt in round_trips:
            start = int(time.time()*1000)-rt
            client.intercept_MsgPong(MsgPong([],[],-1,ping_timestamp=start,
                    pong_timestamp=start+(rt/2)+offset))
        self.assertAlmostEquals(expected_latency, client.get_latency(), delta=10)
        self.assertAlmostEquals(expected_delta, client.get_time_delta(), delta=10)

    def test_handle_pong_calculates_delta_and_latency(self):
        self.pong_test([200,202,198,200],500,100,-500)

    def test_handle_pong_ignores_rogue_measurements(self):
        self.pong_test([200,1000,198,202],500,100,-500)
        
    def test_handle_pong_discards_old_measurements(self):
        self.pong_test([200,205,210,215,220,225,230,235,240,245],500,117,-500)
    
    def test_handle_pong_allows_rogue_measurements_to_become_norm(self):
        self.pong_test([200,202,198,200,1000,1002,998,1000],500,500,-500)
    
    def make_client_handler(self,server,socket,client_id):
        return GameClientHandler(server,socket,client_id,JsonEncoder())

    def test_player_connection(self):
        """    
        Test that GameClient can (or cant) connect to the game accordingly
        """
        
        server = None
        clientA = None
        clientB1 = None
        clientB2 = None
        clientC = None
        try:
        
            server_handler = EventHandler()
            server = GameServer(2,self.make_client_handler,4447)    
            server.start()
            time.sleep(0.1)
        
            encoder = JsonEncoder()
            clientA_handler = EventHandler()
            clientA = GameClient({"name":"testerA"},"localhost", 4447, encoder)
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
        
            # close game, attempt to add player
            server.set_closed(True)
            clientB0_handler = EventHandler()
            clientB0 = GameClient({"name":"testerA1"},"localhost", 4447, encoder)
            clientB0.start()
            time.sleep(0.1)
            
            for i in range(3):
                server.process_events(server_handler)
                clientA.process_events(clientA_handler)
                clientB0.process_events(clientB0_handler)
                time.sleep(0.1)
                
            # player should have been rejected because game is closed
            self.assertEquals(1, server.get_num_players())
            self.assertEquals(1, len(clientB0_handler.messages))
            self.assertEquals(MsgRejectConnect,clientB0_handler.messages[-1].__class__)
            self.assertEquals(2, len(server_handler.messages))
            self.assertEquals(EvtPlayerRejected, server_handler.messages[-1].__class__)
        
            # reopen game, add second player with taken name
            server.set_closed(False)
            clientB1_handler = EventHandler()
            clientB1 = GameClient({"name":"testerA"},"localhost", 4447,  encoder)
            clientB1.start()
            time.sleep(0.1)
        
            for i in range(3):
                server.process_events(server_handler)
                clientA.process_events(clientA_handler)
                clientB0.process_events(clientB0_handler)
                clientB1.process_events(clientB1_handler)
                time.sleep(0.1)
        
            # second player should have been rejected because name is taken
            self.assertEquals(1, server.get_num_players())
            self.assertEquals(1, len(clientB1_handler.messages))
            self.assertEquals(MsgRejectConnect,clientB1_handler.messages[-1].__class__)
            self.assertEquals(3, len(server_handler.messages))
            self.assertEquals(EvtPlayerRejected, server_handler.messages[-1].__class__)
        
            # add second player with unique name
            clientB2_handler = EventHandler()
            clientB2 = GameClient({"name":"testerB"},"localhost", 4447,  encoder)
            clientB2.start()
            time.sleep(0.1)
        
            for i in range(3):
                server.process_events(server_handler)
                clientA.process_events(clientA_handler)
                clientB0.process_events(clientB0_handler)
                clientB1.process_events(clientB1_handler)
                clientB2.process_events(clientB2_handler)
                time.sleep(0.1)
        
            self.assertEquals(2, server.get_num_players())
            self.assertEquals(4, len(server_handler.messages))
            self.assertEquals(EvtPlayerAccepted, server_handler.messages[-1].__class__)
            self.assertEquals(2, len(clientA_handler.messages))
            self.assertEquals(MsgPlayerConnect, clientA_handler.messages[-1].__class__)
            self.assertEquals(clientB2.client_id, clientA_handler.messages[-1].player_id)
            self.assertEquals("testerB", clientA_handler.messages[-1].player_info["name"])
            self.assertEquals(1, len(clientB2_handler.messages))
            self.assertEquals(MsgAcceptConnect, clientB2_handler.messages[-1].__class__)
            self.assertTrue(clientB2_handler.messages[-1].players_info.has_key(0))
            self.assertEquals("testerA", clientB2_handler.messages[-1].players_info[clientA.client_id]["name"])
        
            # add third player
            clientC_handler = EventHandler()
            clientC = GameClient({"name":"testerC"},"localhost", 4447,  encoder)
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
            self.assertEquals(5, len(server_handler.messages))
            self.assertEquals(EvtPlayerRejected, server_handler.messages[-1].__class__)
        
        finally:
            if clientA:
                clientA.stop()
            if clientB0:
                clientB0.stop()
            if clientB1:
                clientB1.stop()
            if clientB2:
                clientB2.stop()
            if clientC:
                clientC.stop()
            if server:
                server.stop()
        
    def test_player_arrive_depart_notification(self):
    
        server = None
        clientA = None
        clientB = None
        try:
    
            # start server
            server_handler = EventHandler()
            server = GameServer(8,self.make_client_handler,4448)    
            server.start()
            time.sleep(0.1)
        
            # add player 0
            encoder = JsonEncoder()
            clientA_handler = EventHandler()
            clientA = GameClient({"name":"testerA"},"localhost", 4448,  encoder)
            clientA.start()
            time.sleep(0.1)
        
            for i in range(2):
                server.process_events(server_handler)
                clientA.process_events(clientA_handler)
                time.sleep(0.1)
            
            # add player 1
            clientB_handler = EventHandler()
            clientB = GameClient({"name":"testerB"},"localhost", 4448,  encoder)
            clientB.start()
            time.sleep(0.1)
        
            for i in range(2):
                server.process_events(server_handler)
                clientA.process_events(clientA_handler)
                clientB.process_events(clientB_handler)
                time.sleep(0.1)
            
            self.assertEquals(2, server.get_num_players())
            
            # player 0 should be notified
            # MsgAcceptConnect, MsgPlayerConnect
            self.assertEquals(2, len(clientA_handler.messages))
            self.assertEquals(MsgPlayerConnect, clientA_handler.messages[-1].__class__)
            self.assertEquals(1, clientA_handler.messages[-1].player_id)
            self.assertEquals({"name":"testerB"}, clientA_handler.messages[-1].player_info)
        
            server.disconnect_client(0)            
            time.sleep(0.1)
        
            server.process_events(server_handler)
            clientA.process_events(clientA_handler)
            clientB.process_events(clientB_handler)
        
            self.assertEquals(1, server.get_num_players())
        
            # player 1 should be notified
            # MsgAcceptConnect, MsgPlayerDisconnect
            self.assertEquals(2, len(clientB_handler.messages))
            self.assertEquals(MsgPlayerDisconnect, clientB_handler.messages[-1].__class__)
            self.assertEquals(0, clientB_handler.messages[-1].player_id)
        
            # server shuts down
            server.stop()
            time.sleep(0.1)
        
            server.process_events(server_handler)
            clientB.process_events(clientB_handler)
        
            # player 1 should be notified
            # MsgAcceptConnect, MsgPlayerDisconnect, MsgServerShutdown
            self.assertEquals(3, len(clientB_handler.messages))
            self.assertEquals(MsgServerShutdown, clientB_handler.messages[-1].__class__)

        finally:
            if clientA:
                clientA.stop()
            if clientB:
                clientB.stop()
            if server:
                server.stop()
