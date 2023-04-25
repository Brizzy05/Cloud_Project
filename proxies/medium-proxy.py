from flask import Flask, jsonify, request
from Node import Node, NodeStatus
import sys
import docker
from haproxyadmin import haproxy
from io import BytesIO
import pandas as pd
import pycurl
import json

cURL = pycurl.Curl()

client = docker.from_env()
app = Flask(__name__)

#Init
init = False

#Paused
paused = True

# Resource manager ip
rm_url = '192.168.64.5:3000'

#List of nodes, 15 max
node_list = []
limit = 15

#1. INIT
@app.route('/init')
def init():
    global init
    #Initialize if not
    if init == True:
        return jsonify({'result' : 'Failure',
                        'reason' : 'Cloud already initialized'})
    else:
        init = True
        return jsonify({'result' : 'Success',
                        'reason' : 'Cloud initialized !'})

#4. NODE REGISTER
@app.route('/register/<node_name>/<port_number>')
def register(node_name, port_number):
    if init == True:
        #If limit reached
        if len(node_list) >= limit:
            return jsonify({'result' : 'Failure',
                            'reason' : 'Node Limit Reached'})

        for node in node_list:
            #Check if port already taken
            if node.port == port_number:
                return jsonify({'result' : 'Failure',
                                'reason' : 'Port Already Taken'})
            
            #Check if name already taken
            elif node.name == node_name:
                return jsonify({'result' : 'Failure',
                                'reason' : 'Name Already Taken'})
        #Add to node list
        node_list.append(Node(port_number, node_name, 0, NodeStatus.NEW))

        return jsonify({'result' : 'Success',
                        'port' : port_number,
                        'name' : node_name,
                        'status' : NodeStatus.NEW.value})
    else:
         return jsonify({'result' : 'Failure',
                         'reason' : 'Cloud not initialized'})


#5. NODE RM
@app.route('/remove/<node_name>')
def remove(node_name):
    if init == True:
        index_to_remove = -1
        #Find index of node to remove
        for i in range(len(node_list)):
            node = node_list[i]
            if node.name == node_name:
                index_to_remove = i
                break

        found = False
        port = -1
        name = ''
        status = NodeStatus.NEW
        
        #If node is found in list, remove node and container
        if index_to_remove != -1:
            node = node_list[index_to_remove]
            port = node.port
            name = node.name
            status = node.status.value
            del node_list[index_to_remove]
            found = True

        for container in client.containers.list():
            if container.name == node_name:
                container.remove(v=True, force=True)
                break

        if found:
            return jsonify({'result' : 'Success',
                            'port' : port,
                            'name' : name,
                            'status' : status})

        return jsonify({'result' : 'Failure',
                        'reason' : 'Container not found'})
    else:
         return jsonify({'result' : 'Failure',
                         'reason' : 'Cloud not initialized'})


#6. NODE LAUNCH
@app.route('/launch')
def launch():
    if init == True:
        #Check node list and find 1st node with NEW status
        for node in node_list:
            if (node.status.value == 'NEW'):
                #Launch node
                l_node = launch_node(node.name, node.port)
                if l_node is not None:
                    return jsonify({'result' : 'Success',
                                    'paused' : paused,
                                    'port' : node.port,
                                    'name' : node.name,
                                    'status' : NodeStatus.ONLINE.value})
            else:
                continue

    else:
        return jsonify({'result' : 'Failure',
                        'reason' : 'Cloud not initialized'})

