import pycurl
import sys
import os
import requests

#Get the URL of the Ressource Manager
cURL = pycurl.Curl()

rm_url = '192.168.64.5:3000'
lb_url_light = '192.168.64.5:5000'
lb_url_medium = '192.168.64.5:5001'
lb_url_heavy = '192.168.64.5:5002'

def error_msg(msg):
    print(msg)
    print("Please check out 'cloud help' for all commad list")
    
#Prints all commands to the console
def cloud_help():
    cmd_lst = {"cloud init" : "Initializes main resource cluster and proxies", 
               "cloud pod register POD_NAME" : "Not Implemented", 
               "cloud pod rm POD_NAME" : "Not Implemented", 
               "cloud register NODE_NAME POD_ID" : "Register node with specified name, port in specified pod", 
               "cloud rm NODE_NAME POD_ID" : "Remove node with specified name from pod", 
               "cloud launch POD_ID" : "Launches a job from specified Job", 
               "cloud resume POD_ID" : "Resume specified pod activity",
               "cloud pause POD_ID" : "Pause specified pod activity",
               "cloud node ls POD_ID" : "Lists all nodes & their infos",
               "cloud request POD_ID" : "Sends HTTP request to LB",
               "clous exit" : "Exits cloud toolset"}
    print("------------------------------------ HELP ------------------------------------")
    print("Welcome to Help, here you will find a list of useful commands")
    print("NOTE : for POD_ID, please use either L (light pod), M (medium pod) or H (heavy pod)")
    print("e.g. 'cloud launch M'\n")

    
    for cmd in cmd_lst:
        print(cmd, "\n\t", cmd_lst[cmd])


#1. Initialize cloud : default pod & 50 default nodes
def cloud_init(url):
    cURL.setopt(cURL.URL, url + '/cloud/init')
    cURL.perform()

#2. Register new pod, must give pod name
#Syntax : $ cloud pod register <pod name>
def cloud_pod_register(url, command):
    error_msg(f"The current cloud system cannot register new pods.")
        

#3. Remove pod, must five pod name
#Syntax : $ cloud pod rm <pod name>
def cloud_pod_rm(url, command):
    error_msg(f"The current cloud system does not allow users to remove pods.")


#4. Register new node. Must specify name, port and pod
#Syntax : $ cloud register <node_name> <pod_ID>
def cloud_register(url, command):
    command_list = command.split()

    #If pod name given
    if len(command_list) == 4:
        cURL.setopt(cURL.URL, url + '/cloud/nodes/' + command_list[2] + '/' + command_list[3])
        cURL.perform()
    else:
        error_msg(f"Command:'{command}' Missing Argument <pod_name>")


#5. Remove existing node. Must specify name and pod
#Syntax : $ cloud rm <node_name> <pod_ID>
def cloud_rm(url, command):
    command_list = command.split()

    if len(command_list) == 4:
        cURL.setopt(cURL.URL, url + '/cloud/nodes/remove/' + command_list[2] + '/' + command_list[3])
        cURL.perform()

    else:
        error_msg(f"Command:'{command}' Missing Argument <pod_name>")


#6. Launch job on specified pod
#Syntax : $ cloud launch <pod_ID>
def cloud_launch(url, command):
    command_list = command.split()

    if len(command_list) == 3:
        cURL.setopt(cURL.URL, url + '/cloud/launch/' + command_list[2])
        cURL.perform()

    else:
        error_msg(f"Command:'{command}' Missing Argument <pod_name>")


#7. Resume specified pod activity
#Syntax : $ cloud resume <pod_ID>
def cloud_resume(url, command):
    command_list = command.split()

    if len(command_list) == 3:
        cURL.setopt(cURL.URL, url + '/cloud/resume/' + command_list[2])
        cURL.perform()

    else:
        error_msg(f"Command:'{command}' Missing Argument <pod_name>")


#8. Pause specified pod activity
#Syntax : $ cloud resume <pod_ID>
def cloud_pause(url, command):
    command_list = command.split()

    if len(command_list) == 3:
        cURL.setopt(cURL.URL, url + '/cloud/pause/' + command_list[2])
        cURL.perform()

    else:
        error_msg(f"Command:'{command}' Missing Argument <pod_name>")


#--------------------- Monitoring -----------------------
#9. List all resource node in specified pod, or in main cluster
# Syntax: cloud node ls <pod_ID>
def cloud_node_ls(url, command):
    command_ls = command.split()
    
    if len(command_ls) == 3:
        cURL.setopt(cURL.URL, url + '/cloud/node/ls')
        cURL.perform()
    
    elif len(command_ls) == 4: 
        cURL.setopt(cURL.URL, url + '/cloud/node/ls/' + command_ls[3])
        cURL.perform()
    
    else:
        error_msg(f"Command:'{command}' Not Correct")


#--------------------- Requests -----------------------
#10. Send a request to one pod
# Syntax: cloud request
def cloud_request(command):
    command_ls = command.split()

    if len(command_ls) == 3: 
        if command_ls[2] == 'L':
            print("Sending light request to lb: " + lb_url_light)
            t = Thread(target=runRequest, args=(lb_url_light,))
            t.start()

        elif command_ls[2] == 'M':
            print("Sending medium request to lb: " + lb_url_medium)
            t = Thread(target=runRequest, args=(lb_url_medium,))
            t.start()

        elif command_ls[2] == 'H':
            print("Sending heavy request to lb: " + lb_url_heavy)
            t = Thread(target=runRequest, args=(lb_url_heavy,))
            t.start()

        else:
            error_msg(f"Error: Please put L (light), M (medium) or H (heavy) as ID")

    else:
        error_msg(f"Command:'{command}' Not Correct")


def runRequest(lb_url):
    t_cURL = pycurl.Curl()
    t_cURL.setopt(t_cURL.URL, lb_url)
    start_time = time.time()
    t_cURL.perform()
    end_time = time.time()
    print("Total time : " + str(end_time-start_time) + " seconds. \n")


#---------- Main function ----------#
#This is where we put the different 
def main():
    while(1):
        command = input('$ ')
        
        #EXIT
        if command == 'exit':
            exit()

        #HELP
        elif command == 'cloud help':
            cloud_help()
        
        #INIT, DEBUG, SANITY CHECK
        elif command == 'cloud hello':
            cloud_hello(rm_url)

        #1
        elif command == 'cloud init':
            cloud_init(rm_url)
        

        #POD MANAGEMENT
        #2
        elif command.startswith('cloud pod register'):
            cloud_pod_register(rm_url, command)

        #3
        elif command.startswith('cloud pod rm'):
            cloud_pod_rm(rm_url, command)

        #NODE MANAGEMENT
        #4
        elif command.startswith('cloud register'):
            cloud_register(rm_url, command)
    
        #5
        elif command.startswith('cloud rm'):
            cloud_rm(rm_url, command)

        #JOB MANAGEMENT
        #6
        elif command.startswith('cloud launch'):
            cloud_launch(rm_url, command)

        #RESUME & PAUSE
        #7
        elif command.startswith('cloud resume'):
            cloud_resume(rm_url, command)

        #8
        elif command.startswith('cloud pause'):
            cloud_pause(rm_url, command)

        #---------- MONOTORING COMMANDS ---------#
        #9
        elif command.startswith('cloud node ls'):
            cloud_node_ls(rm_url, command)
        
        #---------- REQUEST COMMANDS ---------#
        #10
        elif command.startswith('cloud request'):
            cloud_request(command)

        else:
            error_msg(f"Command:'{command}' Not Recognized")

if __name__ == '__main__':
    main()