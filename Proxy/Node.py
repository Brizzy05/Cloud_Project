class Node:
    def __init__(self, name, ID, status, jobs=[]):
        self.name = name
        self.ID = ID
        self.status = status
        self.jobs = jobs