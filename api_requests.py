import requests
settings = None


def init_api_requests(s):
    global settings
    settings = s


def login(username, password):
    payload = {"username": username, "password":  password}
    res = requests.post(settings.backend+"/storage/signin", json=payload)
    # Successful login
    if res.status_code == 200:
        print("Login Successful")
        settings.token = res.json()['token']
        # save token to text file
        with open("Cache/auth.txt", 'w') as file:
            file.writelines(res.json()['token'])
        return True

    # Login failed
    else:
        print("Incorrect username or password")
        return False



def send_heart_beat():
    try:
        requests.get(settings.backend+'/storage/heartbeat', headers={"token": settings.token})
    except:
        print("Can not go online")

def withdraw_request(shard):
    payload = {"shard_id": shard}
    try:
        requests.post(settings.backend + "/storage/withdraw", json=payload, headers={"token": settings.token})
    except:
        print("Can not go online")


def update_connection(ip_address, port):
    payload = {"ip_address": ip_address, "port": port}
    try:
        r = requests.post(settings.backend+"/storage/updateConnection", json=payload, headers={"token": settings.token})
    except:
        print("Can not go online")


def done_uploading(shard_id):
    payload = {"shard_id": shard_id}
    try:
        requests.post(settings.backend + "/storage/shardDoneUploading", json=payload, headers={"token": settings.token})
    except:
        print("Can not go online")


def get_active_contracts():
    res = requests.get(settings.backend + "/storage/activeContracts", headers={"token": settings.token})
    print(res)
    return res