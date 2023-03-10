from flask import Flask, jsonify, request
import requests
import pycurl
import json
import sys
from io import BytesIO
import views

#Get the URL of the Proxy
cURL = pycurl.Curl()
proxy_url = 'http://10.140.17.106:6000'

#Create instance of Flask
app = Flask(__name__, static_folder="static", template_folder="templates")

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
            return jsonify({'result': result})

        else:
            result = dictionary['result']
            rm_pod_ID = dictionary['removed_pod_ID']
            return jsonify({'result': result, 'removed_pod_ID': rm_pod_ID, 'removed_pod_name': name})


#NODE MANAGEMENT
#4. URL ~/cloud/nodes/ to trigger register() function
@app.route('/cloud/nodes/<name>', defaults={'pod_ID': 'default'})
@app.route('/cloud/nodes/<name>/<pod_ID>')
def cloud_register(name, pod_ID):
    if request.method == 'GET':
        print('Request to register new node: ' + str(name) + ' on pod:' + str(pod_ID))
        
        #Logic to invoke RM-Proxy
        data = BytesIO()

        if (pod_ID == 'default'):
            cURL.setopt(cURL.URL, proxy_url + '/cloudproxy/nodes/' + str(name))
            cURL.setopt(cURL.WRITEFUNCTION, data.write)
            cURL.perform()
            dictionary = json.loads(data.getvalue())
            print('This is the dictionary : ' + str(dictionary))
    
        else:
            cURL.setopt(cURL.URL, proxy_url + '/cloudproxy/nodes/' + str(name) + '/' + str(pod_ID))
            cURL.setopt(cURL.WRITEFUNCTION, data.write)
            cURL.perform()
            dictionary = json.loads(data.getvalue())
            print('This is the dictionary : ' + str(dictionary))


        if (dictionary['result'] == 'Failure'):
            result = 'Error - Cloud not initialized!'
            return jsonify({'result': result})
        
        elif (dictionary['result'] == 'node_already_exists'):
            result = 'Error: Node already exists!'
            return jsonify({'result': result})

        elif (dictionary['result'] == 'pod_ID_invalid'):
            result = 'Error: Pod ID invalid!'
            return jsonify({'result': result})

        else:
            result = dictionary['result']
            node_status = dictionary['node_status']
            new_node_name = dictionary['node_name']
            new_node_pod = pod_ID

            return jsonify({'result': result, 'node_status': node_status, 'new_node_name': new_node_name, 'node_pod': new_node_pod})


#5. URL ~/cloud/nodes/remove/ to trigger rm() function
@app.route('/cloud/nodes/remove/<name>')
def cloud_rm(name):
    if request.method == 'GET':
        print('Request to remove node: ' + str(name))

        #Logic to invoke RM-Proxy
        data = BytesIO()

        cURL.setopt(cURL.URL, proxy_url + '/cloudproxy/nodes/remove/' + str(name))
        cURL.setopt(cURL.WRITEFUNCTION, data.write)
        cURL.perform()
        dictionary = json.loads(data.getvalue())
        print('This is the dictionary: '+ str(dictionary))

        if (dictionary['result'] == 'Failure'):
            result = 'Error - Cloud not initialized!'
            return jsonify({'result': result})

        elif (dictionary['result'] == 'node_name_invalid'):
            result = 'Error: Node Name Invalid!'
            return jsonify({'result': result})

        else:
            result = dictionary['result']
            print(result)
            rm_node_name = dictionary['removed_node_name']
            rm_pod_ID = dictionary['removed_from_pod_ID']

            return jsonify({'result': result, 'removed_node_name': rm_node_name, 'removed_from_pod_ID': rm_pod_ID})


#JOB MANAGEMENT
#6. URL ~/cloud/jobs/launch to trigger launch() function
@app.route('/cloud/jobs/launch', methods=['POST'])
def cloud_launch():
    if request.method == 'POST':
        print('Request to post a file: Client -> Resource Manager')
        
        job_file = request.files['file']
        print('------------File Contents-------------')
        print(job_file.read())
        job_file.seek(0)
        print('--------------------------------------')

        print('Sending file to proxy')
        files = {'file' : (job_file.filename, job_file.stream, job_file.mimetype)}
        req = requests.post(proxy_url + '/cloudproxy/jobs', files=files)
        print(req.text)
        
        #if (dictionary['result'] == 'Failure'):
        #    result = 'Error - Cloud not initialized!'
        #else:
        result = 'Success'
        return jsonify({'result': result})


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
            node_status = dictionary['node_status']
            queue = dictionary['queue']
            return jsonify({'result': result, 'removed_job_ID': job_ID, 'removed_from_node': node_ID, 'status_of_node': node_status, 'queue_status': queue})



#--------------------- Monitoring ------------------------

#1. URL ~/cloud/monitor/pod/ls to trigger pod ls command
@app.route('/cloud/monitor/pod/ls')
def cloud_pod_ls():
    if request.method == 'GET':
        print('ls command executing')
        
        #Logic to invoke RM-Proxy
        data = BytesIO()

        cURL.setopt(cURL.URL, proxy_url + '/cloudproxy/monitor/pod/ls')
        cURL.setopt(cURL.WRITEFUNCTION, data.write)
        cURL.perform()
        
        dct = json.loads(data.getvalue())
        
        if (dct['result'] == 'Failure'):
            result = 'Unable to access pods'
            
            return jsonify({'result' : result})
      
        return jsonify(dct)
    
    else:
        result = "Failure" 
        return jsonify({'result' : result})


