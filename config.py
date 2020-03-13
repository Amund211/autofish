import toml

from minecraft import RELEASE_MINECRAFT_VERSIONS


LATEST_VERSION = max(RELEASE_MINECRAFT_VERSIONS.items(), key=lambda x: x[1])[0]

DEFAULT_OPTIONS = {
    "profile_path": "profile.json",
    "print_output": False,
    "greet_message": "><(((('> AFK Fishing... ><(((('>",
    "sleep_message": "Type 'sleep' to log me off for 10 seconds",
    "sleep_command": "sleep",
    "sleep_helper": True,
    "fish_timeout": 120,
}

DEFAULT_HOST = {
    "realm": False,
    "port": "25565",
    "version": LATEST_VERSION,
    "offline": False,
}


def read_config(path=None, fp=None):
    """
    Reads the config.toml file at `path` and inserts default values for missing keys

    Raises RuntimeError if any exceptions are caught
    """
    if path is not None:
        try:
            with open(path, "r") as f:
                config_text = f.read()
        except (FileNotFoundError, IOError, PermissionError) as e:
            raise RuntimeError(e)
    else:
        assert fp is not None, "No path or file passed to read_config"
        config_text = fp.read()

    try:
        config = toml.loads(config_text)
    except toml.decoder.TomlDecodeError as e:
        raise RuntimeError(f"Error decoding config in {path}: " + e)

    # Validate config
    for key in ("options", "host"):
        if key not in config:
            config[key] = {}
        elif type(config[key]) is not dict:
            raise RuntimeError(f"Key '{key}' in config must be a dict")

    # Populate options with default values
    for key in DEFAULT_OPTIONS:
        config["options"][key] = config["options"].get(key, DEFAULT_OPTIONS[key])

    # Populate host with default values
    for key in DEFAULT_HOST:
        config["host"][key] = config["host"].get(key, DEFAULT_HOST[key])

    return config
