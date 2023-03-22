from flask import render_template, request, jsonify
import requests
import pycurl
from io import BytesIO
import json
from __main__ import *
import time

#Get the URL of the Proxy
cURL = pycurl.Curl()
rm_url = 'http://192.168.64.5:3000'

def index():
    try:
        stat = get_cloud_status()
        init = "Connected"
        print("Where am I")
        
    except Exception as e:
        print(e)
        stat = []
        init = "Error Clound not Launched"
        
    cl_avail = "0"
    pd_avail = "0"
    nd_avail = "0"
    total_count = 0
    print(len(stat))
    if len(stat) > 0:
        init = 'Connected'
        cl_avail = "1"
        pd_avail = str(len(stat))
        nd_dct = get_cloud_nodes()
        
        print(nd_dct)
        
        total_count = 0
        # for keys in nd_dct:
        #     if 'IDLE' in nd_dct[keys]:
        #         total_count += 1
        
        nd_avail = 0

    return render_template("index.html", cloud_status=init, avail=cl_avail, 
                           pd_avail=pd_avail, nd_avail=nd_avail, nd_total=str(total_count))

def clusters():
    dct = get_cloud_nodes()
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
    pod_ls = ("L", "M", "H")
    
    result = []

    for id in pod_ls:
        #Logic to invoke RM-Proxy
        data = BytesIO()
        print(f" Now doing {id}, {pod_ls}")
        cURL.setopt(cURL.URL, rm_url + f'/cloud/node/ls/{id}')
        cURL.setopt(cURL.WRITEFUNCTION, data.write)
        cURL.perform()
        print("getting dic val in views")
        dct = json.loads(data.getvalue())
        print("successfuly got dic")
        print(dct)
        
        if (dct['result'] == 'Success'):
            result.append(id)
        
    return result


def get_cloud_nodes():
    pod_ls = ("L", "M", "H")
    
    result = []
    
    for id in pod_ls: 
        #Logic to invoke RM-Proxy
        data = BytesIO()
        
        cURL.setopt(cURL.URL, rm_url + f'/cloud/node/ls/{id}')
        cURL.setopt(cURL.WRITEFUNCTION, data.write)
        cURL.perform()

        
        dct = json.loads(data.getvalue())
        
        if (dct['result'] == 'Success'):
            dct.pop('result')
            result.append(dct)
        
    return result