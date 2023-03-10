from flask import Flask, jsonify, request
from Node import Node, NodeStatus
from Job import Job, JobStatus
from Pod import Pod
from Cluster import Cluster
import json
import docker
from threading import Thread
import time

#Create instance of Flask
app = Flask(__name__)

#initialize docker client
dockerClient = docker.from_env()

#Initialize boolean
init = False
COUNT = 0

#Pods, Nodes and Jobs array
CLUSTERS = []
PODS = []
NODES = []
JOBS = []
JOB_QUEUE = []

#Pods, Nodes and Jobs IDs
podID = -1
nodeID = -1
jobID = -1

#-------------- FUNCTIONS -----------------#

#1. URL ~/cloudproxy to trigger init() function
@app.route('/cloudproxy/init')
def cloud_init():
    if request.method == 'GET':
        
        global init
        result = 'Failure'
        
        if init == False:
            init = True

            #Start by declaring the initialization
            print('Request to initialize cloud.')
            
            #Add default nodes
            default_nodes = []
            existing_containers = dockerClient.containers.list()

            #Link containers to Nodes
            for i in range(0,50):
                #If there are already running containers on the proxy, link them
                if (i < len(existing_containers)):
                    new_node = Node('default_node_'+str(i), getNextNodeID(), NodeStatus.IDLE, existing_containers[i], [])
                #Else create them and link them
                else:
                    container = createContainer()
                    new_node = Node('default_node_'+str(i), getNextNodeID(), NodeStatus.IDLE, container, [])
                default_nodes.append(new_node)
                NODES.append(new_node)


            #Add default pod
            new_pod = Pod('default', getNextPodID(), default_nodes)
            PODS.append(new_pod)

            #Add cluster
            new_cluster = Cluster([new_pod])
            CLUSTERS.append(new_cluster)
            
            print('Successfully added default resource cluster, default pod and default nodes!')

            result = 'Success' 

        else:
            print('Error: Cloud already initialized!')
        
        return jsonify({'result': result})


#2. URL ~/cloudproxy/pods/<name> to trigger cloud_pod_register() function
@app.route('/cloudproxy/pods/<name>')
def cloud_pod_register(name):
    if request.method == 'GET' and init == True:

        #Start by declaring the pod registration. Assume the pod is unknown at 1st
        result = 'unknown'
        pod_ID = 0
        print('Request to register new pod: ' + str(name))

        #Check if pod already exists in pod array
        for pod in PODS:
            if name == pod.name:
                result = 'Already_exists'
                pod_ID = pod.ID
                print('Pod already exists: ' + pod.name)

                
        #Else, edit pod's fields showing that it is added
        if result == 'unknown':
            #Create new pod
            pod_ID = getNextPodID()
            new_pod = Pod(name, pod_ID, [])
            PODS.append(new_pod)
            CLUSTERS[0].add_pod(new_pod) ######

            result = 'pod_added'
            print('Successfully added a new pod: ' + str(name) + 'with ID: ' + str(pod_ID))
        
        return jsonify({'result': result, 'pod_ID': pod_ID, 'pod_name': name})

    else:
        result = 'Failure'
        return jsonify({'result': result})


#3. URL ~/cloudproxy/pods/remove/<name> to trigger pod_rm() function
@app.route('/cloudproxy/pods/remove/<name>')
def cloud_pod_rm(name):
    if request.method == 'GET' and init == True:

        #Start by declaring the removal.
        print('Request to remove pod: ' + str(name))

        #If pod is default pod
        if name == 'default':
            result = 'pod_is_default'
            return jsonify({'result': result, 'pod_ID': 0, 'pod_name': name})
    
        for pod in PODS:
            #If pod exists
            if (name == pod.name):
                #If pod has nodes
                if (pod.get_nbr_nodes() > 0):
                    result = 'pod_has_registered_nodes'
                    return jsonify({'result': result})

                #If pod exists and has no nodes
                else:
                    #Remove from cluster
                    CLUSTERS[0].rm_pod(name)
                    #Remove from pods array
                    PODS.remove(pod)
                    print('Successfully removed: ' + name)

                    result = 'Success'
                    return jsonify({'result': result, 'removed_pod_ID': pod.ID, 'removed_pod_name': name})


        result = 'pod_does_not_exist'
        return jsonify({'result': result})

    else:
        result = 'Failure'
        return jsonify({'result': result})


