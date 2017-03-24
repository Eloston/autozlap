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

"""The main application"""

import asyncio
import signal
import argparse

from .constants import Mode
from . import server_selector, game_client

async def main_routine(loop, address, port, instance_count):
    """Main application routine"""
    if not address or not port:
        print("No address and port combination specified. Finding server...")
        address, port = await server_selector.select_server(loop)
    print(address + ":" + str(port))
    tasks = list()
    for _ in range(instance_count):
        tasks.append(game_client.Session(loop, Mode.ffa).start(address, port))
    await asyncio.wait(tasks)

def main(args):
    """Entry-point"""
    parser = argparse.ArgumentParser(
        description="An experimental autonomous zlap.io client")
    parser.add_argument("--address", "-a", default=None)
    parser.add_argument("--port", "-p", type=int, default=None)
    parser.add_argument("--instances", "-i", type=int, default=1)
    parsed_args = parser.parse_args(args)
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, loop.stop)
    loop.run_until_complete(main_routine(loop, parsed_args.address,
                                         parsed_args.port, parsed_args.instances))
