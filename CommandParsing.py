class CommandType:
    Prepare, Promise, Respond, Accept = ("PREPARE","PROMISE","RESPOND","ACCEPT")
#equivalent-ish to
#class CommandParsing
#{
#   CommandType Type
#   int InstanceId
#   int RequestNumber
#   [Optional]string Value
#}
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
        value = str(segments[3])
        return CommandObject(cmd,requestNumber,instanceId,value)
    @staticmethod
    def ConvertToString(cmdContent):
        #invoke intelliSense
        return "%s %d %d %s" % (cmdContent.Type,
                                cmdContent.InstanceId,
                                cmdContent.RequestNumber,
                                cmdContent.Value)