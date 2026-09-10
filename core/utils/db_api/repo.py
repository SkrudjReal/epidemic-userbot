
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy.sql import select, insert, delete, update

from core.utils.db_api import UserbotVictims, UserbotUserSettings, Victims, User


from datetime import datetime


class Repo:
    
    # async def insert_victim(
    #     session: AsyncSession, infecter_id: int, victimer_id: int,
    #     victimer_name: str, victim_expire: datetime, bio_resource: int
    # ):
    #     async with session.begin():
    #         await session.execute(delete(UserbotVictims).where(UserbotVictims.infecter_id == infecter_id, UserbotVictims.victimer_id == victimer_id))
    #         query = insert(UserbotVictims).values(
    #             infecter_id=infecter_id, victimer_id=victimer_id, victimer_name=victimer_name,
    #             victim_expire=victim_expire, bio_resource=bio_resource
    #         )
    #         await session.execute(query)
    
    async def get_user(session: AsyncSession, link: [int, str]):
        async with session.begin():
            user = (await session.execute(
                select(User).where(User.id == link)
            )).scalars().all()
            if not user:
                user = (await session.execute(
                    select(User).where(User.username == link)
                )).scalars().all()
            if user:
                return user
            else:
                return None
    
    async def get_victim(session: AsyncSession, infecter_id: int, victimer_id: int):
        async with session.begin():
            return (await session.execute(
                select(Victims).where(Victims.victims_owner_id == infecter_id, Victims.victim_id == victimer_id)
            )).scalars().all()
    
    # async def delete_victim(session: AsyncSession, infecter_id: int, victimer_id: int):
    #     async with session.begin():
    #         await session.execute(
    #             delete(UserbotVictims).where(UserbotVictims.infecter_id == infecter_id, UserbotVictims.victimer_id == victimer_id)
    #         )
    
    async def change_prefix(session: AsyncSession, id: int, prefix: str):
        async with session.begin():
            await session.execute(update(UserbotUserSettings).where(UserbotUserSettings.user_id==id).values(prefix=prefix))

