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

'''The main application'''

import asyncio

from . import server_selector, game_client

async def main_routine(loop):
    '''Main application routine'''
    address, port = await server_selector.select_server(loop)
    print(address + ":" + str(port))
    await game_client.game_client_routine(loop, address, port)

def main(args):
    '''Entry-point'''
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_routine(loop))
