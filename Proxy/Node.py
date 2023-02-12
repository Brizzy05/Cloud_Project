from enum import Enum

class Node:
    def __init__(self, name, ID, status, container, jobs=[]):
        self.name = name
        self.ID = ID
        self.status = status
        self.jobs = jobs
        self.container = container


    def __str__(self):
        return "Name: " + str(self.name) + ' - ID: ' + str(self.ID) + ' - Status: ' + self.status.value

class NodeStatus(Enum):
    IDLE = 'IDLE'
    RUNNING = 'RUNNING'