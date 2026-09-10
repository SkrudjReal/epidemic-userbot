from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy.sql import select, delete

from core.utils.db_api import UserbotVictims

from datetime import datetime

import asyncio
import sys
import os

async def expire_victims(session: async_sessionmaker[AsyncSession]):
    async with session() as ses:
        async with ses.begin():
            victims = await ses.execute(select(UserbotVictims).where(UserbotVictims.victim_expire < datetime.utcnow()))
            for victim in victims:
                await ses.execute(delete(UserbotVictims).where(
                    UserbotVictims.infecter_id==victim.infecter_id, UserbotVictims.victimer_id==victim.victimer_id
                ))

async def on_new_session():
    path = os.path.abspath('.')
    session_files_old = [e for e in os.listdir(f'{path}/core/sessions') if e.endswith('session')]
    
    while True:
        await asyncio.sleep(30)
        session_files = [e for e in os.listdir(f'{path}/core/sessions') if e.endswith('session')]
        if session_files != session_files_old:
            python = sys.executable
            os.execl(python, python, *sys.argv)