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
ip_no_port = '192.168.64.8'
light_proxy_ip = 'http://192.168.64.8:5000'
medium_proxy_ip = 'http://192.168.64.8:5001'
heavy_proxy_ip = 'http://192.168.64.8:5002'

#Create instance of Flask
app = Flask(__name__)


#INIT, DEBUG, SANITY CHECK
#1. URL ~/ to trigger init() function
@app.route('/cloud/init')
def cloud_init():
    print('Initializing Cloud')

    #Logic to invoke RM-Proxy (Light)
    data = BytesIO()
    cURL.setopt(cURL.URL, light_proxy_ip + '/init')
    cURL.setopt(cURL.WRITEFUNCTION, data.write)
    cURL.perform()
    dictionary_light = json.loads(data.getvalue())

    #Logic to invoke RM-Proxy (Medium)
    data = BytesIO()
    cURL.setopt(cURL.URL, medium_proxy_ip + '/init')
    cURL.setopt(cURL.WRITEFUNCTION, data.write)
    cURL.perform()
    dictionary_medium = json.loads(data.getvalue())
    
    if (dictionary_light['result'] == 'Failure' or dictionary_medium['result'] == 'Failure'):
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
    #Assign new port number
    port = getNextPort()
    
    #Check which pod is selected
    if pod_ID == 'L':
        ip = light_proxy_ip

    elif pod_ID == 'M':
        ip = medium_proxy_ip

    else:
        return jsonify({'response' : 'Failure',
                        'reason' : 'Wrong ID - Please enter either L (light), M (medium) or H (heavy)'})

    #Connect to correct server
    print('About to get on: ' + ip + '/register/' + name + '/' + str(port))
    cURL.setopt(cURL.URL, ip + '/register/' + name + '/' + str(port))
    buffer = bytearray()
    cURL.setopt(cURL.WRITEFUNCTION, buffer.extend)

    cURL.perform()
    print(cURL.getinfo(cURL.RESPONSE_CODE))

    if cURL.getinfo(cURL.RESPONSE_CODE) == 200:
        response_dict = json.loads(buffer.decode())
        response = response_dict['result']

        #If success, return JSON infos
        if response == 'success':
            port = response_dict['port']
            name = response_dict['name']
            status = response_dict['status']

            return jsonify({'response': 'success',
                            'port' : port,
                            'name' : name,
                            'status' : status})

        #Else, return failure
        else:
            reason = response_dict['reason']
            return jsonify({'response' : response,
                            'reason' : reason})


    return jsonify({'response' : response_dict['result'],
                    'reason' : response_dict['reason']})


#5. URL ~/cloud/nodes/remove/ to trigger rm() function
@app.route('/cloud/nodes/remove/<name>/<pod_ID>')
def cloud_rm(name, pod_ID):
    if pod_ID == 'L':
        ip = light_proxy_ip
        servers = 'light-servers'

    elif pod_ID == 'M':
        ip = medium_proxy_ip
        servers = 'medium-servers'

    else:
        return jsonify({'response' : 'Failure',
                        'reason' : 'Wrong ID - Please enter either L (light), M (medium) or H (heavy)'})

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
            status = response_dict['status']

            if status == 'ONLINE':
                disable_command = f"echo 'experimental-mode on; set server {servers}/'" + name + ' state maint ' + '| sudo socat stdio /var/run/haproxy.sock'
                subprocess.run(disable_command, shell=True, check=True)
                
                command = f"echo 'experimental-mode on; del server {servers}/'" + name + '| sudo socat stdio /var/run/haproxy.sock'
                subprocess.run(command, shell=True, check=True)

            return jsonify({'response': 'success',
                            'port' : port,
                            'name' : name,
                            'status' : status})

    return jsonify({'response' : response_dict['result'],
                    'reason' : response_dict['reason']})

#JOB MANAGEMENT
#6. URL ~/cloud/jobs/launch to trigger launch() function
@app.route('/cloud/launch/<pod_ID>')
def cloud_launch(pod_ID):
    if pod_ID == 'L':
        ip = light_proxy_ip
        servers = 'light-servers'
        
    elif pod_ID == 'M':
        ip = medium_proxy_ip
        servers = 'medium-servers'

    else:
        return jsonify({'response' : 'Failure',
                        'reason' : 'Wrong ID - Please enter either L (light), M (medium) or H (heavy)'})
    
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
            status = response_dict['status']
            print(status)

            if str(status) == 'ONLINE':
                print('HIT 3')
                command = f"echo 'experimental-mode on; add server {servers}/'" + name + ' ' + ip_no_port + ':' + port + '| sudo socat stdio /var/run/haproxy.sock'
                subprocess.run(command, shell=True, check=True)

                enable_command = f"echo 'experimental-mode on; set server {servers}/'" + name + ' state ready ' + '| sudo socat stdio /var/run/haproxy.sock'
                subprocess.run(enable_command, shell=True, check=True)

                return jsonify({'response': 'success',
                            'port' : port,
                            'name' : name,
                            'status' : status})

    return jsonify({'response' : 'failure',
                    'reason' : 'Unknown'})


#--------------------- Monitoring ------------------------
#9. URL ~/cloud/node/ls/<pod_id> to trigger node ls command
@app.route('/cloud/node/ls/<pod_ID>')
def cloud_node_ls(pod_ID):
    print(f"node ls command on {str(pod_ID)} executing")

    #Logic to invoke RM-Proxy
    data = BytesIO()
    if pod_ID == 'L':
        ip = light_proxy_ip

    elif pod_ID == 'M':
        ip = medium_proxy_ip

    else:
        return jsonify({'response' : 'Failure',
                        'reason' : 'Wrong ID - Please enter either L (light), M (medium) or H (heavy)'})
    cURL.setopt(cURL.URL, ip + '/monitor/node/' + str(pod_ID))
    cURL.setopt(cURL.WRITEFUNCTION, data.write)
    cURL.perform()
    dct = json.loads(data.getvalue())

    if dct['result'] == 'Failure':
        result = 'Unable to access pods'

        return jsonify({'result' : result})

    return jsonify(dct)



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