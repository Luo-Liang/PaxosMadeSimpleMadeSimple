#Proposer
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
class ServerNode(DatagramProtocol):
    def datagramReceived(self, data, (host, port)):
