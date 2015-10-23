class ServerNode(DatagramProtocol):
    def datagramReceived(self, data, (host, port)):
