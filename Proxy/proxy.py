from flask import Flask, jsonify, request
from Node import Node, NodeStatus
from Job import Job, JobStatus
from Pod import Pod
from Cluster import Cluster
import json
import docker
import os
from threading import Thread

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
            for i in range(0,10):
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
            checkArrays()

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
        
        checkArrays()
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

                    checkArrays()

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
        new_node = Node(name, getNextNodeID(), NodeStatus.IDLE, container,[])
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


#6. URL ~/cloudproxy/nodes/launch/<name> to trigger launch() function
@app.route('/cloudproxy/jobs', methods=['POST'])
def cloud_launch():
    if request.method == 'POST' and init == True:
        print('Request to post a file: Resource Manager -> Proxy Server')
        job_file = request.files['file']
        print('------------File Contents-------------')
        print(job_file.read())
        job_file.seek(0)
        print('--------------------------------------')

        print('Creating new job')
        createdJob = createJob(job_file)
        print('Find available node for new job')
        findAvailableNode(createdJob)

        result = 'Success'
        return jsonify({'result': result})
    
    else:
        result = 'Failure'
        return jsonify({'result': result})

#-------------- Monitoring -----------------
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

#2 URL ~/cloud/monitor/node/ls/<pod_id> to trigger ls command
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
                node_dct[node.name] = f"node_name: {node.name}, node_ID: {node.ID}, node_status: {node.status.value}"

    node_dct['result'] = result
    return jsonify(node_dct)

#--------------------------HELPER FUNCTIONS-------------------------
def createContainer():
    global dockerClient
    global COUNT
    COUNT=COUNT+1
    print(str(COUNT) + '. Creating new container')
    return dockerClient.containers.run('ubuntu', command='/bin/bash', detach=True, tty = True)

def exitContainer(containerRef):
    containerRef.stop()
    
def removeContainer(containerRef):
    containerRef.remove()

##Might be changes to bring here --> I.E. what happens if stop paused or exited container?
def exitAllContainers():
    for ctn in dockerClient.containers.list():
        ctn.stop()

def removeAllExitedContainers():
    dockerClient.containers.prune()

def getContainerStatus(containerRef):
    containerRef.reload()
    return containerRef.status

def listContainers():
    for ctn in dockerClient.containers.list():
        print('ContainerID: ' + str(ctn.id) + ' - Container Status: ' + str(getContainerStatus(ctn)) + ' - Container logs: ' + str(ctn.logs()))
    print()

def popJobQueueAndAssociate(nodeRef):
    if(len(JOB_QUEUE) > 0):
        job = JOB_QUEUE.pop(0)
        nodeRef.jobs.append(job)
        job.status = JobStatus.RUNNING
        nodeRef.status = NodeStatus.RUNNING
        ####ACTUALLY RUN JOB####I.E. run script on node's container

####-----JOB related helpers-----####
threads = []

def createJob(file):
    new_job = Job(getNextJobID(), JobStatus.REGISTERED, file)
    JOBS.append(new_job)
    return new_job

def findAvailableNode(jobRef):
    for node in NODES:
        if node.status == NodeStatus.IDLE:
            associateJobtoNode(jobRef, node)
            print("Sucessfully associated Job to Node!")
            return
    queueJob(jobRef)
    
def associateJobtoNode(jobRef, nodeRef):
    nodeRef.jobs.append(jobRef)
    jobRef.nodeID = nodeRef.ID
    jobRef.status = JobStatus.RUNNING
    nodeRef.status = NodeStatus.RUNNING
    print("Container ID :" + nodeRef.container.id)
    #run job on associated node
    runJobOnContainer(jobRef, nodeRef)

def runJobOnContainer(jobRef, nodeRef):
    fileContents = jobRef.file.read()
    jobRef.file.seek(0)
    '''
    #Fork to parallelize running of the script
    pid = os.fork() 

    #Parent process
    if (pid > 0):
        pass

    #Child process
    else:
        exit_code,output = nodeRef.container.exec_run(cmd=['/bin/bash', '-c', fileContents.decode()])

        if (exit_code == 0):
            print('Execution Success')
            print('Exit_code ' + str(exit_code))
            print(type(exit_code))
            print('Output ' + str(output))
            jobRef.status = JobStatus.COMPLETED
            nodeRef.status = NodeStatus.IDLE
            nodeRef.container.reload()

            print('jobRef : ' + str(jobRef.status))
            print('nodeRef : ' + str(nodeRef.status))

        else:
            print('Execution Fail')
            print('Exit_code ' + str(exit_code))
            print(type(exit_code))
            print('Output ' + str(output))
            jobRef.status = JobStatus.REGISTERED
            nodeRef.status = NodeStatus.IDLE
        
        exit()
    '''
    
    #We use multi-threading to run the job seperately, such that the execution time of the job does not
    #impede on the client
    function = nodeRef.container.exec_run
    argument = ['/bin/bash', '-c', fileContents.decode()]

    print('---LAUNCHING JOB---')
    t = Thread(target=runJobInThread, args=(function, argument, jobRef, nodeRef))
    threads.append(t)
    t.start()


def runJobInThread(function, arguments, jobRef, nodeRef):
    exit_code, output = function(cmd=arguments)
    
    if (exit_code == 0):
        print('Execution Success')
        print('Exit_code ' + str(exit_code))
        print('Output ' + str(output))
        jobRef.status = JobStatus.COMPLETED
        nodeRef.status = NodeStatus.IDLE
    else:
        print('Execution Fail')
        print('Exit_code ' + str(exit_code))
        print('Output ' + str(output))
        jobRef.status = JobStatus.REGISTERED
        nodeRef.status = NodeStatus.IDLE
    
    #t1 = threads[0]
    #t1.join()


def queueJob(jobRef):
    jobRef.status = JobStatus.REGISTERED
    JOB_QUEUE.append(jobRef)
            
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
    app.run(debug=True, host='0.0.0.0', port=6000)