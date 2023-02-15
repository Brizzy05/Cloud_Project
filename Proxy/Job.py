from enum import Enum

class Job: 
    def __init__(self, ID, status, file=None, nodeID=None):
        self.ID = ID
        self.status = status
        self.file = file
        self.nodeID = nodeID

    
    def __str__(self):
        return "Job ID: " + str(self.ID) + " - Job Status: " + str(self.status)

    
class JobStatus(Enum):
    REGISTERED = 'REGISTERED'
    RUNNING = 'RUNNING'
    COMPLETED = 'COMPLETED'