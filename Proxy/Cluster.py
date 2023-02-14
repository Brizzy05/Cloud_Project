import Pod

class Cluster:
    def __init__(self, pods=[]):
        self.pods = pods

    def __str__(self):
        return str(len(self.pods)) + ' pods'

    def add_pod(self, pod_obj):
        self.pods.append(pod_obj)

    def rm_pod(self, pod_name):
        flag = False
        for p in self.pods:
            if (p.name == pod_name):
                flag = True
                pod_to_rm = p

        if (flag == True):
            self.pods.remove(pod_to_rm)