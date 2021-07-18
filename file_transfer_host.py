import socket
from time import sleep
import os
import threading
import json
import zmq
import pickle

settings = None


def init_file_transfer(s):
    global settings
    settings = s


def send_data(request, start):
    # file does not exist
    if not os.path.isfile(os.path.join(settings.data_directory, request['shard_id'])):
        return

    # create socket and wait for user to connect
    context = zmq.Context()
    socket = context.socket(zmq.PAIR)
    socket.bind("tcp://"+settings.local_ip+":"+str(request['port']))

    # server_socket = socket.socket()
    # server_socket.bind((settings.local_ip, request['port']))
    # server_socket.listen(5)
    # connection, addr = server_socket.accept()

    # Read file
    f = open(os.path.join(settings.data_directory, request['shard_id']), "rb")
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
    settings.semaphore.acquire()
    with open('Cache/connections.txt') as json_file:
        connections = json.load(json_file)
    connections['connections'].remove(request)
    with open('Cache/connections.txt', 'w') as outfile:
        json.dump(connections, outfile)
    settings.semaphore.release()
    print("Done sending...")


def receive_data(request):
    # make sure Data directory exists, If does not exist create directory
    if not os.path.isdir(settings.data_directory):
        os.makedirs(settings.data_directory)

    # create socket and wait for user to connect
    context = zmq.Context()
    server_socket = context.socket(zmq.PAIR)
    server_socket.bind("tcp://"+settings.local_ip+":"+str(request['port']))
    
    connected = True
    f = None

    # if file exists, resume upload, open in append mode, inform sender where it has stopped
    # TODO resume sending
    if os.path.isfile(os.path.join(settings.data_directory, request['shard_id'])):
        resume_msg = os.path.getsize(os.path.join(settings.data_directory, request['shard_id']))
        resume_frame = {"type": "resume", "data": resume_msg}
        resume_frame = pickle.dumps(resume_frame)
        server_socket.send(resume_frame)
        f = open(os.path.join(settings.data_directory, request['shard_id']), "ab")
        print(f.tell())

    # if file does not exist, start upload
    # else:
    f = open(os.path.join(settings.data_directory, request['shard_id']), "wb")
    # receive till end of shard
    try:
        while True:
            frame = server_socket.recv()
            if not frame:
                print("disconnected")
                raise
            frame = pickle.loads(frame)
            if frame["type"] == "data":
                data = frame["data"]
                f.write(data)
            elif frame["type"] == "END":
                break

    # disconnected
    except:
        # set connection status and recreate socket
        connected = False
        print("connection lost.")
        # try to reconnect
        while not connected:
            # attempt to reconnect, otherwise sleep for 2 seconds
            try:
                server_socket.bind("tcp://" + settings.local_ip + ":" + str(request['port']))
                connected = True
                f.close()
                # on reconnect, inform user where it has stopped
                file_size = os.path.getsize(os.path.join(settings.data_directory, request['shard_id']))
                resume_frame = {"type": "resume", "data": file_size}
                resume_frame = pickle.dumps(resume_frame)
                server_socket.send(resume_frame)

                f = open(os.path.join(settings.data_directory, request['shard_id']), "ab")
                print("re-connection successful")
            except socket.error:
                sleep(2)
                print("sleep")

    f.close()
    server_socket.close()
    print("CLOSE PORT : ", request['port'])
    # TODO CLOSE PORT OPENED ON ROUTER

    # remove from text file
    # use semaphore on file to make sure it is not used by another thread
    connections = {}
    settings.semaphore.acquire()
    with open('Cache/connections.txt') as json_file:
        connections = json.load(json_file)
    connections['connections'].remove(request)
    with open('Cache/connections.txt', 'w') as outfile:
        json.dump(connections, outfile)
    settings.semaphore.release()

