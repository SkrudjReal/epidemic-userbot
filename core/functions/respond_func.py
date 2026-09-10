from pyrogram import Client
from pyrogram.types import Message, User

from core.data.tricks.tricks import tricks

from typing import Union, List

import asyncio
import re
import html

async def get_lab(app: Client, me: User) -> Union[None, str]:
    delay = tricks['config']['lab_get_delay']
    retry_count = 3
    while True:
        self_msg_lab = await app.send_message(tricks['game']['bot_username'], 'Моя лаборатория')
        await asyncio.sleep(delay)
        bot_msg_lab = await app.get_messages(tricks['game']['bot_id'], message_ids=self_msg_lab.id+1)
        await self_msg_lab.delete()
        if not bot_msg_lab.empty: await bot_msg_lab.delete()
        if retry_count <= 0:
            return None
        if bot_msg_lab.empty or bot_msg_lab.text and '🍁 Досье лаборатории' not in bot_msg_lab.text:
            delay += 0.2
            retry_count -= 1
            await asyncio.sleep(delay)
            continue
        mention = f'<a href="tg://user?id={me.id}">{html.escape(me.full_name)}</a>'
        text = (
            f'<b>Силуэт лаборатории {mention}</b>\n',
            ''.join(re.findall(r'🧪 Готовых патогенов: \d+/\d+', bot_msg_lab.text, re.IGNORECASE)).strip('\n'),
            ''.join(re.findall(r'☣️ био-опыт: [\d\s]{1,64}', bot_msg_lab.text, re.IGNORECASE)).strip('\n'),
            ''.join(re.findall(r'🧬 био-ресурс: [\d\s]{1,64}', bot_msg_lab.text, re.IGNORECASE)).strip('\n') + '\n',
            ''.join(re.findall(r'❗️ Руководитель в состоянии горячки .+', bot_msg_lab.text, re.IGNORECASE)).strip('\n'),
        )
        return text

async def delete_msg(msgs: Union[Message, List[Message]], delay: int):
    await asyncio.sleep(delay)
    if isinstance(msgs, list):
        for m in msgs:
            await m.delete()
    else:
        await msgs.delete()