#Proposer

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from CommandParsing import *
import socket
import Queue

class ServerNode(DatagramProtocol):
    def __init__(self, acceptorCount, proposalNumberHop, startingRequestNumber):
        self.ReadyList = [] #conceptually a list
        self.AcceptorCount = acceptorCount
        self.ProposalNumberHop = proposalNumberHop
        self.CurrentRequestNumber = startingRequestNumber
        self.CurrentInstanceId = 0
        self.RequestQueue = Queue.deque()

    def __TakeHop__():
        self.CurrentInstanceId+=1
        self.CurrentRequestNumber+=self.ProposalNumberHop
        self.ReadyList = []

    def __PrintInternal__(content):
        print "[Proposer] " + content

    def datagramReceived(self, data, (host, port)):
        #what kind of command is it?
        cmdObj = CommandObject.ParseFromString(data)
        #this is an out of order message.
        if cmdObj.RequestNumber != self.CurrentRequestNumber or cmdObj.InstanceId != self.CurrentInstanceId:
            return
        if(cmdObj.Type == CommandType.Request):
            #fill later - application logic
            self.RequestQueue.append(cmdObj.Value)
            pass
        elif cmdObj.Type == CommandType.Promise:
            #received a promise from a certain node.
            #do we have consensus for that instance?

            instStat = self.ReadyList.append((host,port) + cmdObj.Value)
            if len(instStat) > self.AccepterCount / 2:
                #a consensus for that is reached.
                #issue an accept to everyone in the pool
                #find the largest numbered accepted value
                largestObj = max(instStat,key=lambda p: p[2])
                if largestObj[2] == -1:
                    #hasn't accepted anything yet.
                    #the server has to have request to issue in the first place
                    #before it starts consensus.
                    assert(len(self.RequestQueue) > 0)
                    #not safe to pop even if loss of message is not considered.
                    #no guarentee of learners are made yet.
                    acceptedValue = self.RequestQueue.popleft()
                else:
                    acceptedValue = tuple([largestObj[3]])
                #broadcast this to this set.
                acceptObj = CommandObject(CommandType.Accept,
                                          CurrentRequestNumber,
                                          CurrentInstanceId,
                                          acceptedValue)
                for address in [x[:2] in self.ReadyList]:
                    self.transport.write(CommandObject.ConvertToString(acceptObj),address)
                __PrintInternal__("Consensus reached iid: %d, rid: %d, v: %s" % (CurrentInstanceId,CurrentRequestNumber,str(acceptedValue)))
                #no need to worry about this instance anymore, as recovery is
                #not necessary.
                #The burden is on acceptors - they could have promised to
                #someone else's proposal in the intrim, or would have accepted
                #our proposal - but we do not care about this anymore as a
                #propser.
                #the acceptors are free to accept new proposals anytime, and
                #the learners can only commit after it receives majority vote
                #for certain instance.
                __TakeHop__()
        elif cmdObj.Type == CommandType.Denial:
                #since the acceptance of accept messages are sent from acceptors, we require
                #denial messages to be sent to proposer.
                __TakeHop__()
        elif cmdObj.Type == CommandType.Acceptance:
                #we need to accumulate acceptance per instance.
                #if a majority of the acceptors have accepted a certain value,
                #then that value has to be chosen.
                pass
