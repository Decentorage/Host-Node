import threading

public_ip = ""
local_ip = ""
backend = "http://192.168.1.7:5000"
decentorage_port = 0
open_ports = []
data_directory = "Data"
semaphore = threading.Semaphore()
token = ""