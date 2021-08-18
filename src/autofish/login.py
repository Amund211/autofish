import getpass
import json
from json.decoder import JSONDecodeError

from minecraft import authentication
from minecraft.exceptions import YggdrasilError

from autofish.realmip import loop_realm_address


def get_credentials(username=None):
    if not username:
        username = input("Mojang username (probably your email): ")
    return username, getpass.getpass(f"Password for {username}: ")


def read_profile(profile_path):
    # Opening and parsing profile.json
    has_token = False
    user_data = {}
    try:
        with open(profile_path, "r") as pro_file:
            content = pro_file.read()
        user_data = json.loads(content)
    except FileNotFoundError:
        print(f"File {profile_path} does not exist")
    except JSONDecodeError as e:
        print(f"Invalid JSON in {profile_path}:", e)
    else:
        # profile.json is complete
        if (
            "accessToken" in user_data
            and "clientToken" in user_data
            and "displayName" in user_data
            and "username" in user_data
            and "uuid" in user_data
        ):
            has_token = True

    # Force user to authenticate with username+password
    return has_token, user_data


def create_auth_token(user_data):
    """
    Creates an `AuthenticationToken` instance from `user_data`

    If the provided accessToken is invalid, return `None`
    """
    auth_token = authentication.AuthenticationToken(
        username=user_data["username"],
        access_token=user_data["accessToken"],
        client_token=user_data["clientToken"],
    )
    profile = authentication.Profile(
        id_=user_data["uuid"], name=user_data["displayName"]
    )
    auth_token.profile = profile

    if auth_token.validate():
        print("Validation passed")
        return auth_token
    else:
        print("Validation failed, attempting refresh")
        try:
            auth_token.refresh()
        except YggdrasilError as e:
            print("Unable to refresh token:", e)
            return None
        else:
            print("Token successfully refreshed!")
            return auth_token


def authenticate_user(user_data):
    while True:
        if "username" in user_data:
            # Try using stored username to authenticate
            print("Ctrl+d to use a different account")
            try:
                username, password = get_credentials(username=user_data["username"])
            except EOFError:
                # User aborted login - prompt for
                # new username+password
                username, password = get_credentials()
        else:
            username, password = get_credentials()

        # Update username in user_data
        user_data["username"] = username

        # Authenticate with mojang using username+password
        # Select clientToken
        if "clientToken" in user_data:
            # Use stored clientToken
            auth_token = authentication.AuthenticationToken(
                client_token=user_data["clientToken"]
            )
        else:
            # Use no clientToken - later store recieved
            # clientToken as new clientToken
            auth_token = authentication.AuthenticationToken()

        # Authenticate with given username+password
        try:
            auth_token.authenticate(username, password)
        except YggdrasilError as e:
            print("Authentication failed:", e)
            # Retry login
            continue
        else:
            # Authentication succeeded
            return auth_token


def update_profile(profile_path, user_data, auth_token):
    # Read provided clientToken if no clienToken was stored previously
    if "clientToken" not in user_data:
        user_data["clientToken"] = auth_token.client_token

    # Update accessToken
    user_data["accessToken"] = auth_token.access_token

    # Update name and uuid
    user_data["uuid"] = auth_token.profile.id_
    user_data["displayName"] = auth_token.profile.name

    # Write updated user_data to disk
    with open(profile_path, "w") as pro_file:
        json_data = json.dumps(user_data, sort_keys=True, indent=2)
        pro_file.write(json_data)


def get_host_address(host, auth_token):
    if host["realm"]:
        if "realm_name" not in host:
            raise RuntimeError("Error in host config: missing 'realm_name'")
        if host["offline"]:
            raise RuntimeError(
                "Error in host config: cannot connect to realm in offline mode"
            )
        return loop_realm_address(auth_token, host["realm_name"])

    if "address" not in host:
        raise RuntimeError("Error in host config: missing 'address'")
    elif "port" not in host:
        raise RuntimeError("Error in host config: missing 'port'")

    return host["address"], int(host["port"])
