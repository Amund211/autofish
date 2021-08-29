import time
from collections import deque

import pytest
from mcrcon import MCRcon

from .constants import DEFAULT_CONFIG, FISHING_USERNAME
from .helpers import setup_for_fishing, start_client, stop_client, wait_for_login


def test_login(server, tmp_path):
    """Assert that the client is able to log in properly"""
    client_process = start_client(tmp_path, server)
    wait_for_login(client_process)

    with MCRcon(server.host, server.rcon_password, server.rcon_port) as mcr:
        response = mcr.command("/list")

    assert FISHING_USERNAME in response

    stop_client(client_process)


@pytest.mark.parametrize("should_greet", (False, True))
@pytest.mark.parametrize("should_sleep", (False, True))
def test_messages(server, tmp_path, should_greet, should_sleep):
    """Assert that the greet/sleep helper messages are sent according to preference"""
    if server.process is None:
        pytest.skip(
            "We need to read from the server process to determine if messages were "
            "sent. This does not work when using an external server for the tests."
        )

    SENTINEL_STRING = "AUTOFISH-TESTING-SENTINEL"

    did_message = ("did", "did not")
    should_message = ("should not", "should")

    # Clear output from other tests
    with MCRcon(server.host, server.rcon_password, server.rcon_port) as mcr:
        mcr.command(f"/say START-{SENTINEL_STRING}")

    while server.process.poll() is None and f"[Rcon] START-{SENTINEL_STRING}" not in (
        line := server.process.stdout.readline()
    ):
        pass

    # Start the client
    options = {"sleep_helper": should_sleep}
    if not should_greet:
        options["greet_message"] = ""  # Set to empty string to disable greeting

    client_process = start_client(tmp_path, server, options_override=options)
    wait_for_login(client_process)

    time.sleep(1)  # Give the server time to receive the chat packets

    with MCRcon(server.host, server.rcon_password, server.rcon_port) as mcr:
        mcr.command(f"/say {SENTINEL_STRING}")

    sent_messages = deque()
    while server.process.poll() is None and f"[Rcon] {SENTINEL_STRING}" not in (
        line := server.process.stdout.readline()
    ):
        if f"<{FISHING_USERNAME}>" in line:
            sent_messages.append(line)

    def message_has_been_sent(messages, message):
        return any(message in m for m in messages)

    if should_greet != message_has_been_sent(
        sent_messages, DEFAULT_CONFIG["options"]["greet_message"]
    ):
        stop_client(client_process)
        raise RuntimeError(
            f"Client process {did_message[should_greet]} greet the server when it "
            f"{should_message[should_greet]} have"
        )

    if should_sleep != message_has_been_sent(
        sent_messages, DEFAULT_CONFIG["options"]["sleep_message"]
    ):
        stop_client(client_process)
        raise RuntimeError(
            f"Client process {did_message[should_sleep]} inform the server of the "
            f"sleep helper when it {should_message[should_sleep]} have"
        )

    stop_client(client_process)


def test_catches_fish(server, tmp_path, setup_spawn):
    setup_for_fishing(tmp_path, server)
    client_process = start_client(tmp_path, server)
    wait_for_login(client_process)

    # time.sleep(60)
    print(stop_client(client_process))
