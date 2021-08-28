import hashlib
import os
import signal
import subprocess
import sys
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

import requests
import toml

from .constants import DEFAULT_CONFIG


class InvalidVersionError(ValueError):
    pass


@dataclass
class Server:
    host: str
    port: int
    rcon_port: int
    rcon_password: str
    version: str


def download_file(url, path, chunk_size=128, sha1=False):
    print(f"Downloading {url}", file=sys.stderr)
    m = hashlib.sha1() if sha1 else None
    r = requests.get(url, stream=True)

    with path.open("wb") as file:
        for chunk in r.iter_content(chunk_size=chunk_size):
            file.write(chunk)
            if sha1:
                m.update(chunk)

    print("\tDownload complete", file=sys.stderr)
    return m.hexdigest() if sha1 else None


def ensure_directory_exists(path: Path):
    if not path.is_dir():
        path.mkdir(exist_ok=True)


def start_client(
    client_dir: Path, server: Server, host_override={}, options_override={}
):
    """Start a client process with the given config"""
    config = deepcopy(DEFAULT_CONFIG)
    config["options"] = {**config["options"], **options_override}
    config["host"] = {
        **config["host"],
        "address": server.host,
        "port": server.port,
        "version": server.version,
        **host_override,
    }
    os.chdir(client_dir)
    config_path = str(client_dir / "config.toml")
    with open(config_path, "w") as config_file:
        toml.dump(config, config_file)

    return subprocess.Popen(
        ("python", "-m", "autofish", "--config", config_path),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )


def wait_for_login(client_process):
    """Wait until the user has logged in"""
    # Read from stdout until the process claims to have logged in
    while "Connection established" not in (line := client_process.stdout.readline()):
        print(f"Client output: {line}")
        pass


def stop_client(client_process):
    """Stop the client process by sending sigint"""
    client_process.send_signal(signal.SIGINT)
    return client_process.communicate()
