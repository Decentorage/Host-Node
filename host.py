import threading


from prompt_messages import app_startup_msg, login_prompt
from background_threads import *
from utils import read_config_file, init_utils, init_app
from settings import Settings
from api_requests import init_api_requests
from event_handlers import init_event_handlers
from file_transfer_host import init_file_transfer
settings = Settings()

init_utils(settings)
init_background_threads(settings)
init_api_requests(settings)
init_event_handlers(settings)
init_file_transfer(settings)

init_app()
app_startup_msg()
login_prompt()
read_config_file()

t1 = threading.Thread(target=listen_for_req())
#t2 = threading.Thread(target=heart_beat())
#t3 = threading.Thread(target=track_ip())
#t4 = threading.Thread(target=withdraw())

t1.start()
#t2.start()

while True:
    pass



