import threading
import time
import hashlib
import os.path
import socket
import random
from requests import get
import portforwardlib
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# public_ip = get('https://api.ipify.org').text
public_ip = ""
local_ip = ""
decentorage_port = 0
open_ports = []


# thread to send heartbeat to decentorage every second
def heart_beat():
    while True:
        print("heartbeat")
        time.sleep(5)


# sends message to decentorage node to notify public ip change
def public_ip_change():
    print("manga")
    # send sth to decentorage node


# on audit hash the file concatenated with the received salt
def audit(salt, filename):
    sha256_hash = hashlib.sha256()
    buffer_size = 65536  # read data in 64kb chunks
    with open(filename, "rb") as fn:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: fn.read(buffer_size), b""):
            sha256_hash.update(byte_block)
        print(sha256_hash.hexdigest())
        sha256_hash.update(salt.encode())
        print(sha256_hash.hexdigest())


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
    serverSocket = socket.socket()
    serverSocket.bind((local_ip, decentorage_port))
    serverSocket.listen(1)
    while True:





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

    print("\n\n\nPlease Login First")
    username = input("Username: ")
    password = input("Password: ")


def update_config_file():
    with open("config.txt", "w") as f:
        f.write(local_ip + '\n')
        f.write(str(decentorage_port) + '\n')
        for i in range(len(open_ports)):
            f.write(str(open_ports[i]) + '\n')


def send_file():
    print("sending")


def receive_file():
    print("receiving")


def open_socket(port):
    print("sock")
# ========================= Handling config file ============================

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
update_config_file()



#===========================================================================
#t1 = threading.Thread(target=heart_beat())
#t2 = threading.Thread(target=listen_for_req())

#audit("lakjhflahlaf", "image.jpg")
