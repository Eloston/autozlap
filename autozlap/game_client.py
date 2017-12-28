# -*- coding: UTF-8 -*-

# autozlap: An experimental autonomous zlap.io client
# Copyright (C) 2017  Eloston
#
# This file is part of autozlap.
#
# autozlap is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# autozlap is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with autozlap.  If not, see <http://www.gnu.org/licenses/>.

"""Game client component"""

import aiohttp

from .networking import Connection

class Vector:
    """Represents a 2D vector in cartesian coordinates"""
    def __init__(self, coordinates=None, vector_struct=None):
        if coordinates:
            self.x, self.y = coordinates #pylint: disable=invalid-name
        else:
            self.update(vector_struct)

    def update(self, vector2d_struct):
        """Update the vector values based on a vector2d Struct"""
        self.x = vector2d_struct.x #pylint: disable=invalid-name
        self.y = vector2d_struct.y #pylint: disable=invalid-name

class Mace:
    """Represents a mace"""
    def __init__(self, player, position, velocity):
        self.player = player
        self.position = position
        self.velocity = velocity

class Player:
    """Represents a player"""
    def __init__(self, id_num, player_position, player_velocity, mace_position,
                 mace_velocity):
        self.id = id_num #pylint: disable=invalid-name
        self.position = player_position
        self.velocity = player_velocity
        self.mace = Mace(self, mace_position, mace_velocity)
        self.dead = False
        self.name = None

class Arena:
    """Represents an arena"""
    def __init__(self):
        self.current_player = None
        self.players = dict() # id -> Player
        self.dimensions = None
        self.target_dimensions = None # TODO: Implement dimension transitions

class Leaderboard:
    """Represents a leaderboard"""
    def __init__(self):
        self.king = None

class Session:
    """Represents a session"""
    def __init__(self, loop, mode):
        self._loop = loop
        self._connection = None
        self.mode = mode
        self.arena = Arena()

    def _send_play_packet(self):
        self._connection.send(dict(type="play"))

    def _received_packet_handler(self, packet):
        if packet.type == "setup":
            print("setup", packet.payload.current_player_id)
            if not packet.payload.game_mode is self.mode:
                raise ValueError(
                    "Server-reported mode {} does not match current mode {}".format(
                        packet.payload.mode.value, self.mode.value
                    )
                )
            self.arena.dimensions = packet.payload.dimensions
            self.arena.target_dimensions = packet.payload.target_dimensions
            initial_vectorstruct = (None, None)
            self.arena.current_player = Player(
                packet.payload.current_player_id,
                Vector(coordinates=initial_vectorstruct),
                Vector(coordinates=initial_vectorstruct),
                Vector(coordinates=initial_vectorstruct),
                Vector(coordinates=initial_vectorstruct)
            )
            self.arena.players[packet.payload.current_player_id] = self.arena.current_player
        elif packet.type == "killed":
            print("Got killed. Respawning...")
            self._send_play_packet()
        elif packet.type == "kill":
            print("kill", "-", "killed_id", packet.payload.killed_id, "killer_id",
                  packet.payload.killer_id)
            del self.arena.players[packet.payload.killed_id]
            if packet.payload.killed_id == self.arena.current_player.id:
                self.arena.current_player.name = None
        elif packet.type == "remove":
            print("remove", "-", packet.payload.player_id)
            del self.arena.players[packet.payload.player_id]
        elif packet.type == "sync":
            print("sync -", end="")
            for player_id in packet.payload.removal_array:
                print(" delete", player_id)
                del self.arena.players[player_id]
            for sync_struct in packet.payload.sync_array:
                if sync_struct.is_new_player:
                    player_obj = Player(
                        sync_struct.player_id,
                        Vector(vector_struct=sync_struct.player_state.position),
                        Vector(vector_struct=sync_struct.player_state.velocity),
                        Vector(vector_struct=sync_struct.mace_state.position),
                        Vector(vector_struct=sync_struct.mace_state.velocity)
                    )
                    if sync_struct.player_attributes.player_name:
                        print("New name: " + sync_struct.player_attributes.player_name)
                        player_obj.name = sync_struct.player_attributes.player_name
                    self.arena.players[sync_struct.player_id] = player_obj
                    print(" new", sync_struct.player_id, end="")
                else:
                    player = self.arena.players[sync_struct.player_id]
                    player.position.update(sync_struct.player_state.position)
                    player.velocity.update(sync_struct.player_state.velocity)
                    player.mace.position.update(sync_struct.mace_state.position)
                    player.mace.velocity.update(sync_struct.mace_state.velocity)
                    print(" update", sync_struct.player_id, end="")
            print()
        elif packet.type == "club_collision":
            print("club_collision", "-", "first", packet.payload.first_id,
                  "second", packet.payload.second_id)
        elif packet.type == "wall_collision":
            print("wall_collision", "-", packet.payload.player_id)
        elif packet.type == "set_leaderboard":
            print("set_leaderboard")
        elif packet.type == "set_target_dim":
            print("set_target_dim", "-", packet.payload.target_dimensions)
            self.arena.target_dimensions = packet.payload.target_dimensions
        # Debugging purposes
        if len(packet.extraneous) > 0:
            print("EXTRANEOUS", "-", packet.type, "-", len(packet.extraneous))
            exit()

    def _is_new_player(self, player_id):
        print("checking is new player: {}".format(player_id))
        if player_id == self.arena.current_player.id:
            print("Current player lacks name?: {}".format(not bool(self.arena.current_player.name)))
            if not self.arena.current_player.name:
                self.arena.current_player.name = True
                return True
            return False
        print("Is unknown player?: {}".format(player_id not in self.arena.players))
        return player_id not in self.arena.players

    def _is_current_player(self, player_id):
        print("check: {}, known: {}".format(player_id, self.arena.current_player.id))
        return player_id == self.arena.current_player.id

    async def start(self, address, port):
        """Start the session"""
        async with aiohttp.ClientSession(loop=self._loop) as session:
            async with session.ws_connect("ws://" + address + ":" + str(port)) as websocket:
                self._connection = Connection(
                    websocket,
                    self.mode,
                    self._is_new_player,
                    self._is_current_player
                )
                self._send_play_packet()
                await self._connection.listen_loop(self._received_packet_handler)
