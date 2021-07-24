import api_requests
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import json
import threading
from event_handlers import handle_request


# login message on app startup if no token saved
def login_prompt():
    logged_in = False
    while not logged_in:
        username = input("Username: ")
        password = input("Password: ")
        logged_in = api_requests.login(username, password)


# prompt message on app startup
def app_startup_msg():
    text = "DECENTORAGE"
    my_font = ImageFont.load_default()
    size = my_font.getsize(text)
    img = Image.new("1", size, "black")
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), text, "orange", font=my_font)
    pixels = np.array(img, dtype=np.uint8)
    chars = np.array([' ', '#'], dtype="U1")[pixels]
    strings = chars.view('U' + str(chars.shape[1])).flatten()
    print("\n".join(strings))

    print("\n\n\n")


# read active connections from connections file
def resume_old_connections():
    try:
        connections = {}
        with open('Cache/connections.txt') as json_file:
            connections = json.load(json_file)

        for i in range(len(connections['connections'])):
            request = dict(connections['connections'][i])
            request_thread = threading.Thread(target=handle_request, args=(request,))
            request_thread.start()
    except:
        print("Error")
