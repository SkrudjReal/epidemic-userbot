from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from dispyro import Dispatcher

from typing import List, Tuple

from core.data.tricks.tricks import tricks
from core.data import triggers as trg
from core.filters.is_infect import infect

from .main_skills import main_skills
from .helpers import helper
from .infect_manager import self_victim_infect, auto_write_infect, stop_infect


async def setup_handlers(apps_dp: Tuple[List[Client], List[Dispatcher]]) -> None:
    # Loop through all dispatchers and register handlers
    for dp in apps_dp[1]:
        dp.message.register(main_skills)
        dp.message.register(helper)
        dp.message.register(self_victim_infect, filters.me & infect)
        dp.message.register(auto_write_infect, filters.user(tricks['game']['bot_id']))
        dp.message.register(stop_infect, filters.regex('б стоп'))


