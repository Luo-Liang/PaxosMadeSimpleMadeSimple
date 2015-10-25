"""
Description: This is the implementation of the acceptor node;
"""
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor

from CommandParsing import *

# Promise Format
# CommandType.Promise RequestNumber InstanceId (value)
# Denial Format
# CommandType.Denial RequestNumber InstanceId (value) 
# Acceptance Format
# CommandType.Acceptance RequestNumber InstanceId (value) 


class AcceptorNode(DatagramProtocol):
	def __init__(self):
		self.current_instance_id = 0
		self.current_request_number = -1
		self.current_accept_value = -1 

	def datagramReceived(self, data, (host, port)):
		cmd_obj = CommandObject.ParseFromString(data)

		# Only current instance ID is processed.
		# cmd_obj.InstanceId < self.current_instance_id --> Ignore
		# cmd_obj.InstanceId > self.current_instance_id --> Impossible
		if cmd_obj.InstanceId != self.current_instance_id:
			print "-->" + CommandObject.ConvertToString(cmd_obj) + "--> Ignore"
			return

		if cmd_obj.Type == CommandType.Prepare:
			# Always unique request number
			if cmd_obj.RequestNumber > self.current_request_number:
				# Promise the proposer
				promise_cmd_obj = CommandObject(CommandType.Promise,
												cmd_obj.RequestNumber,
												cmd_obj.InstanceId,
												tuple([self.current_request_number,self.current_accept_value]))
				self.transport.write(CommandObject.ConvertToString(promise_cmd_obj), (host, port))
				print "-->" + "Send promise request " + str(promise_cmd_obj.RequestNumber)
			else:
				# Deny the proposer since the prepare request is smaller than current
				denial_cmd_obj = CommandObject(CommandType.Denial,
												cmd_obj.RequestNumber,
												cmd_obj.InstanceId,
												cmd_obj.Value)
				self.transport.write(CommandObject.ConvertToString(denial_cmd_obj), (host, port))
				print "-->" + "Send denial request " + str(denial_cmd_obj.RequestNumber) + " in the prepare phase"

		elif cmd_obj.Type == CommandType.Accept:
			if cmd_obj.RequestNumber >= self.current_request_number:
				# Accept the value
				acceptance_cmd_obj = CommandObject(CommandType.Acceptance,
													cmd_obj.RequestNumber,
													cmd_obj.InstanceId,
													cmd_obj.Value)
				self.transport.write(CommandObject.ConvertToString(acceptance_cmd_obj), (host, port))
				self.current_reqeust_number = cmd_obj.RequestNumber
				self.current_accept_value = cmd_obj.Value
				print "-->" + "Send acceptance request " + str(acceptance_cmd_obj.RequestNumber)
			else:
				# Acceptor has promised other higher number request.
				# Deny the proposer since the accept request is smaller than current
				denial_cmd_obj = CommandObject(CommandType.Denial,
												cmd_obj.RequestNumber,
												cmd_obj.InstanceId,
												cmd_obj.Value)
				self.transport.write(CommandObject.ConvertToString(denial_cmd_obj), (host, port))
				print "-->" + "Send denial request " + str(denial_cmd_obj.RequestNumber) + " in the accept phase"

		elif cmd_obj.Type == CommandType.Consensus:
			# Achieve the consensus
			self.current_instance_id += 1
			self.current_request_number = -1
			self.current_accept_value = -1 
			print "-->" + "Consensus " + CommandObject.ConvertToString(cmd_obj)

		else:
			# Impossible
			print "-->" + "Why do I receive this?"
