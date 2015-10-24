class CommandType:
    Prepare, Promise, Respond, Accept, Request, Denial, Acceptance = ("PREPARE","PROMISE","RESPOND","ACCEPT","REQUEST","DENIAL","ACCEPTANCE")
#equivalent-ish to
#class CommandParsing
#{
#   CommandType Type
#   int InstanceId
#   int RequestNumber
#   [Optional]string Value
#}

#PREPARE: 


#Promise Response Format:
#Promise InstanceId RequestNumber (Largest Accepted Proposal Number, Accepted Value) 
#                                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#                            Notice that value is a tuple. This is used to facillitate argument passing
class CommandObject:
    def __init__(self, command, requestNumber, instanceId, value):
        self.Type = command
        self.RequestNumber = requestNumber
        self.InstanceId = instanceId
        self.Value = value

    @staticmethod
    def ParseFromString(cmdContent):
        #invoke intelliSense
        strRep = str(cmdContent)
        segments = strRep.split(' ')
        cmd = str(segments[0])
        instanceId = int(segments[1])
        requestNumber = int(segments[2])
        value = tuple(segments[3])
        return CommandObject(cmd,requestNumber,instanceId,value)

    @staticmethod
    def ConvertToString(cmdContent):
        #invoke intelliSense
        return "%s %d %d %s" % (cmdContent.Type,
                                cmdContent.InstanceId,
                                cmdContent.RequestNumber,
                                str(cmdontent.Value))


