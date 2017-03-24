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

"""
Networking component. Implements packet parsing
"""

import construct
import aiohttp

from .constants import CLIENT_VERSION, Mode

vector2d = construct.Struct( #pylint: disable=invalid-name
    "x" / construct.Float32l,
    "y" / construct.Float32l
)

physical_state = construct.Struct( #pylint: disable=invalid-name
    "position" / vector2d,
    "velocity" / vector2d
)

class Connection:
    """Represents the stateful networking connection"""

    def __init__(self, websocket, mode):
        self._websocket = websocket
        self._mode = mode
        self._inbound_packet = construct.Struct(
            "type" / construct.Enum(
                construct.Int8ul,
                setup=0,
                killed=1,
                kill=2,
                remove=3,
                sync=4,
                club_collision=5,
                wall_collision=6,
                set_leaderboard=7,
                set_target_dim=8
            ),
            "payload" / construct.Switch(
                construct.this.type, {
                    "setup": construct.Struct(
                        "server_version" / construct.CString(encoding="utf8"),
                        construct.Check(lambda ctx: ctx.server_version == CLIENT_VERSION),
                        "syncer_value" / construct.Int32ul,
                        "game_mode" / construct.Mapping(
                            construct.Int8ul, {
                                0: Mode.ffa,
                                1: Mode.tdm
                            },
                            dict() # This packet is only received
                        ),
                        "setup_value" / construct.Int32ul
                    ),
                    "killed": construct.Pass,
                    "kill": construct.Struct("stamp" / construct.Int32ul),
                    "remove": construct.Struct(
                        "enqueue_param" / construct.Int32ul, # TODO: Figure out purpose
                        "player_id" / construct.Int32ul
                    ),
                    "sync": construct.Struct(
                        "timestamp" / construct.Int32ul,
                        "remove_count" / construct.Int32ul,
                        "removal_array" / construct.Array(
                            construct.this.remove_count,
                            construct.Int32ul
                        ),
                        "sync_count" / construct.Int32ul,
                        "sync_array" / construct.Array(
                            construct.this.sync_count,
                            construct.Struct(
                                "player_id" / construct.Int32ul,
                                "player_state" / physical_state,
                                "mace_state" / physical_state,
                                "mace_radius" / construct.Float32l
                            )
                        )
                    ),
                    "club_collision": construct.Struct(
                        "enqueue_param" / construct.Int32ul, # TODO: Figure out purpose
                        "p" / vector2d, # TODO: Figure out purpose
                        "i" / construct.Float32l, # TODO: Figure out purpose
                        "first_id" / construct.Int32ul,
                        "first_state" / physical_state,
                        "second_id" / construct.Int32ul,
                        "second_state" / physical_state
                    ),
                    "wall_collision": construct.Struct(
                        "enqueue_param" / construct.Int32ul, # TODO: Figure out purpose
                        "p" / vector2d, # TODO: Figure out purpose
                        "i" / construct.Float32l, # TODO: Figure out purpose
                        "player_id" / construct.Int32ul,
                        "player_state" / physical_state,
                        "mace_radius" / construct.Float32l
                    ),
                    "set_leaderboard": construct.Struct(
                        "player_count" / construct.Int32ul,
                        "total" / construct.Int32ul, # TODO: Figure out purpose,
                        construct.IfThenElse(
                            lambda ctx: self._mode == Mode.ffa,
                            construct.Struct( # FFA
                                "count" / construct.Int8ul,
                                "first_entry_id" / construct.Int32ul,
                                "leaderboard" / construct.Array(
                                    construct.this.count,
                                    construct.Struct(
                                        "name" / construct.CString(encoding="utf8"),
                                        "score" / construct.Int32ul,
                                        )
                                    ),
                                "king_name" / construct.CString(encoding="utf8"),
                                "king_score" / construct.Int32ul,
                                "place" / construct.Int32ul,
                                "score" / construct.Int32ul
                            ),
                            construct.Array(
                                3,
                                construct.Struct(
                                    "id" / construct.Int8ul,
                                    "score" / construct.Int32ul,
                                    "count" / construct.Int32ul
                                )
                            )
                        )
                    ),
                    "set_target_dim": construct.Struct("target_dim" / vector2d)
                }
            )
        )
        self._outbound_packet = construct.Struct(
            "type" / construct.Enum(
                construct.Int8ul,
                play=0,
                direction=1,
                move_up=2,
                move_down=3,
                move_left=4,
                move_right=5,
                stop_move_up=6,
                stop_move_down=7,
                stop_move_left=8,
                stop_move_right=9
            ),
            "payload" / construct.Switch(
                construct.this.type, {
                    "play": construct.Pass
                            # TODO: Implement the rest of the packets
                }
            )
        )

    async def listen_loop(self, parsed_callback):
        """Async listening loop"""
        async for msg in self._websocket:
            if msg.type == aiohttp.WSMsgType.BINARY:
                parsed_callback(self._inbound_packet.parse(msg.data))
            else:
                raise ValueError("Unexpected data type: " + msg.type.name)

    def send(self, packet):
        """Builds and sends a packet"""
        self._websocket.send_bytes(self._outbound_packet.build(packet))
