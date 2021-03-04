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
from tqdm import tqdm
from datetime import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from tipsport.settings import ROOT_PATH
from ts import models

DATE_RE = re.compile(r'([\w\.]+)[\s]*([\w:]+)')
TYPES = {'JED': models.Bet.SINGLE,
         'AKU': models.Bet.ACCU,
         'KOM': models.Bet.COMB,
         'MAX': models.Bet.MAX}


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


def _get_ticket_amount(tr):
    td = tr.find('td', class_='colMoney')

    if td:
        money_text = td.text.strip(string.whitespace)
        money_text = money_text.replace('\xa0Kč', '')
        money_text = money_text.replace(',', '.')

        try:
            amount = Decimal(money_text)
            return amount
        except ValueError:
            pass

    return Decimal('0')


def _get_ticket_rate(tr):
    td = tr.find_all('td', class_='alignR')

    if td:
        rates = []

        for entry in td:
            try:
                rate = Decimal(entry.text.strip(string.whitespace))
                rates.append(rate)
            except ValueError:
                pass

        return round(numpy.product(rates), 2)

    return Decimal('0')


def _get_ticket_status(tr):
    td = tr.find('td', class_='colStatus')

    if td:
        img = td.find('img')

        if img:
            title = img.get('title')

            if title == 'vyhrávající':
                return (True, True)
            elif title == 'prohrávající':
                return (True, False)
            elif title == 'vada':
                return None

    return (False, False)


def _get_ticket_type(tr):
    td = tr.find('td', class_='colType')

    if td:
        text = td.text.strip(string.whitespace)
        return TYPES[text]

    raise ValueError('Cannot find ticket type')


def normal_get_bets(soup):
    bets = []

    for tr in _get_main_table_rows(soup):
        bet = {'closed': False,
               'rate': Decimal('0')}

        bet['date'] = _get_ticket_date(tr)
        bet['amount'] = _get_ticket_amount(tr)
        bet['closed'], bet['won'] = _get_ticket_status(tr)
        bet['type'] = _get_ticket_type(tr)

        bets.append(bet)

    return bets


def live_get_bets(soup):
    bets = []

    for tr in _get_main_table_rows(soup):
        bet = {'type': models.Bet.LIVE,
               'closed': False}

        bet['date'] = _get_ticket_date(tr)
        bet['amount'] = _get_ticket_amount(tr)
        bet['rate'] = _get_ticket_rate(tr)

        status = _get_ticket_status(tr)

        if status is None:
            continue

        bet['closed'], bet['won'] = status

        if 'date' in bet.keys():
            bets.append(bet)

    return bets


def import_file(filename):
    soup = load_soup(filename)

    if is_live(soup):
        bets = live_get_bets(soup)
    else:
        bets = normal_get_bets(soup)

    existing = models.Bet.objects.values_list('date', flat=True)
    existing = [calendar.timegm(x.timetuple()) for x in existing]

    for bet in bets:
        if bet['date'] in existing:
            continue

        if bet['date'] == 0:
            continue

        new_bet = models.Bet()
        new_bet.date = datetime.fromtimestamp(bet['date'])
        new_bet.bet_type = bet['type']
        new_bet.amount = bet['amount']
        new_bet.rate = bet['rate']
        new_bet.won = bet['won']
        new_bet.closed = bet['closed']
        new_bet.save()


def process():
    files = load_files()

    for fl in tqdm(files, 'Importing files'):
        import_file(fl)


class Command(BaseCommand):
    help = 'Parse HTML with bets and import them'

    def handle(self, *args, **options):
        process()
