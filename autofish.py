#! /usr/bin/env python3

import sys
from argparse import ArgumentParser, FileType
from datetime import datetime
from time import sleep

from config import read_config
from fishing import setup_connection, use_item
from gamedata import get_bobber_splash_id
from login import (
    authenticate_user,
    create_auth_token,
    get_host_address,
    read_profile,
    update_profile,
)
from utils import print_timestamped


def get_options():
    parser = ArgumentParser()

    parser.add_argument(
        "-c",
        "--config",
        help="Path to the .toml config-file",
        type=FileType("r", encoding="UTF-8"),
        default="config.toml",
    )

    parser.add_argument(
        "-g",
        "--gamedata",
        help="Path to the .json gamedata cachefile",
        type=FileType("a+", encoding="UTF-8"),
        default="gamedata.json",
    )

    return parser.parse_args()


def check_for_sleep(timeout, state):
    """Wait for `timeout` seconds while checking if someone has requested to sleep"""

    # Seconds the client has been offline due to a sleep-request
    offline_time = 0

    # Sleep for the fractional part of `timeout`
    sleep(timeout % 1)

    time_waited = 1
    while time_waited <= timeout:
        sleep(1)
        time_waited += 1

        if state["sleep_requested"]:
            offline_time += 1
            # Keep the loop from exiting before we have fulfilled the sleep-request
            time_waited = -1

        if offline_time > state["sleep_time"]:
            # Sleep-request fulfilled
            state["sleep_requested"] = False

            # Hack to prevent the client from thinking the rod timed out when
            # we were logged off
            state["recently_cast"] = True

            # Return to main loop to reconnect
            return


def main():
    options = get_options()

    try:
        CONFIG = read_config(fp=options.config)
    except RuntimeError as e:
        print(e)
        sys.exit(1)
    finally:
        options.config.close()

    OPTIONS = CONFIG["options"]
    HOST = CONFIG["host"]

    # Get sound id and close file pointer
    splash_id = get_bobber_splash_id(HOST["version"], fp=options.gamedata)

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
        username = auth_token.profile.name
    else:
        print("Playing in offline mode - skipping authentication")
        if OPTIONS.get("username", None) is None:
            OPTIONS["username"] = input("What username do you want to play with? ")
        auth_token = None
        username = OPTIONS["username"]

    # Program state
    start_time = datetime.now()
    timeouts = []

    # Stores the potential durability that has been taken off the rod due to timeouts
    # minus the durability recovered by mending
    durability_count = 0

    state = {
        "amount_caught": 0,
        "recently_cast": False,
        "sleep_requested": False,
        "connection": None,
        "connected": False,
        "bobber_splash_id": splash_id,
    }

    state.update(OPTIONS)

    try:
        # Reconnect indefinitely
        while True:
            try:
                address, port = get_host_address(HOST, auth_token)
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
                username=username,
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
                check_for_sleep(OPTIONS["fish_timeout"], state)
                if not state["recently_cast"]:
                    # Timed out
                    if durability_count >= OPTIONS["durability_threshold"]:
                        # Log out to save the rod
                        print_timestamped(
                            f"Too many timeouts; rod has, at worst, taken ~{durability_count} "
                            "points of durability. Logging out to save it."
                        )
                        # Ugly hack to display results of session before exiting
                        raise KeyboardInterrupt

                    print_timestamped(
                        f"Timed out; more than {OPTIONS['fish_timeout']} seconds "
                        "since last catch. Using the rod once."
                    )
                    timeouts.append(datetime.now())
                    use_item(state)

                    # Reeling in a mob costs 5 durability
                    # This can be done at most every other use of the rod
                    durability_count += 5 / 2
                else:
                    # Fishing grants 1-6 exp which each gives 2 durability
                    # The rod cannot be repaired past fully repaired
                    durability_count = max(0, durability_count - 2)

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
