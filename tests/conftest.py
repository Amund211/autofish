import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest
import requests
from mcrcon import MCRcon

from autofish.versions import LATEST_VERSION

from .constants import MINECRAFT_PORT, RCON_PASSWORD, RCON_PORT
from .helpers import InvalidVersionError, Server, download_file, ensure_directory_exists

DEFAULT_SERVER_CONFIGS = (f"version:{LATEST_VERSION}",)


def pytest_addoption(parser):
    parser.addoption(
        "--server",
        action="append",
        default=[],
        help=(
            "list of servers to test, either 'version:<versionstring>' or "
            "'server:<host:port:rcon_port:rcon_password:version>'."
            "RCon and offline mode must be enabled for tests to run"
        ),
    )

    parser.addoption(
        "--gui",
        action="store_true",
        default=[],
        help="open the gui",
    )

    parser.addoption(
        "--arg",
        action="append",
        default=[],
        help="list of arguments passed to java when running the server",
    )


@pytest.fixture(scope="session")
def java_args(request):
    return request.config.getoption("arg")


# https://docs.pytest.org/en/latest/how-to/parametrize.html
def pytest_generate_tests(metafunc):
    if "server_config" in metafunc.fixturenames:
        metafunc.parametrize(
            "server_config",
            metafunc.config.getoption("server") or DEFAULT_SERVER_CONFIGS,
            scope="session",
        )


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
def server(
    request,
    server_config,
    java_args,
    version_manifest,
    minecraft_server_directory,
    server_properties_path,
    eula_path,
    tmp_path_factory,
):
    """Return a `Server` instance for a running minecraft server"""
    if server_config.startswith("server:"):
        host, port, rcon_port, rcon_password, version = server_config[7:].split(":")
        yield Server(
            host=host,
            port=int(port),
            rcon_port=int(rcon_port),
            rcon_password=rcon_password,
            version=version,
        )
    else:
        requested_version = server_config[8:]
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

        show_gui = request.config.getoption("gui")
        server_process = subprocess.Popen(
            (
                "java",
                "-jar",
                str(run_dir.joinpath(server_path.name)),
                *(() if show_gui else ("nogui",)),
                *java_args,
            ),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )

        # Wait for the server to start
        while "[Server thread/INFO]: RCON running on" not in (
            line := server_process.stdout.readline()
        ):
            if (
                "[Server thread/ERROR]: Exception stopping the server" in line
                or "[Server thread/WARN]: **** FAILED TO BIND TO PORT!" in line
            ):
                raise RuntimeError("Failed to start the server")

        yield Server(
            host="localhost",
            port=MINECRAFT_PORT,
            rcon_port=RCON_PORT,
            rcon_password=RCON_PASSWORD,
            version=requested_version,
        )
        # Shut down server
        server_process.communicate("stop")


@pytest.fixture()
def setup_spawn(server):
    with MCRcon(server.host, server.rcon_password, server.rcon_port) as mcr:
        # Set world spawn so that the set area is loaded
        mcr.command("/setworldspawn 0 254 0")

        mcr.command("/weather rain")
        mcr.command("/gamerule doDaylightCycle false")
        mcr.command("/time set 6000")
        mcr.command("/kill @e[type=!player]")
        mcr.command("/kill @e[type=!player]")  # kill any dropped items

        # Create a hallway where we can perform our tests
        mcr.command("/fill -1 252 -1 10 255 1 minecraft:glass")
        mcr.command("/fill 0 253 0 9 255 0 minecraft:air")
        mcr.command("/fill 0 253 0 9 253 0 minecraft:water")
        mcr.command("/setblock 0 255 0 minecraft:glass")
