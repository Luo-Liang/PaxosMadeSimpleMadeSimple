#This serves as a Paxos node - a listener, a proposer and an accepter
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import argparse
import sys
import Acceptor
import Proposer

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--index',type=int, action='store')
parser.add_argument('-ip','--node-ips',nargs='+')
parser.add_argument('-pp','--proposer-ports',nargs='+')
parser.add_argument('-ap','--acceptor-ports',nargs='+')

parseResult = parser.parse_args(sys.argv[1:])
servIndex = parseResult.index
proposerIPs = parseResult.node_ips
proposerPorts = [int(x) for x in parseResult.proposer_ports]
acceptorPorts = [int(x) for x in parseResult.acceptor_ports]

# Initialize a proposer
reactor.listenUDP(proposerPorts[servIndex], Proposer.ServerNode(zip(proposerIPs, acceptorPorts), len(proposerIPs), servIndex))
# Initialize an acceptor
reactor.listenUDP(acceptorPorts[servIndex], Acceptor.AcceptorNode())

reactor.run()
