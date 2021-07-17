import threading


class Settings:
    def __init__(self):
        self.backend = "http://192.168.1.3:5000"
        self.data_directory = "Data"
        self.cache_directory = "Cache"
        self.public_ip = ""
        self.local_ip = ''
        self.token = ""
        self.decentorage_port = 0
        self.semaphore = threading.Semaphore()