#2. URL ~/cloud/monitor/node/ls/<pod_id> to trigger node ls command
@app.route('/cloud/monitor/node/ls', defaults={'pod_id': 'cluster'})
@app.route('/cloud/monitor/node/ls/<pod_id>')
def cloud_node_ls(pod_id):
    if request.method == 'GET':
        print(f"node ls command on {str(pod_id)} executing")

        #Logic to invoke RM-Proxy
        data = BytesIO()
        if pod_id == 'cluster':
            cURL.setopt(cURL.URL, proxy_url + '/cloudproxy/monitor/node/ls')
            cURL.setopt(cURL.WRITEFUNCTION, data.write)
            cURL.perform()

        else:
            cURL.setopt(cURL.URL, proxy_url + '/cloudproxy/monitor/node/ls/' + str(pod_id))
            cURL.setopt(cURL.WRITEFUNCTION, data.write)
            cURL.perform()

        dct = json.loads(data.getvalue())

        if dct['result'] == 'Failure':
            result = 'Unable to access pods'

            return jsonify({'result' : result})

        return jsonify(dct)

    else:
        return jsonify({'result' : f'Failure {request.method}'})


#3. URL ~/cloud/monitor/jobs/ls/<node_id> to trigger job ls command
@app.route('/cloud/monitor/jobs/ls', defaults={'node_id': 'none'})
@app.route('/cloud/monitor/jobs/ls/<node_id>')
def cloud_jobs_ls(node_id):
    if request.method == 'GET':
        print('Request to list jobs')

        #Logic to invoke RM-Proxy
        data = BytesIO()
        if node_id == 'none':
            cURL.setopt(cURL.URL, proxy_url + '/cloudproxy/monitor/jobs/ls')
            cURL.setopt(cURL.WRITEFUNCTION, data.write)
            cURL.perform()

        else:
            cURL.setopt(cURL.URL, proxy_url + '/cloudproxy/monitor/jobs/ls/' + str(node_id))
            cURL.setopt(cURL.WRITEFUNCTION, data.write)
            cURL.perform()

        dictionary = json.loads(data.getvalue())
        
        if dictionary['result'] == 'Failure':
            result = 'Unable to access jobs'
            return jsonify({'result' : result})
        
        elif dictionary['result'] == 'invalide_node_ID':
            result = 'Error: Invalid Node ID!'
            return jsonify({'result': result})

        return jsonify(dictionary)

    else:
        return jsonify({'result' : f'Failure {request.method}'})


#4. URL ~/cloud/monitor/jobs/log/<job_id> to trigger job log command
@app.route('/cloud/monitor/jobs/log/<job_id>')
def cloud_job_log(job_id):
    if request.method == 'GET':
        print('Request to list job log')

        #Logic to invoke RM-Proxy
        data = BytesIO()
        cURL.setopt(cURL.URL, proxy_url + '/cloudproxy/monitor/jobs/log/' + str(job_id))
        cURL.setopt(cURL.WRITEFUNCTION, data.write)
        cURL.perform()
        dictionary = json.loads(data.getvalue())
        
        if dictionary['result'] == 'Failure':
            result = 'Unable to access jobs'
            return jsonify({'result' : result})

        elif dictionary['result'] == 'invalid_job_ID':
            print('job invalid')
            result = 'Error: Invalid Job ID!'
            return jsonify({'result': result})

        elif dictionary['result'] == 'job_not_done_running':
            result = 'Error: No log available, Job Currently Running!'
            return jsonify({'result': result})

        else:

            return jsonify(dictionary)

    else:
        return jsonify({'result' : f'Failure {request.method}'})


#5. URL ~/cloud/monitor/nodes/log/<node_id> to trigger node log command
@app.route('/cloud/monitor/nodes/log/<node_id>')
def cloud_node_log(node_id):
    if request.method == 'GET':
        print('Request to list node log')

        #Logic to invoke RM-Proxy
        data = BytesIO()
        cURL.setopt(cURL.URL, proxy_url + '/cloudproxy/monitor/nodes/log/' + str(node_id))
        cURL.setopt(cURL.WRITEFUNCTION, data.write)
        cURL.perform()
        dictionary = json.loads(data.getvalue())

        if dictionary['result'] == 'Failure':
            result = 'Unable to access nodes'
            return jsonify({'result' : result})

        elif dictionary['result'] == 'invalid_node_ID':
            result = 'Error: Invalid Node ID'
            return jsonify({'result' : result})

        else:
            return jsonify(dictionary)

    else:
        return jsonify({'result' : f'Failure {request.method}'})

#--------------------------DASHBOARD WEBSITE--------------------------
app.add_url_rule("/cloud/dashboard/", view_func=views.index)
app.add_url_rule("/cloud/dashboard/clusters", view_func=views.clusters)  
app.add_url_rule("/cloud/dashboard/cluster/<pod_id>", view_func=views.pods)

#--------------------------HELPER FUNCTIONS-------------------------


if __name__ == '__main__':
    print("Dashboard Website on 'http://10.140.17.105/cloud/dashboard'\n")
    app.run(debug=True, host='0.0.0.0', port=3000)