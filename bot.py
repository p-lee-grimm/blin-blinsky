#!/usr/bin/python3
from time import sleep
from requests import post, get
from datetime import datetime as dt, timedelta as td
from calendar import WEDNESDAY
from random import randint
import re
import pytz

url = f'''https://api.telegram.org/{open('~/telegram.token').read()}/'''


def how_long_to_session() -> str:
    wdd = (dt.now(tz=pytz.utc) - td(dt.now(tz=pytz.utc).weekday() - WEDNESDAY)).replace(hour=16, minute=0, second=0,
                                                                                        microsecond=0)
    if wdd < dt.now(tz=pytz.utc):
        wdd += td(7)
    delta = int((wdd - dt.now(tz=pytz.utc)).total_seconds())

    days = delta // (60 * 60 * 24)
    hours = delta // (60 * 60) % 24
    minutes = delta // 60 % 60
    seconds = delta % 60
    return f'''{f"{days} д{'ень' if days == 1 else 'ня' if 2 <= days <= 4 else 'ней'}, " if days > 0 else ""}''' + \
        f'''{f"{hours} час{'' if hours % 10 == 1 and hours // 10 != 1 else 'а' if hours in (2, 3, 4, 22, 23) else 'ов'}, " if hours > 0 else ""}''' + \
        f'''{f"{minutes} минут{'а' if minutes % 10 == 1 and minutes // 10 != 1 else 'ы' if minutes % 10 in (2, 3, 4) and minutes // 10 != 1 else ''}, " if minutes > 0 else ""}''' + \
        f'''{seconds} секунд{'а' if seconds % 10 == 1 and seconds // 10 != 1 else 'ы' if seconds % 10 in (2, 3, 4) and seconds // 10 != 1 else ""}'''


def is_dice_query(query: str) -> bool:
    return re.match(r'(\d+)?d\d+([+\-]\d+)?$', query) is not None


def parse_dice_query(query: str) -> str:
    multiplier, rest = query.split('d', maxsplit=1)
    if multiplier == '':
        multiplier = 1
    dice, add = (rest if '+' in rest else rest + '+0').split('+')
    if dice == '0':
        return 'Егор'
    dice_throw = [randint(1, int(dice)) for _ in range(int(multiplier))]
    return f'''({'+'.join(map(str, dice_throw))}) + {add} = {sum(dice_throw) + int(add)}'''


while True:
    sleep(1)
    data = get(url + 'getUpdates').json()['result']
    rs = [x['inline_query'] for x in data if 'inline_query' in x]
    for x in rs:
        if is_dice_query(x['query']):
            try:
                result = parse_dice_query(x['query'])
            except ValueError as ve:
                print(x['query'])
                raise ve
            results = [
                {
                    'type': 'article',
                    'id': str(hash(result)),
                    'title': 'Бросаю...',
                    'input_message_content': {
                        'message_text': f'''{x['query']}: {result}''' if result != 'Егор' else f'{x["from"]["first_name"]}, иди нахуй'
                    }
                }
            ]
        else:
            result_how_long = how_long_to_session()
            results = [
                {
                    'type': 'article',
                    'id': str(hash(str(result_how_long))),
                    'title': 'Считаю...',
                    'input_message_content': {
                        'message_text': f'блин блинский до сессии {result_how_long}'
                    }
                },
                {
                    'type': 'article',
                    'id': str(hash('zoom')),
                    'title': 'Ссылка на Zoom',
                    'input_message_content': {
                        'message_text': f'Ссылка на Zoom: https://yandex.zoom.us/j/2463068144'
                    }
                }
            ]
        r = post(url + 'answerInlineQuery', json={
            'inline_query_id': x['id'],
            'cache_time': 1,
            'results': results
        })

