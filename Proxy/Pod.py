import Node

class Pod:
    def __init__(self, name, ID, nodes=[]):
        self.name = name
        self.ID = ID
        self.nodes = nodes

    def __str__(self):
        return str(self.name) + ' ' + str(self.ID) + ' - ' + str(len(self.nodes)) + ' nodes' 

 