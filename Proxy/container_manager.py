import docker 

client = docker.from_env()

try:
    network = client.networks.get('container_network')

except docker.errors.NotFound:
    network = client.networks.create('container_network', driver='bridge')
    