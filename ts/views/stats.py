# -*- coding: utf-8 -*-
"""

"""

import datetime
from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Sum, Count, F
import pandas as pd
from django_pandas.io import read_frame
from ts import models


def stats(request):
    cont = {'title': 'Stats'}

    return render(request, 'ts/stats/index.html', cont)


def stats_overview(request):
    cont = {'title': 'Overview'}

    total_bets = models.Bet.objects.filter(closed=True).aggregate(total=Count('id'))
    cont['total_bets'] = total_bets['total']

    won_bets = models.Bet.objects.filter(closed=True).filter(won=True).aggregate(total=Count('id'))
    cont['won_bets'] = won_bets['total']
    cont['lost_bets'] = cont['total_bets'] - cont['won_bets']

    return render(request, 'ts/stats/overview.html', cont)


def stats_counts(request):
    cont = {'title': 'Number of bets'}

    bets_by_sport = models.Bet.objects.filter(closed=True)
    bets_by_sport = bets_by_sport.values('sport__name')
    bets_by_sport = bets_by_sport.annotate(total=Count('sport__name'))
    cont['bets_by_sport'] = bets_by_sport.order_by('-total')

    wins_by_sport = models.Bet.objects.filter(closed=True).filter(won=True)
    wins_by_sport = wins_by_sport.values('sport__name')
    wins_by_sport = wins_by_sport.annotate(total=Count('sport__name'))
    cont['wins_by_sport'] = wins_by_sport.order_by('-total')

    losses_by_sport = models.Bet.objects.filter(closed=True).filter(won=False)
    losses_by_sport = losses_by_sport.values('sport__name')
    losses_by_sport = losses_by_sport.annotate(total=Count('sport__name'))
    cont['losses_by_sport'] = losses_by_sport.order_by('-total')

    all_bets = models.Bet.objects.filter(closed=True).select_related('sport')
    df = read_frame(all_bets)

    success_rates = df\
                    .groupby('sport')['won']\
                    .mean()\
                    .sort_values(ascending=False)\
                    .apply(lambda x: round(100*x, 2))

    cont['success_rates'] = success_rates.to_dict()

    return render(request, 'ts/stats/counts.html', cont)


def stats_results(request):
    cont = {'title': 'Bet result details'}

    all_bets = models.Bet.objects.filter(closed=True).select_related('sport')

    if request.GET.get('days', False):
        days = int(request.GET.get('days'))

        if days:
            filter_date = datetime.datetime.now() - datetime.timedelta(days=days)
            all_bets = all_bets.filter(date__gt=filter_date)

    df = read_frame(all_bets)
    df = df.set_index('sport')

    df['revenue'] = df.apply(lambda x: (round(x['amount']*x['rate'], 2)\
                             if x['rate'] > 0 and x['rate'] < 1
                             else round(x['amount']*x['rate']*int(x['won']), 2)), axis=1)
    df['profit'] = df.apply(lambda x: x['revenue'] - x['amount'], axis=1)

    results = df.groupby('sport')['amount', 'revenue', 'profit'].sum()
    results['profit_perc'] = results.apply(lambda x: round(100*x['revenue']/x['amount'] - 100, 2),
                                           axis=1)

    cont['amounts'] = results.sort_values('amount', ascending=False)['amount']
    cont['revenues'] = results.sort_values('revenue', ascending=False)['revenue']
    cont['profits'] = results.sort_values('profit', ascending=False)\
                             .loc[:, 'amount':'profit_perc']\
                             .T.apply(tuple)\
                             .to_dict()

    cont['sums'] = {'amount': results['amount'].sum(),
                    'revenue': results['revenue'].sum(),
                    'profit': results['profit'].sum()}

    profit_perc = 100*cont['sums']['revenue']/cont['sums']['amount'] - 100
    cont['sums']['profit_perc'] = profit_perc

    return render(request, 'ts/stats/results.html', cont)


def stats_sport(request, sport=''):
    cont = {'title': 'Bet results by sport'}
    cont['sports'] = models.Sport.objects.order_by('name')

    if sport:
        sport = models.Sport.objects.get(name=sport)
    elif request.POST.get('view', False):
        sport = models.Sport.objects.get(id=request.POST.get('id_sport'))
    else:
        sport = None

    if sport:
        cont['sport_detail'] = sport

        bets = models.Bet.objects.filter(sport=sport).filter(closed=True)
        df = read_frame(bets)
        df = df.set_index('date')

        df['revenue'] = df.apply(lambda x: (round(x['amount']*x['rate'], 2)\
                                 if x['rate'] > 0 and x['rate'] < 1
                                 else round(x['amount']*x['rate']*int(x['won']), 2)), axis=1)
        df['profit'] = df.apply(lambda x: x['revenue'] - x['amount'], axis=1)

        cont['profit_history'] = df.groupby(pd.Grouper(freq='M'))['profit'].sum().to_dict()

        cont['profit'] = df['profit'].sum()
        cont['profit_perc'] = round(100*df['revenue'].sum()/df['amount'].sum() - 100, 2)

        profit_by_type = df.groupby('bet_type')['profit'].sum().sort_values(ascending=False)
        cont['profit_by_type'] = profit_by_type.to_dict()


    return render(request, 'ts/stats/sport.html', cont)


def stats_history(request):
    cont = {'title': 'Profit history'}

    bets = models.Bet.objects.filter(closed=True)
    df = read_frame(bets)
    df = df.set_index('date')

    df['revenue'] = df.apply(lambda x: (round(x['amount']*x['rate'], 2)\
                             if x['rate'] > 0 and x['rate'] < 1
                             else round(x['amount']*x['rate']*int(x['won']), 2)), axis=1)
    df['profit'] = df.apply(lambda x: x['revenue'] - x['amount'], axis=1)

    cont['profit_history'] = df.groupby(pd.Grouper(freq='M'))['profit'].sum().to_dict()

    return render(request, 'ts/stats/history.html', cont)
