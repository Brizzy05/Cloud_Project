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

#URL ~/ to trigger hello() function
@app.route('/', methods=['GET', 'POST'])
def cloud():
    if request.method == 'GET':
        print('A client says hello')
        response = 'Cloud says hello!'
        return jsonify({'response': response})

#URL ~/cloud/nodes/ to trigger register() function
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
        print(dictionary)

        result = dictionary['result']
        node_status = dictionary['node_status']
        new_node_name = dictionary['node_name']
        new_node_pod = pod_name

        return jsonify({'result': result, 'node_status': node_status, 'new_node_name': str(name), 'new_node_pod': new_node_pod})

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
