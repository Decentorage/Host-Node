import threading


class Settings:
    def __init__(self):
        self.backend = "http://a9422c7200db042f59a56cdbf90ae1d2-2016308976.eu-central-1.elb.amazonaws.com:5000"
        #self.backend = "http://192.168.1.10:5000"
        self.data_directory = "Data"
        self.cache_directory = "Cache"
        self.local = False
        self.hosted = True
        self.chunk_size = (2**19)
        self.public_ip = ""
        self.local_ip = ""
        self.token = ""
        self.decentorage_port = 0
        self.chunk_timeout = 8000
        self.disconnected_timeout = 60*60*1000
        self.semaphore = threading.Semaphore()
