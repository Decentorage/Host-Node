import socket
from time import sleep
import os
import threading
import json
import upnp
import zmq
import pickle
from api_requests import done_uploading

settings = None


def init_file_transfer(s):
    global settings
    settings = s


def send_data(request, start):
    # file does not exist
    if not os.path.isfile(os.path.join(settings.data_directory, request['shard_id'])):
        print("Shard does not exist")
        return

    # create socket and wait for user to connect
    context = zmq.Context()
    server_socket = context.socket(zmq.PAIR)
    server_socket.bind("tcp://"+settings.local_ip+":"+str(request['port']))

    # send start frame
    start_frame = {"type": "start"}
    start_frame = pickle.dumps(start_frame)
    server_socket.send(start_frame)
    #print("sent start frame")

    # Read file
    f = open(os.path.join(settings.data_directory, request['shard_id']), "rb")
    # if disconnected, resume sending
    if not start:
        print("---------- Resume Sending ----------")
        # get from receiver where it has stopped
        resume_frame = server_socket.recv()
        resume_frame = pickle.loads(resume_frame)
        resume_msg = resume_frame["data"]
        f.seek(resume_msg, 0)
        #print("Resume sending from ", resume_msg)
        # seek to the last point the user has received
        f.seek(resume_msg, 0)
    else:
        print("---------- Sending Data ----------")

    data = f.read(settings.chunk_size)
    server_socket.SNDTIMEO = settings.chunk_timeout
    server_socket.RCVTIMEO = settings.chunk_timeout
    success = True

    # send until the end of the file
    while data:
        try:
            # send data frame to user
            data_frame = {"type": "data", "data": data}
            data_frame = pickle.dumps(data_frame)
            server_socket.send(data_frame)
            #print("sent frame")

            # receive Ack from user
            ack_frame = server_socket.recv()
            ack_frame = pickle.loads(ack_frame)
            #print("Received frame ", ack_frame["type"])
            data = f.read(settings.chunk_size)

        # in case of disconnection
        except:
            print("Disconnected")
            try:
                server_socket.close()
                context = zmq.Context()
                server_socket = context.socket(zmq.PAIR)
                server_socket.bind("tcp://" + settings.local_ip + ":" + str(request['port']))
                # time out 1 hour for reconnecting
                server_socket.SNDTIMEO = settings.disconnected_timeout
                server_socket.RCVTIMEO = settings.disconnected_timeout
                # wait for user to reconnect
                # if messaege delivered, reconnected to user
                print("Trying to reconnect ......")
                start_frame = {"type": "start"}
                start_frame = pickle.dumps(start_frame)
                server_socket.send(start_frame)
                print("Reconnected successfully")

                # get from receiver where it has stopped
                resume_frame = server_socket.recv()
                resume_frame = pickle.loads(resume_frame)
                resume_msg = resume_frame["data"]
                #print(resume_msg)
                f.seek(resume_msg, 0)
                print("Resume sending data")
                # seek to the last point the user has received

                server_socket.SNDTIMEO = settings.chunk_timeout
                server_socket.RCVTIMEO = settings.chunk_timeout
                f.seek(resume_msg, 0)
                data = f.read(settings.chunk_size)

            except:
                success = False
                print("Unable to reconnect, Terminating connection")
                break

    #print("sending end frame")
    if success:
        end_frame = {"type": "END"}
        end_frame = pickle.dumps(end_frame)
        server_socket.send(end_frame)
        print("---------- Done Sending ----------")

    #print("sent end frame")
    # terminate connection after complete transmission
    f.close()
    server_socket.close()
    print("---------- CLOSE PORT : ", request['port'], " ----------")

    # close port at router
    if not settings.local and not settings.hosted:
        upnp.forward_port(request['port'], request['port'], router=None, lanip=None,
                          disable=True, protocol="TCP", duration=0, description=None, verbose=False)

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


def receive_data(request):
    # make sure Data directory exists, If does not exist create directory
    if not os.path.isdir(settings.data_directory):
        os.makedirs(settings.data_directory)

    # create socket and wait for user to connect
    context = zmq.Context()
    server_socket = context.socket(zmq.PAIR)
    server_socket.bind("tcp://" + settings.local_ip + ":" + str(request['port']))

    start_frame = {"type": "start"}
    start_frame = pickle.dumps(start_frame)
    #print("sending start frame")
    server_socket.send(start_frame)
    #print("start frame sent")

    connected = True
    f = None

    # if file exists, resume upload, open in append mode, inform sender where it has stopped
    if os.path.isfile(os.path.join(settings.data_directory, request['shard_id'])):
        resume_msg = os.path.getsize(os.path.join(settings.data_directory, request['shard_id']))
        resume_frame = {"type": "resume", "data": resume_msg}
        resume_frame = pickle.dumps(resume_frame)
        server_socket.send(resume_frame)
        f = open(os.path.join(settings.data_directory, request['shard_id']), "ab")
        #print(f.tell())

    # if file does not exist, start upload
    else:
        f = open(os.path.join(settings.data_directory, request['shard_id']), "wb")

    # receive till end of shard or connection failed and unable to reconnect
    server_socket.RCVTIMEO = settings.chunk_timeout
    server_socket.SNDTIMEO = settings.chunk_timeout
    success = True
    print("---------- Receiving Data ----------")
    while True:
        try:
            frame = server_socket.recv()
            frame = pickle.loads(frame)
            #print("received frame of type ", frame["type"])
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
            print("Disconnected")
            # try to reconnect
            try:
                server_socket.close()
                context = zmq.Context()
                server_socket = context.socket(zmq.PAIR)
                server_socket.bind("tcp://" + settings.local_ip + ":" + str(request['port']))
                # time out 1 hour for reconnecting
                server_socket.SNDTIMEO = settings.disconnected_timeout
                print("Trying to reconnect ......")


                # if messaege delivered, reconnected to user
                start_frame = {"type": "start"}
                start_frame = pickle.dumps(start_frame)

                server_socket.send(start_frame)
                print("Reconnected successfully")
                server_socket.SNDTIMEO = settings.chunk_timeout
                server_socket.RCVTIMEO = settings.chunk_timeout

                f.close()
                # on reconnect, inform user where it has stopped
                file_size = os.path.getsize(os.path.join(settings.data_directory, request['shard_id']))
                resume_frame = {"type": "resume", "data": file_size}
                resume_frame = pickle.dumps(resume_frame)
                server_socket.send(resume_frame)
                print("Resume receiving data")
                #print("sent resume frame")
                f = open(os.path.join(settings.data_directory, request['shard_id']), "ab")
            except socket.error:
                print("Unable to reconnect, Terminating connection")
                success = False
                break

    f.close()
    server_socket.close()

    if success:
        print("---------- Done Receiving ----------")
        done_uploading(request["shard_id"])

    print("---------- CLOSE PORT : ", request['port'], " ----------")

    # Close port at router
    if not settings.local and not settings.hosted:
        upnp.forward_port(request['port'], request['port'], router=None, lanip=None,
                          disable=True, protocol="TCP", duration=0, description=None, verbose=False)

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

