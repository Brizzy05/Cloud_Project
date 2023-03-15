from enum import Enum

class Node:
    def __init__(self, port, name, ID, status, container=None):
        self.port = port
        self.name = name
        self.ID = ID
        self.status = status
        self.container = container

    def __str__(self):
        return str(self.port) + ' ' + str(self.name)  + ' ' + str(self.ID) + ' - ' + self.status.value
    
class NodeStatus(Enum):
    NEW = 'NEW'
    ONLINE = 'ONLINE'
