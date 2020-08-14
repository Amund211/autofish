# Autofish
Autofish is a simple python script built on [pyCraft](https://github.com/ammaraskar/pyCraft/) to automatically fish in minecraft.
Autofish can connect directly to any server, and can even connect to realms.

Please contact your server administrator/realm owner before using this script, as it may be considered cheating on many servers, and could ruin the gameplay experience of others.
This software may trigger all sorts of anticheats, and so you should use it at your own risk. You have been warned.

## Nerf and legitimacy
Starting with version 20w12a, which is a 1.16 snapshot, afk fish farms have been nerfed.
To be be eligible to catch treasure in these versions, it is required that the bobber be surrounded by non-solid blocks such as air, water, waterlogged blocks, etc. in a 5x5x5 cube centered on the bobber, at all times.
To use this script effectively in these versions you could, for example, stand on a block three blocks above a deep and wide pool of water, and face straight down when fishing.

Originally, this script was intended to be a way of "using" an afk fish farm on low power devices, or without the graphical interface.
This gave no in-game advantage compared to an actual fish farm, and would arguably make for a better gameplay experience for other players, since they could request to sleep.
With this change, however, the script is doing something which is impossible without the attention of a player; giving an advantage over completely vanilla players.

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
To properly run this application you must make sure that the script is running under the virtual environment.
A simple way of doing this is to run
```shell
pipenv run fish
```

To start fishing you need to:
1. Get into a safe spot
1. Equip a rod (preferably with mending)
1. Point your crosshair towards some water
1. Log out and run the script

If you see timeouts in the console output, this may indicate that you can't reach the water.

To log out and stop fishing; abort the script with <kbd>Ctrl</kbd>+<kbd>C</kbd>.

## Updating
When changes have been made to this repository, you can download them using git while in the folder:
```shell
git pull
```

If this fails you may have edited some files locally.
To discard these changes:
```shell
git fetch
git reset --hard origin/master
```
Note that this will not change untracked files, like `config.toml`, `profile.json`, or any other files you might have put there.

After this you should update the virtual environment to make sure you have the latest version of `pyCraft`:
```shell
pipenv sync
```

## Notes
### Version support
Minecraft's network protocol changes with almost every new version of minecraft.
This script uses the implementation of the protocol from [pyCraft](https://github.com/ammaraskar/pyCraft/), and therefore only supports the versions that pyCraft supports.
A list of supported versions can be found [here](https://github.com/ammaraskar/pyCraft#supported-minecraft-versions).

This script uses only a relatively small subset of the network protocol, so new protocol versions may not present any relevant changes.
In this case you are able to connect to a server using an earlier version; i. e. connecting to a `20w10a` server using the `1.15.2` protocol.

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
