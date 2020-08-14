import sys
from time import sleep
from json import JSONDecodeError

import requests

from utils import error_msg, print_timestamped

REALMS_ENDPOINT = "https://pc.realms.minecraft.net"


def get_realm_address(name, uuid, access_token, realm_name, realms=REALMS_ENDPOINT):
    """
    Return IP address and port of realm with given name.

    Raises ValueError if no realm with given name is found.
    Raises KeyError if a key is missing in the request data.
    Raises RuntimeError if any request fails.
    """
    # Constructing session id cookie
    sid_cookie = {}
    sid_cookie["version"] = "1.13.1"
    sid_cookie["user"] = name
    sid_cookie["sid"] = f"token:{access_token}:{uuid}"

    # Requesting list of realms
    worlds_response = requests.get(realms + "/worlds", cookies=sid_cookie)
    if not worlds_response:
        raise RuntimeError(error_msg(worlds_response) + "\nAre you authenticated?")

    try:
        worlds_data = worlds_response.json()
        worlds = worlds_data["servers"]
    except (KeyError, JSONDecodeError):
        raise KeyError(
            "Key 'servers' not found in response from /worlds endpoint."
            f"Response data: '{worlds_data}'"
        )

    for world in worlds:
        if world["name"] == realm_name:
            realmID = world["id"]
            break
    else:
        raise ValueError(f"Realm with name '{realm_name}' not found")

    # Requesting ip-address of selected realm
    join_response = requests.get(
        realms + f"/worlds/v1/{realmID}/join/pc", cookies=sid_cookie
    )
    if not join_response:
        raise RuntimeError(error_msg(join_response) + "\nIs the realm active?")

    try:
        realm_data = join_response.json()
        ip = realm_data["address"]
    except (KeyError, JSONDecodeError):
        raise KeyError(
            "Key 'address' not found in realm data." f"Response data: '{realm_data}'"
        )

    address, port = ip.split(":")
    return address, int(port)


def loop_realm_address(auth_token, realm_name):
    # Getting ip and port of realm until successful
    while True:
        try:
            address, port = get_realm_address(
                name=auth_token.profile.name,
                uuid=auth_token.profile.id_,
                access_token=auth_token.access_token,
                realm_name=realm_name,
            )
        except ValueError as e:
            # Could not find realm with given name
            print_timestamped(str(e))
            sys.exit(1)
        except RuntimeError as e:
            # Error in request
            print_timestamped(str(e))
            sleep(5)
        else:
            # Got ip and port
            return address, port