#NODE MANAGEMENT
#4. URL ~/cloudproxy/nodes/<name> to trigger register() function
@app.route('/cloudproxy/nodes/<name>')
def cloud_register(name):
    if request.method == 'GET' and init == True:

        #Start by declaring the registration. Assume the node is unknown at 1st
        print('Request to register new node: ' + str(name))
        result = 'unknown'
        node_status = 'unknown'
        
        #Check if name already taken
        for node in NODES:
            if name == node.name:
                result = 'node_already_exists'
                return jsonify({'result': result})
            
        #If does not exist, create, add to default pod and nodes array
        container = createContainer()
        new_node = Node(name, getNextNodeID(), NodeStatus.IDLE, container, [])
        PODS[0].add_node(new_node)
        NODES.append(new_node)

        #Check if available job, if so, assign it to newly created Node
        popJobQueueAndAssociate(new_node)
                
        result = 'Success'
        return jsonify({'result': result, 'node_status': new_node.status.value, 'node_name': new_node.name})
            
    else:
        result = 'Failure'
        return jsonify({'result': result})


@app.route('/cloudproxy/nodes/<name>/<pod_ID>')
def cloud_register_with_ID(name, pod_ID):
    if request.method == 'GET' and init == True:

        #Start by declaring the registration. Assume the node is unknown at 1st
        print('Request to register new node: ' + str(name) + ' on pod: ' + str(pod_ID))
        
        #Check if name already taken
        for node in NODES:
            if name == node.name:
                result = 'node_already_exists'
                return jsonify({'result': result})
        
        #Check if pod ID valid
        for pod in PODS:
            if pod_ID == str(pod.ID):
                #Success
                container = createContainer()
                new_node = Node(name, getNextNodeID(), NodeStatus.IDLE, container, [])
                pod.add_node(new_node)
                NODES.append(new_node)

                #Check if available job, if so, assign it to newly created Node
                popJobQueueAndAssociate(new_node)

                result = 'Success'
                return jsonify({'result': result, 'node_status': new_node.status.value, 'node_name': new_node.name})

        #Else, pod does not exist
        result = 'pod_ID_invalid'
        return jsonify({'result': result})

    else:
        result = 'Failure'
        return jsonify({'result': result})


#5. URL ~/cloudproxy/nodes/remove/<name> to trigger rm() function
@app.route('/cloudproxy/nodes/remove/<name>')
def cloud_rm(name):
    if request.method == 'GET' and init == True:
        
        #Start by declaring the registration. Assume the node is unknown at 1st
        print('Request to remove existing node: ' + str(name))

        #Check if node name valid
        for node in NODES:
            if name == node.name and node.status != NodeStatus.RUNNING:
                #If hit && staus != RUNNING, find corresp. pod and remove from it
                NODES.remove(node)
                for pod in PODS:
                    for node_of_pod in pod.nodes:
                        if name == node_of_pod.name:
                            rm_pod = pod
                            pod.rm_node(node.name)

                result = 'Success'
                return jsonify({'result': result, 'removed_node_name': node.name, 'removed_from_pod_ID': rm_pod.ID})

            elif name == node.name and node.status == NodeStatus.RUNNING:
                result = 'node_status_RUNNING'
                return jsonify({'result': result})

        
        #Else, node does not exist
        result = 'node_name_invalid'
        return jsonify({'result': result})

    else:
        result = 'Failure'
        return jsonify({'result': result})

