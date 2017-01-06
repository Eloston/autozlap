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

'''Constants'''

import enum

CLIENT_VERSION = "32"

class Mode(enum.Enum):
    '''Enum for game modes'''
    ffa = "ffa"
    tdm = "tdm"

class GameSendType(enum.IntEnum):
    '''Enum for packet sending headers'''
    play = 0
    direction = 1
    move_up = 2
    move_down = 3
    move_left = 4
    move_right = 5
    stop_move_up = 6
    stop_move_down = 7
    stop_move_left = 8
    stop_move_right = 9

class GameReceiveType(enum.IntEnum):
    '''Enum for packet receiving headers'''
    setup = 0
    killed = 1
    kill = 2
    remove = 3
    sync = 4
    club_collision = 5
    wall_collision = 6
    set_leaderboard = 7
    set_target_dim = 8
