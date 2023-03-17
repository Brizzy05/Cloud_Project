from flask import Flask, jsonify, request
import requests
import pycurl
import json
import sys
import views
import subprocess
from io import BytesIO

#Get the URL of the Proxy
cURL = pycurl.Curl()

#Keep IPs of servers
medium_proxy_ip = 'http://192.168.64.8:5000'
medium_proxy_ip_no_port = '192.168.64.8'

#Create instance of Flask
app = Flask(__name__)


#INIT, DEBUG, SANITY CHECK
#1. URL ~/ to trigger init() function
@app.route('/cloud/init')
def cloud_init():
    print('Initializing Cloud')

    #Logic to invoke RM-Proxy
    data = BytesIO()

    cURL.setopt(cURL.URL, medium_proxy_ip + '/init')
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
#2. Not Implemented
@app.route('/cloud/pods/<name>')
def cloud_pod_register(name):
    pass

#3. Not Implemented
@app.route('/cloud/pods/remove/<name>')
def cloud_pod_rm(name):
    pass

#NODE MANAGEMENT
#4. URL ~/cloud/nodes/ to trigger register() function
@app.route('/cloud/nodes/<name>/<pod_ID>')
def cloud_register(name, pod_ID):
    port = getNextPort()

    if pod_ID == 'M':
        ip = medium_proxy_ip

    print('About to get on: ' + ip + '/register/' + name + '/' + str(port))
    cURL.setopt(cURL.URL, ip + '/register/' + name + '/' + str(port))
    buffer = bytearray()

    cURL.setopt(cURL.WRITEFUNCTION, buffer.extend)

    cURL.perform()
    print(cURL.getinfo(cURL.RESPONSE_CODE))

    if cURL.getinfo(cURL.RESPONSE_CODE) == 200:
        response_dict = json.loads(buffer.decode())
        response = response_dict['result']

        if response == 'success':
            port = response_dict['port']
            name = response_dict['name']
            running = response_dict['running']

            return jsonify({'response': 'success',
                            'port' : port,
                            'name' : name,
                            'running' : running})

        else:
            reason = response_dict['reason']
            return jsonify({'response' : response,
                            'reason' : reason})


    return jsonify({'response' : response_dict['result'],
                    'reason' : response_dict['reason']})


#5. URL ~/cloud/nodes/remove/ to trigger rm() function
@app.route('/cloud/nodes/remove/<name>/<pod_ID>')
def cloud_rm(name, pod_ID):
    if pod_ID == 'M':
        ip = medium_proxy_ip
        servers = 'medium-servers'

    print('About to get on: ' + ip + '/remove/' + name)
    cURL.setopt(cURL.URL, ip + '/remove/' + name)
    buffer = bytearray()

    cURL.setopt(cURL.WRITEFUNCTION, buffer.extend)
    cURL.perform()
    print(cURL.getinfo(cURL.RESPONSE_CODE))

    if cURL.getinfo(cURL.RESPONSE_CODE) == 200:
        response_dict = json.loads(buffer.decode())
        response = response_dict['result']

        if response == 'success':
            port = response_dict['port']
            name = response_dict['name']
            running = response_dict['running']

            if running == 'true':
                disable_command = f"echo 'experimental-mode on; set server {servers}/'" + name + ' state maint ' + '| sudo socat stdio /var/run/haproxy.sock'
                subprocess.run(disable_command, shell=True, check=True)
                
                command = f"echo 'experimental-mode on; del server {servers}/'" + name + '| sudo socat stdio /var/run/haproxy.sock'
                subprocess.run(command, shell=True, check=True)

            return jsonify({'response': 'success',
                            'port' : port,
                            'name' : name,
                            'running' : running})

    return jsonify({'response' : response_dict['result'],
                    'reason' : response_dict['reason']})

