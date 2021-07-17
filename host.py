import threading
import time
from time import sleep
import hashlib
import os.path
import socket
import random
import requests
import json
from requests import get
import portforwardlib
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from file_transfer_host import send_data, receive_data
import api_requests
from prompt_messages import app_startup_msg, login_prompt
from background_threads import *
from utils import read_config_file, init_utils, init_app
from settings import Settings
from api_requests import init_api_requests
from event_handlers import init_event_handlers
from file_transfer_host import init_file_transfer
settings = Settings()

init_utils(settings)
init_background_threads(settings)
init_api_requests(settings)
init_event_handlers(settings)
init_file_transfer(settings)

init_app()
app_startup_msg()
login_prompt()
read_config_file()

t1 = threading.Thread(target=listen_for_req())
#t2 = threading.Thread(target=heart_beat())

t1.start()
#t2.start()

while True:
    pass

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


