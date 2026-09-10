from pyrogram import Client, idle, filters, enums
from pyrogram.handlers import MessageHandler
from dispyro.enums import RunLogic
from dispyro import Dispatcher

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.sql import select, insert, text

from redis.asyncio import Redis

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from typing import List, Tuple
from loguru import logger
from datetime import datetime

# local imports
from core.settings import settings
from core.handlers import setup_handlers
from core.utils.db_api import UserUserBot, UserbotUserSettings, UserbotTrustedUsers, UserUserBotData
from core.filters.is_user import is_user
from core.services.loop_tasks import expire_victims, on_new_session

import asyncio
import uvloop
import logging
import json
import os

async def load_user_settings(
    apps_dp: Tuple[List[Client], List[Dispatcher]],
    session: async_sessionmaker[AsyncSession],
    redis: Redis
):
    # Load prefixes value from db and save it to redis
    async with session() as ses:
        # Query to select distinct owner_id, api_id, and api_hash
        distinct_query = (text("""
            SELECT DISTINCT owner_id, api_id, api_hash, phone_number FROM UsersUserbots 
            INNER JOIN UsersUserbotsData ON UsersUserbots.id=UsersUserbotsData.ub_id;
            """)
        )
        
        # Execute the query and fetch results
        results = (await ses.execute(distinct_query)).all()
        
        # check on prefix
        for uid in results:
            user_id = uid[0]
            query = (await ses.execute(select(UserbotUserSettings).where(UserbotUserSettings.user_id==user_id))).scalars().all()
            if not query:
                await ses.execute(insert(UserbotUserSettings).values(user_id=user_id))
        prefixes = (await ses.execute(select(UserbotUserSettings))).scalars().all()
        trusted = (await ses.execute(select(UserbotTrustedUsers))).scalars().all()
        async with redis.pipeline() as pipe:
            for row in prefixes:
                pipe.hset(f'epidemic_userbot:{row.user_id}', 'prefix', row.prefix)
            for row in trusted:
                await redis.delete(f'epidemic_userbot_trusted:{row.user_id}')
                pipe.rpush(f'epidemic_userbot_trusted:{row.user_id}', row.trusted_user_id)
            await pipe.execute()
        

async def start_clients(session: async_sessionmaker[AsyncSession], redis: Redis) -> Tuple[List[Client], List[Dispatcher]]:
    apps_dp = [[], []]
    app_ids = {}
    path = os.path.abspath('.')
    session_files = [e.replace('.session', '') for e in os.listdir(f'{path}/core/sessions') if e.endswith('session')]
    # Get all users api from db and creating client object
    async with session() as ses:
        # Query to select distinct owner_id, api_id, and api_hash
        distinct_query = (text("""
            SELECT DISTINCT owner_id, api_id, api_hash, phone_number FROM UsersUserbots 
            INNER JOIN UsersUserbotsData ON UsersUserbots.id=UsersUserbotsData.ub_id;
            """)
        )
        
        # Execute the query and fetch results
        users = (await ses.execute(distinct_query)).all()
        for row in users:
            if str(row[0]) not in session_files:
                continue
            app = Client(
                f'core/sessions/{row[0]}',
                row[1],
                row[2],
                phone_number=[3],
                parse_mode=enums.ParseMode.HTML
            )
            apps_dp[0].append(app)
            app_ids[app] = str(row[0])
    
    for c in apps_dp[0].copy():
        try:
            await c.start()
        except:
            app_id = app_ids.get(c)
            if app_id and app_id in session_files:
                os.remove(f'{path}/core/sessions/{app_id}.session')
            apps_dp[0].pop(str(c))
        else:
            await c.stop()
    
    # Invoke start method of all clients & dispatchers
    await asyncio.gather(*[c.start() for c in apps_dp[0]])
    
    for app in apps_dp[0]:
        me = await app.get_me()
        dp = Dispatcher(app, me=me, session=session, redis=redis, run_logic=RunLogic.UNLIMITED)
        dp.message.filter(filters.text & is_user & ~filters.forwarded & (filters.private | filters.group))
        apps_dp[1].append(dp)
    
    return apps_dp

# Looped tasks
async def loop_tasks(scheduler: AsyncIOScheduler, session: async_sessionmaker[AsyncSession]):
    scheduler.add_job(expire_victims, 'interval', minutes=30, kwargs={'session': session})
    scheduler.add_job(on_new_session, 'date', run_date=datetime.now())
    

async def main():
    
    logging.basicConfig(level=logging.ERROR,
                        format = '%(asctime)s - [%(levelname)s] - %(name)s - '
                        '(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s')
    engine = create_async_engine(url=settings.db_url.get_secret_value(), echo=False, isolation_level='AUTOCOMMIT')
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    redis = Redis(host=settings.redis_ip.get_secret_value(), port=6379, db=0, decode_responses=True)
    scheduler = AsyncIOScheduler()
    
    # apps & dispatcher objects
    apps_dp = await start_clients(sessionmaker, redis)
    
    asyncio.create_task(loop_tasks(scheduler, sessionmaker))
    
    await load_user_settings(apps_dp, sessionmaker, redis)
    await setup_handlers(apps_dp)
    
    try:
        logger.info('Started successfully')
        scheduler.start()
        await idle()
    finally:
        pass


if __name__ == '__main__':
    try:
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print('Goodbye!')