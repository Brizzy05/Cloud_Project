class Job: 
    def __init__(self, job_id, job_file, job_name, node_id):
        self_job_id = job_id
        self.job_file = job_file
        self.job_name = job_name
        self.node_id = node_id