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
 
#Register new node, possibility to give pod name 
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

#Main function
#This is where we put the different 
def main():
    rm_url = sys.argv[1]
    while(1):
        command = input('$ ')
        if command == 'exit':
            exit()
        elif command == 'cloud hello':
            cloud_hello(rm_url)
        elif command.startswith('cloud register'):
            cloud_register(rm_url, command)
        elif command.startswith('cloud launch'):
            cloud_launch(rm_url, command)

if __name__ == '__main__':
    main()
