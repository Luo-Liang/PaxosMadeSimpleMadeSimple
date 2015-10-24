#Proposer

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from CommandParsing import *
import socket
import Queue

class ServerNode(DatagramProtocol):
    def __init__(self, acceptorAddresses, proposalNumberHop, startingRequestNumber):
        self.ReadyList = [] #conceptually a list
        self.AcceptanceCount = 0
        self.AcceptorCount = len(acceptorAddresses)
        self.AcceptorAddresses = acceptorAddresses
        self.ProposalNumberHop = proposalNumberHop
        self.CurrentRequestNumber = startingRequestNumber
        self.CurrentInstanceId = 0
        self.RequestQueue = Queue.deque()
        self.Helping = False

    def __TakeHop__():
        self.CurrentRequestNumber+=self.ProposalNumberHop
        self.ReadyList = []
        self.AcceptanceCount = 0

    def __PrintInternal__(content):
        print "[Proposer] " + content

    def __IssuePromise__(value):
        promiseObject = CommandObject(CommandType.Promise,
                                      CurrentRequestNumber,
                                      CurrentInstanceId,
                                      value)
        for address in self.AcceptorAddresses:
            self.transport.write(CommandObject.ConvertToString(promiseObject),address)

    def datagramReceived(self, data, (host, port)):
        #what kind of command is it?
        cmdObj = CommandObject.ParseFromString(data)
        #this is an out of order message.
        if cmdObj.Type != CommandType.Request and (cmdObj.RequestNumber != self.CurrentRequestNumber or cmdObj.InstanceId != self.CurrentInstanceId):
            return
        if(cmdObj.Type == CommandType.Request):
            #save it first, as we may be busy processing other things.
            self.RequestQueue.append(cmdObj.Value)
            if len(self.RequestQueue) == 1:
                #this is the only pending request.  We can send this promise
                #request out to start consensus.
                #we do NOT allow in flight messages, that means the proposer
                #can NOT get ANY message ahead.
                #somewhat easy to change
                __IssuePromise__(cmdObj.Value)
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
                    #no guarentee of acceptors are determined yet.
                    acceptedValue = self.RequestQueue[0]
                    self.Helping = False

                else:
                    acceptedValue = tuple([largestObj[3]])
                    #The next series of Acceptance will result in a request to
                    #NOT pop from the Queue.
                    #We've learned that in this instance, someone has already
                    #announced they have accepted some other value.  We must
                    #push this value through (helping)
                    self.Helping = True 
                #broadcast this to this set.
                acceptObj = CommandObject(CommandType.Accept,
                                          CurrentRequestNumber,
                                          CurrentInstanceId,
                                          acceptedValue)
                for address in [x[:2] in self.ReadyList]:
                    self.transport.write(CommandObject.ConvertToString(acceptObj),address)
                #avoid other later messages to trigger this multiple times.
                self.ReadyList = []
                #no need to worry about this instance anymore, as recovery is
                #not necessary.
                #The burden is on acceptors - they could have promised to
                #someone else's proposal in the intrim, or would have accepted
                #our proposal - but we do not care about this anymore as a
                #propser.
                #the acceptors are free to accept new proposals anytime, and
                #the learners can only commit after it receives majority vote
                #for certain instance.
        elif cmdObj.Type == CommandType.Denial:
                #since the acceptance of accept messages are sent from
                #acceptors, we require
                #denial messages to be sent to proposer.
                __TakeHop__()
        elif cmdObj.Type == CommandType.Acceptance:
                #we need to accumulate acceptance per instance.
                #if a majority of the acceptors have accepted a certain value,
                #then that value has to be chosen.
                self.AcceptanceCount+=1
                if self.AcceptanceCount > self.AcceptorCount / 2:
                    #a consensus has been made.  fulfill this to
                    #the state machine.
                    __TakeHop__()
                    self.CurrentInstanceId+=1
                    #pop one of the pending messages if necessary.
                    if self.Helping==False:
                        self.RequestQueue.popleft()
                    consensusValue = cmdObj.Value
                    #deliver to state machine.
                    if len(self.RequestQueue) != 0:
                        #More work.
                        __IssuePromise__(self.RequestQueue[0])
