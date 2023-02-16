from enum import Enum

class Job: 
    def __init__(self, ID, status, file, nodeID=None, log=None):
        self.ID = ID
        self.status = status
        self.file = file
        self.nodeID = nodeID
        self.log = log

    
    def __str__(self):
        return "Job ID: " + str(self.ID) + " - Job Status: " + str(self.status.value) + " - Associated Node (ID): " + str(self.nodeID)

    
class JobStatus(Enum):
    ABORTED = 'ABORTED'
    REGISTERED = 'REGISTERED'
    RUNNING = 'RUNNING'
    COMPLETED = 'COMPLETED'

    