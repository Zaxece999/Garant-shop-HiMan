from urllib.parse import urlparse
import datetime
import decimal
import random
import string
import json
import re

from aiohttp import ClientSession
from cachetools import TTLCache
from asyncache import cached
from pytils import numeral
from aiogram.types import *
from peewee import fn

from tables import *
from init import *


def generate_random_string(length):
    source_string = string.ascii_letters + string.digits
    random_characters = [random.choice(source_string) for _ in range(length)]
    return ''.join(random_characters)


def get_random_smile(for_what=None):
    if for_what is None or for_what == 'menu':
        return random.choice(['🌁', '🌃', '🏙️', '🌄', '🌅', '🌆', '🌇', '🌉', '🌌'])
    elif for_what == 'footer menu':
        return random.choice(['🏠', '🏡'])
    elif for_what == 'dice':
        return random.choice(['🎲', '🎯', '⚽', '🎳', '🎰', '🏀'])
    elif for_what == 'anger':
        return random.choice(['👿', '😠', '💀', '😡', '🤬'])
    elif for_what == 'anim':
        return random.choice(['🚀', '✈️', '🔮'])
    elif for_what == 'time':
        return random.choice(['⌛', '⏳', '⏱', '🕰'])
    elif for_what == 'money':
        return random.choice(['🫰', '💰', '💵', '💸', '💳'])
    elif for_what == 'star':
        return random.choice(['💫', '⭐', '🌃', '🌟', '✨', '🌠'])
    elif for_what == 'phone':
        return random.choice(['📱', '📲', '☎️', '📞', '📳'])


def word_declesion(number, word, lang: str):
    if word == 'hour':
        if lang == 'ru':
            return numeral.get_plural(number, 'час, часа, часов').split(' ', 1)[1]
        else:
            return numeral.get_plural(number, 'hour, hours, hours').split(' ', 1)[1]

    elif word == 'day':
        if lang == 'ru':
            return numeral.get_plural(number, 'день, дня, дней').split(' ', 1)[1]
        else:
            return numeral.get_plural(number, 'day, days, days').split(' ', 1)[1]

    elif word == 'review':
        if lang == 'ru':
            return numeral.get_plural(number, 'отзыв, отзыва, отзывов').split(' ', 1)[1]
        else:
            return numeral.get_plural(number, 'review, review, reviews').split(' ', 1)[1]


def format_duration(duration, language = 'ru'):
    if isinstance(duration, datetime.datetime):
        days = duration.day
        hours, remainder = divmod(duration.second, 3600)
    elif isinstance(duration, datetime.timedelta):
        days = duration.days
        hours, remainder = divmod(duration.seconds, 3600)
    else:
        raise TypeError('Unkown type time. Use timedelta or datetime')

    minutes, seconds = divmod(remainder, 60)
    parts = []

    if days:
        parts.append(
            format_unit(
                days,
                'день' if language == 'ru' else 'day',
                'дня' if language == 'ru' else 'day',
                'дней' if language == 'ru' else 'days'
            ))
    if hours:
        parts.append(
            format_unit(
                hours,
                'час' if language == 'ru' else 'hour',
                'часа' if language == 'ru' else 'hour',
                'часов' if language == 'ru' else 'hours'
            ))
    if minutes:
        parts.append(
            format_unit(
                minutes,
                'минуту' if language == 'ru' else 'min',
                'минуты' if language == 'ru' else 'min',
                'минут' if language == 'ru' else 'min'
            ))
    if not days and not hours and seconds or not parts:
        parts.append(
            format_unit(
                seconds,
                'секунду' if language == 'ru' else 'second',
                'секунды' if language == 'ru' else 'seconds',
                'секунд' if language == 'ru' else 'seconds'
            ))

    word_and = 'и' if language == 'ru' else 'and'
    return f' {word_and} '.join(parts)


def format_unit(number, unit_rus_singular, unit_rus_few, unit_rus_many):
    if (number % 10) == 1 and number != 11:
        return f"{number} {unit_rus_singular}"
    elif 5 > (number % 10) >= 2 and not 12 <= number % 100 <= 14:
        return f"{number} {unit_rus_few}"
    else:
        return f"{number} {unit_rus_many}"


def calculate_percentage(amount, percentage):
    return float(amount) * float((percentage / 100))


def is_url(text):
    try:
        _ = urlparse(text)
        return True
    except ValueError:
        return False
