from pyrogram import filters

from core.data.triggers import re_infect, re_infect_reply

import re

async def func(_, __, msg):
    return (re.fullmatch(re_infect, msg.text) or re.fullmatch(re_infect_reply, msg.text) and msg.reply_to_message)

infect = filters.create(func)