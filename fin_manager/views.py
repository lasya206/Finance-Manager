from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from fin_manager import models
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F
from django.views.generic import TemplateView
from .models import Account, Liability, Investments, Subscription
from .forms import LiabilityForm, InvestmentForm
from django.views.generic.edit import FormView
from django.views.generic import ListView

import matplotlib.pyplot as plt
#import numpy as np
from io import BytesIO
import base64


def home(request):
    user = request.user
    try:
        account = Account.objects.get(user=user)
        income = account.calculate_income()
        expense = account.calculate_expense()

        context = {
                'income': income,
                'expense': expense,
        }
        return render(request, 'fin_manager/home.html', context)
    
    except (Account.DoesNotExist, TypeError, UnboundLocalError):
        account = None
    
    return render(request, 'fin_manager/home.html')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in
            login(request, user)
            return redirect('home')  # Change 'home' to your desired URL
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


def generate_graph(data):
    plt.bar(data['months'], data['expenses'])
    plt.xlabel('Month')
    plt.ylabel('Total Expenses')
    plt.title('Monthly Expenses')
    
    # Create a PNG image and return it
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    
    # Encode the image in base64
    return base64.b64encode(buffer.getvalue()).decode()


class ExpenseListView(FormView):
    template_name = 'expenses/expense_list.html'
    form_class = LiabilityForm
    success_url = '/expenses/'  # Update this with the correct URL

    def form_valid(self, form):
        # Retrieve the user's account
        account, _ = Account.objects.get_or_create(user=self.request.user)
        
        # Create a new liability instance and link it to the user's account
        liability = Liability(
            name=form.cleaned_data['name'],
            amount=form.cleaned_data['amount'],
            interest_rate=form.cleaned_data['interest_rate'],
            date=form.cleaned_data['date'],
            end_date=form.cleaned_data['end_date'],
            long_term=form.cleaned_data['long_term'],
            user=self.request.user
        )
        liability.save()
        account.liability_list.add(liability)
        return super().form_valid(form)
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        accounts = Account.objects.filter(user=user)
        expense_data = {}

        for account in accounts:
            liabilities = account.liability_list.all()
            for liability in liabilities:
                year_month = liability.date.strftime('%Y-%m')
                if liability.long_term:
                    if year_month not in expense_data:
                        expense_data[year_month] = []

                    expense_data[year_month].append({
                        'name': liability.name,
                        'amount': liability.amount,
                        'end_date': liability.end_date,
                        'date': liability.date,
                    })
                else:
                    if year_month not in expense_data:
                        expense_data[year_month] = []

                    expense_data[year_month].append({
                        'name': liability.name,
                        'amount': liability.amount,
                        'date': liability.date,
                    })
        

        context['expense_data'] = expense_data

        graph_data = {
            'months': [item['year_month'] for item in aggregated_data],
            'expenses': [item['expenses'] for item in aggregated_data]
        }
        graph_data['chart'] = generate_bar_chart(graph_data)
        
        context['graph_data'] = graph_data

        return context


class InvestmentListView(FormView):
    template_name = 'investments/investment_list.html'
    form_class = InvestmentForm
    success_url = '/investments/'  # Update this with the correct URL

    def form_valid(self, form):
        # Retrieve the user's account
        account, _ = Account.objects.get_or_create(user=self.request.user)
        
        # Create a new liability instance and link it to the user's account
        investment = Investments(
            name=form.cleaned_data['name'],
            amount=form.cleaned_data['amount'],
            return_rate=form.cleaned_data['return_rate'],
            end_date=form.cleaned_data['end_date'],
            user=self.request.user
        )
        investment.save()
        account.investment_list.add(investment)
        return super().form_valid(form)
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        # Retrieve user's account data and related liabilities
        accounts = Account.objects.filter(user=user)
        print(accounts)
        # Create a dictionary to store expense data grouped by month
        investment_data = {}

        for account in accounts:
            investments = account.investment_list.all()
            for investment in investments:
                year_month = investment.end_date.strftime('%Y-%m')

                if year_month not in investment_data:
                    investment_data[year_month] = []

                investment_data[year_month].append({
                    'name': investment.name,
                    'amount': investment.amount,
                    'end_date': investment.end_date,
                })
        
        context['investment_data'] = investment_data
        return context
