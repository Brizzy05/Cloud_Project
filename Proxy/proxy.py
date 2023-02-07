from flask import Flask, jsonify, request
from Node import Node, NodeStatus
from Pod import Pod
from Cluster import Cluster
import json

#Create instance of Flask
app = Flask(__name__)

#Initialize boolean
init = False

#Pods, Nodes and Jobs array
clusters = []
pods = []
nodes = []
jobs = []

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
            for i in range(0,50):
                new_node = Node('default_node_'+str(i), getNextNodeID(), NodeStatus.IDLE, [])
                default_nodes.append(new_node)
                nodes.append(new_node)


            #Add default pod
            new_pod = Pod('default', getNextPodID(), default_nodes)
            pods.append(new_pod)

            #Add cluster
            new_cluster = Cluster([new_pod])
            clusters.append(new_cluster)
            
            print('Successfully added default pod and default nodes!')

            result = 'Success' 
            checkArrays()

        else:
            print('Error: Cloud already initialized!')
        
        return jsonify({'result': result})


#2. URL ~/cloudproxy/pods/<name> to trigger pod_register() function
@app.route('/cloudproxy/pods/<name>')
def cloud_pod_register(name):
    if request.method == 'GET' and init == True:

        #Start by declaring the pod registration. Assume the pod is unknown at 1st
        result = 'unknown'
        pod_ID = 0
        print('Request to register new pod: ' + str(name))

        #Check if pod already exists in pod array
        for pod in pods:
            if name == pod.name:
                result = 'Already_exists'
                pod_ID = pod.ID
                print('Pod already exists: ' + pod.name)

        #Else, edit pod's fields showing that it is added
        if result == 'unknown':
            #Create new pod
            pod_ID = getNextPodID()
            new_pod = Pod(name, pod_ID, [])
            pods.append(new_pod)
            clusters[0].add_pod(new_pod)

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
    
        for pod in pods:
            #If pod exists
            if (name == pod.name):
                #If pod has nodes
                if (pod.get_nbr_nodes() > 0):
                    result = 'pod_has_registered_nodes'
                    return jsonify({'result': result, 'pod_ID': pod.ID, 'pod_name': name, 'number_of_nodes': pod.get_nbr_nodes()})

                #If pod exists and has no nodes
                else:
                    #Remove from cluster
                    clusters[0].rm_pod(name)
                    #Remove from pods array
                    pods.remove(pod)
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
#URL ~/cloudproxy/nodes/all/ to trigger get_all_nodes() function
@app.route('/cloudproxy/nodes/all')
def cloud_get_all_nodes():
    #TODO: function to return all nodes in proxy
    return jsonify({})


#4. URL ~/cloudproxy/nodes/<name> to trigger register() function
@app.route('/cloudproxy/nodes/<name>')
def cloud_register(name):
    if request.method == 'GET' and init == True:

        #Start by declaring the registration. Assume the node is unknown at 1st
        print('Request to register new node: ' + str(name))
        result = 'unknown'
        node_status = 'unknown'

        #Check if pod exists
        for pod in pods:
            pass 

        #Check if node already exists in node array
        for node in nodes:
            if name == node['name']:
                print('Node already exists: ' + node['name'] + ' with status: ' + node['status'])
                result = 'already_exists'
                node_status = node['status']

        #Else, edit node's fields showing that it is added
        if result == 'unknown' and node_status == 'unknown':
            result = 'node_added'
            nodes.append({'name': name, 'status': 'IDLE'})
            node_status = 'IDLE'
            print('Successfully added a new node: ' + str(name))

        checkArrays()
        return jsonify({'result': result, 'node_status': node_status, 'node_name': name})
    else:
        result = 'Failure'
        return jsonify({'result': result})


#-------------- Monitoring -----------------

#URL ~//cloudproxy/monitor/pod/ls to trigger ls command
@app.route('/cloudproxy/monitor/pod/ls')
def cloud_pod_ls():

    result = "Failure"
    pod_dct = {'result' : result}

    if request.method == 'GET' and init:
        main_cluster = clusters[0]
        result = 'Success'
        for pod in main_cluster.pods:
            pod_dct[pod.name] = f"pod_name: {pod.name}, pod_ID: {pod.ID}, pod_size: {len(pod.nodes)}"

    pod_dct['result'] = result
    return jsonify(pod_dct)


#HELPER FUNCTIONS
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
    print('Clusters')
    for c in clusters:
        print(str(c))
    print()
    print('Pods:')
    for p in pods:
        print(str(p))
    print()
    print('Nodes:')
    for n in nodes:
        print(str(n))
    print()
    print('Jobs:')
    print(jobs)
    print()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=6000)