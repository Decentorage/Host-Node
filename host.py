import threading
import time
from time import sleep
import hashlib
import os.path
import socket
import random
import requests
import json
from settings import semaphore, backend, token
from requests import get
import portforwardlib
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from file_transfer_host import send_data, receive_data

# public_ip = get('https://api.ipify.org').text
public_ip = ""
local_ip = ""
decentorage_port = 0
open_ports = []
data_directory = "Data"


def update_connection(ip_address, port):
    payload = {"ip_address": ip_address, "port": port}
    r = requests.post(backend+"/storage/updateConnection", json=payload, headers={"token": token})
    print(r.text)


def withdraw_request(payload):
    requests.post(backend + "/storage/withdraw", json=payload)


def withdraw():
    shards = os.listdir(data_directory)
    for shard in shards:
        payload = {"shard_id": shard}
        withdraw_request(payload)

    # send withdraw every 12 hours
    sleep(12*60*60)


def send_heart_beat():
    requests.get(backend+'/storage/heartbeat', headers={"token": token})


def login_prompt():
    logged_in = False
    while not logged_in:
        username = input("Username: ")
        password = input("Password: ")
        logged_in = login(username, password)


def login(username, password):
    payload = {"username": username, "password":  password}
    res = requests.post(backend+"/storage/signin", json=payload)
    # Successful login
    if res.status_code == 200:
        print("Login Successful")
        global token
        token = res.json()['token']
        # save token to text file
        with open("auth.txt", 'w') as file:
            file.writelines(res.json()['token'])
        return True

    # Login failed
    else:
        print("Incorrect username or password")
        return False

# thread to send heartbeat to decentorage every second
def heart_beat():
    while True:
        pload = {'username': 'shady', 'password': '1234'}
        r = requests.post(backend, data=pload)

        # TODO send to decentorage
        print("heartbeat")
        time.sleep(5)


# sends message to decentorage node to notify public ip change
def public_ip_change():
    # TODO
    print("IP TO DECENTORAGE")
    # send sth to decentorage node


# on audit hash the file concatenated with the received salt
def audit(salt, request):
    sha256_hash = hashlib.sha256()
    buffer_size = 65536  # read data in 64kb chunks
    with open(os.path.join(data_directory,request['shard_id']), "rb") as fn:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: fn.read(buffer_size), b""):
            sha256_hash.update(byte_block)
        print(sha256_hash.hexdigest())
        sha256_hash.update(salt.encode())
        print(sha256_hash.hexdigest())
        # TODO send audit result to decentorage


# if ip changes disable current port forwarding and create new port forwarding
def local_ip_change(new_local_ip):
    print("helwa")
    # disable port forward on old ip for decentorage port
    portforwardlib.forwardPort(decentorage_port, decentorage_port, router=None, lanip=local_ip,
                               disable=True, protocol="TCP", duration=0, description=None, verbose=True)
    # port forward on new ip for decentorage port
    portforwardlib.forwardPort(decentorage_port, decentorage_port, router=None, lanip=new_local_ip,
                               disable=False, protocol="TCP", duration=0, description=None, verbose=True)

    for i in range(len(open_ports)):
        # disable port forward on old ip for open ports with clients
        portforwardlib.forwardPort(open_ports[i], open_ports[i], router=None, lanip=local_ip,
                                   disable=True, protocol="TCP", duration=0, description=None, verbose=True)
        # port forward on new ip for open ports with clients
        portforwardlib.forwardPort(open_ports[i], open_ports[i], router=None, lanip=new_local_ip,
                                   disable=False, protocol="TCP", duration=0, description=None, verbose=True)


# track changes in ip
def track_ip():
    while True:
        p_ip = get('https://api.ipify.org').text    # use Decentorage to get ip
        if p_ip != public_ip:
            public_ip_change()

        l_ip = portforwardlib.get_my_ip()
        if l_ip != local_ip:
            local_ip_change(l_ip)

        time.sleep(1)


