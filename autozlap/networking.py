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

    def __init__(self, websocket, mode, new_player_checker, current_player_checker):
        self._websocket = websocket
        self._mode = mode
        self._is_new_player = new_player_checker
        self._is_current_player = current_player_checker
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
                        construct.Check(construct.this.server_version == CLIENT_VERSION),
                        "initial_time" / construct.Int32ul,
                        "game_mode" / construct.Mapping(
                            construct.Int8ul, {
                                0: Mode.ffa,
                                1: Mode.tdm
                            },
                            dict() # This packet is only received
                        ),
                        "current_player_id" / construct.Int32ul,
                        "dimensions" / vector2d,
                        "target_dimensions" / vector2d
                    ),
                    "killed": construct.Pass,
                    "kill": construct.Struct(
                        "timestamp" / construct.Int32ul,
                        "killed_id" / construct.Int32ul,
                        "death_position" / vector2d,
                        "killer_id" / construct.Int32ul,
                        "point_orb_count" / construct.Int32ul
                    ),
                    "remove": construct.Struct(
                        "timestamp" / construct.Int32ul,
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
                                "is_new_player" / construct.Computed(
                                    lambda ctx: self._is_new_player(ctx.player_id)
                                ),
                                "player_attributes" / construct.If(
                                    construct.this.is_new_player,
                                    construct.Embedded(
                                        construct.Struct(
                                            "player_name" / construct.IfThenElse(
                                                lambda ctx: not self._is_current_player(
                                                    ctx._.player_id
                                                ),
                                                construct.CString(encoding="utf8"),
                                                construct.Pass
                                            ),
                                            "shield" / construct.Float32l,
                                            "team_or_skin" / construct.Int8ul
                                        )
                                    )
                                ),
                                "player_state" / physical_state,
                                "mace_state" / physical_state,
                                "mace_radius" / construct.Float32l
                            )
                        )
                    ),
                    "club_collision": construct.Struct(
                        "timestamp" / construct.Int32ul,
                        "p" / vector2d, # TODO: Figure out purpose
                        "i" / construct.Float32l, # TODO: Figure out purpose
                        "first_id" / construct.Int32ul,
                        "first_state" / physical_state,
                        "second_id" / construct.Int32ul,
                        "second_state" / physical_state
                    ),
                    "wall_collision": construct.Struct(
                        "timestamp" / construct.Int32ul,
                        "p" / vector2d, # TODO: Figure out purpose
                        "i" / construct.Float32l, # TODO: Figure out purpose
                        "player_id" / construct.Int32ul,
                        "player_state" / physical_state,
                        "mace_radius" / construct.Float32l
                    ),
                    "set_leaderboard": construct.Struct(
                        "player_count" / construct.Int32ul,
                        "total" / construct.Int32ul, # TODO: Figure out purpose,
                        construct.Check(lambda ctx: self._mode in Mode),
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
                    "set_target_dim": construct.Struct("target_dimensions" / vector2d)
                }
            ),
            "extraneous" / construct.GreedyBytes # For debugging
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
                parsed_packet = self._inbound_packet.parse(msg.data)
                if parsed_packet.extraneous: # For debugging
                    print("Entire packet with extraneous: " + str(msg.data))
                    print("Packet: " + str(parsed_packet))
                parsed_callback(parsed_packet)
            else:
                raise ValueError("Unexpected data type: " + msg.type.name)

    def send(self, packet):
        """Builds and sends a packet"""
        self._websocket.send_bytes(self._outbound_packet.build(packet))
