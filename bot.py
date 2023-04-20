#!/usr/bin/python3
from time import sleep
from requests import post, get
from datetime import datetime as dt, timedelta as td
from calendar import WEDNESDAY
from random import randint
from os import getcwd, listdir, environ
import re
import pytz

print(environ.get('TGTOKEN'))
url = f'''https://api.telegram.org/bot{environ.get('TGTOKEN').strip()}/'''


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
    return re.match(r'((\d+)?d?\d+)((\+(\d+)?d\d+)|([+\-]\d+))+$', query) is not None


def parse_dice_query(query: str) -> str:
    def human_readable_throw_result(throw_result: tuple) -> str:
        result_num, throw = throw_result
        first_char = '-' if throw[1] < 0 else '+' if result_num > 0 else ''
        if throw[0] == 'const':
            return first_char + str(abs(throw[1]))
        else:
            return first_char + f'''({'+'.join(map(str, throw[2]))})'''

    result = []
    for throw in re.finditer(r'[+-^](\d+)?d?\d+', query):
        if 'd' in throw.group():
            multiplier, dice = throw.group().split('d')
            if len(dice) > 3:
                return 'Too big dice can\'t throw it'
            if len(multiplier) > 3:
                return 'Got tired while throwing a dice so many times'
            if dice == '0':
                return 'Егор'
            if multiplier in '+-':
                multiplier += '1'
            dice_throw = [randint(1, int(dice)) for _ in range(abs(int(multiplier)))]
            multiplier = int(multiplier)
            result.append(('throw', multiplier, dice_throw))
        else:
            result.append(('const', int(throw.group())))
    const = sum(x[1] for x in result if x[0] == 'const')
    result = [x for x in result if x[0] != 'const'] + [('const', const)]
    return f'''{query} = {''.join(map(human_readable_throw_result, enumerate(result)))}''' \
           f''' = {sum((x[1] if x[0] == 'const' else sum(x[2]) * x[1] // abs(x[1]) for x in result))}'''


if __name__ == '__main__':
    while True:
        sleep(1)
        data = get(url + 'getUpdates').json()
        try:
            data = data['result']
        except KeyError as ke:
            print(data)
            print(url + 'getUpdates')
            raise ke
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
