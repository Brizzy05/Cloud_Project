import pycurl
import sys

cURL = pycurl.Curl()

def cloud_hello(url):
    cURL.setopt(cURL.URL, url)
    cURL.perform()

def cloud_register(url, command):
    command_list = command.split()
    if len(command_list) == 3:
        cURL.setopt(cURL.URL, url + '/cloud/nodes/' + command_list[2])
        cURL.perform()

def main():
    rm_url = sys.argv[1]
    while(1):
        command = input('$ ')
        if command == 'cloud hello':
            cloud_hello(rm_url)
        elif command.startswith('cloud register'):
            cloud_register(rm_url, command)

if __name__ == '__main__':
    main()
