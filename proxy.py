from flask import Flask, jsonify, request

#Create instance of Flask
app = Flask(__name__)

#Nodes and Jobs array
nodes = []
jobs = []

#URL ~/cloudproxy/nodes/all/ to trigger get_al_nodes() function
@app.route('/cloudproxy/nodes/all')
def cloud_get_all_nodes():
    #TODO: function to return all nodes in proxy
    return jsonify({})

#URL ~/cloudproxy/nodes/ to trigger register() function
@app.route('/cloudproxy/nodes/<name>')
def cloud_register(name):
    if request.method == 'GET':

        #Start by declaring the registration. Assume the node is unknown at 1st
        print('Request to register new node: ' + str(name))
        result = 'unknown'
        node_status = 'unknown'

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

        return jsonify({'result': result, 'node_status': node_status, 'node_name': name})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=6000)
