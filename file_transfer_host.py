import socket
from time import sleep
import os
import threading
import json
from settings import data_directory, local_ip, semaphore


def send_data(request, start):
    # file does not exist
    if not os.path.isfile(os.path.join(data_directory, request['shard_id'])):
        return

    # create socket and wait for user to connect
    server_socket = socket.socket()
    server_socket.bind((local_ip, request['port']))
    server_socket.listen(5)
    connection, addr = server_socket.accept()

    # Read file
    f = open(os.path.join(data_directory, request['shard_id']), "rb")
    # if disconnected, resume sending
    if not start:
        # get from receiver where it has stopped
        resume_msg = connection.recv(1024).decode("UTF-8")
        print(resume_msg)
        # seek to the last point the user has received
        f.seek(int(resume_msg), 0)

    data = f.read(1024)
    # send until the end of the file
    while data:
        try:
            connection.send(data)
            data = f.read(1024)
        # in case of disconnection
        except socket.error:
            print("disconnected")
            # wait for user to reconnect
            connection, addr = server_socket.accept()
            # get from receiver where it has stopped
            resume_msg = connection.recv(1024).decode("UTF-8")
            print(resume_msg)
            # seek to the point the user has received
            f.seek(int(resume_msg), 0)
            data = f.read(1024)
            print("reconnecting")

    # terminate connection after complete transmission
    f.close()
    connection.close()
    print("CLOSE PORT : ", request['port'])
    # TODO CLOSE OPEN PORT AT ROUTER

    # remove from text file
    # use semaphore on file to make sure it is not used by another thread
    connections = {}
    semaphore.acquire()
    with open('connections.txt') as json_file:
        connections = json.load(json_file)
    connections['connections'].remove(request)
    with open('connections.txt', 'w') as outfile:
        json.dump(connections, outfile)
    semaphore.release()
    print("Done sending...")


def receive_data(request):
    # make sure Data directory exists, If does not exist create directory
    if not os.path.isdir(data_directory):
        os.makedirs(data_directory)

    # create socket and wait for user to connect
    server_socket = socket.socket()
    server_socket.bind((local_ip, request['port']))
    server_socket.listen(5)
    connection, addr = server_socket.accept()
    connected = True
    f = None

    # if file exists, resume upload, open in append mode, inform sender where it has stopped
    if os.path.isfile(os.path.join(data_directory, request['shard_id'])):
        connection.send(bytes(str(os.path.getsize(os.path.join(data_directory, request['shard_id']))), "UTF-8"))
        f = open(os.path.join(data_directory, request['shard_id']), "ab")
        print(f.tell())

    # if file does not exist, start upload
    else:
        f = open(os.path.join(data_directory, request['shard_id']), "wb")

    # receive till end of shard
    while True:
        try:
            data = connection.recv(1024)
            while data:
                # Done uploading
                if data == bytes("END", "UTF-8"):
                    break

                f.write(data)
                data = connection.recv(1024)

                # Disconnected
                if not data:
                    raise

            f.close()
            break

        # disconnected
        except:
            # set connection status and recreate socket
            connected = False
            print("connection lost... reconnecting")
            # try to reconnect
            while not connected:
                # attempt to reconnect, otherwise sleep for 2 seconds
                try:
                    connection, addr = server_socket.accept()
                    connected = True
                    f.close()
                    # on reconnect, inform user where it has stopped
                    connection.send(bytes(str(os.path.getsize(os.path.join(data_directory, request['shard_id']))), "UTF-8"))
                    f = open(os.path.join(data_directory, request['shard_id']), "ab")
                    print("re-connection successful")
                except socket.error:
                    sleep(2)
                    print("sleep")

    connection.close()
    print("CLOSE PORT : ", request['port'])
    # TODO CLOSE PORT OPENED ON ROUTER

    # remove from text file
    # use semaphore on file to make sure it is not used by another thread
    connections = {}
    semaphore.acquire()
    with open('connections.txt') as json_file:
        connections = json.load(json_file)
    connections['connections'].remove(request)
    with open('connections.txt', 'w') as outfile:
        json.dump(connections, outfile)
    semaphore.release()


#====================================================================================
# read active connections from connections file
def resume_old_connections():
    try:
        connections = {}
        with open('connections.txt') as json_file:
            connections = json.load(json_file)

        for i in range(len(connections['connections'])):
            request = dict(connections['connections'][i])
            request_thread = threading.Thread(target=handle_request, args=(request,))
            request_thread.start()
    except:
        print("Error")
