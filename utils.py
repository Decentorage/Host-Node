import json
import socket
import psutil
import random
import os
import requests
import upnp
import zmq

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
    used = False
    try:
        context = zmq.Context()
        socket = context.socket(zmq.PAIR)
        socket.bind("tcp://127.0.0.1:" + str(port))
        socket.close()
    except:
        used = True
        socket.close()

    if settings.local:
        return used
    else:
        ret = used or upnp.is_port_open(port)
        return ret


# pick a random port and check that it is not in use
def open_port(decentorage=False):
    opened = False
    port = 50000
    while not opened:
        # if decentorage open port 50000 by default, if already in use, find another port
        if decentorage:
            if not is_port_in_use(port):
                opened = True
                settings.decentorage_port = port
            else:
                port = port + 1

        else:
            port = random.randint(50100, 60000)
            if not is_port_in_use(port):
                opened = True

    # if not running local open port in the router
    if not settings.local:
        upnp.forward_port(port, port, router=None, lanip=None,
                         disable=False, protocol="TCP", duration=0, description=None, verbose=False)

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


# create directories and files needed by the app if
def init_app():
    # Create data directory to store downloaded data shards
    if not os.path.isdir("Data"):
        os.makedirs("Data")

    # create cache directory to store app configuration and active connections
    if not os.path.isdir("Cache"):
        os.makedirs("Cache")
        connections = {}
        connections['connections'] = []

        # create file for active connections and initialize it with empty array of connections
        with open('Cache/connections.txt', 'w') as outfile:
            json.dump(connections, outfile)

        # create file to store authentication token
        with open('Cache/auth.txt', 'w'):
            pass

        # store the current local ip in a variable
        settings.local_ip = upnp.get_my_ip()

        # open port for decentorage to send messages on and save it in a variable
        settings.decentorage_port = open_port(True)

        # save local ip and decentorage port to config file
        update_config_file()

    if not settings.local:
        try:
            # get public ip and store it
            settings.public_ip = get_public_ip()
        except:
            print("Check your internet connection")


def check_decentorage_port():
    used = is_used()
    if used:
        open_port(True)
    else:
        if not settings.local:
            upnp.forward_port(settings.decentorage_port, settings.decentorage_port, router=None, lanip=None,
                              disable=False, protocol="TCP", duration=0, description=None, verbose=False)


def is_used():
    used = False
    try:
        context = zmq.Context()
        socket = context.socket(zmq.PAIR)
        socket.bind("tcp://127.0.0.1:" + str(settings.decentorage_port))
        socket.close()
    except:
        used = True
        socket.close()

    return used