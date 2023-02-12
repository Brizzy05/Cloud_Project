import pycurl
import sys
import os
import requests

#Get the URL of the Ressource Manager
cURL = pycurl.Curl()

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
               "cloud pod register POD_NAME" : "Register pod with specified name", 
               "cloud pod rm POD_NAME" : "Remoce pod with specified name", 
               "cloud register NODE_NAME [POD_ID]" : "Register node with optional pod name", 
               "cloud rm NODE_NAME" : "Remove node with specified name", 
               "cloud launch PATH_TO_JOB" : "Launches a specified job", 
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
    command_list = command.split()

    if len(command_list) == 4:
        cURL.setopt(cURL.URL, url + '/cloud/pods/' + command_list[3])
        cURL.perform()
    else:
        error_msg(f"Command:'{command}' Missing Argument <pod_name>")

#3. Remove pod, must five pod name
#Syntax : $ cloud pod rm <pod name>
def cloud_pod_rm(url, command):
    command_list = command.split()

    if len(command_list) == 4:
        cURL.setopt(cURL.URL, url + '/cloud/pods/remove/' + command_list[3])
        cURL.perform()
    else:
        error_msg(f"Command:'{command}' Missing Argument <pod_name>")

#4. Register new node, possibility to give pod name
#Syntax : $ cloud register <node_name> <pod_name>
def cloud_register(url, command):
    command_list = command.split()

    #If no pod name given
    if len(command_list) == 3:
        cURL.setopt(cURL.URL, url + '/cloud/nodes/' + command_list[2])
        cURL.perform()

    #If pod name given
    elif len(command_list) == 4:
        cURL.setopt(cURL.URL, url + '/cloud/nodes/' + command_list[2] + '/' + command_list[3])
        cURL.perform()
    else:
        error_msg(f"Command:'{command}' Missing Argument <pod_name>")


#5. Remove existing node
#Syntax : $ cloud rm <node_name>
def cloud_rm(url, command):
    command_list = command.split()

    if len(command_list) == 3:
        cURL.setopt(cURL.URL, url + '/cloud/nodes/remove/' + command_list[2])
        cURL.perform()

    else:
        error_msg(f"Command:'{command}' Missing Argument <pod_name>")


#6. Send files to cloud, this is where we will input bash scripts
#Syntax : $cloud launch <file_name.sh>
def cloud_launch(url, command):
    command_list = command.split()

    if len(command_list) == 3:
        file_path = command_list[2]
        if (os.path.isfile(file_path)):
            files = {'file': open(file_path, 'rb')}
            ret = requests.post(url + '/cloud/jobs/launch', files=files)
            print(ret.text)
        else:
            print('Error: File Not Found. Please enter existing filename.')
    else:
        error_msg(f"Command:'{command}' Missing Argument <pod_name>")


# -------------------- Monitoring -----------------------
#1 list all resource pods in main cluster, name, ID, number of nodes
# Syntax: cloud pod ls
def cloud_pod_ls(url, command):
    command_ls = command.split()
    
    if len(command_ls) == 3:
        cURL.setopt(cURL.URL, url + '/cloud/monitor/pod/ls')
        cURL.perform()
        
    else:
        error_msg(f"Command:'{command}' Not Correct")


#2 list all resource node in specified pod, or in main cluster
# Syntax: cloud node ls [POD_ID]
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


def notImplemented():
    print('Function not yet implemented.')

#Main function
#This is where we put the different 
def main():
    rm_url = sys.argv[1]
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
            return notImplemented()

        #----------- MONOTORING COMMANDS ------------
        
        #1
        elif command.startswith('cloud pod ls'):
            cloud_pod_ls(rm_url, command)

        #2
        elif command.startswith('cloud node ls'):
            cloud_node_ls(rm_url, command)
        
        #3
        elif command.startswith('cloud job log'):
            notImplemented()
        
        #4
        elif command.startswith('cloud log node'):
            notImplemented()

        else:
            error_msg(f"Command:'{command}' Not Recognized")

if __name__ == '__main__':
    main()