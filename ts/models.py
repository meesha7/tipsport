from django.db import models
from django.db.models import deletion


class Sport(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class Bet(models.Model):
    SINGLE = 0
    ACCU = 1
    COMB = 2
    LIVE = 3
    MAX = 4
    TYPES = [(SINGLE, 'Single'),
             (ACCU, 'Accu'),
             (COMB, 'Combined'),
             (LIVE, 'Live'),
             (MAX, 'Max')]

    date = models.DateTimeField()
    rate = models.DecimalField(decimal_places=2, max_digits=5)
    amount = models.DecimalField(decimal_places=2, max_digits=10)
    bet_type = models.PositiveSmallIntegerField(choices=TYPES)
    won = models.BooleanField(default=False)
    closed = models.BooleanField(default=False)
    sport = models.ForeignKey(Sport, null=True, blank=True,
                              on_delete=deletion.PROTECT)

    def result(self):
        """
        If the rate is in interval (0, 1), returns amount*rate,
        for rate >= 1, returns amount*rate if won, or 0 if not.
        """

        if self.rate > 0 and self.rate < 1:
            return round(self.amount*self.rate, 2)

        return round(self.amount*self.rate*int(self.won), 2)

    def revenue(self):
        """
        Returns the bet's revenue (amount of money won).
        """

        return self.result()

    def profit(self):
        """
        Returns revenue - amount bet
        """

        return self.revenue() - self.amount

    def potential_profit(self):
        """
        Returns bet's potential profit
        """

        return round(self.amount*(self.rate - 1), 2)

    def type_str(self):
        return self.TYPES[self.bet_type][1]

    def __str__(self):
        return f'{self.date} {self.type_str()} {self.amount} @{self.rate}'


class Account(models.Model):
    balance = models.DecimalField(decimal_places=2, max_digits=10)
