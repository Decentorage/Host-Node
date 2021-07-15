import requests


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



def send_heart_beat():
    requests.get(backend+'/storage/heartbeat', headers={"token": token})


def withdraw_request(payload):
    requests.post(backend + "/storage/withdraw", json=payload, headers={"token": token})


def update_connection(ip_address, port):
    payload = {"ip_address": ip_address, "port": port}
    r = requests.post(backend+"/storage/updateConnection", json=payload, headers={"token": token})
    print(r.text)