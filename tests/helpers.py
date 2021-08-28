import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

import requests


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


def start_client(server: Server):
    pass
