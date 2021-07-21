import threading


class Settings:
    def __init__(self):
        self.backend = "http://192.168.1.10:5000"
        self.data_directory = "Data"
        self.cache_directory = "Cache"
        self.chunk_size = 10*(2**20)
        self.public_ip = ""
        self.local_ip = ''
        self.token = ""
        self.decentorage_port = 0
        self.semaphore = threading.Semaphore()
