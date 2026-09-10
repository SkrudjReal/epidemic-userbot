from pyrogram.types import Message, User
from pyrogram.errors.exceptions import PeerIdInvalid, FloodWait
from pyrogram import Client, enums

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql import select, insert, delete
from redis.asyncio import Redis

from core.utils.db_api import UserbotTrustedUsers
from core.utils.db_api.repo import Repo
from core.data.tricks.tricks import tricks
from core.data import triggers as trg
from core.functions import base_func, respond_func

from humanize import intcomma
from datetime import datetime, timedelta
from loguru import logger

import re
import asyncio
import json
import html

async def main_skills(app: Client, msg: Message, me: User, session: async_sessionmaker[AsyncSession], redis: Redis):
    
    trusted_ids = await redis.lrange(f'epidemic_userbot_trusted:{me.id}', 0, -1)
    
    if msg.from_user.id != me.id and str(msg.from_user.id) not in trusted_ids:
        return
    
    if msg.reply_to_message:
        reply_text = msg.reply_to_message.text
    
    prefix = await redis.hget(f'epidemic_userbot:{me.id}', 'prefix')
    
    # Infect
    if msg.text is not None and (
        re.fullmatch(f'{re.escape(prefix)}б' + r'\s{1,3}' + r'(\d{1,2}\s{1,3}|)' + trg.re_link_sup, msg.text, re.IGNORECASE)
        or
        re.fullmatch(f'{prefix}б' + r'(\s{1,3}\d{1,2}|)', msg.text.lower()) and msg.reply_to_message and (
            reply_text and msg.reply_to_message.text.lower().startswith(tricks['game_texts']['sec_serv']) or
            reply_text and
            re.findall(r'🦠 .+ подвер[гла]{1,3} заражению', msg.reply_to_message.text.splitlines()[0], re.IGNORECASE)
            or reply_text and '🪬 Иммунитет объекта' in msg.reply_to_message.text and
            msg.reply_to_message.entities and
            len(msg.reply_to_message.entities) == 1
        ) or
        msg.reply_to_message and (
            reply_text and '@' in msg.reply_to_message.text
            or
            msg.reply_to_message.entities and len(msg.reply_to_message.entities) >= 1
        ) and
        re.fullmatch(f'{re.escape(prefix)}б' + r'\s{1,3}([-\d\s]{1,20})', msg.text, re.IGNORECASE)
    ):
        quote = False
        list_infect = False
        msg_to = msg
        link = None
        pathogens_to_use = False
        # Check usage pathogens
        if len(msg.text.split()) > 1 and msg.text.split()[1].isdigit():
            pathogens_to_use = msg.text.split()[1]
        # Default self message tag
        if re.fullmatch(f'{re.escape(prefix)}б' + r'\s{1,3}' + r'(\d{1,2}\s{1,3}|)' + trg.re_link_sup, msg.text, re.IGNORECASE):
            link = base_func.link_getter(msg.text)
        # Reply to security service
        if (
            msg.reply_to_message and
            msg.reply_to_message.text.lower().startswith(tricks['game_texts']['sec_serv']) and
            len(msg.reply_to_message.entities) >= 3
        ):
            link = base_func.link_getter(msg.reply_to_message.entities[2].url)
            quote = True
            msg_to = msg.reply_to_message
        # Reply to infect bot message
        elif (
            msg.reply_to_message and
            re.findall(r'🦠 .+ подвер[гла]{1,3} заражению', msg.reply_to_message.text.splitlines()[0], re.IGNORECASE) and
            len(msg.reply_to_message.entities) >= 2
        ):
            link = base_func.link_getter(msg.reply_to_message.entities[1].url)
        # Reply to failed infect bot message
        elif (
            msg.reply_to_message and '🪬 Иммунитет объекта' in msg.reply_to_message.text and
            msg.reply_to_message.entities and len(msg.reply_to_message.entities) == 1
        ):
            link = base_func.link_getter(msg.reply_to_message.entities[0].url)
        # Reply to entities/link list
        elif (
            msg.reply_to_message and
            re.fullmatch(f'{re.escape(prefix)}б' + r'\s{1,3}([-\d\s]{1,20})', msg.text, re.IGNORECASE)
        ):
            list_infect = True
            link = [base_func.link_getter(link) for link in msg.reply_to_message.text.html.splitlines() if base_func.link_getter(link)]
            nums = msg.text.split()[1:]
            nums_list = []
            links_list = []
            for num in nums:
                if '-' in num:
                    num_spl = num.split('-')
                    nums_list += [n - 1 for n in range(int(num_spl[0]), int(num_spl[1]) + 1)]
                else:
                    nums_list.append(int(num)-1)
            links_list += [l for n, l in enumerate(link, 0) if n in nums_list]
            link = links_list
        
        if not link:
            err = await msg.reply(tricks['errors']['something_went_wrong'])
            return asyncio.create_task(respond_func.delete_msg([err, msg], tricks['config']['small_timeout']))
        
        text = f'Заразить{" "+pathogens_to_use+" " if pathogens_to_use else " "}@{link}'
        
        if list_infect:
            link_list = link
            link = link[-1]
            await redis.set(f'epidemic_userbot_infect_stop:{me.id}', 0)
            if link_list[:-1] != []:
                for lnk in link_list[:-1]:
                    infect_is_stop = await redis.get(f'epidemic_userbot_infect_stop:{me.id}')
                    
                    if infect_is_stop and int(infect_is_stop) == 1:
                        err = await msg.reply(tricks['errors']['infect_list_stop'])
                        await redis.set(f'epidemic_userbot_infect_stop:{me.id}', 0)
                        return asyncio.create_task(respond_func.delete_msg([err, msg], tricks['config']['medium_timeout']))
                        
                    
                    msg_infect = await msg_to.reply(f'Заразить @{lnk}', quote=quote)
                    exp = 0
                    async with session() as ses:
                        user = await Repo.get_user(ses, lnk)
                        if user:
                            get_victim = await Repo.get_victim(ses, me.id, user[0].id)
                            if get_victim:
                                exp = get_victim[0].victim_bio_resource_earn
                    
                    await redis.lpush(f'epidemic_userbot_victim:{me.id}:{lnk}', f'{msg_infect.id}:{exp}')
                    await redis.expire(f'epidemic_userbot_victim:{me.id}:{lnk}', 6)
                    await asyncio.sleep(tricks['config']['list_infect_delay'])
            text = f'Заразить @{link}'
            quote = True
            msg_to = msg.reply_to_message
        
        exp = 0
        async with session() as ses:
            user = await Repo.get_user(ses, link)
            if user:
                get_victim = await Repo.get_victim(ses, me.id, user[0].id)
                if get_victim:
                    exp = get_victim[0].victim_bio_resource_earn
        
        msg_infect = await msg_to.reply(text, quote=quote)
        await redis.lpush(f'epidemic_userbot_victim:{me.id}:{link}', f'{msg_infect.id}:{exp}')
        await redis.expire(f'epidemic_userbot_victim:{me.id}:{link}', 6)
        if not list_infect: await msg.delete()
    
    # Buy vaccine
    if msg.text.lower() == f'{prefix}х':
        await msg.reply(tricks['triggers']['buy_vaccine'], quote=False)
        await msg.delete()
    
    # Get small info about lab
    if msg.text.lower() == f'{prefix}ла':
        lab_receive = await redis.hget(f'epidemic_userbot:{me.id}', 'lab_receive_progress')
        if lab_receive and int(lab_receive):
            err = await msg.reply(tricks['errors']['lab_receive_in_progress'])
            return asyncio.create_task(respond_func.delete_msg([err, msg], tricks['config']['small_timeout']))
        await redis.hset(f'epidemic_userbot:{me.id}', 'lab_receive_progress', 1)
        
        lab = await respond_func.get_lab(app, me)
        
        # error
        if not lab:
            err = await msg.reply(tricks['errors']['something_went_wrong'])
            await redis.hset(f'epidemic_userbot:{me.id}', 'lab_receive_progress', 0)
            return asyncio.create_task(respond_func.delete_msg([err, msg], tricks['config']['medium_timeout']))
        await redis.hset(f'epidemic_userbot:{me.id}', 'lab_receive_progress', 0)
        
        msg_lab = await msg.reply('<blockquote>' + '\n'.join(lab) + '</blockquote>')
        asyncio.create_task(respond_func.delete_msg([msg_lab, msg], tricks['config']['medium_timeout']))
    
    # Trusted
    if (
        msg.from_user.id == me.id and (
            msg.reply_to_message and re.fullmatch(r'(-|\+)дов', msg.text, re.IGNORECASE)
            or
            re.fullmatch(r'(-|\+)дов\s{1,3}' + trg.re_link_sup, msg.text, re.IGNORECASE)
        )
    ):
        trusted_name = False
        trust_id = base_func.link_getter(msg.text)
        
        if msg.reply_to_message and not trust_id:
            trust_id = msg.reply_to_message.from_user.id
            trusted_name = msg.reply_to_message.from_user.full_name
        else:
            try:
                trusted_entity = await app.get_users(trust_id)
            except PeerIdInvalid:
                err = await msg.reply(tricks['errors']['user_not_found'])
                return asyncio.create_task(respond_func.delete_msg([err, msg], tricks['config']['medium_timeout']))
            except FloodWait as err:
                err = await msg.reply(tricks['errors']['flood_wait'].format(err.value / 60))
                return asyncio.create_task(respond_func.delete_msg([err, msg], tricks['config']['medium_timeout']))
            trusted_name = trusted_entity.full_name
            trust_id = trusted_entity.id
        
        async with session() as ses:
            is_trusted = (await ses.execute(
                select(UserbotTrustedUsers).where(UserbotTrustedUsers.user_id == me.id, UserbotTrustedUsers.trusted_user_id == trust_id)
                )).all()
        
        trusted_mention = base_func.entity_create(trust_id, html.escape(trusted_name))
        
        # errors
        if '+' in msg.text and is_trusted:
            err = await msg.reply(tricks['errors']['already_trusted'].format(trusted_mention))
            return asyncio.create_task(respond_func.delete_msg([err, msg], tricks['config']['small_timeout']))
        elif '-' in msg.text and not is_trusted:
            err = await msg.reply(tricks['errors']['trusted_not_exist'].format(trusted_mention))
            return asyncio.create_task(respond_func.delete_msg([err, msg], tricks['config']['small_timeout']))
        
        
        if '+' in msg.text:
            async with session() as ses:
                await ses.execute(insert(UserbotTrustedUsers).values(user_id=me.id, trusted_user_id=trust_id))
            await redis.rpush(f'epidemic_userbot_trusted:{me.id}', trust_id)
            text = tricks['game_texts']['add_trusted'].format(trusted_mention)
            if me.id == trust_id:
                text = tricks['game_texts']['add_trusted_self'].format(trusted_mention)
        else:
            async with session() as ses:
                await ses.execute(
                    delete(UserbotTrustedUsers).where(UserbotTrustedUsers.user_id == me.id, UserbotTrustedUsers.trusted_user_id == trust_id)
                )
            await redis.lrem(f'epidemic_userbot_trusted:{me.id}', 1, str(trust_id))
            text = tricks['game_texts']['remove_trusted'].format(trusted_mention)
            if me.id == trust_id:
                text = tricks['game_texts']['remove_trusted_self'].format(trusted_mention)
        
        await msg.edit(text)
    
    # check victim
    if (
        re.fullmatch('(' + re.escape(prefix) + r'|)(оп|о)\s' + trg.re_link_sup, msg.text, re.IGNORECASE)
        or
        re.fullmatch('(' + re.escape(prefix) + r'|)(оп|о)', msg.text, re.IGNORECASE) and
        msg.reply_to_message and (
            reply_text and msg.reply_to_message.text.lower().startswith(tricks['game_texts']['sec_serv']) or
            reply_text and
            re.findall(r'🦠 .+ подвер[гла]{1,3} заражению', msg.reply_to_message.text.splitlines()[0], re.IGNORECASE)
            or reply_text and '🪬 Иммунитет объекта' in msg.reply_to_message.text and
            msg.reply_to_message.entities and
            len(msg.reply_to_message.entities) == 1
    )):
        victim_id = base_func.link_getter(msg.text)
        victim = victim_name = victim_mention = None
        
        # Reply to security service
        if (
            msg.reply_to_message and
            msg.reply_to_message.text.lower().startswith(tricks['game_texts']['sec_serv']) and
            len(msg.reply_to_message.entities) >= 3
        ):
            victim_id = base_func.link_getter(msg.reply_to_message.entities[2].url)
        # Reply to infect bot message
        elif (
            msg.reply_to_message and
            re.findall(r'🦠 .+ подвер[гла]{1,3} заражению', msg.reply_to_message.text.splitlines()[0], re.IGNORECASE) and
            len(msg.reply_to_message.entities) >= 2
        ):
            victim_id = base_func.link_getter(msg.reply_to_message.entities[1].url)
        # Reply to failed infect bot message
        elif (
            msg.reply_to_message and '🪬 Иммунитет объекта' in msg.reply_to_message.text and
            msg.reply_to_message.entities and len(msg.reply_to_message.entities) == 1
        ):
            victim_id = base_func.link_getter(msg.reply_to_message.entities[0].url)
        
        if not str(victim_id).isdigit():
            try:
                entity = await app.get_users(victim_id)
            except PeerIdInvalid:
                err = await msg.reply(tricks['errors']['user_not_found'])
                return asyncio.create_task(respond_func.delete_msg([err, msg], tricks['config']['medium_timeout']))
            except FloodWait as err:
                err = await msg.reply(tricks['errors']['flood_wait'].format(err.value / 60))
                return asyncio.create_task(respond_func.delete_msg([err, msg], tricks['config']['medium_timeout']))
            except Exception as e:
                logger.erorr(e)
            victim_id = entity.id
            victim_name = html.escape(entity.full_name)
        
        async with session() as ses:
            victim = await Repo.get_victim(ses, me.id, victim_id)
            victim_user = await Repo.get_user(ses, victim_id)
            if victim and not victim_name:
                victim_name = victim_user[0].full_name
                victim_id = victim[0].victim_id
        
        if victim_name:
            victim_mention = base_func.entity_create(victim_id, victim_name)
        
        if victim:
            text = tricks['game_texts']['check_victim_infected'].format(
                victim_mention, intcomma(victim[0].victim_bio_resource_earn), victim_id
            )
        else:
            text = tricks['game_texts']['check_victim_new'].format(victim_id)
            if victim_mention:
                text = tricks['game_texts']['check_victim_new_entity'].format(victim_mention, victim_id)
        
        # trigger on all trusted by o, but solve problem with spam by trusted users
        if prefix in msg.text.split()[0]:
            sended_msg = await msg.reply(text, quote=False)
        else:
            sended_msg = await msg.reply(text)
        asyncio.create_task(respond_func.delete_msg([sended_msg, msg], tricks['config']['smal_plus_timeout']))
    
    # notexec
    if f'{prefix}зз' == msg.text.lower() and msg.reply_to_message and msg.reply_to_message.text:
        
        title = msg.reply_to_message.text.splitlines()[0]
        
        if title not in tricks['game_texts']['notexec_allow_list']:
            err = await msg.reply(tricks['errors']['notexec_list_not_supported'])
            return asyncio.create_task(respond_func.delete_msg([err, msg], tricks['config']['medium_timeout']))
        
        biotop_chat = tricks['game_texts']['biotop_chat']
        biotop = tricks['game_texts']['biotop']
        my_victims = tricks['game_texts']['my_victims']
        
        victims_list = []
        for titles in tricks['game_texts']['notexec_allow_list']:
            if title == titles:
                victims_list.append('<b>' + titles.replace('🔬', '📖') + '</b>\n')
                break
        num = 0
        
        async with session() as ses:
            for r in msg.reply_to_message.text.html.splitlines():
                if '?user_id=' in r:
                    num += 1
                    id = re.search(r'\?user_id=(\d{4,16})">.+</a>', r).group(1)
                    name = re.search(r'\?user_id=\d{4,16}">(.+)</a>', r).group(1)
                    if title == biotop or title == biotop_chat:
                        exp = int(re.search(r'\| ([\d,]{1,64}) опыт', r).group(1).replace(',', ''))
                    elif title == my_victims:
                        exp = int(re.search(r'\| (\+[,\d]{1,64}) \|', r).group(1).replace(',', ''))
                    victim = await Repo.get_victim(ses, me.id, id)
                    victim_user = await Repo.get_user(ses, id)
                    if victim:
                        mention = base_func.entity_create(id, victim_user[0].full_name)
                        mention_nostyle = mention
                        plus_exp = int(exp*0.20)-victim[0].victim_bio_resource_earn
                        mention = (f'<b>{mention}</b>' if plus_exp>0 else f'<i>{mention}</i>')
                        plus_exp_nostyle = (f'+{intcomma(plus_exp)} 🧬' if plus_exp>0 else f'{intcomma(plus_exp)} ☁️')
                        if plus_exp == 0:
                            plus_exp_nostyle = f'{intcomma(plus_exp)} 💭'
                        if plus_exp == 0:
                            plus_exp = f'<b>{intcomma(plus_exp)}</b> 💭'
                        else:
                            plus_exp = (f'<b>+{intcomma(plus_exp)}</b> 🧬' if plus_exp>0 else f'<i>{intcomma(plus_exp)}</i> ☁️')
                        text = (
                            f'{num}. {mention_nostyle if title == my_victims else mention} '
                            f'{plus_exp_nostyle if title == my_victims else plus_exp}'
                        )
                    else:
                        mention = base_func.entity_create(id, name)
                        get_exp = (1 if int(exp*0.20) <= 0 else intcomma(int(exp*0.20)))
                        text = f'{num}. {mention} {f"+<b>{get_exp}</b>" if title == my_victims else f"+{get_exp}"} ✨'
                    victims_list.append(text)
        
        send_msg = await msg.reply_to_message.reply('\n'.join(victims_list))
        asyncio.create_task(respond_func.delete_msg([send_msg, msg], tricks['config']['huge_timeout']))
    
    # change prifix
    if msg.from_user.id == me.id and re.fullmatch(r'\.(преф|префикс) .+', msg.text, re.IGNORECASE):
        pref = msg.text.split()[1]
        mention = base_func.entity_create(me.id, me.full_name)
        
        # errors
        if len(pref) >= 2:
            err = await msg.reply(tricks['errors']['prefix_too_long'])
            return asyncio.create_task(respond_func.delete_msg([err, msg], tricks['config']['small_timeout']))
        
        async with session() as ses:
            await Repo.change_prefix(ses, me.id, pref)
            await redis.hset(f'epidemic_userbot:{me.id}', 'prefix', pref)
        
        send_msg = await msg.reply(tricks['game_texts']['change_prefix'].format(mention, pref))
        asyncio.create_task(respond_func.delete_msg([send_msg, msg], tricks['config']['medium_timeout']))
    
    # calculator skiils level up
    if (
        msg.from_user.id == me.id and
        re.fullmatch(r'\.к (%(skills)s \d{1,64}|\d{1,64} %(skills)s) \d{1,64}' % {'skills': trg.re_skills}, msg.text, re.IGNORECASE)
    ):
        parts = msg.text.split()
        if parts[1].isdigit():
            from_lvl, skill, to_lvl = int(parts[1]), parts[2], int(parts[3])
        else:
            skill, from_lvl, to_lvl = parts[1], int(parts[2]), int(parts[3])
        
        # errors
        if from_lvl > to_lvl or from_lvl == to_lvl or from_lvl == 0 or to_lvl == 0:
            err = await msg.reply(tricks['errors']['invalid_skills_level'])
            return asyncio.create_task(respond_func.delete_msg([err, msg], tricks['config']['small_timeout']))
        if to_lvl - from_lvl > 999999:
            err = await msg.reply(tricks['errors']['skills_level_too_high'])
            return asyncio.create_task(respond_func.delete_msg([err, msg], tricks['config']['small_timeout']))
        
        text = base_func.skills_calc(skill, from_lvl, to_lvl)
        
        sended_msg = await msg.reply(text, quote=False)
        asyncio.create_task(respond_func.delete_msg([sended_msg, msg], tricks['config']['huge_timeout']))
    


