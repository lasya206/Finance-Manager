from django.db import models
from django.db.models import Sum, Count, F, Q
from datetime import datetime
from dateutil.relativedelta import relativedelta


class Account(models.Model):
    name = models.CharField(max_length=100)
    balance = models.FloatField(default=0)
    income = models.FloatField(default=0)
    expense = models.FloatField(default=0)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    saving_goal = models.FloatField(default=0)
    subscription_list = models.ManyToManyField('Subscription', blank=True)
    liability_list = models.ManyToManyField('Liability', blank=True)
    investment_list = models.ManyToManyField('Investments', blank=True)
    salary = models.FloatField(default=0)
    

class Investments(models.Model):
    name = models.CharField(max_length=100)
    amount = models.FloatField(default=0)
    return_rate = models.FloatField(default=0)
    end_date = models.DateField()
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    return_amount = models.FloatField(default=0)
    monthly_return = models.FloatField(default=0)

    def calculate_return_amount(self):
        today = datetime.date.today()
        time_period = (self.end_date - today).days / 365.0  # Calculate time period in years
        compounded_amount = self.amount * (1 + self.return_rate / 100) ** time_period
        self.return_amount = round(compounded_amount, 2)
        self.save()
        return self.return_amount

    def calculate_monthly_return(self):
        total_months = (self.end_date.year - datetime.date.today().year) * 12 + self.end_date.month - datetime.date.today().month
        if total_months <= 0:
            return 0
        monthly_return = self.return_amount / total_months
        return round(monthly_return, 2)


class Liability(models.Model):
    name = models.CharField(max_length=100)
    amount = models.FloatField(default=0)
    date = models.DateField(null=False, default=datetime.now().date())
    long_term = models.BooleanField(default=False)
    interest_rate = models.FloatField(default=0, blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    monthly_expense = models.FloatField(default=0, blank=True, null=True)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)

    
    def save(self, *args, **kwargs):
        if self.long_term:
            self.monthly_expense = self.calculate_monthly_expense()
        super(Liability, self).save(*args, **kwargs)


    def calculate_monthly_expense(self):
        if self.long_term:
            if self.interest_rate == 0:
                return self.amount / ((self.end_date - self.date) / 30)  # Assuming a month has 30 days
            else:
                months = (self.end_date.year - datetime.now().year) * 12 + self.end_date.month - datetime.now().month
                monthly_rate = self.interest_rate / 12 / 100
                monthly_expense = (self.amount * monthly_rate) / (1 - (1 + monthly_rate) ** -months)
                return round(monthly_expense, 2)
        else:
            return self.monthly_expense


class Subscription(models.Model):
    name = models.CharField(max_length=100)
    amount = models.FloatField(default=0)
    end_date = models.DateField()
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
