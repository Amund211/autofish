import hashlib
import os
import subprocess
import sys
from collections import deque
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

import requests
import toml
from mcrcon import MCRcon

from .constants import DEFAULT_CONFIG, FISHING_USERNAME


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
        ("python", "-u", "-m", "autofish", "--config", config_path),
        stdout=subprocess.PIPE,
        text=True,
    )


def wait_for_login(client_process):
    """Wait until the user has logged in"""
    # Read from stdout until the process claims to have logged in
    output = deque()
    while client_process.poll() is None and "Connection established" not in (
        line := client_process.stdout.readline()
    ):
        if line:
            output.append(line)

    client_process.poll()
    if client_process.returncode is not None:
        client_output = "\n\t".join(output)
        raise RuntimeError(
            f"Client process exited with code {client_process.returncode}."
            f"{client_output}"
        )


def setup_for_fishing(tmp_path, server):
    """Log in to receive items and get teleported"""
    client_process = start_client(tmp_path, server)
    wait_for_login(client_process)

    with MCRcon(server.host, server.rcon_password, server.rcon_port) as mcr:
        mcr.command(f"/clear {FISHING_USERNAME}")
        mcr.command(f"/tp {FISHING_USERNAME} 0 253 0 -90 0")
        mcr.command(f"/give {FISHING_USERNAME} minecraft:fishing_rod")
        mcr.command(f"/enchant {FISHING_USERNAME} minecraft:lure 3")

    stop_client(client_process)


def stop_client(client_process):
    """Stop the client process and return remaining output"""
    client_process.terminate()
    return client_process.communicate()
