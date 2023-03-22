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
        
    except Exception as e:
        print(e)
        stat = []
        init = "Error Clound not Launched"
        
    lg_avail = "0"
    md_avail = "0"
    hv_avail = "0"
    if len(stat) > 0:
        nd_ls = get_cloud_nodes(stat)
        for nodes in nd_ls:
            if 'LIGHT' == nodes['Pod']:
                lg_avail = str(len(nodes) - 1)
            if 'MEDIUM' == nodes['Pod']:
                md_avail = str(len(nodes) - 1)
            else:
                hv_avail = str(len(nodes) - 1)
        

    return render_template("index.html", cloud_status=init, light_avail=lg_avail, 
                           med_avail=md_avail, heavy_avail=hv_avail)

def stats():
    return render_template("stats.html")

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
    dct = get_cloud_nodes([pod_id])[0]
    dct.pop('Pod')
    val = []
    
    data = BytesIO()
    cURL.setopt(cURL.URL, rm_url + f'/dashboard/status/{pod_id}')
    cURL.setopt(cURL.WRITEFUNCTION, data.write)
    cURL.perform()
    dct_2 = json.loads(data.getvalue())
    paused = dct_2['result']
    
    if pod_id == 'L':
        pod_id = 'Light Pod'
    elif pod_id == 'M':
        pod_id = 'Medium Pod'
    else:
        pod_id = 'Heavy Pod'
    
    if paused:
        paused = "Paused"
    else:
        paused = "Resumed"
      
    for k in dct:
        l = dct[k].split("-")
        print(l)
        id_num = k
        nd_name = l[0].split()[1]
        num_port = l[1].split()[1]
        nd_status = l[2].split()[1]
        val.append([nd_name, id_num, num_port, nd_status])
    
    val.sort(key=lambda v : int(v[1])) 
    
    return render_template("cluster_overview.html", pod_id=pod_id, lst=val, running=paused)

#--------------------------HELPER FUNCTIONS-------------------------
def get_nodes_info(node_ls):
    pass

def get_cloud_status(): 
    pod_ls = ("L", "M", "H")
    
    result = []

    for id in pod_ls:
        #Logic to invoke RM-Proxy
        data = BytesIO()
        cURL.setopt(cURL.URL, rm_url + f'/cloud/node/ls/{id}')
        cURL.setopt(cURL.WRITEFUNCTION, data.write)
        cURL.perform()
        dct = json.loads(data.getvalue())
        print(dct)
        
        if (dct['result'] == 'Success'):
            result.append(id)
        
    return result


def get_cloud_nodes(pod_ls):
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
    
    print("\n Printing node dict")
    print(result)
    print("\n")
    
    return result