#JOB MANAGEMENT
#6. URL ~/cloudproxy/jobs/launch/<name> to trigger launch() function
@app.route('/cloudproxy/jobs', methods=['POST'])
def cloud_launch():
    if request.method == 'POST' and init == True:
        print('Request to post a file: Resource Manager -> Proxy Server')
        job_file = request.files['file']

        print('Creating new job')
        createdJob = createJob(job_file)
        print('Find available node for new job')
        findAvailableNode(createdJob)

        result = 'Success'
        return jsonify({'result': result})
    
    else:
        result = 'Failure'
        return jsonify({'result': result})


#7. URL ~/cloud/jobs/abort to trigger abort() function
@app.route('/cloudproxy/jobs/abort/<job_ID>')
def cloud_abort(job_ID):
    if request.method == 'GET' and init == True:
        print('Request to abort a job')
        job_to_abort = getJob(job_ID) 

        #If no job with such ID
        if job_to_abort == None:
            result = 'invalid_ID'
            return jsonify({'result': result})
        
        #If job already completed
        elif job_to_abort.status.value == 'COMPLETED':
            result = 'job_completed'
            return jsonify({'result': result})

        #If job in waiting queue
        elif job_to_abort.status.value == 'REGISTERED':
            JOB_QUEUE.remove(job_to_abort)
            result = 'Success'
            return jsonify({'result': result, 'job_ID': job_ID})
        
        #If job currently running
        else:
            node_ID = job_to_abort.nodeID
            node = getNode(node_ID)
            container = node.container
            container.kill(signal='SIGINT')

            node.status = NodeStatus.IDLE
            job_to_abort.status = JobStatus.ABORTED

            result = 'Success'
            return jsonify({'result': result, 'job_ID': job_ID, 'node_associated': node_ID, 'node_status': node.status.value, 'queue': str(JOB_QUEUE)})

    else:
        result = 'Failure'
        return jsonify({'result': result})


#-------------- MONITORING -----------------#

#1. URL ~/cloudproxy/monitor/pod/ls to trigger pod ls command
@app.route('/cloudproxy/monitor/pod/ls')
def cloud_pod_ls():

    result = "Failure"
    pod_dct = {'result' : result}

    if request.method == 'GET' and init:
        main_cluster = CLUSTERS[0]
        result = 'Success'
        for pod in main_cluster.pods:
            pod_dct[pod.name] = f"pod_name: {pod.name}, pod_ID: {pod.ID}, pod_size: {len(pod.nodes)}"

    pod_dct['result'] = result
    return jsonify(pod_dct)

#2. URL ~/cloud/monitor/node/ls/<pod_id> to trigger node ls command
@app.route('/cloudproxy/monitor/node/ls/<pod_id>')
def cloud_node_ls_podID(pod_id):
    result = "Failure"
    node_dct = {}

    node_dct['result'] = result

    if request.method == 'GET' and init:
        main_cluster = CLUSTERS[0]
        for pod in main_cluster.pods:
            if pod_id == str(pod.ID):
                result = 'Success'
                for node in pod.nodes:
                    node_dct[node.name] = f"node_name: {node.name}, node_ID: {node.ID}, node_status: {node.status.value}"

            else:
                result = f"Failure POD_ID: {pod_id} does not exit"


    node_dct['result'] = result
    return jsonify(node_dct)


@app.route('/cloudproxy/monitor/node/ls')
def cloud_node_ls():
    result = "Failure"
    node_dct = {}

    node_dct['result'] = result
    if request.method == 'GET' and init:
        main_cluster = CLUSTERS[0]
        result = 'Success'
        for pod in main_cluster.pods:
            for node in pod.nodes:
                node_dct[node.name] = f"node_ID: {node.ID}, node_status: {node.status.value}"

    node_dct['result'] = result
    return jsonify(node_dct)


