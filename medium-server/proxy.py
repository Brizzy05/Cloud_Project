from flask import Flask, jsonify, request
from Node import Node, NodeStatus
import sys
import docker

client = docker.from_env()
app = Flask(__name__)

#List of nodes, 15 max
node_list = []
limit = 15

#SANITY CHECK
@app.route('/check')
def check():
    for node in node_list:
        print(str(node))
    return ''


#4. NODE REGISTER
@app.route('/register/<node_name>/<port_number>')
def register(node_name, port_number):
    #If limit reached 

    for node in node_list:
        if node.port == port_number:
            return jsonify({'result' : 'Failure',
                            'reason' : 'Port Already Taken'})

        elif node.name == node_name:
            return jsonify({'result' : 'Failure',
                            'reason' : 'Name Already Taken'})

    node_list.append(Node(port_number, node_name, 0, NodeStatus.NEW))

    return jsonify({'result' : 'success',
                    'port' : port_number,
                    'name' : node_name,
                    'running' : 'false'})

#5. NODE RM
@app.route('/remove/<node_name>')
def remove(node_name):
    index_to_remove = -1
    for i in range(len(node_list)):
        node = node_list[i]
        if node.name == node_name:
            index_to_remove = i
            break

    found = False
    port = -1
    name = ''
    running = 'false'

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
        return jsonify({'result' : 'success',
                        'port' : port,
                        'name' : name,
                        'running' : running})

    return jsonify({'result' : 'failure',
                    'reason' : 'Container not found'})


@app.route('/launch')
def launch():
    for node in node_list:
        print(node.status.value)
        if (node.status.value == 'NEW'):
            l_node = launch_node(node.name, node.port)
            if l_node is not None:
                return jsonify({'result' : 'success',
                                'port' : node.port,
                                'name' : node.name,
                                'running' : 'true'})
        else:
            continue
    
    return jsonify({'result' : 'failure',
                    'reason' : 'Error'})


def launch_node(container_name, port_number):
    [img, logs] = client.images.build(path='/home/ubuntu', rm=True, dockerfile='/home/ubuntu/app/Dockerfile')
    for container in client.containers.list():
        if container.name == container_name:
            container.remove(v=True, force=True)
    
    container = client.containers.run(image = img,
                          detach = True,
                          name = container_name,
                          command = ['python3', 'app.py', container_name],
                          ports = {'5000/tcp' : port_number})

    index = -1
    for i in range(len(node_list)):
        node = node_list[i]
        if container_name == node.name:
            index = i
            node_list[i] = Node(port_number, container_name, 0, NodeStatus.ONLINE) 
            break

    print('Successfully launched a node')
    return node_list[index]


if __name__ == "__main__":
    app.run(debug = True, host='0.0.0.0', port=5000)
