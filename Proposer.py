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
        self.ServerIndex = startingRequestNumber
        self.CurrentInstanceId = 0
        self.RequestQueue = Queue.deque()
        #self.ClientRequests = Queue.deque()
        self.Helping = False
        self.MajorityPromiseReceived = False
        self.MajorityAcceptObj = None
        #in order to support general application logic snap-ins, such as lock
        #service,
        #a processability will need to be tested before any attempt to process
        #it happens.
        #this is important as some commands require blocking behavior - these
        #commands need to be temporarily postponed from proposing, otherwise it
        #will cause endless proposal in the system (cannot execute)
        #Can use drop in replacement as long as the interface match.
        #Decouple Paxos with Application Logic
        self.ApplicationService = LockService(startingRequestNumber)
        self.ApplicationServiceDelayProcessQueue = []

    def __TakeHop__(self):
        self.CurrentRequestNumber+=self.ProposalNumberHop
        self.ReadyList = []
        self.AcceptanceCount = 0
        self.MajorityPromiseReceived = False
        self.MajorityAcceptObj = None


    def __PrintInternal__(self,content):
        print ("[Proposer %d] " % self.ServerIndex) + content

    def __IssuePrepare__(self,value):
        prepareObject = CommandObject(CommandType.Prepare,
                                      self.CurrentRequestNumber,
                                      self.CurrentInstanceId,
                                      value)
        self.__PrintInternal__("Prepared Issued %s" % CommandObject.ConvertToString(prepareObject))
        for address in self.AcceptorAddresses:
            self.transport.write(CommandObject.ConvertToString(prepareObject),address)

    def datagramReceived(self, data, (host, port)):
        #what kind of command is it?
        cmdObj = CommandObject.ParseFromString(data)
        #this is an out of order message.
        if cmdObj.Type != CommandType.Request and (cmdObj.RequestNumber != self.CurrentRequestNumber or cmdObj.InstanceId != self.CurrentInstanceId):
            self.__PrintInternal__("Packet Ignored %s" % CommandObject.ConvertToString(cmdObj))
            return
        if(cmdObj.Type == CommandType.Request):
            self.__PrintInternal__("Request Receive " + CommandObject.ConvertToString(cmdObj))
            #save it first, as we may be busy processing other things.
            if len(self.RequestQueue) == 0 or len(filter(lambda p: p in self.ApplicationServiceDelayProcessQueue,self.RequestQueue)) == len(self.RequestQueue):
                #this is the only pending request.  We can send this promise
                #request out to start consensus.
                #we do NOT allow in flight messages, that means the proposer
                #can NOT get ANY message ahead.
                #somewhat easy to change
                self.__IssuePrepare__((host, port) + cmdObj.Value)
            self.RequestQueue.append((host, port) + cmdObj.Value)
                
        elif cmdObj.Type == CommandType.Promise:
            #received a promise from a certain node.
            #do we have consensus for that instance?

            self.__PrintInternal__("Promise Receive %s" % CommandObject.ConvertToString(cmdObj))
            self.ReadyList.append(cmdObj.Value + tuple([(host, port)]))
            instStat = self.ReadyList
            if len(instStat) > self.AcceptorCount / 2:
                #issue an accept to everyone in the pool
                #find the largest numbered accepted value
                largestObj = max(instStat,key=lambda p: p[0])
                if largestObj[0] == -1:
                    #hasn't accepted anything yet.
                    #the server has to have request to issue in the first place
                    #before it starts consensus.
                    assert(len(self.RequestQueue) > 0)
                    #not safe to pop even if loss of message is not considered.
                    #no guarentee of acceptors are determined yet.
                    acceptedValue = self.RequestQueue[0]
                    self.Helping = False

                else:
                    acceptedValue = largestObj[1]
                    #The next series of Acceptance will result in a request to
                    #NOT pop from the Queue.
                    #We've learned that in this instance, someone has already
                    #announced they have accepted some other value.  We must
                    #push this value through (helping)
                    self.Helping = True 

                #broadcast this to this set.
                acceptObj = CommandObject(CommandType.Accept,
                                          self.CurrentRequestNumber,
                                          self.CurrentInstanceId,
                                          acceptedValue)
                for address in [x[2] for x in self.ReadyList]:
                    self.transport.write(CommandObject.ConvertToString(acceptObj),address)
                #avoid other later messages to trigger this multiple times.
                self.ReadyList = []
                self.MajorityPromiseReceived = True
                self.MajorityAcceptObj = acceptObj
            elif self.MajorityPromiseReceived:
                self.transport.write(CommandObject.ConvertToString(self.MajorityAcceptObj),(host, port))
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
                self.__PrintInternal__("Denial Received %s" % CommandObject.ConvertToString(cmdObj))
                self.__TakeHop__()
                self.__IssuePrepare__(cmdObj.Value)
        elif cmdObj.Type == CommandType.Acceptance:
                self.__PrintInternal__("Acceptance Received %s" % CommandObject.ConvertToString(cmdObj))
                self.AcceptanceCount+=1
                #we need to accumulate acceptance per instance.
                #if a majority of the acceptors have accepted a certain value,
                #then that value has to be chosen.
                if self.AcceptanceCount > self.AcceptorCount / 2:
                    #a consensus has been made.  fulfill this to
                    #the state machine.
                    consensusValue = cmdObj.Value[-3:]
                    address = cmdObj.Value[0:2]
                    requestProcessable = self.ApplicationService.ProcessRequest(consensusValue)
                    #pop one of the pending messages if necessary.
                    #queuedTask = self.RequestQueue[0]
                    if requestProcessable:
                        #deliver to state machine.
                        #if self.Helping == False:
                        if self.Helping == False:
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

                            self.__PrintInternal__("Consensus Reached ---->" + str(CommandObject.ConvertToString(responseObj)))
                            self.transport.write(CommandObject.ConvertToString(responseObj),address)
                            self.RequestQueue.popleft()
                        elif cmdObj.Value in self.RequestQueue:
                            self.RequestQueue.remove(cmdObj.Value)
                        #clean up application request delay process queue,
                        #as some
                        #requests may be available to proceed.
                        self.ApplicationServiceDelayProcessQueue = []
                        #self.RequestQueue.popleft()
                    #else:
                    elif self.Helping == False:
                        #try again, put to last.
                        #self.RequestQueue.popleft()
                        queuedTask = self.RequestQueue.popleft()
                        self.RequestQueue.append(queuedTask)
                        #needs to make sure we are not trying everything
                        #over and over again, e.g.
                        #Lock(A) Lock(A)....
                        self.ApplicationServiceDelayProcessQueue.append(queuedTask)
                        self.__PrintInternal__("Delay Queue %s" % str(self.ApplicationServiceDelayProcessQueue))
                    #Send Consensus notification, so that acceptors can fix
                    #(potentially faulty) instance numbers and reset request
                    #number
                    self.__TakeHop__()
                    #self.__PrintInternal__("Consensus Send %s" %
                    #CommandObject.ConvertToString(consensusObj))
                    self.CurrentInstanceId+=1
                    self.CurrentRequestNumber = 0

                    #print str(self.ReqeustQueue)
                    #self.__PrintInternal__(str(self.RequestQueue))
                    if len(self.RequestQueue) != 0:
                        #More work.
                        #see if this thing is in delayed processing queue.
                        #clients response may appear out of order, however, if
                        #the clients' logic is correct, then this will not be
                        #problematic, as if requests are not concurrent, then
                        #the clients will probably serialize the request in the
                        #first place.
                        for i in range(len(self.RequestQueue)):
                            if self.RequestQueue[i] not in self.ApplicationServiceDelayProcessQueue:
                                self.__IssuePrepare__(self.RequestQueue[i])
                                break
