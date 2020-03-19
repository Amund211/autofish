# Autofish
Autofish is a simple python script built on [pyCraft](https://github.com/ammaraskar/pyCraft/) to automatically fish in minecraft.
Autofish can connect directly to any server, and can even connect to realms.

Please contact your server administrator/realm owner before using this script, as it may be considered cheating on many servers, and could ruin the gameplay experience of others.
This software may trigger all sorts of anticheats, and so you should use it at your own risk. You have been warned.

## Note
Autofish is currently in development, and all features may not work as advertised.

The id of the sound that plays when you have caught a fish changes between versions, the script is currently configured to fish on version 1.15.x.
If you wish to fish on a different version you need to find the sound id for that version, and replace the old one in the function `handle_sound_play` in `fishing.py`.
To find the correct id visit <https://pokechu22.github.io/Burger/VERSION.html#sounds:entity.fishing_bobber.splash>, where you replace VERSION with the name of the version you want to play on.

Examples:
- <https://pokechu22.github.io/Burger/1.15.2.html#sounds:entity.fishing_bobber.splash>
- <https://pokechu22.github.io/Burger/20w12a.html#sounds:entity.fishing_bobber.splash>

This is temporary, and an automatic solution is being worked on.

## Installation
To install autofish make sure you have:
1. [git](https://git-scm.com/) (for cloning the repository)
1. [Python](https://www.python.org/downloads/)
1. Pipenv (```pip install pipenv```)

First clone the repository:
```shell
git clone https://github.com/Amund211/autofish/
```
And then create the virtual environment:
```shell
cd autofish
pipenv sync
```

Copy one of the configuration-files to ```config.toml``` and edit it to your needs.

## Usage
To properly run this application you must make sure that the script is running under the virtual environment. A simple way of doing this is to run
```shell
pipenv run python autofish.py
```

To start fishing you need to:
1. Get into a safe spot
1. Equip a rod (preferably with mending)
1. Point your crosshair towards some water
1. Log out and run the script

If you see timeouts in the console output, this may indicate that you can't reach the water.

### Arguments
When run without arguments ```autofish.py``` looks for a configuration-file named ```config.toml``` in the current directory.
To specify a different configuration, pass the path to this file as the first argument i.e.
```shell
pipenv run python autofish.py /path/to/config.toml
```

## Notes
### Principle
The script reels in the rod when it hears the bobber splash sound played on the server.
This makes it weak to:
1. Large latency to the server
1. Other people fishing near you

### Authentication
This application handles authentication just like the vanilla minecraft client, and does not store your password.
You may not always need to enter your password to authenticate; this is because the application stores an accesstoken, which is used instead of your password.
This is the same reason that you do not need to log in every time you open minecraft.

When authenticating for the first time, pyCraft creates a random ```clientToken```, which means that using this application should not interfere with your other minecraft sessions.

#### Authenticating without a password
If you for any reason do not wish to type your password into this application, you can generate a fresh ```accessToken``` and use that for authentification instead.
To do this, log into your account on the vanilla client to make sure that your token is refreshed, and copy the relevant values from ```/path/to/.minecraft/launcher_profiles.json``` into ```profile.json``` in the project directory.
The file should look like:
```json
{
  "accessToken": "some string of hex characters",
  "clientToken": "some string of hex characters",
  "displayName": "your displayname",
  "username": "your mojang username (probably your email)",
  "uuid": "some string of hex characters"
}
```
After you do this you should generate a new ```clientToken``` for your vanilla client to make sure the two clients don't interfere with each other.
Note that this will log you out of your vanilla client.
