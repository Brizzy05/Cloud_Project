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
ip_no_port = '192.168.64.6'
light_proxy_ip = 'http://192.168.64.6:5000'
medium_proxy_ip = 'http://192.168.64.6:5001'
heavy_proxy_ip = 'http://192.168.64.6:5002'

#Create instance of Flask
app = Flask(__name__)

# For test purposes
@app.route('/')
def cloud_hello():
    return "Hello from Resource Manager\n"

#INIT, DEBUG, SANITY CHECK
#1. URL ~/ to trigger init() function
@app.route('/cloud/init')
def cloud_init():
    print('Initializing Cloud')
    #All 3 backends are initialized at the same time

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
    
    #Logic to invoke RM-Proxy (Heavy)
    data = BytesIO()
    cURL.setopt(cURL.URL, heavy_proxy_ip + '/init')
    cURL.setopt(cURL.WRITEFUNCTION, data.write)
    cURL.perform()
    dictionary_heavy = json.loads(data.getvalue())
    
    #If one backend returns Failure, then it means all 3 are already initialized
    if (dictionary_light['result'] == 'Failure' or dictionary_medium['result'] == 'Failure' or dictionary_heavy['result'] == 'Failure'):
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
        
    elif pod_ID == 'H':
        ip = heavy_proxy_ip

    else:
        return jsonify({'response' : 'Failure',
                        'reason' : 'Wrong ID - Please enter either L (light), M (medium) or H (heavy)'})

    #Connect to correct backend
    print('About to get on: ' + ip + '/register/' + name + '/' + str(port))
    cURL.setopt(cURL.URL, ip + '/register/' + name + '/' + str(port))
    buffer = bytearray()
    cURL.setopt(cURL.WRITEFUNCTION, buffer.extend)
    cURL.perform()
    print(cURL.getinfo(cURL.RESPONSE_CODE))

    #If connection successful
    if cURL.getinfo(cURL.RESPONSE_CODE) == 200:
        #Load dictionary
        result_dict = json.loads(buffer.decode())
        result = result_dict['result']

        #If success, return JSON infos
        if result == 'Success':
            port = result_dict['port']
            name = result_dict['name']
            status = result_dict['status']

            return jsonify({'result': 'Success',
                            'port' : port,
                            'name' : name,
                            'status' : status})

        #Else, return failure
        else:
            reason = result_dict['reason']
            return jsonify({'result' : result,
                            'reason' : reason})

    return jsonify({'response' : 'failure',
                    'reason' : 'Unknown'})


#5. URL ~/cloud/nodes/remove/ to trigger rm() function
@app.route('/cloud/nodes/remove/<name>/<pod_ID>')
def cloud_rm(name, pod_ID):
    #Check which pod is selected
    if pod_ID == 'L':
        ip = light_proxy_ip
        servers = 'light-servers'

    elif pod_ID == 'M':
        ip = medium_proxy_ip
        servers = 'medium-servers'
    
    elif pod_ID == 'H':
        ip = heavy_proxy_ip
        servers = 'heavy-servers'

    else:
        return jsonify({'response' : 'Failure',
                        'reason' : 'Wrong ID - Please enter either L (light), M (medium) or H (heavy)'})

    #Connect to correct backend
    print('About to get on: ' + ip + '/remove/' + name)
    cURL.setopt(cURL.URL, ip + '/remove/' + name)
    buffer = bytearray()
    cURL.setopt(cURL.WRITEFUNCTION, buffer.extend)
    cURL.perform()
    print(cURL.getinfo(cURL.RESPONSE_CODE))

    #If connection successful
    if cURL.getinfo(cURL.RESPONSE_CODE) == 200:
        response_dict = json.loads(buffer.decode())
        response = response_dict['result']

        #If success
        if response == 'Success':
            port = response_dict['port']
            name = response_dict['name']
            status = response_dict['status']

            #If node is ONLINE, then we must remove it from the LB  
            #Use 2 commands to remove server in real-time
            if status == 'ONLINE':
                disable_command = f"echo 'experimental-mode on; set server {servers}/'" + name + ' state maint ' + '| sudo socat stdio /var/run/haproxy.sock'
                subprocess.run(disable_command, shell=True, check=True)
                
                command = f"echo 'experimental-mode on; del server {servers}/'" + name + '| sudo socat stdio /var/run/haproxy.sock'
                subprocess.run(command, shell=True, check=True)
            
            #Return success
            return jsonify({'response': 'Success',
                            'port' : port,
                            'name' : name,
                            'status' : status})
    
        #Else, return failure
        else:
            reason = response_dict['reason']
            return jsonify({'result' : response,
                            'reason' : reason})

    return jsonify({'response' : 'failure',
                    'reason' : 'Unknown'})


