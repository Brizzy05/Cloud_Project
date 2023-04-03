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
ip_no_port = '192.168.64.9'
light_proxy_ip = 'http://192.168.64.9:5000'
medium_proxy_ip = 'http://192.168.64.9:5001'
heavy_proxy_ip = 'http://192.168.64.9:5002'
em_url = '192.168.64.3:4000'


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
        return jsonify({'result' : 'Failure',
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
            return jsonify({'result' : 'Failure',
                            'reason' : reason})

    return jsonify({'result' : 'Failure',
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
        return jsonify({'result' : 'Failure',
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
            return jsonify({'result': 'Success',
                            'port' : port,
                            'name' : name,
                            'status' : status})
    
        #Else, return failure
        else:
            reason = response_dict['reason']
            return jsonify({'result' : 'Failure',
                            'reason' : reason})

    return jsonify({'result' : 'Failure',
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
        return jsonify({'result' : 'Failure',
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

                return jsonify({'result': 'Success',
                            'port' : port,
                            'name' : name,
                            'status' : status})
            
            #If Pod paused, do not add to LB
            elif paused == True:
                return jsonify({'result': 'Success',
                                'pod' : 'paused'})
                                

    return jsonify({'result' : 'Failure',
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
        return jsonify({'result' : 'Failure',
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

    return jsonify({'result' : 'Failure',
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
        return jsonify({'result' : 'Failure',
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

    return jsonify({'result' : 'Failure',
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
    print("we in resource")
    cURL.setopt(cURL.URL, ip + '/monitor/node')
    cURL.setopt(cURL.WRITEFUNCTION, data.write)
    print("setting up curl")
    cURL.perform()
    print("we have done curl")
    dct = json.loads(data.getvalue())
    
    print("returning")
    if dct['result'] == 'Failure':
        return jsonify({'result' : 'Failure', 'reason': 'Unable to access pods'})

    return jsonify(dct)

#--------------------- Elasticity ------------------------
#10. URL ~/cloud/elasticity/enable/<pod_ID>/<lower_size>/<upper_size> to trigger enable elasticity command
@app.route('/cloud/elasticity/enable/<pod_ID>/<lower_size>/<upper_size>')
def cloud_elasticity_enable(pod_ID, lower_size, upper_size):
    print(f"\nElasticity Enable command on {pod_ID} executing. Lower_size: {lower_size} - Upper_size: {upper_size}.")
    
    #Input validation
    if pod_ID not in "LMH":
        return jsonify({'result' : 'Failure',
                        'reason' : 'Wrong ID - Please enter either L (light), M (medium) or H (heavy)'})
    
    else:
        #Validate <lower_size> && <upper_size> inputs
        if(int(lower_size) < 0 or int(upper_size) < 0):
            return jsonify({'result': 'Failure',
                            'reason': 'lower_size and upper_size must both be positive values'})
        
        elif(int(lower_size) >= int(upper_size)):
            return jsonify({'result': 'Failure',
                            'reason': 'lower_size must be smaller than upper_size'})
            
        #Request to EM
        data = BytesIO()
        cURL.setopt(cURL.URL, em_url + '/enable/' + pod_ID + '/' + lower_size + '/' + upper_size)
        cURL.setopt(cURL.WRITEFUNCTION, data.write)
        cURL.perform()
        print(f"Sending Elasticity Enable Request for '{pod_ID}' to Elastic Manager.")
        print(cURL.getinfo(cURL.RESPONSE_CODE))

        if cURL.getinfo(cURL.RESPONSE_CODE) == 200:
            dct = json.loads(data.getvalue())
            result = dct['result']
            
            if result == 'Success':
                print(f"Elasticity Successfully Enabled for '{pod_ID}'")
                return jsonify({'result': 'Success',
                                'pod_id': str(pod_ID),
                                'elasticity': 'enabled'})
            
            else:
                reason = dct['reason']
                print(f"Elasticity Unsuccessfully Enabled for '{pod_ID}'. Reason: {reason}")
                return jsonify({'result': 'Failure',
                                'reason': reason})
        
        return jsonify({'result' : 'Failure',
                        'reason' : 'Unknown'})
    
#11. URL ~/cloud/elasticity/disable/<pod_ID> to trigger disable elasticity command
@app.route('/cloud/elasticity/disable/<pod_ID>')
def cloud_elasticity_disable(pod_ID):
    print(f"\nElasticity Disable command on {pod_ID} executing.")
    #Input validation
    if pod_ID not in "LMH":
        return jsonify({'result' : 'Failure',
                        'reason' : 'Wrong ID - Please enter either L (light), M (medium) or H (heavy)'})

    #Request to EM
    data = BytesIO()
    cURL.setopt(cURL.URL, em_url + '/disable/' + pod_ID)
    cURL.setopt(cURL.WRITEFUNCTION, data.write)
    cURL.perform()
    print(f"Sending Elasticity Disable Request for '{pod_ID}' to Elastic Manager.")
    print(cURL.getinfo(cURL.RESPONSE_CODE))
    
    if cURL.getinfo(cURL.RESPONSE_CODE) == 200:
        dct = json.loads(data.getvalue())
        result = dct['result']
        if result == 'Success':
            print(f"Elasticity Successfully Disabled for '{pod_ID}'")
            return jsonify({'result': 'Success',
                            'pod_id': str(pod_ID),
                            'elasticity': 'disabled'})
        
        else:
            reason = dct['reason']
            print(f"Elasticity Unsuccessfully Disabled for '{pod_ID}'. Reason: {reason}")
            return jsonify({'result': 'Failure',
                            'reason': reason})
    

    return jsonify({'result' : 'Failure',
                    'reason' : 'Unknown'})


#12. URL ~/cloud/elasticity/lowerthreshold/<pod_ID>/<value> to trigger  elasticity lower threshold command
@app.route('/cloud/elasticity/lowerthreshold/<pod_ID>/<value>')
def cloud_elasticity_lower_threshold(pod_ID, value):
    print(f"\nSetting Elasticity Lower Threshold ({value}) for backend: {pod_ID}.")

    #Input validation
    if pod_ID not in "LMH":
        return jsonify({'result' : 'Failure',
                        'reason' : 'Wrong ID - Please enter either L (light), M (medium) or H (heavy)'})
    
    elif value.startswith('-') or (not is_float_between_0_and_1(value)):
        return jsonify({'result' : 'Failure',
                        'reason' : 'Wrong value - Please enter a positive float between [0,1] for lower threshold value'})

    
    #Request to EM
    data = BytesIO()
    cURL.setopt(cURL.URL, em_url + '/lowerthreshold/' + pod_ID + '/' + value)
    cURL.setopt(cURL.WRITEFUNCTION, data.write)
    cURL.perform()
    print(f"Sending lower threshold request for '{pod_ID}' to Elastic Manager.")
    print(cURL.getinfo(cURL.RESPONSE_CODE))
    
    if cURL.getinfo(cURL.RESPONSE_CODE) == 200:
        dct = json.loads(data.getvalue())
        result = dct['result']
        if result == 'Success':
            print(f"Elasticity Lower-Threshold Successfully set for '{pod_ID}'")
            return jsonify({'result': 'Success',
                            'pod_id': pod_ID,
                            'elasticity LT': value})

    print(f"Elasticity Lower-Threshold Unsuccessfully set for '{pod_ID}'")
    return jsonify({'result' : 'Failure',
                    'reason' : 'Unknown'})

#13. URL ~/cloud/elasticity/upperthreshold/<pod_ID>/<value> to trigger  elasticity upper threshold command
@app.route('/cloud/elasticity/upperthreshold/<pod_ID>/<value>')
def cloud_elasticity_upper_threshold(pod_ID, value):
    print(f"\nSetting Elasticity Upper Threshold ({value}) for backend: {pod_ID}.")

    #Input validation
    if pod_ID not in "LMH":
        return jsonify({'result' : 'Failure',
                        'reason' : 'Wrong ID - Please enter either L (light), M (medium) or H (heavy)'})
    
    elif value.startswith('-') or (not is_float_between_0_and_1(value)):
        return jsonify({'result' : 'Failure',
                        'reason' : 'Wrong value - Please enter a positive float between [0,1] for upper threshold value'})

    
    #Request to EM
    data = BytesIO()
    cURL.setopt(cURL.URL, em_url + '/upperthreshold/' + pod_ID + '/' + value)
    cURL.setopt(cURL.WRITEFUNCTION, data.write)
    cURL.perform()
    print(f"Sending upper threshold request for '{pod_ID}' to Elastic Manager.")
    print(cURL.getinfo(cURL.RESPONSE_CODE))
    
    if cURL.getinfo(cURL.RESPONSE_CODE) == 200:
        dct = json.loads(data.getvalue())
        result = dct['result']
        if result == 'Success':
            print(f"Elasticity Upper-Threshold Successfully set for '{pod_ID}'")
            return jsonify({'result': 'Success',
                            'pod_id': pod_ID,
                            'elasticity UT': value})
        

    print(f"Elasticity Upper-Threshold Unsuccessfully set for '{pod_ID}'")
    return jsonify({'result' : 'Failure',
                    'reason' : 'Unknown'})





#--------------------------HELPER FUNCTIONS--------------------------
portCount = 14999

def getNextPort():
    global portCount
    portCount = portCount + 1
    return portCount

def is_float_between_0_and_1(string):
    try:
        value = float(string)
        if 0.0 <= value <= 1.0:
            return True
        else:
            return False
    except ValueError:
        return False

#--------------------------DASHBOARD WEBSITE--------------------------
app.add_url_rule("/cloud/dashboard/", view_func=views.index)
app.add_url_rule("/cloud/dashboard/clusters", view_func=views.clusters)  
app.add_url_rule("/cloud/dashboard/cluster/<pod_id>", view_func=views.pods)


if __name__ == '__main__':
    print("Dashboard Website on 'http://192.168.64.5:3000/cloud/dashboard'\n")
    app.run(debug=True, host='0.0.0.0', port=3000)