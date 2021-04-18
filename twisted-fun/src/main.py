from twisted.internet import protocol, reactor, endpoints

class Echo(protocol.Protocol):
    def dataReceived(self, data):
        self.transport.write(data)

class EchoFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return Echo()

print("Running on 127.0.1:1234")
endpoints.serverFromString(reactor, "tcp:1234").listen(EchoFactory())
reactor.run()