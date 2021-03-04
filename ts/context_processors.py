# -*- coding: utf-8 -*-
"""

"""

from ts import models
import numpy


def global_vars(request):
    cont = {'REQ': request.path}

    acc = models.Account.objects.get(id=1)
    cont['ACC'] = acc

    pending = models.Bet.objects.filter(closed=False)
    cont['amount_bet'] = numpy.sum(pending.values_list('amount'))
    cont['amount_total'] = cont['amount_bet'] + acc.balance

    return cont
