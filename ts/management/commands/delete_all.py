# -*- coding: utf-8 -*-
"""

"""

from django.core.management.base import BaseCommand
from ts import models


class Command(BaseCommand):
    help = 'Parse HTML with bets and import them'

    def handle(self, *args, **options):
        bets = models.Bet.objects.all()
        bets.delete()
