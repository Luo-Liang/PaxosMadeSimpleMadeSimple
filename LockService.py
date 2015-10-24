#This is a snap-in for the user logic.
#PAXOS is by no means coupled with this logic.
#Drop in replacement is possible as long as the CommandParsing 
class LockService:
    def __init__(self):
        self.EngagedLocks = []
    
    def ProcessRequest(self,value):
        #client dedup
        seq = value[0]
        action = value[1]
        object = value[2]
        if action == "LOCK":
            if object in self.EngagedLocks:
                return False
            else:
                self.EngagedLocks.append(object)
                return True
        else:
            #This silly LockService does not track lock ownership, nor does it do deadlock detection, nor does it care about freeing before acquiring
            if object in self.EngagedLocks:
                self.EngagedLocks.remove(object)
            return True