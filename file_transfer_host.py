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
    server_socket = context.socket(zmq.PAIR)
    server_socket.bind("tcp://"+settings.local_ip+":"+str(request['port']))

    # send start frame
    start_frame = {"type": "start"}
    start_frame = pickle.dumps(start_frame)
    server_socket.send(start_frame)

    # Read file
    f = open(os.path.join(settings.data_directory, request['shard_id']), "rb")
    # if disconnected, resume sending
    if not start:
        # get from receiver where it has stopped
        resume_frame = server_socket.recv()
        resume_frame = pickle.loads(resume_frame)
        resume_msg = resume_frame["data"]
        f.seek(resume_msg, 0)
        print("Resume sending from ", resume_msg)
        # seek to the last point the user has received
        f.seek(resume_msg, 0)

    data = f.read(1024)
    server_socket.SNDTIMEO = 1000

    # send until the end of the file
    while data:
        try:
            # send data frame to user
            data_frame = {"type": "data", "data": data}
            data_frame = pickle.dumps(data_frame)
            server_socket.send(data_frame)

            # receive Ack from user
            #ack_frame = server_socket.recv()
            #data = f.read(1024)

        # in case of disconnection
        except:
            print("Disconnected")
            try:
                server_socket.close()
                context = zmq.Context()
                server_socket = context.socket(zmq.PAIR)
                server_socket.bind("tcp://" + settings.local_ip + ":" + str(request['port']))
                # time out 1 hour for reconnecting
                server_socket.SNDTIMEO = 1000*60*60

                # wait for user to reconnect
                # if messaege delivered, reconnected to user
                start_frame = {"type": "start"}
                start_frame = pickle.dumps(start_frame)
                server_socket.send(start_frame)
                print("Reconnected successfully")

                # get from receiver where it has stopped
                resume_frame = server_socket.recv()
                resume_frame = pickle.loads(resume_frame)
                resume_msg = resume_frame["data"]
                print(resume_msg)
                f.seek(resume_msg, 0)
                print("Resume sending from ", resume_msg)
                # seek to the last point the user has received

                server_socket.SNDTIMEO = 1000
                f.seek(resume_msg, 0)
                data = f.read(1024)

            except:
                print("Unable to reconnect, terminating connection")
                break

    end_frame = {"type": "END"}
    end_frame = pickle.dumps(end_frame)
    server_socket.send(end_frame)
    # terminate connection after complete transmission
    f.close()
    server_socket.close()
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

    start_frame = {"type": "start"}
    start_frame = pickle.dumps(start_frame)
    server_socket.send(start_frame)

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
    # receive till end of shard or connection failed and unable to reconnect
    server_socket.RCVTIMEO = 1000
    server_socket.SNDTIMEO = 1000

    while True:
        try:
            frame = server_socket.recv()
            frame = pickle.loads(frame)

            if frame["type"] == "data":
                ack_frame = {"type": "ACK"}
                ack_frame = pickle.dumps(ack_frame)
                server_socket.send(ack_frame)

                data = frame["data"]
                f.write(data)

            elif frame["type"] == "END":
                break

        # disconnected
        except:
            # set connection status and recreate socket
            print("connection lost.")
            # try to reconnect
            try:
                server_socket.close()
                context = zmq.Context()
                server_socket = context.socket(zmq.PAIR)
                server_socket.bind("tcp://" + settings.local_ip + ":" + str(request['port']))
                # time out 1 hour for reconnecting
                server_socket.SNDTIMEO = 1000*60*60


                # if messaege delivered, reconnected to user
                start_frame = {"type": "start"}
                start_frame = pickle.dumps(start_frame)
                server_socket.send(start_frame)
                print("re-connection successful")
                server_socket.SNDTIMEO = 1000

                f.close()
                # on reconnect, inform user where it has stopped
                file_size = os.path.getsize(os.path.join(settings.data_directory, request['shard_id']))
                resume_frame = {"type": "resume", "data": file_size}
                resume_frame = pickle.dumps(resume_frame)
                server_socket.send(resume_frame)

                f = open(os.path.join(settings.data_directory, request['shard_id']), "ab")
            except socket.error:
                print("Unable to reconnect, closing connection")
                break

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

