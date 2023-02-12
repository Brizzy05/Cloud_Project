from enum import Enum

class Job: 
    def __init__(self, ID, status, file, nodeID= None):
        self.ID = ID
        self.status = status
        self.file = file
        self.nodeID = nodeID

    
    def __str__(self):
        return "Job ID: " + str(self.ID) + " - Job Status: " + str(self.status) + " - Associated Node (ID): " + str(self.nodeID)

    
class JobStatus(Enum):
    REGISTERED = 'REGISTERED'
    RUNNING = 'RUNNING'
    COMPLETED = 'COMPLETED'

    