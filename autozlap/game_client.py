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

'''Game client component'''

import io
import struct
import shlex

import aiohttp

from .constants import CLIENT_VERSION, GameSendType, GameReceiveType

_STRUCT_FLOAT32 = struct.Struct("<f")
_STRUCT_VEC2 = struct.Struct("<ff")

def _send_single_u8(websocket, data):
    websocket.send_bytes(data.to_bytes(1, byteorder="little"))

def _send_direction(websocket, direction):
    raise NotImplementedError()

def _read_u8(buf):
    return int.from_bytes(buf.read(1), byteorder="little", signed=False)

def _read_u32(buf):
    return int.from_bytes(buf.read(4), byteorder="little", signed=False)

def _read_f32(buf):
    return _STRUCT_FLOAT32.unpack(buf.read(4))[0]

def _read_vec2(buf):
    return _STRUCT_VEC2.unpack(buf.read(8))

def _read_string(buf):
    full_str = bytes()
    while True:
        tmp_value = buf.read(1)
        if tmp_value == b'\x00':
            break
        full_str += tmp_value
    return full_str.decode("UTF-8")

async def game_client_routine(loop, address, port):
    '''Main client routine'''
    async with aiohttp.ClientSession(loop=loop) as session:
        async with session.ws_connect("ws://" + address + ":" + str(port)) as websocket:
            _send_single_u8(websocket, GameSendType.play.value)
            async for msg in websocket:
                if msg.type == aiohttp.WSMsgType.BINARY:
                    with io.BytesIO(msg.data) as databuf:
                        packet_type = _read_u8(databuf)
                        if packet_type == GameReceiveType.setup:
                            print("Setup values:")
                            server_version = _read_string(databuf)
                            if server_version != CLIENT_VERSION:
                                raise Exception("Server version is: '{}'".format(server_version))
                            print("Syncer setup value:", _read_u32(databuf))
                            game_mode = _read_u8(databuf)
                            if game_mode == 0:
                                print("Game mode: FFA")
                            else:
                                print("Game mode: TDM")
                            print("setup() value:", _read_u32(databuf))
                        elif packet_type == GameReceiveType.killed:
                            print("Got killed")
                            _send_single_u8(websocket, GameSendType.play.value)
                        elif packet_type == GameReceiveType.kill:
                            stamp = _read_u32(databuf)
                            print("Kill stamp value:", stamp)
                        elif packet_type == GameReceiveType.remove:
                            print("Remove:", databuf.read())
                        elif packet_type == GameReceiveType.sync:
                            continue
                            print("sync packet: ", end="")
                            timestamp = _read_u32(databuf)
                            print("timestamp:", timestamp, end=", ")
                            players_to_remove = _read_u32(databuf)
                            print("Removing", players_to_remove, "players: ", end="")
                            for i in range(players_to_remove):
                                print(_read_u32(databuf), end=", ")
                            players_to_sync = _read_u32(databuf)
                            print("Syncing", players_to_sync, "players: ", end="")
                            for i in range(players_to_sync):
                                print("Player id:", _read_u32(databuf), end=", ")
                                print("pos:", _read_vec2(databuf), end=", ")
                                print("vel:", _read_vec2(databuf), end=", ")
                                print("club pos:", _read_vec2(databuf), end=", ")
                                print("club vel:", _read_vec2(databuf), end=", ")
                                print("radius:", _read_f32(databuf))
                        elif packet_type == GameReceiveType.club_collision:
                            print("club collision: ", end="")
                            print("i:", _read_f32(databuf), end=", ")
                            print("first id:", _read_u32(databuf), end=", ")
                            print("first pos:", _read_vec2(databuf), end=", ")
                            print("first vel:", _read_vec2(databuf), end=", ")
                            print("second id:", _read_u32(databuf), end=", ")
                            print("second pos:", _read_vec2(databuf), end=", ")
                            print("second vel:", _read_vec2(databuf))
                        elif packet_type == GameReceiveType.wall_collision:
                            print("wall collision: ", end="")
                            print("p:", _read_vec2(databuf), end=", ")
                            print("i:", _read_f32(databuf), end=", ")
                            print("player:", _read_u32(databuf), end=", ")
                            print("pos:", _read_vec2(databuf), end=", ")
                            print("vel:", _read_vec2(databuf), end=", ")
                            print("rad:", _read_f32(databuf))
                        elif packet_type == GameReceiveType.set_leaderboard:
                            print("set leaderboard: ", end="")
                            print("# of players:", _read_u32(databuf), end=", ")
                            print("total:", _read_u32(databuf), end=", ")
                            # TODO: Assuming FFA for now
                            count = _read_u8(databuf)
                            print("count:", count)
                            for i in range(count):
                                if i == 0:
                                    print("    id:", _read_u32(databuf), end=" ")
                                else:
                                    print("    ", end="")
                                print("name:", shlex.quote(_read_string(databuf)),
                                      "score:", _read_u32(databuf))
                            print("    king:", shlex.quote(_read_string(databuf)),
                                  "score:", _read_u32(databuf),
                                  end=", ")
                            print("my place:", _read_u32(databuf), "my score:", _read_u32(databuf))
                        elif packet_type == GameReceiveType.set_target_dim:
                            print("set target dim:", _read_vec2(databuf))
                        else:
                            raise Exception("Unexpected packet type: " + str(packet_type))
                else:
                    raise Exception("Unexpected data type: " + msg.type.name)
