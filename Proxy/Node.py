from enum import Enum

class Node:
    def __init__(self, name, ID, status, jobs=[]):
        self.name = name
        self.ID = ID
        self.status = status
        self.jobs = jobs

    def __str__(self):
        return str(self.name) + ' ' + str(self.ID) + ' - ' + self.status.value + ' - ' + str(len(self.jobs)) + ' jobs'

class NodeStatus(Enum):
    IDLE = 'IDLE'
    RUNNING = 'RUNNING'