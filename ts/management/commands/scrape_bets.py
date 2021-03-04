# -*- coding: utf-8 -*-
"""

"""

import os
import time
import pyautogui
import bs4
import numpy as np
from decimal import Decimal
from django.core.management.base import BaseCommand
from tipsport.settings import ROOT_PATH
from ts import models


SCRAPE_FILE = f'{ROOT_PATH}/downloads/scrape'


def get_sports():
    sports = models.Sport.objects.all()

    return {x.name: x for x in sports}


def save_page():
    time.sleep(5)

    if os.path.exists(f'{SCRAPE_FILE}.html'):
        os.unlink(f'{SCRAPE_FILE}.html')

    pyautogui.hotkey('winleft', 'f')
    time.sleep(0.2)

    pyautogui.hotkey('ctrl', 's')
    time.sleep(1)

    pyautogui.typewrite(SCRAPE_FILE)
    time.sleep(0.5)
    pyautogui.press('enter')

    while not os.path.exists(f'{SCRAPE_FILE}.html'):
        print('Waiting for scrape file to be saved')
        time.sleep(0.5)

    time.sleep(2)


def _get_event_name(match):
    match_name = match.select('div.matchName')

    if match_name:
        return match_name[0].select('a span')[0].attrs['title']

    match_name = match.select('a.matchName')

    if match_name:
        return match_name[0].attrs['title']

    return ''


def _get_match_rates(match):
    div = match.select('div.rowMatchOdds')

    if not div:
        return []

    rates = div[0].select('div.btnRate')

    if not rates:
        return []

    rates_nums = []

    for rate in rates:
        if rate:
            rates_nums.append(Decimal(rate.text))

    return rates_nums


def _get_match_sport(match):
    div = match.select('div.colSport')

    if not div:
        return ''

    img = div[0].select('img')

    if not img:
        return ''

    return img[0].attrs['title']


def _parse_sport_name(sport):
    sport = sport.strip().lower()

    if 'lední hokej' in sport:
        return 'Hockey'

    if 'fotbal' in sport:
        return 'Football'

    if 'basketbal' in sport:
        return 'Basketball'

    if 'stolní' in sport:
        return 'Table tennis'

    if 'tenis' in sport:
        return 'Tennis'

    return ''


def _calc_rates(rates):
    return min(rates), max(rates), np.mean(rates), np.std(rates)


def parse_page():
    with open(f'{SCRAPE_FILE}.html', 'r') as fread:
        soup = bs4.BeautifulSoup(fread.read(), 'html.parser')

    matches = soup.select('div.rowMatch')
    sports = get_sports()

    output = []

    for match in matches:
        event_name = _get_event_name(match)
        rates = _get_match_rates(match)
        sport = _get_match_sport(match)
        sport = _parse_sport_name(sport)
        sport = sports.get(sport, None)

        rmin, rmax, ravg, rstd = _calc_rates(rates)

        match_data = {'name': event_name,
                      'rates': rates,
                      'sport': sport,
                      'rmin': rmin,
                      'rmax': rmax,
                      'ravg': ravg,
                      'rstd': rstd}

        output.append(match_data)

    for match in sorted(output, key=lambda x: x['rstd']):
        print('{:10s} {:5.2f} {:5.2f} {:5.3f} {:5.4f}  {}'.format(match['sport'].name,
                                                                  match['rmin'],
                                                                  match['rmax'],
                                                                  match['ravg'],
                                                                  match['rstd'],
                                                                  match['name']))



class Command(BaseCommand):
    help = 'Parse HTML with bet rates'

    def add_arguments(self, parser):
        parser.add_argument('--download', action='store_true')
        parser.add_argument('--parse', action='store_true')

    def handle(self, *args, **options):
        if options['download']:
            save_page()

        if options['parse']:
            parse_page()
