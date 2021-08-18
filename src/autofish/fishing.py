import json
from functools import partial

from minecraft.networking.connection import Connection
from minecraft.networking.packets import clientbound, serverbound

from autofish.utils import print_timestamped


def use_item(state):
    """Send a `UseItemPacket` to `connection`"""
    packet = serverbound.play.UseItemPacket()
    packet.hand = packet.Hand.MAIN
    state["connection"].write_packet(packet)


def handle_join_game(pak, state):
    print_timestamped("Connection established")

    # Cast the rod
    use_item(state)

    # Greet the server
    if state["greet_message"] != "" and state["greet_message"] is not None:
        greet_packet = serverbound.play.ChatPacket()
        greet_packet.message = state["greet_message"]
        state["connection"].write_packet(greet_packet)

    # Inform the server of the sleep command
    if state["sleep_helper"]:
        sleep_packet = serverbound.play.ChatPacket()
        sleep_packet.message = state["sleep_message"]
        state["connection"].write_packet(sleep_packet)


def handle_sound_play(pak, state):
    if pak.sound_id != state["bobber_splash_id"]:
        return

    # Reel in and cast
    use_item(state)
    use_item(state)

    state["recently_cast"] = True
    state["amount_caught"] += 1

    if state["print_output"]:
        print_timestamped("Caught one!")


def handle_dc(pak, state):
    print_timestamped("DC-packet recieved, id: " + str(pak.id))

    # Disconnected from server - restart connection
    state["connection"].disconnect(immediate=True)
    state["connected"] = False


def handle_chat(pak, state):
    data = json.loads(pak.json_data)

    if pak.position == clientbound.play.ChatMessagePacket.Position.SYSTEM and (
        data.get("translate", "") == "commands.message.display.incoming"
        or data.get("translate", "") == "chat.type.announcement"
    ):
        # Whispers and such
        name = data["with"][0]["text"]
        message = data["with"][1]["text"]
    elif pak.position == clientbound.play.ChatMessagePacket.Position.CHAT:
        # Chat message
        name = data["with"][0]["insertion"]
        message = data["with"][1]
    else:
        return

    if message != state["sleep_command"]:
        return

    print_timestamped("Sleep requested by " + name)

    # Notify main loop that sleep has been requested
    state["sleep_requested"] = True

    # Disconnected from server
    state["connection"].disconnect(immediate=True)
    state["connected"] = False


def handle_exception(exc, sysstat, state):
    """Handle exceptions in the connection"""
    if isinstance(exc, KeyboardInterrupt):
        return
    print_timestamped("Exception handled: ", exc)
    print_timestamped(sysstat)

    # Disconnected from server - restart connection
    state["connection"].disconnect(immediate=True)
    state["connected"] = False


def setup_connection(address, port, version, auth_token, state, username=None):
    connection = Connection(
        address,
        port,
        auth_token=auth_token,
        initial_version=version,
        username=username,
        handle_exception=partial(handle_exception, state=state),
    )
    print_timestamped(f"Connecting to {address}:{port}")

    # Cast rod on join
    connection.register_packet_listener(
        partial(handle_join_game, state=state), clientbound.play.JoinGamePacket
    )

    # Reel in and recast rod on bobber splash
    connection.register_packet_listener(
        partial(handle_sound_play, state=state), clientbound.play.SoundEffectPacket
    )

    if state["sleep_helper"]:
        # Disconnect for a while when people need to sleep
        connection.register_packet_listener(
            partial(handle_chat, state=state), clientbound.play.ChatMessagePacket
        )

    # Handle disconnects
    connection.register_packet_listener(
        partial(handle_dc, state=state), clientbound.play.DisconnectPacket
    )
    connection.register_packet_listener(
        partial(handle_dc, state=state), clientbound.login.DisconnectPacket
    )

    return connection
