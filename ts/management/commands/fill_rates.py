# -*- coding: utf-8 -*-
"""

"""

import bs4
import os
import string
import re
import time
import calendar
import numpy
import warnings
import decimal
from tqdm import tqdm
from datetime import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from tipsport.settings import ROOT_PATH
from ts import models

DATE_RE = re.compile(r'([\w\.]+)[\s]*([\w:]+)')


def load_files():
    path = f'{ROOT_PATH}/downloads'
    lst = [x for x in os.listdir(path) if x.endswith('.html')]

    return [f'{ROOT_PATH}/downloads/{x}' for x in lst]


def load_soup(filename):
    with open(filename, 'r') as fread:
        soup = bs4.BeautifulSoup(fread.read(), 'html.parser')

    return soup


def is_live(soup):
    ul = soup.find('ul', id='menuMyTickets')
    a = ul.find('a', class_='selected')

    return 'LIVE' in str(a)


def _get_main_table_rows(soup):
    table = soup.find('table', id='tblTicketHistoryId')
    tbody = table.tbody

    trs = []

    for tr in tbody.find_all('tr'):
        if 'rowHeader' in tr.get('class', []):
            continue

        trs.append(tr)

    return trs


def _get_ticket_date(tr):
    td = tr.find('td', class_='colDate')

    if td:
        date_text = td.text.strip(string.whitespace).replace('\n', '')
        match = DATE_RE.search(date_text)

        if match:
            date_s = match.group(1)
            time_s = match.group(2)
            dt = datetime.strptime(f'{date_s} {time_s}',
                                   '%d.%m.%Y %H:%M:%S')

            return time.mktime(dt.timetuple())

    return 0


def _get_ticket_rate(tr):
    tds = tr.find_all('td', class_='colMoney')

    def _get_one(tds, idx):
        money_text = tds[idx].text.strip(string.whitespace)
        money_text = money_text.replace('\xa0Kč', '')
        money_text = money_text.replace('...', '')
        money_text = money_text.replace(',', '.')
        money_text = money_text.strip()

        try:
            amount = Decimal(money_text)
            return amount
        except (ValueError, decimal.InvalidOperation):
            pass

        return Decimal('0')

    if tds:
        amount_bet = _get_one(tds, 0)
        amount_won = _get_one(tds, 1)

        rate = round(amount_won/amount_bet, 2)
        return rate

    return Decimal('0')


def normal_get_bets(soup):
    bets = []

    for tr in _get_main_table_rows(soup):
        bet = {'rate': Decimal('0')}

        bet['date'] = _get_ticket_date(tr)
        bet['rate'] = _get_ticket_rate(tr)

        bets.append(bet)

    return bets


def import_file(filename):
    soup = load_soup(filename)

    if is_live(soup):
        return

    bets = normal_get_bets(soup)

    for bet in bets:
        if bet['date'] == 0:
            continue

        with warnings.catch_warnings():
            warnings.filterwarnings('ignore')

            new_bet = models.Bet.objects.get(date=datetime.fromtimestamp(bet['date']))

            if new_bet.rate > 0:
                continue

            new_bet.rate = bet['rate']
            new_bet.save()

            print(f'Updating rate of [{new_bet.date}] to: {new_bet.rate}')
        # new_bet.save()


def process():
    files = load_files()

    for fl in tqdm(files, 'Importing files'):
        import_file(fl)


class Command(BaseCommand):
    help = 'Parse HTML with bets and import them'

    def handle(self, *args, **options):
        process()