#JOB MANAGEMENT
#6. URL ~/cloud/launch to trigger launch() function
@app.route('/cloud/launch/<pod_ID>')
def cloud_launch(pod_ID):
    #Check which pod is selected
    if pod_ID == 'L':
        ip = light_proxy_ip
        servers = 'light-servers'
        
    elif pod_ID == 'M':
        ip = medium_proxy_ip
        servers = 'medium-servers'
        
    elif pod_ID == 'H':
        ip = heavy_proxy_ip
        servers = 'heavy-servers'

    else:
        return jsonify({'response' : 'Failure',
                        'reason' : 'Wrong ID - Please enter either L (light), M (medium) or H (heavy)'})
    
    #Connect to correct backend
    print('About to get on: ' + ip + '/launch')
    cURL.setopt(cURL.URL, ip + '/launch')
    buffer = bytearray()
    cURL.setopt(cURL.WRITEFUNCTION, buffer.extend)
    cURL.perform()
    
    #If connection successful
    if cURL.getinfo(cURL.RESPONSE_CODE) == 200:
        response_dict = json.loads(buffer.decode())
        response = response_dict['result']

        #If success
        if response == 'Success':
            paused = response_dict['paused']
            port = response_dict['port']
            name = response_dict['name']
            status = response_dict['status']
    
            #If node ONLINE and if Pod not paused, add to LB 
            if str(status) == 'ONLINE' and paused == False:
                command = f"echo 'experimental-mode on; add server {servers}/'" + name + ' ' + ip_no_port + ':' + port + '| sudo socat stdio /var/run/haproxy.sock'
                print(command)
                subprocess.run(command, shell=True, check=True)

                enable_command = f"echo 'experimental-mode on; set server {servers}/'" + name + ' state ready ' + '| sudo socat stdio /var/run/haproxy.sock'
                subprocess.run(enable_command, shell=True, check=True)

                return jsonify({'response': 'Success',
                            'port' : port,
                            'name' : name,
                            'status' : status})
            
            #If Pod paused, do not add to LB
            elif paused == True:
                return jsonify({'response': 'Success',
                                'pod' : 'paused'})
                                

    return jsonify({'response' : 'failure',
                    'reason' : 'Unknown'})


#PAUSE & RESUME
#7. URL ~/cloud/resume to trigger resume() function
@app.route('/cloud/resume/<pod_ID>')
def cloud_resume(pod_ID):
    #Pod ID check
    if pod_ID == 'L':
        ip = light_proxy_ip
        servers = 'light-servers'

    elif pod_ID == 'M':
        ip = medium_proxy_ip
        servers = 'medium-servers'
        
    elif pod_ID == 'H':
        ip = heavy_proxy_ip
        servers = 'heavy-servers'

    else:
        return jsonify({'response' : 'Failure',
                        'reason' : 'Wrong ID - Please enter either L (light), M (medium) or H (heavy)'})

    #Connect to correct backend
    print('About to get on: ' + ip + '/resume')
    cURL.setopt(cURL.URL, ip + '/resume')
    buffer = bytearray()
    cURL.setopt(cURL.WRITEFUNCTION, buffer.extend)
    cURL.perform()

    #If connection successful
    if cURL.getinfo(cURL.RESPONSE_CODE) == 200:
        response_dict = json.loads(buffer.decode())
        response = response_dict['result']
        
        #If Pod paused
        if response == 'Success':
            name_ls = response_dict['name'].split()
            port_ls = response_dict['port'].split()
            #If there are nodes ONLINE, add them to the LB
            print(response_dict)
            for i in range(len(name_ls)):
                name = name_ls[i]
                port = port_ls[i]
                
                command = f"echo 'experimental-mode on; add server {servers}/'" + name + ' ' + ip_no_port + ':' + port + '| sudo socat stdio /var/run/haproxy.sock'
            
                subprocess.run(command, shell=True, check=True)

                enable_command = f"echo 'experimental-mode on; set server {servers}/'" + name + ' state ready ' + '| sudo socat stdio /var/run/haproxy.sock'
                subprocess.run(enable_command, shell=True, check=True)
            
            return jsonify ({'result' : 'Success',
                             'pods launched' : str(len(name_ls))})

        else:
            return jsonify ({'result' : 'Failure',
                             'reason' : 'Pod Already Running'})

    return jsonify({'response' : 'failure',
                    'reason' : 'Unknown'})

