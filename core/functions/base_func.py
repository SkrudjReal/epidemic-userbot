from redis.asyncio import Redis
from humanize import intcomma
from functools import lru_cache

from core.data.triggers import deep_links

import unicodedata
import html
import re

def link_getter(text: str) -> [str, bool]:
    expression = r'((https://t\.me/|@)[\w\d]{5,32}|tg://openmessage\?user_id=\d{6,14})'
    result = re.search(expression, text)
    if result:
        result = result[0].replace('https://t.me/', '').replace('tg://openmessage?user_id=', '').strip('@')
        if result.isdigit():
            return int(result)
        else:
            return str(result)
    else:
        return None

def strip_non_ascii(string) -> str:
    return ' '.join(re.findall(r'[\d\w\s]+', string))

def anti_specific_symbols_name(name: str, username: [str, bool], id: int) -> str:
    asci_name = strip_non_ascii(name)
    if asci_name != '':
        return asci_name
    elif username:
        return username
    else:
        return str(id)

def clear_name_universal(name: str, username: [str, bool], id: int) -> [int, str]:
    re_pattern1 = re.compile(r'[^\u0000-\u007F\u00A0-\uFFFF]+')


    clear_name = anti_specific_symbols_name(
        html.escape(name), username, id
    )
    clear_name = re_pattern1.sub('', unicodedata.normalize('NFKC', clear_name))
    clear_name = re.sub(r'[^ -~А-Яа-яЁё]', '', clear_name)
    
    if re.fullmatch(r'[\s‎ ]+', clear_name) or not clear_name:
        clear_name = (username if username else id)
    
    return clear_name

def entity_create(id: int, name: str, entity: str=deep_links['mention']) -> str:
    return f'<a href="{entity}{id}">{name}</a>'

@lru_cache
def skills_calc(skill: str, from_lvl: int, to_lvl: int):
    
    skill_string, price = '', 0
    
    for i in range(from_lvl, to_lvl):
        if [i for i in ['заразность', 'зараз', 'зз'] if i == skill]:
            price += (i + 1)**2.5
            skill_string = f'🧬 Улучшение <b>заразности</b> с <i>{from_lvl} до {to_lvl}</i> уровня стоит'
        elif [i for i in ['иммунитет', 'иммун', 'имун'] if i == skill]:
            price += (i + 1)**2.45
            skill_string = f'🧬 Улучшение <b>иммунитета</b> с <i>{from_lvl} до {to_lvl}</i> уровня стоит'
        elif [i for i in ['летальность', 'летал', 'леталка'] if i == skill]:
            price += (i + 1)**1.95
            skill_string = f'🧬 Улучшение <b>летальности</b> с <i>{from_lvl} до {to_lvl}</i> уровня стоит'
        elif [i for i in ['квалификация', 'квала', 'скорость'] if i == skill]:
            price += (i + 1)**2.6
            skill_string = f'🧬 Улучшение <b>квалификации</b> с <i>{from_lvl} до {to_lvl}</i> уровня стоит'
        elif [i for i in ['патогены', 'паты', 'патоген', 'пат'] if i == skill]:
            price += (i + 1)**2
            skill_string = f'🧬 Улучшение <b>патогена</b> с <i>{from_lvl} до {to_lvl}</i> уровня стоит'
        elif [i for i in ['безопасность', 'сб', 'служба'] if i == skill]:
            price += (i + 1)**2.1
            skill_string = f'🧬 Улучшение <b>безопасности</b> с <i>{from_lvl} до {to_lvl}</i> уровня стоит'
    
    return f'{skill_string} <b>{intcomma(int(price))}</b> био-ресурсов.'

