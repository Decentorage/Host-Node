import threading


from prompt_messages import app_startup_msg, login_prompt
from background_threads import *
from utils import read_config_file, init_utils, init_app
from settings import Settings
from api_requests import init_api_requests, update_connection
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
l_ip = upnp.get_my_ip()
if l_ip != settings.local_ip:
    local_ip_change(l_ip)
    update_config_file()

update_connection(settings.local_ip, str(settings.decentorage_port))

t1 = threading.Thread(target=listen_for_req)
t2 = threading.Thread(target=heart_beat)
#t3 = threading.Thread(target=track_ip)
t4 = threading.Thread(target=withdraw)

t1.start()
t2.start()
#t3.start()
t4.start()

while True:
    pass



