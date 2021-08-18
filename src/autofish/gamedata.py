"""
Module to download and cache gamedata using pokechu22.github.io.

Used to get the sound-id for the bobber splash for a given version.
"""

import json
import sys
from json.decoder import JSONDecodeError
from time import sleep

import requests

from autofish.versions import LATEST_VERSION, Version, is_supported

BURGER_ENDPOINT = "https://pokechu22.github.io/Burger/{version}.json"

BOBBER_SPLASH_SOUND_IDS = {
    "1.9": 140,
    "1.9.1": 140,
    "1.9.2": 140,
    "1.9.3": 140,
    "1.9.4": 140,
    "1.10": 141,
    "1.10.1": 141,
    "1.10.2": 141,
    "1.11": 143,
    "1.11.1": 143,
    "1.11.2": 143,
    "1.12": 153,
    "1.12.1": 153,
    "1.12.2": 153,
    "1.12": 153,
    "1.13": 184,
    "1.13.1": 184,
    "1.13.2": 184,
    "1.14": 62,
    "1.14.1": 62,
    "1.14.2": 62,
    "1.14.3": 62,
    "1.14.4": 62,
    "1.15": 73,
    "1.15.1": 73,
    "1.15.2": 73,
    "1.16": 272,
    "1.16.1": 272,
    "1.16.2": 272,
    "1.16.3": 272,
    "1.16.4": 272,
}


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
                    f"The data for version {version} does not exist. "
                    f"Check that you entered the version correctly, "
                    "or wait for the data to be updated."
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

    if not is_supported(version):
        print(
            f"Version {version} not supported. If you're really lucky, "
            f"it might work with {LATEST_VERSION}."
        )
        sys.exit(1)

    # Use hard coded sound ids
    if version in BOBBER_SPLASH_SOUND_IDS:
        return BOBBER_SPLASH_SOUND_IDS[version]

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
