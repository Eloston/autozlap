# -*- coding: UTF-8 -*-

# autozlap: An experimental autonomous zlap.io client
# Copyright (C) 2018  Eloston
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

"""Pre-game client component for selecting servers"""

import time

import aiohttp

from .constants import Mode, CLIENT_VERSION

_SERVERS_URL = "http://zlap.io/servers.json?_={time}"

async def _fetch_servers_json(loop):
    """Fetches the list of servers in JSON format"""
    async with aiohttp.ClientSession(loop=loop) as session:
        current_time = int(time.time()*1000)
        async with session.get(_SERVERS_URL + str(current_time)) as response:
            return await response.json()

async def select_server(loop, mode=Mode.ffa, ignore_empty_servers=True):
    """Picks a server given argument restrictions and returns a tuple (address, port)"""
    server_list = await _fetch_servers_json(loop)
    for server_sub_list in server_list:
        for server in server_sub_list:
            if not server["version"] == CLIENT_VERSION:
                raise Exception("Unsupported server version: " + server["version"])
            if not server["mode"] == mode.value:
                continue
            if ignore_empty_servers and not server["players"] > 0:
                continue
            return tuple(server["address"].split(":"))
