from flask import Flask, jsonify, request
import pycurl
import json
from io import BytesIO

#Get the URL of the Proxy
cURL = pycurl.Curl()
proxy_url = 'http://192.168.64.6:6000'

#Create instance of Flask
app = Flask(__name__)

#Some infos on the app.route() call:
#app.route('<URL>', methods=['GET', 'POST'])
#     ↑                        ↑       ↑
#   we tell Flask which URL should trigger our function
#                              |       |
#                  Query to server, server returns data
#                                      |
#                               Send HTML form data to server


#INIT, DEBUG, SANITY CHECK
#URL ~/ to trigger hello() function
@app.route('/', methods=['GET', 'POST'])
def cloud():
    if request.method == 'GET':
        print('A client says hello')
        response = 'Cloud says hello!'
        return jsonify({'response': response})


#1. URL ~/ to trigger init() function
@app.route('/cloud/init')
def cloud_init():
    if request.method == 'GET':
        print('Initializing Cloud')

        #Logic to invoke RM-Proxy
        data = BytesIO()

        cURL.setopt(cURL.URL, proxy_url + '/cloudproxy/init')
        cURL.setopt(cURL.WRITEFUNCTION, data.write)
        cURL.perform()

        dictionary = json.loads(data.getvalue())
        print('This is the dictionary: '+ str(dictionary))
        
        if (dictionary['result'] == 'Failure'):
            result = 'Cloud already initialized!'
        
        else:
            result = 'Cloud initialized!'

        return jsonify({'result': result})


#POD MANAGEMENT
#2. URL ~/cloud/pods/ to trigger pod_register() function
@app.route('/cloud/pods/<name>')
def cloud_pod_register(name):
    if request.method == 'GET':
        print('Request to register new pod: ' + str(name))

        #Logic to invoke RM-Proxy
        data = BytesIO()

        cURL.setopt(cURL.URL, proxy_url + '/cloudproxy/pods/' + str(name))
        cURL.setopt(cURL.WRITEFUNCTION, data.write)
        cURL.perform()
        dictionary = json.loads(data.getvalue())
        print('This is the dictionary: '+ str(dictionary))

        if (dictionary['result'] == 'Failure'):
            result = 'Error: Cloud not initialized!'
            return jsonify({'result': result})
        
        elif (dictionary['result'] == 'Already_exists'):
            result = dictionary['result']
            pod_ID = dictionary['pod_ID']
            pod_name = dictionary['pod_name']
            
            return jsonify({'result': result, 'existing_pod_ID': pod_ID, 'existing_pod_name': pod_name})
        else:
            result = dictionary['result']
            new_pod_ID = dictionary['pod_ID']
            new_pod_name = dictionary['pod_name']

            return jsonify({'result': result, 'new_pod_ID': new_pod_ID, 'new_pod_name': new_pod_name})


#3. URL ~/cloud/pods/ to trigger pod_rm() function
@app.route('/cloud/pods/remove/<name>')
def cloud_pod_rm(name):
    if request.method == 'GET':
        print('Request to remove pod: ' + str(name))

        #Logic to invoke RM-Proxy
        data = BytesIO()

        cURL.setopt(cURL.URL, proxy_url + '/cloudproxy/pods/remove/' + str(name))
        cURL.setopt(cURL.WRITEFUNCTION, data.write)
        cURL.perform()
        dictionary = json.loads(data.getvalue())
        print('This is the dictionary: '+ str(dictionary))

        if (dictionary['result'] == 'Failure'):
            result = 'Error: Cloud not initialized!'
            return jsonify({'result': result})
        
        elif (dictionary['result'] == 'pod_is_default'):
            result = 'Error: Cannot remove default pod!'
            return jsonify({'result': result})

        elif (dictionary['result'] == 'pod_does_not_exist'):
            result = 'Error: Pod does not exist!'
            return jsonify({'result': result})

        elif (dictionary['result'] == 'pod_has_registered_nodes'):
            result = 'Error: Pod has registered nodes!'
            pod_ID = dictionary['pod_ID']
            pod_nbr_nodes = dictionary['number_of_nodes']
            return jsonify({'result': result, 'pod_ID': pod_ID, 'pod_name': name, 'number_of_nodes': pod_nbr_nodes})

        else:
            result = dictionary['result']
            rm_pod_ID = dictionary['removed_pod_ID']
            return jsonify({'result': result, 'removed_pod_ID': rm_pod_ID, 'removed_pod_name': name})


#NODE MANAGEMENT
#4. URL ~/cloud/nodes/ to trigger register() function
@app.route('/cloud/nodes/<name>', defaults={'pod_name': 'default'})
@app.route('/cloud/nodes/<name>/<pod_name>')
def cloud_register(name, pod_name):
    if request.method == 'GET':
        print('Request to register new node: ' + str(name) + ' on pod:' + str(pod_name))
        #TODO: Management for pod_name
        
        #Logic to invoke RM-Proxy
        data = BytesIO()

        cURL.setopt(cURL.URL, proxy_url + '/cloudproxy/nodes/' + str(name))
        cURL.setopt(cURL.WRITEFUNCTION, data.write)
        cURL.perform()
        dictionary = json.loads(data.getvalue())
        print('This is the dictionary : ' + str(dictionary))
    
        if (dictionary['result'] == 'Failure'):
             result = 'Error - Cloud not initialized!'
             return jsonify({'result': result})

        else:
            result = dictionary['result']
            node_status = dictionary['node_status']
            new_node_name = dictionary['node_name']
            new_node_pod = pod_name

            return jsonify({'result': result, 'node_status': node_status, 'new_node_name': new_node_name, 'new_node_pod': new_node_pod})


#JOB MANAGEMENT
#URL ~/cloud/jobs/launch to trigger launch() function
@app.route('/cloud/jobs/launch', methods=['POST'])
def cloud_launch():
    if request.method == 'POST':
        print('Request to post a file')
        job_file = request.files['file']
        print(job_file.read())
        #TODO: Send job to proxy
        result = 'success'
        return jsonify({'result': result})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)