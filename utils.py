import json
import socket
import psutil
import random
import os
import requests
import upnp

settings = None


def init_utils(s):
    global settings
    settings = s


# get free space on disk in kilobytes
def get_free_space():
    hdd = psutil.disk_usage('/')
    print(hdd.free / (2**10))


def get_public_ip():
    pub_ip = requests.get('https://api.ipify.org').text
    return pub_ip


# check that port is not in use by any other process and not forwarded by router
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return (s.connect_ex(('localhost', port)) == 0 or upnp.is_port_open(port))


# pick a random port and check that it is not in use
def open_port(decentorage=False):
    opened = False
    port = 0
    while not opened:
        if decentorage:
            port = 50000
            if not is_port_in_use(port):
                opened = True
                settings.decentorage_port
                settings.decentorage_port = port
            else:
                port = port + 1

        else:
            port = random.randint(50005, 60000)
            if not is_port_in_use(port):
                opened = True

        '''            upnp.forwardPort(port, port, router=None, lanip=local_ip,
                                               disable=False, protocol="TCP", time=0, description=None, verbose=True)'''
    return port


# read saved data in the config file
def read_config_file():
    file = open("Cache/config.txt", "r")
    lines = file.readlines()

    settings.local_ip = lines[0].replace(" ", "").strip()
    settings.decentorage_port = int(lines[1])

    file.close()


def update_config_file():
    with open("Cache/config.txt", "w") as f:
        f.write(settings.local_ip + '\n')
        f.write(str(settings.decentorage_port))


def init_app():
    if not os.path.isdir("Data"):
        os.makedirs("Data")

    if not os.path.isdir("Cache"):
        os.makedirs("Cache")
        connections = {}
        connections['connections'] = []
        with open('Cache/connections.txt', 'w') as outfile:
            json.dump(connections, outfile)

        with open('Cache/auth.txt', 'w'):
            pass

        settings.local_ip = upnp.get_my_ip()
        settings.decentorage_port = open_port(True)
        # save local ip and decentorage port to config file
        update_config_file()

    try:
        settings.public_ip = get_public_ip()
    except:
        print("Check your internet connection")
