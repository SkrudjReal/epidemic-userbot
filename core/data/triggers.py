import re

re_pref = r'([!./]|)'
re_pref_ = r'[!./]'
re_pref_minus = r'([!./]|-|)'
refp = r'[!./]'
re_link_sup = r'(https://t\.me/|tg://openmessage\?user_id=|@)(\d{6,14}|[\w\d]{5,32})'
re_skills = r'(патоген|разработка|заразность|и[м]{1,2}у[н]{1,2}итет|летальность|безопасность|пат|квала|зз|и[м]{1,2}ун|летал|сб)'

deep_links = {
    'tag': '@',
    'link': 'https://t.me/',
    'mention': 'tg://openmessage?user_id=',
    'mention_click': 'tg://user?id='
}


re_infect = re.compile(
    re_pref +
    '('
    r'заразить\s{1,3}(|\d{1,2}\s{1,3})' + re_link_sup + '|'
    r'заразить\s{1,3}(-|=|\+|слаб(ее|ый|ого)|равн(ее|ый|ого)|сильн(ее|ый|ого)|рандом(|ный|ного))(|\s{1,3}\d{1,2})' +
    ')',
    re.IGNORECASE
)
re_infect_reply = re.compile(re_pref + r'заразить(|\s{1,3}\d{1,2})', re.IGNORECASE)