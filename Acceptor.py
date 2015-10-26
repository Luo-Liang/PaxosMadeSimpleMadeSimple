"""
Description: This is the implementation of the acceptor node
"""
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor

from CommandParsing import *
from collections import defaultdict

# Promise Format
# CommandType.Promise RequestNumber InstanceId (value)
# Denial Format
# CommandType.Denial RequestNumber InstanceId (value) 
# Acceptance Format
# CommandType.Acceptance RequestNumber InstanceId (value) 

class AcceptorNode(DatagramProtocol):
	def __init__(self):
		# RequestNumberQueue --> Record the highest proposal number for each instance
		# ConsenusQueue --> Record the accept value for each instance
		# ProposalQueue --> Record the promised proposal number for each instance
		self.RequestNumberQueue = defaultdict(lambda: -1)
		self.ConsensusQueue = defaultdict(lambda: -1)
		self.ProposalQueue = defaultdict(lambda: -1)

	def datagramReceived(self, data, (host, port)):
		cmd_obj = CommandObject.ParseFromString(data)

		# Prepare request
		if cmd_obj.Type == CommandType.Prepare:
			# Always unique request number
			if cmd_obj.RequestNumber > self.ProposalQueue[cmd_obj.InstanceId]:
				# Promise the proposer
				response_value = cmd_obj.Value if self.RequestNumberQueue[cmd_obj.InstanceId] == -1 else self.ConsensusQueue[cmd_obj.InstanceId]
				promise_cmd_obj = CommandObject(CommandType.Promise,
												cmd_obj.RequestNumber,
												cmd_obj.InstanceId,
												tuple([self.RequestNumberQueue[cmd_obj.InstanceId],response_value]))
				self.transport.write(CommandObject.ConvertToString(promise_cmd_obj), (host, port))
				self.ProposalQueue[cmd_obj.InstanceId] = cmd_obj.RequestNumber
			else:
				# Deny the proposer since the prepare request is smaller than current
				denial_cmd_obj = CommandObject(CommandType.Denial,
												cmd_obj.RequestNumber,
												cmd_obj.InstanceId,
												cmd_obj.Value)
				self.transport.write(CommandObject.ConvertToString(denial_cmd_obj), (host, port))

		elif cmd_obj.Type == CommandType.Accept:
            #the promise says we cannot accept anything less than previously promised number.
			if cmd_obj.RequestNumber >= self.ProposalQueue[cmd_obj.InstanceId]:
				# Accept the value
				acceptance_cmd_obj = CommandObject(CommandType.Acceptance,
													cmd_obj.RequestNumber,
													cmd_obj.InstanceId,
													cmd_obj.Value)
				self.transport.write(CommandObject.ConvertToString(acceptance_cmd_obj), (host, port))
				self.RequestNumberQueue[cmd_obj.InstanceId] = cmd_obj.RequestNumber
				self.ConsensusQueue[cmd_obj.InstanceId] = cmd_obj.Value
			else:
				# Acceptor has promised other higher number request.
				# Deny the proposer since the accept request is smaller than current
				denial_cmd_obj = CommandObject(CommandType.Denial,
												cmd_obj.RequestNumber,
												cmd_obj.InstanceId,
												cmd_obj.Value)
				self.transport.write(CommandObject.ConvertToString(denial_cmd_obj), (host, port))

		else:
			assert(False)
