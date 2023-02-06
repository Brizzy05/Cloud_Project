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

#3. Remove pod, must five pod name
#Syntax : $ cloud pod rm <pod name>
def cloud_pod_rm(url, command):
    command_list = command.split()

    if len(command_list) == 4:
        cURL.setopt(cURL.URL, url + '/cloud/pods/remove/' + command_list[3])
        cURL.perform()

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


#Send files to cloud, this is where we will input bash scripts
#Syntax : $cloud launch <file_name.sh>
def cloud_launch(url, command):
    command_list = command.split()

    if len(command_list) == 3:
        file_path = command_list[2]
        if (os.path.isfile(file_path)):
            files = {'file': open(file_path, 'rb')}
            ret = requests.post(url + '/cloud/jobs/launch', files=files)
            print(ret.text)

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

        #8
        elif command == 'command pod ls':
            return notImplemented()

        #NODE MANAGEMENT
        #4
        elif command.startswith('cloud register'):
            cloud_register(rm_url, command)
    
        #5
        elif command.startswith('cloud rm'):
            return notImplemented()

        #9
        elif command.startswith('cloud node ls'):
            return notImplemented()

        #10
        elif command.startswith('cloud node ls'):
            return notImplemented()

        #11
        elif command.startswith('cloud log node'):
            return notImplemented()

        #JOB MANAGEMENT
        #6
        elif command.startswith('cloud launch'):
            cloud_launch(rm_url, command)

        #7
        elif command.startswith('cloud abort'):
            return notImplemented()

        #11
        elif command.startswith('cloud job log'):
            return notImplemented()

if __name__ == '__main__':
    main()