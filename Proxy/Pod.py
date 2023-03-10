import Node

class Pod:
    def __init__(self, name, ID, nodes=[]):
        self.name = name
        self.ID = ID
        self.nodes = nodes

    def __str__(self):
        return str(self.name) + ' ' + str(self.ID) + ' - ' + str(len(self.nodes)) + ' node'

    def get_nbr_nodes(self):
        return len(self.nodes)

    def add_node(self, node):
        self.nodes.append(node)

    def rm_node(self, node_name):
        flag = False
        for n in self.nodes:
            if (n.name == node_name):
                flag = True
                node_to_rm = n

        if (flag == True):
            self.nodes.remove(node_to_rm)