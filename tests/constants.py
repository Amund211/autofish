# Params used for spinning up servers for testing
# NOTE: Must match those in server.properties
RCON_PASSWORD = "autofish-testing"
RCON_PORT = 25575
MINECRAFT_PORT = 25565
FISHING_USERNAME = "testfisherman"


DEFAULT_CONFIG = {
    "options": {
        "profile_path": "profile.json",
        "print_output": True,
        "greet_message": "TESTING GREET MESSAGE",
        "sleep_message": "TESTING SLEEP MESSAGE",
        "sleep_command": "sleep",
        "sleep_time": 10,
        "sleep_helper": True,
        "fish_timeout": 60,
        "durability_threshold": 30,
        "username": FISHING_USERNAME,
    },
    "host": {
        "offline": True,
    },
}
