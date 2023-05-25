#!/usr/bin/python3
from time import sleep
from requests import post, get
from datetime import datetime as dt, timedelta as td
from calendar import WEDNESDAY
from random import randint
from os import getcwd, listdir, environ
from os.path import isfile
import re
import pytz
import logging

url = f'''https://api.telegram.org/bot{environ.get('TGTOKEN').strip()}/'''
log_path = environ.get('LOGPATH').strip()
logging.basicConfig(level=logging.INFO, filename=f'''{log_path}/{dt.today().date()}.log''', filemode='w')
last_update_filepath = '/tmp/blin/lastupdate'


def how_long_to_session() -> str:
    if dt.now().weekday() == WEDNESDAY and 16 <= dt.now(tz=pytz.utc).hour < 20:
        return 'сессия уже идёт!'
    wdd = (dt.now(tz=pytz.utc) - td(dt.now(tz=pytz.utc).weekday() - WEDNESDAY)).replace(hour=16, minute=0, second=0,
                                                                                        microsecond=0)
    if wdd < dt.now(tz=pytz.utc):
        wdd += td(7)
    delta = int((wdd - dt.now(tz=pytz.utc)).total_seconds())

    days = delta // (60 * 60 * 24)
    hours = delta // (60 * 60) % 24
    minutes = delta // 60 % 60
    seconds = delta % 60
    return f'''до сессии {f"{days} д{'ень' if days == 1 else 'ня' if 2 <= days <= 4 else 'ней'}, " if days > 0 else ""}''' + \
        f'''{f"{hours} час{'' if hours % 10 == 1 and hours // 10 != 1 else 'а' if hours in (2, 3, 4, 22, 23) else 'ов'}, " if hours > 0 else ""}''' + \
        f'''{f"{minutes} минут{'а' if minutes % 10 == 1 and minutes // 10 != 1 else 'ы' if minutes % 10 in (2, 3, 4) and minutes // 10 != 1 else ''}, " if minutes > 0 else ""}''' + \
        f'''{seconds} секунд{'а' if seconds % 10 == 1 and seconds // 10 != 1 else 'ы' if seconds % 10 in (2, 3, 4) and seconds // 10 != 1 else ""}'''


def is_dice_query(query: str) -> bool:
    return re.match(r'((\d+)?d?\d+)((\+(\d+)?d\d+)|([+\-]\d+))*$', query) is not None


def parse_dice_query(query: str) -> str:
    def human_readable_throw_result(throw_result: tuple) -> str:
        result_num, throw = throw_result
        first_char = '-' if throw[1] < 0 else '+' if result_num > 0 else ''
        if throw[0] == 'const':
            return first_char + str(abs(throw[1]))
        else:
            return first_char + f'''({'+'.join(map(str, throw[2]))})'''

    result = []
    for throw in re.finditer(r'(^|[+-])\d*d?\d+', query):
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
    print('Я запустился!')
    while True:
        if isfile(last_update_filepath):
            last_update_id = int(open(last_update_filepath, 'r').read() or -1) + 1
        else:
            last_update_id = 0
        data = get(url + 'getUpdates', json={'offset': last_update_id}).json()
        print(data)
        try:
            data = data['result']
        except KeyError as ke:
            logging.error('KeyError', exc_info=True)
            post(
                url + 'sendMessage',
                json={
                    'chat_id': '91717534',
                    'text': f'Шеф, всё упало: {ke}'
                }
            )
            continue
        if data:
            with open(last_update_filepath, 'w') as f:
                f.write(str(max((x['update_id'] for x in data))))
        rs = [x['inline_query'] for x in data if 'inline_query' in x]
        for x in rs:
            logging.info(x)
            if is_dice_query(x['query']):
                try:
                    logging.info('Is dice query')
                    result = parse_dice_query(x['query'])
                except ValueError as ve:
                    logging.info(x['query'], ve)
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
                    {  # Compute time to session
                        'type': 'article',
                        'id': str(hash(str(result_how_long))),
                        'title': 'Считаю...',
                        'input_message_content': {
                            'message_text': f'блин блинский {result_how_long}'
                        }
                    },
                    {  # Link to Zoom
                        'type': 'article',
                        'id': str(hash('zoom')),
                        'title': 'Ссылка на Zoom',
                        'input_message_content': {
                            'message_text': f'Ссылка на Zoom: https://yandex.zoom.us/j/2463068144'
                        }
                    },
                    {  # Link to GitHub
                        'type': 'article',
                        'id': str(hash('github')),
                        'title': 'Ссылка на Github',
                        'input_message_content': {
                            'message_text': f'Ссылка на GitHub: https://github.com/p-lee-grimm/blin-blinsky'
                        }
                    }
                ]
            r = post(url + 'answerInlineQuery', json={
                'inline_query_id': x['id'],
                'cache_time': 1,
                'results': results
            })