# main thread waits for a request from decentorage node (audit/download/upload)
def listen_for_req():
    print("waiting for req")
    server_socket = socket.socket()
    server_socket.bind((local_ip, 54545))
    server_socket.listen(5)
    while True:
        connection, addr = server_socket.accept()
        request = connection.recv(1024).decode("utf-8")
        request = json.loads(request)
        request_thread = threading.Thread(target=handle_request, args=(request,))
        request_thread.start()


# thread to handle requests
def handle_request(request):
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
            semaphore.acquire()
            with open('connections.txt') as json_file:
                connections = json.load(json_file)
            connections['connections'].append(request)
            with open('connections.txt', 'w') as outfile:
                json.dump(connections, outfile)
            semaphore.release()
            # TODO
            # send port to decentorage
        except:
            print("Connections file corrupted")

    if request['type'] == 'upload':
        receive_data(request)
    elif request['type'] == 'download':
        send_data(request, start)
    elif request['type'] == 'audit':
        audit(request)


# check that port is not in use
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


# pick a random port and check that it is not in use
def open_port(decentorage=False):
    print("opening port")
    opened = False
    port = 0
    while not opened:
        port = random.randint(50000, 60000)
        if not is_port_in_use(port):
            portforwardlib.forwardPort(port, port, router=None, lanip=local_ip,
                                       disable=False, protocol="TCP", time=0, description=None, verbose=True)
            opened = True

    if decentorage:
        decentorage_port = port
    else:
        open_ports.append(port)

    return port


# read saved data in the config file
def read_config_file():
    print("file Exists")
    file = open("config.txt", "r")
    lines = file.readlines()

    read_local_ip = lines[0]
    read_decentorage_port = int(lines[1])

    for i in range(2, len(lines)):
        open_ports.append(int(lines[i]))

    file.close()
    return read_local_ip, read_decentorage_port


# prompt message on app startup
def prompt_msg():
    text = "DECENTORAGE"
    my_font = ImageFont.truetype("verdanab.ttf", 12)
    size = my_font.getsize(text)
    img = Image.new("1", size, "black")
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), text, "orange", font=my_font)
    pixels = np.array(img, dtype=np.uint8)
    chars = np.array([' ', '#'], dtype="U1")[pixels]
    strings = chars.view('U' + str(chars.shape[1])).flatten()
    print("\n".join(strings))

    print("\n\n\n")


def update_config_file():
    with open("config.txt", "w") as f:
        f.write(local_ip + '\n')
        f.write(str(decentorage_port) + '\n')
        for i in range(len(open_ports)):
            f.write(str(open_ports[i]) + '\n')


def open_socket(port):
    print("sock")
# ========================= Handling config file ============================
'''
file_exists = os.path.isfile("config.txt")

if file_exists:
    # do something
    local_ip, decentorage_port = read_config_file()
    print(local_ip)
    print(decentorage_port)
    print(open_ports)

    current_ip = portforwardlib.get_my_ip()

    # if ip changes disable old configurations and initiate new port forwards
    if current_ip != local_ip:
        print("btengan")
        #local_ip_change(current_ip)
else:
    # create config file and add local ip and decentorage port to it
    print("Creating file")
    local_ip = portforwardlib.get_my_ip()
    f = open("config.txt", "w")
    f.write(local_ip + "\n")
    # open port for decontorage
    open_port(decentorage=True)
    f.write(str(decentorage_port) + "\n")

# send public ip and port to decentorage
public_ip_change()
#===========================================================================
update_config_file()'''



#===========================================================================
#t1 = threading.Thread(target=heart_beat())
#t2 = threading.Thread(target=listen_for_req())

#audit("lakjhflahlaf", "image.jpg")
'''print(token)
login("shady", "1234")
print(token)

update_connection("192.168.1.5", "50504")'''



import psutil
def get_free_space():
    hdd = psutil.disk_usage('/')
    print(hdd.free / (2**10))