#HELPER FOR LAUNCH 
def launch_node(container_name, port_number):
    #Create image for container (/home/ubuntu/COMP598/Project/proxies)
    [img, logs] = client.images.build(path='/home/ubuntu/COMP598/Project/proxies/medium-app', rm=True, dockerfile='/home/ubuntu/COMP598/Project/proxies/medium-app/Dockerfile')
    for container in client.containers.list():
        if container.name == container_name:
            container.remove(v=True, force=True)
    
    #Create and run container
    container = client.containers.create(image = img,
                          detach = True,
                          name = container_name,
                          command = ['python3', 'app.py', container_name],
                          ports = {'5001/tcp' : port_number},
                          cpu_quota = 50000,
                          mem_limit = '300m')
    container.start()

    index = -1
    #Replace node with new node with ONLINE STATUS
    for i in range(len(node_list)):
        node = node_list[i]
        if container_name == node.name:
            index = i
            node_list[i] = Node(port_number, container_name, 0, NodeStatus.ONLINE, container) 
            break

    print('Successfully launched a node')
    return node_list[index]


#PAUSE & RESUME
#7
@app.route('/resume')
def resume_pod():
    if init == True:
        global paused
        if paused == True:
            paused = False

            node_dict = {}
            node_dict["name"] = ""
            node_dict["port"] = ""
            for node in node_list:
                if node.status == NodeStatus.ONLINE:
                    node_dict['name'] += str(node.name) + " "
                    node_dict['port'] += str(node.port) + " "

            node_dict['result'] = 'Success'
            return jsonify(node_dict)

        else:
            return jsonify({'result' : 'Failure',
                            'reason' : 'Cloud Already Running'})
                
    else:
        return jsonify({'result' : 'Failure',
                        'reason' : 'Cloud not initialized'})
    

#PAUSE & RESUME
#8
@app.route('/pause')
def pause_pod():
    if init == True:
        global paused
        if paused == False:
            paused = True

            node_dict = {}
            node_dict["name"] = ""
            node_dict["port"] = ""
            for node in node_list:
                if node.status == NodeStatus.ONLINE:
                    node_dict['name'] += str(node.name) + " "
                    node_dict['port'] += str(node.port) + " "

            node_dict['result'] = 'Success'
            return jsonify(node_dict)

        else:
            return jsonify({'result' : 'Failure',
                            'reason' : 'Cloud Already Paused'})

    else:
        return jsonify({'result' : 'Failure',
                        'reason' : 'Cloud not initialized'})


#--------------------------MONITORING----------------------
@app.route('/monitor/node')
def monitor():
    if init == True:
        node_dict = {}
        node_dict["Pod"] = "MEDIUM"
        for i in range (0,len(node_list)):
            node_dict[str(i+1)] = str(node_list[i])

        node_dict['result'] = 'Success'
        return  jsonify(node_dict)
        
    else:
        return jsonify({'result' : 'Failure',
                        'reason' : 'Cloud not initialized'})
        

#Dashboard helper to know if paused
@app.route('/dashboard/status')
def get_paused():
    global paused
    return jsonify({'result' : paused})


#--------------------------ELASTIC----------------------
@app.route('/elastic')
def elastic_cloud():
    print("Medium Elasticity Check Running")
    # cpu usage of heavy node
    cpu_usage = 0.65
    # number of nodes running a job currently
    dct = get_running_jobs()
    # current running jobs
    jobs_rn = "-1"
    #number of nodes online
    nodes_online = -1
    
    i = 0
    # getting current number of requests for heavy
    for v in dct["pxname"]:
        if v == "medium-servers" and dct["svname"][i] == "BACKEND":
            jobs_rn = dct["scur"][i]
            nodes_online += 1
        else:
            if v == "medium-servers":
                nodes_online += 1
            i += 1
    
    return jsonify({'current jobs': jobs_rn, 'nodes online': nodes_online})
    
    
        
#--------------------------HELPER----------------------
def get_running_jobs():
    #Connecting to the HAProxy listener server
    
    
    data = BytesIO()
    cURL.setopt(cURL.URL, rm_url + '/cloud/haproxy/stats')
    cURL.setopt(cURL.WRITEFUNCTION, data.write)
    cURL.perform()
    data_dct = json.loads(data.getvalue())
    
    print(data_dct)

    return data_dct



if __name__ == "__main__":
    app.run(debug = True, host='0.0.0.0', port=5001)