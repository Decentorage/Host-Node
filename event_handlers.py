import api_requests
import hashlib
from utils import open_port
import json
import os
import upnp
from file_transfer_host import send_data, receive_data

settings = None


def init_event_handlers(s):
    global settings
    settings = s


# thread to handle requests
def handle_request(request, connection=None):
    if request['type'] == 'audit':
        res = audit(request, connection)
        connection.send(bytes(res, "UTF-8"))
        return

    # request from decentorage
    start = False
    if request['port'] == 0:
        # open port
        start = True
        port = open_port(False)

        # add port to connections dictionary
        print("OPENED PORT : ", port)
        request['port'] = port
        try:
            connections = {}
            print("waiit for semaphore")
            settings.semaphore.acquire()

            print("got semaphore")
            with open('Cache/connections.txt') as json_file:
                connections = json.load(json_file)
            connections['connections'].append(request)
            with open('Cache/connections.txt', 'w') as outfile:
                json.dump(connections, outfile)
            settings.semaphore.release()
            # TODO
            # send port to decentorage
            connection.send(bytes(str(port), "UTF-8"))
        except Exception as e:
            print(e)
            print("Connections file corrupted")

    if request['type'] == 'upload':
        receive_data(request)
    elif request['type'] == 'download':
        send_data(request, start)


# sends message to decentorage node to notify public ip change
def public_ip_change():
    api_requests.update_connection()


# on audit hash the file concatenated with the received salt
def audit(salt, request):
    sha256_hash = hashlib.sha256()
    buffer_size = 65536  # read data in 64kb chunks
    with open(os.path.join(settings.data_directory, request['shard_id']), "rb") as fn:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: fn.read(buffer_size), b""):
            sha256_hash.update(byte_block)
        #print(sha256_hash.hexdigest())
        sha256_hash.update(salt.encode())
        return sha256_hash.hexdigest()
        # TODO send audit result to decentorage


# if ip changes disable current port forwarding and create new port forwarding
def local_ip_change(new_local_ip):
    print("Local IP changed, Change port mappings on router")
    # disable port forward on old ip for decentorage port
    upnp.forward_port(settings.decentorage_port, settings.decentorage_port, router=None, lanip=settings.local_ip,
                               disable=True, protocol="TCP", duration=0, description=None, verbose=True)
    # port forward on new ip for decentorage port
    upnp.forward_port(settings.decentorage_port, settings.decentorage_port, router=None, lanip=new_local_ip,
                               disable=False, protocol="TCP", duration=0, description=None, verbose=True)


    settings.semaphore.acquire()
    with open('Cache/connections.txt') as json_file:
        connections = json.load(json_file)
    settings.semaphore.release()

    for i in range(len(connections['connections'])):
        # disable port forward on old ip for open ports with clients
        upnp.forwardPort(connections['connections'][i]['port'], connections['connections'][i]['port'], router=None, lanip=settings.local_ip,
                                   disable=True, protocol="TCP", duration=0, description=None, verbose=True)
        # port forward on new ip for open ports with clients
        upnp.forwardPort(connections['connections'][i]['port'], connections['connections'][i]['port'], router=None, lanip=new_local_ip,
                                   disable=False, protocol="TCP", duration=0, description=None, verbose=True)

    settings.local_ip = new_local_ip