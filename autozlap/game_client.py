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
    """Represents a 2D vector"""
    pass

class Player:
    """Represents a player"""
    def __init__(self):
        self.id = None
        self.position = None
        self.velocity = None
        self.mace = None

class Mace:
    """Represents a mace"""
    def __init__(self):
        self.position = None
        self.velocity = None
        self.player = None

class Arena:
    """Represents an arena"""
    def __init__(self):
        self.players = dict() # id -> Player

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
        self.arena = None

    def _send_play_packet(self):
        self._connection.send(dict(type="play"))

    def _received_packet_handler(self, packet):
        if packet.type == "setup":
            print("setup", packet.payload.server_version, packet.payload.syncer_value,
                  packet.payload.setup_value)
        elif packet.type == "killed":
            print("Got killed. Respawning...")
            self._send_play_packet()
        elif packet.type == "kill":
            print("kill", "-", "stamp", packet.payload.stamp)
        elif packet.type == "remove":
            print("remove", "-", packet.payload.player_id)
        elif packet.type == "sync":
            pass
            #print("sync", "-", "remove_count", packet.payload.remove_count,
            #      "sync_count", packet.payload.sync_count)
        elif packet.type == "club_collision":
            print("club_collision", "-", "first", packet.payload.first_id,
                  "second", packet.payload.second_id)
        elif packet.type == "wall_collision":
            print("wall_collision", "-", packet.payload.player_id)
        elif packet.type == "set_leaderboard":
            print("set_leaderboard")
        elif packet.type == "set_target_dim":
            print("set_target_dim", "-", packet.payload.target_dim)

    async def start(self, address, port):
        """Start the session"""
        async with aiohttp.ClientSession(loop=self._loop) as session:
            async with session.ws_connect("ws://" + address + ":" + str(port)) as websocket:
                self._connection = Connection(websocket, self.mode)
                self._send_play_packet()
                await self._connection.listen_loop(self._received_packet_handler)
