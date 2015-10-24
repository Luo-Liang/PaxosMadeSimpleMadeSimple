#Proposer

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from CommandParsing import *
import socket
import Queue
from LockService import LockService

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
        #in order to support general application logic snap-ins, such as lock
        #service,
        #a processability will need to be tested before any attempt to process
        #it happens.
        #this is important as some commands require blocking behavior - these
        #commands need to be temporarily postponed from proposing, otherwise it
        #will cause endless proposal in the system (cannot execute)
        #Can use drop in replacement as long as the interface match.
        #Decouple Paxos with Application Logic
        self.ApplicationService = LockService()
        self.ApplicationServiceDelayProcessQueue = []

    def __TakeHop__(self):
        self.CurrentRequestNumber+=self.ProposalNumberHop
        self.ReadyList = []
        self.AcceptanceCount = 0

    def __PrintInternal__(self,content):
        print "[Proposer] " + content

    def __IssuePrepare__(self,value):
        prepareObject = CommandObject(CommandType.Prepare,
                                      CurrentRequestNumber,
                                      CurrentInstanceId,
                                      value)
        for address in self.AcceptorAddresses:
            self.transport.write(CommandObject.ConvertToString(prepareObject),address)

    def datagramReceived(self, data, (host, port)):
        #what kind of command is it?
        cmdObj = CommandObject.ParseFromString(data)
        #this is an out of order message.
        if cmdObj.Type != CommandType.Request and (cmdObj.RequestNumber != self.CurrentRequestNumber or cmdObj.InstanceId != self.CurrentInstanceId):
            return
        if(cmdObj.Type == CommandType.Request):
            #save it first, as we may be busy processing other things.
            self.RequestQueue.append(cmdObj.Value + (host,port))
            if len(self.RequestQueue) == 1:
                #this is the only pending request.  We can send this promise
                #request out to start consensus.
                #we do NOT allow in flight messages, that means the proposer
                #can NOT get ANY message ahead.
                #somewhat easy to change
                __IssuePrepare__(cmdObj.Value + (host,port))
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
                __IssuePrepare__(cmdObj.Value + (host,port))
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
                    consensusValue = cmdObj.Value[0:-2]
                    address = cmdObj.Value[-2:]
                    requestProcessable = self.ApplicationService.ProcessRequest(consensusValue)
                    #pop one of the pending messages if necessary.
                    queuedTask = self.RequestQueue.popleft()
                    if self.Helping == False:
                        #deliver to state machine.
                        if requestProcessable:
                            #Application Logic says we can process this request
                            #no problem.
                            #note on the application prospective, this op may
                            #be illegal, because
                            #consecutive LOCK(A) may appear on the Paxos Log,
                            #however, on the perspective of
                            #PAXOS, this is legal, as it can portrait the
                            #consecutive LOCK(A)s as failed.
                            #send response.
                            #duplicate messages will be sent from EACH and
                            #EVERY server, it is the client's responsibility to
                            #deal with duplicates (using sequence number)
                            responseObj = CommandObject(CommandType.Respond,
                                                -1,
                                                -1,
                                                consensusValue)
                            self.transport.write(CommandObject.ConvertToString(responseObj),address)
                            #clean up application request delay process queue, as some
                            #requests may be available to proceed.
                            self.ApplicationServiceDelayProcessQueue = []
                        else:
                            #try again, put to last.
                            self.RequestQueue.append(queuedTask)
                            #needs to make sure we are not trying everything over and over again, e.g.
                            #Lock(A) Lock(A)....
                            self.ApplicationServiceDelayProcessQueue.append(queuedTask)

                    if len(self.RequestQueue) != 0:
                        #More work.
                        #see if this thing is in delayed processing queue.
                        for i in range(len(self.RequestQueue)):
                            if self.RequestQueue[i] not in self.ApplicationServiceDelayProcessQueue:
                                __IssuePrepare__(self.RequestQueue[0])
                                break