#8
@app.route('/cloud/pause/<pod_ID>')
def cloud_pause(pod_ID):
    #Pod ID check
    if pod_ID == 'L':
        ip = light_proxy_ip
        servers = 'light-servers'

    elif pod_ID == 'M':
        ip = medium_proxy_ip
        servers = 'medium-servers'
        
    elif pod_ID == 'H':
        ip = heavy_proxy_ip
        servers = 'heavy-servers'

    else:
        return jsonify({'response' : 'Failure',
                        'reason' : 'Wrong ID - Please enter either L (light), M (medium) or H (heavy)'})

    #Connect to correct backend
    print('About to get on: ' + ip + '/pause')
    cURL.setopt(cURL.URL, ip + '/pause')
    buffer = bytearray()
    cURL.setopt(cURL.WRITEFUNCTION, buffer.extend)
    cURL.perform()

    #If connection successful
    if cURL.getinfo(cURL.RESPONSE_CODE) == 200:
        response_dict = json.loads(buffer.decode())
        response = response_dict['result']
        
        
        #If Pod running
        if response == 'Success':
            name_ls = response_dict['name'].split()
            port_ls = response_dict['port'].split()
            #If there are nodes ONLINE, add them to the LB
            if len(response_dict) > 1:
                print(response_dict)
                for i in range(len(name_ls)):
                    name = name_ls[i]
                    port = port_ls[i]
            
                    disable_command = f"echo 'experimental-mode on; set server {servers}/'" + name + ' state maint ' + '| sudo socat stdio /var/run/haproxy.sock'
                    subprocess.run(disable_command, shell=True, check=True)

                    command = f"echo 'experimental-mode on; del server {servers}/'" + name + '| sudo socat stdio /var/run/haproxy.sock'
                    subprocess.run(command, shell=True, check=True)


            return jsonify ({'result' : 'Success',
                             'pods removed from Load Balancer' : str(len(name_ls))})
            

        else:
            return jsonify ({'result' : 'Failure',
                             'reason' : 'Pod already paused'})

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
        
    elif pod_ID == 'H':
        ip = heavy_proxy_ip
        

    else:
        return jsonify({'result' : 'Failure',
                        'reason' : 'Wrong ID - Please enter either L (light), M (medium) or H (heavy)'})

    #Connect to correct backend
    cURL.setopt(cURL.URL, ip + '/monitor/node')
    cURL.setopt(cURL.WRITEFUNCTION, data.write)
    cURL.perform()
    dct = json.loads(data.getvalue())
    if dct['result'] == 'Failure':
        return jsonify({'result' : 'Failure', 'reason': 'Unable to access pods'})

    return jsonify(dct)


#Dashboard helper to know if cloud is paused or not
@app.route('/dashboard/status/<pod_ID>')
def get_status(pod_ID):
    print(f"node ls command on {str(pod_ID)} executing")

    #Logic to invoke RM-Proxy
    data = BytesIO()
    if pod_ID == 'L':
        ip = light_proxy_ip

    elif pod_ID == 'M':
        ip = medium_proxy_ip
        
    else:
        ip = heavy_proxy_ip
        
    #Connect to correct backend
    cURL.setopt(cURL.URL, ip + '/dashboard/status')
    cURL.setopt(cURL.WRITEFUNCTION, data.write)
    cURL.perform()
    dct = json.loads(data.getvalue())
    if dct['result'] == 'Failure':
        return jsonify({'result' : 'Failure', 'reason': 'Unable to access pods'})

    return jsonify(dct)



#--------------------------HELPER FUNCTIONS--------------------------
portCount = 14999

def getNextPort():
    global portCount
    portCount = portCount + 1
    return portCount

#--------------------------DASHBOARD WEBSITE--------------------------
app.add_url_rule("/cloud/dashboard/", view_func=views.index)
app.add_url_rule("/cloud/dashboard/stats", view_func=views.stats)  
app.add_url_rule("/cloud/dashboard/cluster/<pod_id>", view_func=views.pods)


if __name__ == '__main__':
    print("Dashboard Website on 'http://192.168.64.5:3000/cloud/dashboard'\n")
    app.run(debug=True, host='0.0.0.0', port=3000)