#JOB MANAGEMENT
#6. URL ~/cloud/jobs/launch to trigger launch() function
@app.route('/cloud/launch/<pod_ID>')
def cloud_launch(pod_ID):
    if pod_ID == 'M':
        ip = medium_proxy_ip
        ip_no_port = medium_proxy_ip_no_port
        servers = 'medium-servers'
    
    print('About to get on: ' + ip + '/launch')
    cURL.setopt(cURL.URL, ip + '/launch')
    buffer = bytearray()

    cURL.setopt(cURL.WRITEFUNCTION, buffer.extend)
    cURL.perform()
    print(cURL.getinfo(cURL.RESPONSE_CODE))

    if cURL.getinfo(cURL.RESPONSE_CODE) == 200:
        response_dict = json.loads(buffer.decode())
        response = response_dict['result']

        if response == 'success':
            port = response_dict['port']
            name = response_dict['name']
            running = response_dict['running']
            print('port: ' + port)

            if running == 'true':
                command = f"echo 'experimental-mode on; add server {servers}/'" + name + ' ' + ip_no_port + ':' + port + '| sudo socat stdio /var/run/haproxy.sock'
                subprocess.run(command, shell=True, check=True)

                enable_command = f"echo 'experimental-mode on; set server {servers}/'" + name + ' state ready ' + '| sudo socat stdio /var/run/haproxy.sock'
                subprocess.run(enable_command, shell=True, check=True)

                return jsonify({'response': 'success',
                            'port' : port,
                            'name' : name,
                            'running' : running})

    return jsonify({'response' : 'failure',
                    'reason' : 'Unkonwn'})


#7. URL ~/cloud/jobs/abort to trigger abort() function
@app.route('/cloud/jobs/abort/<job_ID>')
def cloud_abort(job_ID):
    if request.method == 'GET':
        print('Request to abort job with ID ' + str(job_ID))
    
        #Logic to invoke RM-Proxy
        data = BytesIO()

        cURL.setopt(cURL.URL, proxy_url + '/cloudproxy/jobs/abort/' + str(job_ID))
        cURL.setopt(cURL.WRITEFUNCTION, data.write)
        cURL.perform()
        dictionary = json.loads(data.getvalue())
        print('This is the dictionary: '+ str(dictionary))

        if (dictionary['result'] == 'Failure'):
            result = 'Error - Cloud not initialized!'
            return jsonify({'result': result})

        elif (dictionary['result'] == 'invalid_ID'):
            result = 'Error: Job ID Invalid!'
            return jsonify({'result': result})

        elif (dictionary['result'] == 'job_completed'):
            result = 'Error: Job Already Completed!'
            return jsonify({'result': result})

        else:
            result = 'Success'
            node_ID = dictionary['node_associated']
            node_status = ['node_status']
            queue = dictionary['queue']
            return jsonify({'result': result, 'removed_job_ID': job_ID, 'removed_from_node': node_ID, 'status_of_node': node_status, 'queue_status': queue})



#--------------------- Monitoring ------------------------
#9. URL ~/cloud/monitor/node/ls/<pod_id> to trigger node ls command
@app.route('/cloud/monitor/node/ls', defaults={'pod_id': 'all'})
@app.route('/cloud/monitor/node/ls/<pod_id>')
def cloud_node_ls(pod_id):
    if request.method == 'GET':
        print(f"node ls command on {str(pod_id)} executing")

        #Logic to invoke RM-Proxy
        data = BytesIO()
        if pod_id == 'all':
            cURL.setopt(cURL.URL, medium_proxy_ip + '/monitor/node')
            cURL.setopt(cURL.WRITEFUNCTION, data.write)
            cURL.perform()

        else:
            cURL.setopt(cURL.URL, medium_proxy_ip + '/monitor/node/' + str(pod_id))
            cURL.setopt(cURL.WRITEFUNCTION, data.write)
            cURL.perform()

        dct = json.loads(data.getvalue())

        if dct['result'] == 'Failure':
            result = 'Unable to access pods'

            return jsonify({'result' : result})

        return jsonify(dct)

    else:
        return jsonify({'result' : f'Failure {request.method}'})


#--------------------------HELPER FUNCTIONS--------------------------
portCount = 14999

def getNextPort():
    global portCount
    portCount = portCount + 1
    return portCount

#--------------------------DASHBOARD WEBSITE--------------------------
app.add_url_rule("/cloud/dashboard/", view_func=views.index)
app.add_url_rule("/cloud/dashboard/clusters", view_func=views.clusters)  
app.add_url_rule("/cloud/dashboard/cluster/<pod_id>", view_func=views.pods)

if __name__ == '__main__':
    print("Dashboard Website on 'http://10.140.17.105/cloud/dashboard'\n")
    app.run(debug=True, host='0.0.0.0', port=6000)
