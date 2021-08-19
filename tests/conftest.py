import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests
from autofish.versions import LATEST_VERSION

# Args passed to java for running the minecraft server
DEFAULT_JAVA_ARGS = []

# Params used for spinning up servers for testing
# NOTE: Must match those in server.properties
RCON_PASSWORD = "autofish-testing"
RCON_PORT = 25575
MINECRAFT_PORT = 25565


class InvalidVersionError(ValueError):
    pass


# https://docs.pytest.org/en/latest/how-to/parametrize.html
def pytest_addoption(parser):
    parser.addoption(
        "--server",
        action="append",
        default=[],
        help=(
            "list of servers to test, either 'version:<versionstring>' or "
            "'server:<ip:port:rcon_port:rcon_password>'"
        ),
    )

    parser.addoption(
        "--arg",
        action="append",
        default=DEFAULT_JAVA_ARGS,
        help="list of arguments passed to java when running the server",
    )


@pytest.fixture(scope="session")
def java_args(request):
    return request.config.getoption("arg")


def pytest_generate_tests(metafunc):
    if "server" in metafunc.fixturenames:
        metafunc.parametrize(
            "server",
            metafunc.config.getoption("server", f"version:{LATEST_VERSION}"),
            scope="session",
        )


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
    return m.digest() if sha1 else None


def ensure_directory_exists(path):
    if not path.is_dir():
        path.mkdir(exist_ok=True)


@pytest.fixture(scope="session")
def data_directory():
    """Create and return a Path to the persistent data directory"""
    data_dir = Path(__file__).parent / "data"
    ensure_directory_exists(data_dir)
    return data_dir


@pytest.fixture(scope="session")
def eula_path(data_directory):
    """Return the path to the accepted eula.txt file"""
    return data_directory / "eula.txt"


@pytest.fixture(scope="session")
def server_properties_path(data_directory):
    """Return the path to the server.properties file"""
    return data_directory / "server.properties"


@pytest.fixture(scope="session")
def minecraft_server_directory(data_directory):
    """Create and return a Path to the server directory"""
    server_dir = data_directory / "servers"
    ensure_directory_exists(server_dir)
    return server_dir


@pytest.fixture(scope="session")
def version_manifest_path(minecraft_server_directory):
    """Return the path to the version manifest"""
    return minecraft_server_directory / "version_manifest.json"


@pytest.fixture(scope="session")
def version_manifest_url():
    """Return the url to the version manifest"""
    return "https://launchermeta.mojang.com/mc/game/version_manifest.json"


@pytest.fixture(scope="session")
def version_manifest(version_manifest_path, version_manifest_url):
    """Return the version manifest as a python dictionary"""
    if (
        not version_manifest_path.is_file()
        or version_manifest_path.stat().st_mtime < time.time() - 3600 * 24
    ):
        # Get the manifest if we don't have it or if it's more than a day old
        download_file(version_manifest_url, version_manifest_path)

    return json.loads(version_manifest_path.read_text())


@pytest.fixture(scope="session")
def minecraft_server(
    server,
    java_args,
    version_manifest,
    minecraft_server_directory,
    server_properties_path,
    eula_path,
    tmp_path_factory,
):
    """Return the (port, ip) to a running minecraft server"""
    if server.startswith("server:"):
        ip, port, rcon_port, rcon_password = server[7:].split(":")
        yield ip, port, rcon_port, rcon_password
    else:
        requested_version = server[8:]
        server_path = minecraft_server_directory / f"{requested_version}.jar"

        if not server_path.is_file():
            try:
                version = next(
                    version
                    for version in version_manifest["versions"]
                    if version["id"] == requested_version
                )
            except StopIteration as e:
                raise InvalidVersionError(
                    f"Could not find version {requested_version} "
                    "in the version manifest"
                ) from e

            server_info = requests.get(version["url"]).json()["downloads"]["server"]
            sha1 = download_file(server_info["url"], server_path, sha1=True)
            try:
                assert server_path.stat().st_size == server_info["size"]
                assert sha1 == server_info["sha1"]
            except AssertionError as e:
                server_path.unlink(missing_ok=True)
                raise RuntimeError("Bad download!") from e

        run_dir = tmp_path_factory.mktemp("running-server")
        # Move to our temp directory
        shutil.copy(server_path, run_dir)
        shutil.copy(server_properties_path, run_dir)
        shutil.copy(eula_path, run_dir)
        # Start server
        os.chdir(str(run_dir))
        server_process = subprocess.Popen(
            (
                "java",
                "-jar",
                str(run_dir.joinpath(server_path.name)),
                "nogui",
                *java_args,
            )
        )
        # Wait for server to start
        yield "localhost", MINECRAFT_PORT, RCON_PORT, RCON_PASSWORD  # Temp for testing
        # yield ip, port
        # Shut down server
        pass


@pytest.fixture()
def working_fishing_setup(minecraft_server):
    # Do some rcon magic to fix the setup
    pass