#3. URL ~/cloud/monitor/jobs/ls/<node_id> to trigger job ls command
@app.route('/cloudproxy/monitor/jobs/ls') 
def cloud_jobs_ls(): 
    if request.method == 'GET' and init == True:
        job_dct = {}

        for job in JOBS:
            print(job)
            job_dct['Job ' + str(job.ID)] = f"job_ID: {job.ID}, job_status = {job.status.value}, node_associated = {job.nodeID}"

        result = 'Success'
        job_dct['result'] = result
        return jsonify(job_dct)

    else:
        result = 'Failure'
        return jsonify({'result': result})


@app.route('/cloudproxy/monitor/jobs/ls/<node_id>')
def cloud_jobs_ls_nodeID(node_id):
    if request.method == 'GET' and init == True:
        job_dct = {}
        node = getNode(node_id)

        if node == None:
            result = 'invalid_node_ID'
            return jsonify({'result': result})

        for job in node.jobs:
            job_dct['Job ' + str(job.ID)] = f"job_ID: {job.ID}, job_status = {job.status.value}, node_associated = {job.nodeID}"
        
        result = 'Success'
        job_dct['result'] = result
        print(node.container.logs())
        return jsonify(job_dct)

    else:
        result = 'Failure'
        return jsonify({'result': result})


#4. URL ~/cloud/monitor/jobs/log/<job_id> to trigger job log command
@app.route('/cloudproxy/monitor/jobs/log/<job_id>')
def cloud_job_log(job_id):
    if request.method == 'GET' and init == True:
        job = getJob(job_id)

        if job == None:
            result = 'invalid_job_ID'
            return jsonify({'result': result})

        else:
            if job.status.value == 'RUNNING':
                result = 'job_not_node_running'
                return jsonify({'result': result})

            else:
                result = 'Success'
                return jsonify({'result': result, 'job_id': job_id, 'log': str(job.log)})

    else:
        result = 'Failure'
        return jsonify({'result': result})


#5. URL ~/cloud/monitor/nodes/log/<node_id> to trigger node log command
@app.route('/cloudproxy/monitor/nodes/log/<node_id>')
def cloud_node_log(node_id):
    if request.method == 'GET' and init == True:
        node = getNode(node_id)
        node_dct = {}

        if node == None:
            result = 'invalid_node_ID'
            return jsonify({'result': result})

        for job in node.jobs:
            node_dct['Job ' + str(job.ID)] = f"log: {str(job.log)}"

        result = 'Success'
        node_dct['result'] = result
        print(node.container.logs())
        return jsonify(node_dct)

    else:
        result = 'Failure'
        return jsonify({'result': result})


#-------------- HELPERS -----------------#

#Creates container object
#Imager : Ubuntu
def createContainer():
    global dockerClient
    global COUNT
    COUNT=COUNT+1
    print(str(COUNT) + '. Creating new container')
    return dockerClient.containers.run('ubuntu', command='/bin/bash', detach=True, tty = True)

#Exits given contianer : RUNNING --> EXITED
def exitContainer(containerRef):
    containerRef.stop()
    
#Removes given container 
def removeContainer(containerRef):
    containerRef.remove()

#Exit all RUNNING conatiners : RUNNING --> EXITED
def exitAllContainers():
    for ctn in dockerClient.containers.list():
        ctn.stop()

#Remove all containers
def removeAllExitedContainers():
    dockerClient.containers.prune()

#Returns status of given container
def getContainerStatus(containerRef):
    containerRef.reload()
    return containerRef.status

#Lists all RUNNING containers
def listContainers():
    for ctn in dockerClient.containers.list():
        print('ContainerID: ' + str(ctn.id) + ' - Container Status: ' + str(getContainerStatus(ctn)) + ' - Container logs: ' + str(ctn.logs()))
    print()

#Pops Job from the queue and associates it to a free node. Updates statuses of Job and Node
def popJobQueueAndAssociate(nodeRef):
    if(len(JOB_QUEUE) > 0):
        job = JOB_QUEUE.pop(0)
        nodeRef.jobs.append(job)
        job.nodeID = nodeRef.ID
        job.status = JobStatus.RUNNING
        nodeRef.status = NodeStatus.RUNNING

