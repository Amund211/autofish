from functools import partial

from minecraft.networking.connection import Connection
from minecraft.networking.packets import clientbound, serverbound

from utils import print_timestamped


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
    greet_packet = serverbound.play.ChatPacket()
    greet_packet.message = state["greet_message"]
    state["connection"].write_packet(greet_packet)

    # Inform the server of the sleep command
    sleep_packet = serverbound.play.ChatPacket()
    sleep_packet.message = state["sleep_message"]
    state["connection"].write_packet(sleep_packet)


def handle_sound_play(pak, state):
    # https://pokechu22.github.io/Burger/1.13.2.html#sounds:entity.fishing_bobber.splash
    # 184 = Bobber down / hook splash
    if pak.sound_id != 184:
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

    # Handle disconnects
    connection.register_packet_listener(
        partial(handle_dc, state=state), clientbound.play.DisconnectPacket
    )
    connection.register_packet_listener(
        partial(handle_dc, state=state), clientbound.login.DisconnectPacket
    )

    return connection
