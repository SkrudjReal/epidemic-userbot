from pyrogram.errors.exceptions import PeerIdInvalid, FloodWait
from pyrogram.types import Message, User
from pyrogram import Client

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy.sql import select
from redis.asyncio import Redis

from core.utils.db_api import UserbotTrustedUsers
from core.data.tricks.tricks import tricks
from core.data.triggers import deep_links
from core.functions import base_func, respond_func

import re
import html
import asyncio

async def helper(app: Client, msg: Message, me: User, session: async_sessionmaker[AsyncSession], redis: Redis):
    
    trusted_ids = await redis.lrange(f'epidemic_userbot_trusted:{me.id}', 0, -1)
    
    if msg.from_user.id != me.id and str(msg.from_user.id) not in trusted_ids:
        return
    
    prefix = await redis.hget(f'epidemic_userbot:{me.id}', 'prefix')
    
    # Userbot menu
    if (
        re.fullmatch(prefix + r'\s(помощь|help|хелп|меню|менюшка)', msg.text, re.IGNORECASE) or
        msg.from_user.id == me.id and re.fullmatch(r'(мой свиток|\.меню|\.менюшка|\.х[еэ]лп|мое меню)', msg.text, re.IGNORECASE)
    ):
        me_entity = base_func.entity_create(me.id, html.escape(me.full_name), deep_links['mention_click'])
        
        trusted_list_text, trusted_list = '', []
        
        async with session() as ses:
            trusted_users = (await ses.execute(select(UserbotTrustedUsers).where(UserbotTrustedUsers.user_id == me.id))).scalars().all()
            trusted_list.extend(id.trusted_user_id for id in trusted_users)
        
        if not trusted_list:
            trusted_list_text = tricks['game_texts']['no_trusted_users']
        else:
            for num, id in enumerate(trusted_list, 1):
                try:
                    trusted_entities = await app.get_users(id)
                except (PeerIdInvalid, FloodWait):
                    trusted_list_text += f'<i>{"💗" if me.id==id else str(num)+"."} {id}</i>\n'
                else:
                    mention = base_func.entity_create(id, html.escape(trusted_entities.full_name))
                    trusted_list_text += f'<i>{"💗" if me.id==id else str(num)+"."} {mention}</i>\n'
        
        text = (
            tricks['game_texts']['userbot_menu'].format(
                me_entity, trusted_list_text
            ) % {'prefix': prefix.title(), 'me_id': me.id, 'bot_username': tricks['game']['bot_username']}
        )
        
        sended_msg = await msg.reply(text, disable_web_page_preview=True)
        asyncio.create_task(respond_func.delete_msg([sended_msg, msg], tricks['config']['6_minutes_timeout']))



