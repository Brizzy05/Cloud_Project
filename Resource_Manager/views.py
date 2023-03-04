from flask import render_template, request, jsonify
import requests
import pycurl
from io import BytesIO
import json
from __main__ import *

#Get the URL of the Proxy
cURL = pycurl.Curl()
rm_url = 'http://10.140.17.105:3000'

def index():
    try:
        stat = get_cloud_status()
    except:
        stat = "Error Clound not Launched"
    cl_avail = "0"
    pd_avail = "0"
    nd_avail = "0"
    total_count = 0
    
    if stat == 'Success':
        stat = 'Connected'
        cl_avail = "1"
        pd_avail = str(len(get_cloud_pods()))
        nd_dct = get_cloud_nodes()
        
        total_count = 0
        for keys in nd_dct:
            if 'IDLE' in nd_dct[keys]:
                total_count += 1
        
        nd_avail = str((len(nd_dct) - total_count))

    return render_template("index.html", cloud_status=stat, avail=cl_avail, 
                           pd_avail=pd_avail, nd_avail=nd_avail, nd_total=str(total_count))

def clusters():
    dct = get_cloud_pods()
    val = []
    for k in dct:
        l = dct[k].split(",")
        name = l[0].split()[1]
        id_num = l[1].split()[1]
        num_nodes = l[2].split()[1]
        val.append([name + id_num, id_num, num_nodes])
    
    return render_template("clusters.html", lst=val)

def pods(pod_id):
    dct = get_cloud_nodes()
    val = []
    for k in dct:
        l = dct[k].split(",")
        id_num = l[0].split()[1]
        num_nodes = l[1].split()[1]
        val.append([k, id_num, num_nodes])
    
    val.sort(key=lambda v : int(v[1])) 
    
    return render_template("cluster_overview.html", pod_id=pod_id, lst=val)

#--------------------------HELPER FUNCTIONS-------------------------
def get_cloud_status():
    #Logic to invoke RM-Proxy
    data = BytesIO()

    cURL.setopt(cURL.URL, rm_url + '/cloud/monitor/pod/ls')
    cURL.setopt(cURL.WRITEFUNCTION, data.write)
    cURL.perform()

    dct = json.loads(data.getvalue())
    
    if (dct['result'] != 'Success'):
        result = 'Disconnected'
    
    else:
        result = 'Success'
        
    return result

def get_cloud_clusters():
    pass

def get_cloud_pods():
    #Logic to invoke RM-Proxy
    data = BytesIO()

    cURL.setopt(cURL.URL, rm_url + '/cloud/monitor/pod/ls')
    cURL.setopt(cURL.WRITEFUNCTION, data.write)
    cURL.perform()

    dct = json.loads(data.getvalue())
    
    if (dct['result'] != 'Success'):
        result = 'Disconnected'
    
    else:
        dct.pop('result')
        
    return dct

def get_cloud_nodes():
    #Logic to invoke RM-Proxy
    data = BytesIO()

    cURL.setopt(cURL.URL, rm_url + '/cloud/monitor/node/ls')
    cURL.setopt(cURL.WRITEFUNCTION, data.write)
    cURL.perform()

    dct = json.loads(data.getvalue())
    
    if (dct['result'] != 'Success'):
        result = 'Disconnected'
    
    else:
        dct.pop('result')
        
    return dct