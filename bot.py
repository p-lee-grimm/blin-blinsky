#!/home/tolord/blinenv/bin/python3
from time import sleep
from requests import post, get
from datetime import datetime as dt, timedelta as td
from calendar import WEDNESDAY, THURSDAY
from random import randint
from os import getcwd, listdir, environ, getenv, makedirs
from os.path import isfile, join, exists
from random import sample
from traceback import print_exception, format_exc
from json import loads, JSONDecodeError
from dotenv import load_dotenv
import logging
import telebot as tb
import re
import pytz

load_dotenv('/home/tolord/blin-blinsky/.env')

log_directory = getenv('LOGPATH') + f'/{dt.today().date().isoformat()}'
if not exists(log_directory):
    makedirs(log_directory)

# Имя лог-файла
log_file_name = "error.log"

# Полный путь к файлу
log_file_path = join(log_directory, log_file_name)

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,  # Уровень логгирования
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Формат сообщения
    datefmt='%Y-%m-%d %H:%M:%S',  # Формат времени
    handlers=[
        logging.FileHandler(log_file_path),  # Обработчик для записи в файл
        logging.StreamHandler()  # Также можно настроить вывод в консоль
    ]
)

print(environ)

bot = tb.TeleBot(getenv('TGTOKEN').strip())

error_msg = 'Sorry, something went wrong. If you see this message, text to my creator please: @tolord'

def get_first_or_obj(obj):
    try:
        return obj[0]
    except Exception:
        return obj


def how_long_to_session() -> str:
    def is_after_11_23():
        return dt.now() >= dt(2023, 11, 24)
    
    if dt.now().weekday() == WEDNESDAY and 16 <= dt.now(tz=pytz.utc).hour < 20:
        return 'сессия уже идёт!'
    wdd = (
        dt.now(tz=pytz.utc) - td(dt.now(tz=pytz.utc).weekday() - (WEDNESDAY if is_after_11_23() else THURSDAY))).replace(
        hour=16 if is_after_11_23() else 17, 
        minute=0 if is_after_11_23() else 30, 
        second=0, 
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
    return re.match(r'((\d+)?d?\d+)((\+(\d+)?d\d+)|([+\-]\d+))*$', query or '') is not None


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

@bot.message_handler(commands=['kto'])
def list_shortcuts_handler(message):
    bot.send_message(chat_id=91717534, text=f'''{message.chat.__dict__}''')
    logging.info(f'''{message.from_user.username or message.from_user.id}: list''')
    bot.reply_to(message=message, text='И правда, кто?')
    bot.send_poll(
        chat_id=message.chat.id,
        question='Кто?',
        options=sample([
            'Кюин',
            'Гай',
            'Ния',
            'Танингур',
            'Мастер',
            'Тангвилт',
            'Рунгерд'
        ], k=7)
    )

@bot.inline_handler(lambda query: is_dice_query(query.query))
def process_dice_query(inline_query):
    try:
        logging.info('Is dice query')
        result = parse_dice_query(inline_query.query)
    except ValueError as ve:
        logging.info(inline_query.query, ve)
    results = [
        tb.types.InlineQueryResultArticle(
            id=str(hash(result)),
            title='Бросаю...',
            input_message_content=tb.types.InputTextMessageContent(
                **{
                    'message_text': f'''{inline_query.query}: {result}''' if result != 'Егор' else f'''{inline_query.from_user.first_name}, иди нахуй'''
                }
            )
        )
    ]
    bot.answer_inline_query(
        inline_query.id, 
        results, 
        cache_time=1, 
        is_personal=True
    )

@bot.inline_handler(lambda query: not is_dice_query(query.query))
def process_not_dice_query(inline_query):
    result_how_long = how_long_to_session()
    results = [
        tb.types.InlineQueryResultArticle(  # Compute time to session
        **{
            'id': str(hash(str(result_how_long))),
            'title': 'Считаю...',
            'input_message_content': tb.types.InputTextMessageContent(
                **{'message_text': f'блин блинский {result_how_long}'}
            )
        }),
        tb.types.InlineQueryResultArticle(
        **{  # Link to Zoom
            'id': str(hash('zoom')),
            'title': 'Ссылка на Zoom',
            'input_message_content': tb.types.InputTextMessageContent(
                **{'message_text': f'Ссылка на Zoom: https://yandex.zoom.us/j/2463068144'}
            )
        }),
        tb.types.InlineQueryResultArticle(
        **{  # Link to GitHub
            'id': str(hash('github')),
            'title': 'Ссылка на Github',
            'input_message_content': tb.types.InputTextMessageContent(
                **{'message_text': f'Ссылка на GitHub: https://github.com/p-lee-grimm/blin-blinsky'}
            )
        })
    ]
    bot.answer_inline_query(
        inline_query.id,
        results,
        cache_time=1,
        is_personal=False
    )

if __name__ == '__main__':
    bot.infinity_polling()
