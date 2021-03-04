# -*- coding: utf-8 -*-
"""

"""

import re
from datetime import datetime
import time
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from ts import models
from ts import libts


MULTIEDIT_SPORT_RE = re.compile(r'([\d]+)__id_sport')
MULTIEDIT_RATE_RE = re.compile(r'([\d]+)__rate')


def list_bets(request):
    cont = {'title': 'Bet list'}

    sports = models.Sport.objects.order_by('name')

    bets = models.Bet.objects.order_by('-date')
    bets = bets.select_related('sport')

    pager = libts.pager.Pager(request, bets)
    cont['pager'] = pager
    cont['bets'] = pager.get_page()
    cont['last_bet'] = bets[0]

    if request.POST.get('save', False):
        for key in request.POST:
            match = MULTIEDIT_SPORT_RE.search(key)

            if match:
                id_bet = int(match.group(1))
                id_sport = int(request.POST.get(key))

                if id_sport:
                    bet = bets.get(id=id_bet)
                    bet.sport = sports.get(id=id_sport)
                    bet.save()

            match = MULTIEDIT_RATE_RE.search(key)

            if match:
                id_bet = int(match.group(1))
                rate_str = request.POST.get(key, '0')

                if rate_str:
                    rate = Decimal(rate_str)

                    if rate > 1:
                        bet = bets.get(id=id_bet)
                        bet.rate = rate
                        bet.save()

    if request.POST.get('add', False):
        bet = models.Bet()
        bet.date = datetime.now()
        bet.rate = Decimal(request.POST.get('rate'))
        bet.amount = Decimal(request.POST.get('amount'))
        bet.sport = models.Sport.objects.get(id=request.POST.get('id_sport'))
        bet.bet_type = int(request.POST.get('bet_type'))

        if request.POST.get('date', ''):
            dt = datetime.strptime(request.POST.get('date'), '%d.%m.%Y %H:%M:%S')
            bet.date = datetime.fromtimestamp(time.mktime(dt.timetuple()))

        bet.save()

        acc = models.Account.objects.get(id=1)
        acc.balance -= bet.amount
        acc.save()

        return redirect('ts:list_bets')

    if request.POST.get('make_won', False):
        bet = models.Bet.objects.get(id=request.POST['bet_id'])
        bet.won = True
        bet.closed = True
        bet.save()

        acc = models.Account.objects.get(id=1)
        acc.balance += bet.revenue()
        acc.save()

    if request.POST.get('make_lost', False):
        bet = models.Bet.objects.get(id=request.POST['bet_id'])
        bet.won = False
        bet.closed = True
        bet.save()

    cont['sports'] = sports
    cont['bet_types'] = models.Bet.TYPES
    cont['now'] = time.strftime('%d.%m.%Y %H:%M:%S')

    return render(request, 'ts/bets/list_bets.html', cont)


def view_bet(request, id_bet):
    cont = {}

    bet = get_object_or_404(models.Bet, id=id_bet)

    if request.POST.get('save', False):
        id_sport = int(request.POST.get('id_sport'))

        if id_sport:
            bet.sport = models.Sport.objects.get(id=id_sport)

        bet.amount = Decimal(request.POST.get('amount', '0'))
        bet.rate = Decimal(request.POST.get('rate', '0'))
        bet.won = 'won' in request.POST
        bet.closed = 'closed' in request.POST
        bet.save()

    if request.POST.get('make_won', False):
        bet.won = True
        bet.closed = True
        bet.save()

        acc = models.Account.objects.get(id=1)
        acc.balance += bet.revenue()
        acc.save()

    if request.POST.get('make_lost', False):
        bet.won = False
        bet.closed = True
        bet.save()

    cont['bet'] = bet
    cont['sports'] = models.Sport.objects.order_by('name')

    return render(request, 'ts/bets/view_bet.html', cont)
