import pycurl
import sys
import os
import requests

#Get the URL of the Ressource Manager
cURL = pycurl.Curl()

rm_url = '192.168.64.5:6000'

#Ping the cloud
#Syntax : $ cloud hello
def cloud_hello(url):
    cURL.setopt(cURL.URL, url)
    cURL.perform()

def error_msg(msg):
    print(msg)
    print("Please check out 'cloud help' for all commad list")
    
#Prints all commands to the console
def cloud_help():
    cmd_lst = {"cloud init" : "Initializes main resource cluster", 
               "cloud pod register POD_NAME" : "Not Implemented", 
               "cloud pod rm POD_NAME" : "Not Implemented", 
               "cloud register NODE_NAME PORT_NUMBER POD_ID" : "Register node with specified name, port in specified pod", 
               "cloud rm NODE_NAME POD_ID" : "Remove node with specified name from pod", 
               "cloud launch POD_ID" : "Launches a job from specified Job", 
               "cloud abort JOB_ID" : "Aborts a specidfied job",
               "cloud pod ls" : "Lists all resource pod in the main cluster",
               "cloud job ls [NODE_ID]" : "Lists all the jobs launched or just the one assigned by the specified node",
               "cloud job log JOB_ID" : "Gets a specified job's log",
               "cloud log node NODE_ID" : "Gets a specified node's log"}
    print("---------------------------------------- HELP ----------------------------------------")
    print("Welcome to Help, here you will find a list of useful commands")
    
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
#Syntax : $ cloud register <node_name> <node_port> <pod_ID>
def cloud_register(url, command):
    command_list = command.split()

    #If pod name given
    if len(command_list) == 5:
        cURL.setopt(cURL.URL, url + '/cloud/nodes/' + command_list[2] + '/' + command_list[3] + '/' + command_list[4])
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


#7. Abort job if running
#Syntax : $ cloud abort <job_id>
def cloud_abort(url, command):
    command_list = command.split()

    if len(command_list) == 3:
        cURL.setopt(cURL.URL, url + '/cloud/jobs/abort/' + command_list[2])
        cURL.perform()

    else:
        error_msg(f"Command:'{command}' Missing Argument <pod_ID>")


# -------------------- Monitoring -----------------------
#1. List all resource pods in main cluster, name, ID, number of nodes
# Syntax: cloud pod ls
def cloud_pod_ls(url, command):
    command_ls = command.split()
    
    if len(command_ls) == 3:
        cURL.setopt(cURL.URL, url + '/cloud/monitor/pod/ls')
        cURL.perform()
        
    else:
        error_msg(f"Command:'{command}' Not Correct")


#2. List all resource node in specified pod, or in main cluster
# Syntax: cloud node ls <pod_ID>
def cloud_node_ls(url, command):
    command_ls = command.split()
    
    if len(command_ls) == 3:
        cURL.setopt(cURL.URL, url + '/cloud/monitor/node/ls')
        cURL.perform()
    
    elif len(command_ls) == 4: 
        cURL.setopt(cURL.URL, url + '/cloud/monitor/node/ls/' + command_ls[3])
        cURL.perform()
    
    else:
        error_msg(f"Command:'{command}' Not Correct")


#3. List all jobs assigned to specified node.
# Syntax : cloud job ls <node_ID>
def cloud_job_ls(url, command):
    command_ls = command.split()

    if len(command_ls) == 3:
        cURL.setopt(cURL.URL, url + '/cloud/monitor/jobs/ls')
        cURL.perform()

    elif len(command_ls) == 4:
        cURL.setopt(cURL.URL, url + '/cloud/monitor/jobs/ls/' + command_ls[3])
        cURL.perform()

    else:
        error_msg(f"Command:'{command}' Not Correct")


#4. Print out specified job log
# Syntax : cloud job log <job_ID>
def cloud_job_log(url, command):
    command_ls = command.split()

    if len(command_ls) == 4:
        cURL.setopt(cURL.URL, url + '/cloud/monitor/jobs/log/' + command_ls[3])
        cURL.perform()

    else:
        error_msg(f"Command:'{command}' Not Correct")


#5. Prints out specified node entire log file
# Syntax : cloud log node <node_ID>
def cloud_log_node(url, command):
    command_ls = command.split()
        
    if len(command_ls) == 4:
        cURL.setopt(cURL.URL, url + '/cloud/monitor/nodes/log/' + command_ls[3])
        cURL.perform()

    else:
        error_msg(f"Command:'{command}' Not Correct")

def notImplemented():
    print('Function not yet implemented.')


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

        #7
        elif command.startswith('cloud abort'):
            cloud_abort(rm_url, command)

        #---------- MONOTORING COMMANDS ---------#
        
        #1
        elif command.startswith('cloud pod ls'):
            cloud_pod_ls(rm_url, command)

        #2
        elif command.startswith('cloud node ls'):
            cloud_node_ls(rm_url, command)
        
        #3
        elif command.startswith('cloud job ls'):
            cloud_job_ls(rm_url, command)

        #4
        elif command.startswith('cloud job log'):
            cloud_job_log(rm_url, command)
        
        #5
        elif command.startswith('cloud log node'):
            cloud_log_node(rm_url, command)

        else:
            error_msg(f"Command:'{command}' Not Recognized")

if __name__ == '__main__':
    main()
