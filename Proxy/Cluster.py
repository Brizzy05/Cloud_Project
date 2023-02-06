import Pod

class Cluster:
    def __init__(self, pods=[]):
        self.pods = pods

    def __str__(self):
        return str(len(self.pods)) + ' pods' 