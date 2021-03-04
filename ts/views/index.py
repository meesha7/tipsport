# -*- coding: utf-8 -*-
"""

"""

from django.shortcuts import render


def index(request):
    cont = {}
    return render(request, 'ts/index/index.html', cont)
