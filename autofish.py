#! /usr/bin/env python3

from realmip import loop_realm_address

import sys
from time import sleep
from datetime import datetime
from argparse import ArgumentParser, FileType

from utils import print_timestamped
from config import read_config
from fishing import setup_connection, use_item
from login import (
    read_profile,
    create_auth_token,
    authenticate_user,
    update_profile,
    get_host_address,
)


def get_options():
    parser = ArgumentParser()

    parser.add_argument(
        "config_path",
        metavar="CONFIG",
        help="Path to the .toml config-file",
        type=FileType("r", encoding="UTF-8"),
        default="config.toml",
        nargs="?",
    )

    return parser.parse_args()


def main():
    options = get_options()

    try:
        CONFIG = read_config(fp=options.config_path)
    except RuntimeError as e:
        print(e)
        sys.exit(1)
    else:
        fp.close()
    OPTIONS = CONFIG["options"]
    HOST = CONFIG["host"]
    sys.exit(0)

    # Read stored profile
    has_token, user_data = read_profile(OPTIONS["profile_path"])

    if not HOST["offline"]:
        # Validate/refresh token
        if has_token:
            auth_token = create_auth_token(user_data)

        # Client has no token, or the token was invalid
        if not has_token or not auth_token:
            print("Authenticate with username+password")
            auth_token = authenticate_user(user_data)

        # Update profile and write to disk
        update_profile(OPTIONS["profile_path"], user_data, auth_token)
    else:
        print("Playing in offline mode - skipping authentication")
        if OPTIONS["username"] is None:
            OPTIONS["username"] = input("What username do you want to play with? ")
        auth_token = None

    # Program state
    start_time = datetime.now()
    timeouts = []

    state = {
        "amount_caught": 0,
        "recently_cast": False,
        "connection": None,
        "connected": False,
    }

    state.update(OPTIONS)

    try:
        # Reconnect indefinitely
        while True:
            try:
                address, port = get_host_address(HOST, realm_name)
            except RuntimeError as e:
                print(e)
                sys.exit(1)

            # Establish connection
            state["connection"] = setup_connection(
                address=address,
                port=port,
                version=HOST["version"],
                auth_token=auth_token,
                state=state,
                username=OPTIONS["username"],
            )
            try:
                state["connection"].connect()
            except ConnectionRefusedError as e:
                print(e)
                sys.exit(1)

            state["connected"] = True

            while state["connected"]:
                # Check for timeouts, fishing is handled by eventlisteners
                state["recently_cast"] = False
                sleep(OPTIONS["fish_timeout"])
                if not state["recently_cast"]:
                    # Timed out
                    print_timestamped(
                        f"Timed out; more than {OPTIONS['fish_timeout']} seconds "
                        "since last catch. Using the rod once."
                    )
                    timeouts.append(datetime.now())
                    state["recently_cast"] = True
                    use_item(state)

    except KeyboardInterrupt:
        print_timestamped("Ending session")
        state["connection"].disconnect()

        time_diff = datetime.now() - start_time
        seconds = time_diff.days * 24 * 60 * 60 + time_diff.seconds

        print("Time elapsed:", time_diff)
        print("Fish caught: " + str(state["amount_caught"]))
        print("Fish/minute: " + str(state["amount_caught"] / seconds * 60))

        if state["amount_caught"] != 0:
            print("Seconds/fish: " + str(seconds / state["amount_caught"]))
        if len(timeouts) != 0:
            print("Timeouts:")
            for t in timeouts:
                print("\t" + str(t))
        sys.exit()


if __name__ == "__main__":
    main()
