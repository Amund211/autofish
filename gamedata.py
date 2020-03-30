"""
Module to download and cache gamedata using pokechu22.github.io.

Used to get the sound-id for the bobber splash for a given version.
"""

import json
import sys
from json.decoder import JSONDecodeError
from time import sleep

import requests

from minecraft import SUPPORTED_MINECRAFT_VERSIONS

BURGER_ENDPOINT = "https://pokechu22.github.io/Burger/{version}.json"


class Version:
    """
    Class that implements a partial ordering on minecraft versions
    using the protocol version.
    """

    def __init__(self, version):
        self.version = version

    @property
    def protocol(self):
        return SUPPORTED_MINECRAFT_VERSIONS[self.version]

    def __lt__(self, other):
        return self.protocol < other.protocol

    def __le__(self, other):
        return self.protocol <= other.protocol

    def __eq__(self, other):
        # Handle both Version instances and strings
        return self.version == getattr(other, "version", other)

    def __ne__(self, other):
        # Handle both Version instances and strings
        return self.version != getattr(other, "version", other)

    def __gt__(self, other):
        return self.protocol > other.protocol

    def __ge__(self, other):
        return self.protocol >= other.protocol


def _write_cache(cache, fp):
    json.dump(cache, fp, sort_keys=True, indent=2)


def _load_cache(fp):
    return json.load(fp)


def _download_sound_id(version, sound):
    response = requests.get(
        BURGER_ENDPOINT.format(version=requests.utils.quote(version))
    )
    response.raise_for_status()

    return response.json()[0]["sounds"][sound]["id"]


def _loop_download_sound_id(version, sound):
    # Try 5 times
    for i in range(5):
        try:
            _id = _download_sound_id(version, sound)
        except (JSONDecodeError, KeyError) as e:
            # Failed interpreting the API
            print("Call to Burger-API failed: ", str(e))
            sys.exit(1)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                # No data found
                print(
                    f"The data for version {version} does not exist. Check that you entered the version correctly, or wait for the data to be updated."
                )
                sys.exit(1)
            else:
                # Some other error, try again in a bit
                print(e)
                print("Error in request to Burger-API, trying again...")
                sleep(5)
        else:
            return _id
    else:
        print(f"Failed to get sound id for version {version}.")


def get_bobber_splash_id(version, fp):
    """
    Return the bobber splash sound id for a given version.
    Closes fp after use.

    On error prints and exits.
    """

    if version not in SUPPORTED_MINECRAFT_VERSIONS:
        latest_supported_version = max(
            SUPPORTED_MONECRAFT_VERSIONS.values(),
            key=lambda pair: pair[1],  # Get protocol version
        )[0]
        print(
            f"Version {version} not supported. If you're really lucky, it might work with {latest_supported_version}."
        )
        sys.exit(1)

    # Read stored cache
    try:
        fp.seek(0)
        cache = _load_cache(fp)
    except (OSError, IOError, JSONDecodeError):
        print("Could not read from cache-file")
        cache = {}
    finally:
        fp.close()

    if version not in cache:
        # Add the version to the cache and store the new cache
        # Determine sound name
        if Version(version) >= Version("1.13-pre5"):
            sound_name = "entity.fishing_bobber.splash"
        else:
            sound_name = "entity.bobber.splash"

        print(f"Downloading sound id for version {version}")
        cache[version] = _loop_download_sound_id(version, sound_name)

        with open(fp.name, "w") as fp2:
            _write_cache(cache, fp2)

    return cache[version]
