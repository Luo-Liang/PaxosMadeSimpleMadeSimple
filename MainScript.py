#this serves as a Paxos node - a listener, a proposer and an accepter

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import argparse
import sys
import Acceptor
import Proposer

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--index',type=int, action='store')
parser.add_argument('-s','--server-ips',nargs='+')
parser.add_argument('-p','--server-ports',nargs='+')
parseResult = parser.parse_args(sys.argv[1:])
servIndex = parseResult.index
servIPs = parseResult.server_ips
servPorts = [int(x) for x in parseResult.server_ports]
servCount = len(servPorts)
thisPort = servPorts[servIndex]
thisIP = servIPs[servIndex]

reactor.listenUDP(thisPort, ServerNode())
reactor.listenUDP(thisPort, AcceporNode())
reactor.run()
