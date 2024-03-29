import hashlib
import os
import subprocess
import sys
from collections import deque
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

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
    process: Optional[subprocess.Popen]


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
    client_dir: Path,
    server: Server,
    host_override={},
    options_override={},
    capture_output=True,
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

    output_pipe = subprocess.PIPE if capture_output else None

    return subprocess.Popen(
        ("python", "-u", "-m", "autofish", "--config", config_path),
        stdout=output_pipe,
        stderr=output_pipe,
        text=True,
    )


def wait_for_login(client_process):
    """Wait until the user has logged in"""
    # Read from stdout until the process claims to have logged in
    output = deque(maxlen=1000)
    while client_process.poll() is None and "Connection established" not in (
        line := client_process.stdout.readline()
    ):
        if line:
            output.append(line)

    if client_process.poll() is not None:
        client_output = "\n\t".join(output)
        remaining_stdout, stderr = client_process.communicate()
        stdout = "\n\t\t".join(client_output) + f"\n\t\t{remaining_stdout}"
        raise RuntimeError(
            f"Client process exited with code {client_process.returncode}."
            f"\n\tStdout: {stdout}"
            f"\n\tStderr: {stderr}"
        )


def setup_for_fishing(tmp_path, server, water=True):
    """Log in to receive items and get teleported"""
    client_process = start_client(tmp_path, server)
    wait_for_login(client_process)

    height = 253 if water else 250

    with MCRcon(server.host, server.rcon_password, server.rcon_port) as mcr:
        mcr.command(f"/clear {FISHING_USERNAME}")
        mcr.command(f"/tp {FISHING_USERNAME} 0 {height} 0 -90 0")
        mcr.command(f"/give {FISHING_USERNAME} minecraft:fishing_rod")
        mcr.command(f"/enchant {FISHING_USERNAME} minecraft:lure 3")

    stop_client(client_process)


def stop_client(client_process):
    """Stop the client process and return remaining output"""
    client_process.terminate()
    return client_process.communicate()


@dataclass
class ManagedClient:
    """
    Context manager handling setup and shutdown of fishing clients
    """

    client_dir: Path
    server: Server
    host_override: Optional[dict] = None
    options_override: Optional[dict] = None
    capture_output: bool = True
    process: Optional[subprocess.Popen] = None

    def __enter__(self):
        self.process = start_client(
            client_dir=self.client_dir,
            server=self.server,
            host_override=self.host_override or {},
            options_override=self.options_override or {},
            capture_output=self.capture_output,
        )
        wait_for_login(self.process)
        return self.process

    def __exit__(self, *args, **kwargs):
        self.process.terminate()