#Creates Job object
def createJob(file):
    new_job = Job(getNextJobID(), JobStatus.REGISTERED, file)
    JOBS.append(new_job)
    return new_job

#Return either a Node if it is IDLE or None if no nodes are IDLE
def availableNode():
    for node in NODES:
        if node.status == NodeStatus.IDLE:
            return node
    return None

#Associates a Job with a Node if there is an available node. Else, job is queued.
def findAvailableNode(jobRef):
    for node in NODES:
        if node.status == NodeStatus.IDLE:
            associateJobtoNode(jobRef, node)
            print("Sucessfully associated Job to Node!")
            return
    queueJob(jobRef)

#Associates Job to Node by changing their respective statuses
def associateJobtoNode(jobRef, nodeRef):
    nodeRef.jobs.append(jobRef)
    jobRef.nodeID = nodeRef.ID
    jobRef.status = JobStatus.RUNNING
    nodeRef.status = NodeStatus.RUNNING
    print(jobRef)
    #run job on associated node
    runJobOnContainer(jobRef, nodeRef)

#Prepares variables to run the Job in separate Thread. 
def runJobOnContainer(jobRef, nodeRef):
    fileContents = jobRef.file.read()
    #We use multi-threading to run the job seperately, such that the execution time
    #of the job does not impede on the client
    function = nodeRef.container.exec_run
    argument = ['/bin/bash', '-c', fileContents.decode()]
    print()
    print('---LAUNCHING JOB---')
    print()
    t = Thread(target=runJobInThread, args=(function, argument, jobRef, nodeRef))
    t.start()

#Performs Job in thread
def runJobInThread(function, arguments, jobRef, nodeRef):
    exit_code, output = function(cmd=arguments)
    
    if (exit_code == 0):
        print('Execution Success')
        print()
        jobRef.log = output
        jobRef.status = JobStatus.COMPLETED
        nodeRef.status = NodeStatus.IDLE
    else:
        print('Execution Fail')
        print()
        jobRef.log = output
        jobRef.status = JobStatus.REGISTERED
        nodeRef.status = NodeStatus.IDLE
    
#Adds Job to queue    
def queueJob(jobRef):
    jobRef.status = JobStatus.REGISTERED
    JOB_QUEUE.append(jobRef)

#Given an ID, retrieve Job
def getJob(job_ID):
    for j in JOBS:
        if str(job_ID) == str(j.ID):
            return j
    else:
        return None

#Given an ID, retrieve Node
def getNode(node_ID):
    for n in NODES:
        if str(node_ID) == str(n.ID):
            return n
    else:
        return None

def monitorQueue():
    while 1:
        
        ### THIS PART NOT NECESSARY -- SIMPLY FOR DEBUGGING ###
        #time.sleep(3)
        #print('JOBS:')
        #for j in JOBS:
        #    print(str(JOBS.index(j)) + '. ' + str(j))
        #print()
        ###

        node = availableNode()
        if node != None:
            popJobQueueAndAssociate(node)

def getNextNodeID():
    global nodeID
    nodeID = nodeID + 1
    return nodeID

def getNextPodID():
    global podID
    podID = podID + 1
    return podID

def getNextJobID():
    global jobID
    jobID = jobID + 1
    return jobID

def checkArrays():
    print('\n--------Clusters-------')
    for c in CLUSTERS:
        print(str(c))
    print('\n---------Pods----------')
    for p in PODS:
        print(str(p))
    print('\n---------Nodes---------')
    for n in NODES:
        print(str(n))
    print('\n---------Jobs---------')
    print(JOBS)
    print()
    print('\n----Containter Inf----')
    listContainers()

if __name__ == '__main__':
    #Create thread that will monitor the Job queue
    t = Thread(target=monitorQueue, args=())
    t.start()
    app.run(debug=True, host='0.0.0.0', port=6000)
