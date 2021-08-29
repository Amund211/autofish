import time

from mcrcon import MCRcon

from .constants import FISHING_USERNAME
from .helpers import setup_for_fishing, start_client, stop_client, wait_for_login


def test_login(server, tmp_path):
    client_process = start_client(tmp_path, server)
    wait_for_login(client_process)

    with MCRcon(server.host, server.rcon_password, server.rcon_port) as mcr:
        response = mcr.command("/list")

    assert FISHING_USERNAME in response
    stop_client(client_process)


def test_catches_fish(server, tmp_path, setup_spawn):
    setup_for_fishing(tmp_path, server)
    client_process = start_client(tmp_path, server)
    wait_for_login(client_process)

    # time.sleep(60)
    print(stop_client(client_process))
