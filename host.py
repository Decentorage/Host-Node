import threading


from prompt_messages import app_startup_msg, login_prompt, resume_old_connections
from background_threads import *
from utils import read_config_file, init_utils, init_app, check_decentorage_port
from settings import Settings
from api_requests import init_api_requests, update_connection
from event_handlers import init_event_handlers
from file_transfer_host import init_file_transfer
import time
import click



@click.command()
@click.option('--username')
@click.option('--password')
@click.option('--starting_port', default=str(50000))
def run(username, password, starting_port):
    settings = Settings()
    settings.starting_port = starting_port
    init_utils(settings)
    init_background_threads(settings)
    init_api_requests(settings)
    init_event_handlers(settings)
    init_file_transfer(settings)
    app_startup_msg()               # print startup message
    init_app()                      # create directories and files if not exist and read public ip if not local mode
    login_prompt(username, password)                  # login and save token
    read_config_file()              # load IP and port
    track_ip(True)                  # check that IP read from file is same as current IP
    check_decentorage_port()

    update_connection(settings.public_ip, str(settings.decentorage_port))
    resume_old_connections()

    t1 = threading.Thread(target=listen_for_req)
    t2 = threading.Thread(target=heart_beat)
    #t3 = threading.Thread(target=track_ip)
    t4 = threading.Thread(target=withdraw)

    t1.start()
    t2.start()
    #t3.start()
    t4.start()
    # while True:
    #     time.sleep(100)
    t1.join()
    t2.join()
    t4.join()


if __name__ == '__main__':
    run()