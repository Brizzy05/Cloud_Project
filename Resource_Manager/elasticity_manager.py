from flask import Flask, jsonify, request
import pycurl
import json
from io import BytesIO
from threading import Thread

#Create instance of Flask
app = Flask(__name__)

cURL = pycurl.Curl()
light_proxy_ip = 'http://192.168.64.9:5000'
medium_proxy_ip = 'http://192.168.64.9:5001'
heavy_proxy_ip = 'http://192.168.64.9:5002'


#Pod elasticity Status Identifiers
PodElasticityIdentifierDict = {'L': False,
                               'M': False, 
                               'H': False
                               }

elasticResouceManagementThreads = {'L': None,
                                   'M': None,
                                   'H': None}


def runERMThreads(pod_ID, pod_url):
    t_cURL = pycurl.Curl()
    t_cURL.setopt(cURL.URL, pod_url + '/elastic/resource/management')
    while(1):
        ##If Elastic Manager is disabled for specific pod, do not do anything
        global PodElasticityIdentifierDict
        if PodElasticityIdentifierDict[pod_ID] == False:
            continue

        else:
            cURL.perform()
            ##do some other stuff


#Setup threads responsible for elastic management of backend resources (1 for each backend
elasticResouceManagementThreads['L'] = Thread(target=runERMThreads, args=('L', light_proxy_ip,))
elasticResouceManagementThreads['M'] = Thread(target=runERMThreads, args=('M', medium_proxy_ip,))
elasticResouceManagementThreads['H'] = Thread(target=runERMThreads, args=('H', heavy_proxy_ip,))

for key, value in elasticResouceManagementThreads:
    value.start()







@app.route('/enable/<pod_ID>/<lower_size>/<upper_size>')
def enableElasticityPod(pod_ID, lower_size, upper_size):
    print(f"\nElasticity Enable command on {pod_ID} executing. Lower_size: {lower_size} - Upper_size: {upper_size}.")
    ip = ''
    if pod_ID == 'L':
        ip = light_proxy_ip

    elif pod_ID == 'M':
        ip = medium_proxy_ip
        
    elif pod_ID == 'H':
        ip = heavy_proxy_ip

    data = BytesIO()
    cURL.setopt(cURL.URL, ip + '/enable/elasticity/' + lower_size + '/' + upper_size)
    cURL.setopt(cURL.WRITEFUNCTION, data.write)
    cURL.perform()
    print(f"Sending request to setup elasticity parameters (lower size: {lower_size} & upper size: {upper_size}) to backend: {pod_ID}.")
    print(cURL.getinfo(cURL.RESPONSE_CODE))

    #If connection successful
    if cURL.getinfo(cURL.RESPONSE_CODE) == 200:
        dct = json.loads(data.getvalue())
        result = dct['result']

        if result == 'Success':
            global PodElasticityIdentifierDict
            PodElasticityIdentifierDict[pod_ID] = True
            print(f"POD: {pod_ID} Elastic mode on --> {PodElasticityIdentifierDict[pod_ID]}")
            return jsonify({'result': 'Success',
                            'pod_id': pod_ID,
                            'elasticity': 'enabled'})
        
        else:
            reason = dct['reason']
            return jsonify({'result': result,
                            'reason': reason})
    
    return jsonify({'response' : 'failure',
                    'reason' : 'Unknown'})


@app.route('/disable/<pod_ID>')
def disableElasticityPod(pod_ID):
    print(f"\nElasticity Disable command on {pod_ID} executing.")
    ip = ''
    if pod_ID == 'L':
        ip = light_proxy_ip

    elif pod_ID == 'M':
        ip = medium_proxy_ip
        
    elif pod_ID == 'H':
        ip = heavy_proxy_ip

    data = BytesIO()
    cURL.setopt(cURL.URL, ip + '/disable/elasticity')
    cURL.setopt(cURL.WRITEFUNCTION, data.write)
    cURL.perform()
    print(cURL.getinfo(cURL.RESPONSE_CODE))

    #If connection successful
    if cURL.getinfo(cURL.RESPONSE_CODE) == 200:
        dct = json.loads(data.getvalue())
        result = dct['result']

        if result == 'Success':
            global PodElasticityIdentifierDict
            PodElasticityIdentifierDict[pod_ID] = False
            print(f"POD: {pod_ID} Elastic mode on --> {PodElasticityIdentifierDict[pod_ID]}")
            return jsonify({'result': 'Success',
                            'pod_id': pod_ID,
                            'elasticity': 'disabled'})
        
        else:
            reason = dct['reason']
            return jsonify({'result': result,
                            'reason': reason})
    
    return jsonify({'response' : 'failure',
                    'reason' : 'Unknown'})

@app.route('/lowerthreshold/<pod_ID>/<value>')
def elasticityLowerThreshold(pod_ID, value):
    print(f"\nSetting Elasticity Lower Threshold ({value}) for backend: {pod_ID}.")
    ip = ''
    if pod_ID == 'L':
        ip = light_proxy_ip

    elif pod_ID == 'M':
        ip = medium_proxy_ip
        
    elif pod_ID == 'H':
        ip = heavy_proxy_ip

    data = BytesIO()
    cURL.setopt(cURL.URL, ip + '/lowerthreshold/' + value)
    cURL.setopt(cURL.WRITEFUNCTION, data.write)
    cURL.perform()
    print(cURL.getinfo(cURL.RESPONSE_CODE))

    #If connection successful
    if cURL.getinfo(cURL.RESPONSE_CODE) == 200:
        dct = json.loads(data.getvalue())
        result = dct['result']

        if result == 'Success':
            return jsonify({'result': 'Success',
                            'pod_id': pod_ID,
                            'elasticity LT': value})
    
    return jsonify({'response' : 'failure',
                    'reason' : 'Unknown'})


@app.route('/upperthreshold/<pod_ID>/<value>')
def elasticityUpperThreshold(pod_ID, value):
    print(f"\nSetting Elasticity Upper Threshold ({value}) for backend: {pod_ID}.")
    ip = ''
    if pod_ID == 'L':
        ip = light_proxy_ip

    elif pod_ID == 'M':
        ip = medium_proxy_ip
        
    elif pod_ID == 'H':
        ip = heavy_proxy_ip

    data = BytesIO()
    cURL.setopt(cURL.URL, ip + '/upperthreshold/' + value)
    cURL.setopt(cURL.WRITEFUNCTION, data.write)
    cURL.perform()
    print(cURL.getinfo(cURL.RESPONSE_CODE))

    #If connection successful
    if cURL.getinfo(cURL.RESPONSE_CODE) == 200:
        dct = json.loads(data.getvalue())
        result = dct['result']

        if result == 'Success':
            return jsonify({'result': 'Success',
                            'pod_id': pod_ID,
                            'elasticity UT': value})
    
    return jsonify({'response' : 'failure',
                    'reason' : 'Unknown'})





if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=4000)