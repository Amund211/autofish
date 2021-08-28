import time

from .helpers import start_client, stop_client, wait_for_login


def test_login(server, working_fishing_setup, tmp_path):
    client_process = start_client(tmp_path, server)
    wait_for_login(client_process)
    print(stop_client(client_process))


def test_not_fish(server, working_fishing_setup):

    time.sleep(1)
