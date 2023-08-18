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
from django.utils.safestring import mark_safe
import matplotlib.pyplot as plt
#import numpy as np
from io import BytesIO
import base64
from datetime import datetime
from dateutil.relativedelta import relativedelta
import plotly.express as px
from plotly.graph_objs import *

def home(request):
    user = request.user    
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
    # plt.bar(data['months'], data['expenses'])
    # plt.xlabel('Month')
    # plt.ylabel('Total Expenses')
    # plt.title('Monthly Expenses')
    
    # # Create a PNG image and return it
    # buffer = BytesIO()
    # plt.savefig(buffer, format='png')
    # plt.close()
    
    # # Encode the image in base64
    # return base64.b64encode(buffer.getvalue()).decode()
    
    fig = px.bar(data, x='months', y='expenses', title='Monthly Expenses')
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='rgba(255,255,255,100)',
    )

    # fig.update_traces(marker_color='green') 
    
    # Convert the figure to a JSON string
    graph_json = fig.to_json()

    return graph_json
    # fig = px.bar(data, x='months', y='expenses', title='Monthly Expenses')
    # fig.update_layout(
    #     paper_bgcolor='rgba(0,0,0,0)',
    #     plot_bgcolor='rgba(0,0,0,0)',
    #     font_color='rgba(255,255,255,100)',
    #     barmode='relative',  # This line is important to ensure the correct behavior of the bars
    #     showlegend=True,
    #     legend=dict(x=0, y=1),
    #     yaxis=dict(showline=True, showgrid=True, linecolor='rgba(255,255,255,0.2)'),
    #     xaxis=dict(showline=True, showgrid=True, linecolor='rgba(255,255,255,0.2)'),
    #     font=dict(color='rgba(255,255,255,0.8)'),
    #     hovermode="x unified"
    # )

    # # Set the default color to 'red' for all bars
    # fig.update_traces(marker_color='red')

    # graph_json = fig.to_json()
    # return graph_json


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
    
    
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     user = self.request.user
    #     accounts = Account.objects.filter(user=user)
    #     expense_data = {}

        # for account in accounts:
        #     liabilities = account.liability_list.all()
        #     for liability in liabilities:
        #         if liability.long_term and liability.monthly_expense:
        #             current_date = liability.date
        #             while current_date <= liability.end_date:
        #                 year_month = current_date.strftime('%Y-%m')
        #                 if year_month not in expense_data:
        #                     expense_data[year_month] = []

        #                 expense_data[year_month].append({
        #                     'name': liability.name,
        #                     'amount': liability.monthly_expense,
        #                     'date': current_date,
        #                 })

        #                 # Move to the next month
        #                 current_date = current_date + relativedelta(months=1)
        #         else:
        #             year_month = liability.date.strftime('%Y-%m')
        #             if year_month not in expense_data:
        #                 expense_data[year_month] = []

        #             expense_data[year_month].append({
        #                 'name': liability.name,
        #                 'amount': liability.amount,
        #                 'date': liability.date,
        #             })

    #     # Convert the expense_data into aggregated_data
    #     aggregated_data = [{'year_month': key, 'expenses': sum(item['amount'] for item in value)} for key, value in expense_data.items()]

    #     context['expense_data'] = expense_data
    #     context['aggregated_data'] = aggregated_data

    #     # Prepare graph_data for generating the bar chart
    #     graph_data = {
    #         'months': [item['year_month'] for item in aggregated_data],
    #         'expenses': [item['expenses'] for item in aggregated_data]
    #     }
    #     graph_data['chart'] = generate_graph(graph_data)
    #     context['graph_data'] = graph_data

    #     return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        accounts = Account.objects.filter(user=user)
        expense_data_graph = {}
        expense_data = {}

        for account in accounts:
            liabilities = account.liability_list.all()
            for liability in liabilities:
                if liability.long_term and liability.monthly_expense:
                    current_date = liability.date
                    while current_date <= liability.end_date:
                        year_month = current_date.strftime('%Y-%m')
                        if year_month not in expense_data_graph:
                            expense_data_graph[year_month] = []

                        expense_data_graph[year_month].append({
                            'name': liability.name,
                            'amount': liability.monthly_expense,
                            'date': current_date,
                            'end_date': liability.end_date,
                        })

                        # Move to the next month
                        current_date = current_date + relativedelta(months=1)
                else:
                    year_month = liability.date.strftime('%Y-%m')
                    if year_month not in expense_data_graph:
                        expense_data_graph[year_month] = []

                    expense_data_graph[year_month].append({
                        'name': liability.name,
                        'amount': liability.amount,
                        'date': liability.date,
                    })               

        for account in accounts:
            liabilities = account.liability_list.all()
            for liability in liabilities:
                if liability.long_term and liability.monthly_expense:
                    current_date = liability.date
                    year_month = current_date.strftime('%Y-%m')
                    if year_month not in expense_data:
                        expense_data[year_month] = []

                    expense_data[year_month].append({
                        'name': liability.name,
                        'amount': liability.monthly_expense,
                        'date': current_date,
                        'end_date': liability.end_date,
                        'long_term': liability.long_term,
                    })

                        # Move to the next month
                    current_date = current_date + relativedelta(months=1)
                else:
                    year_month = liability.date.strftime('%Y-%m')
                    if year_month not in expense_data:
                        expense_data[year_month] = []

                    expense_data[year_month].append({
                        'name': liability.name,
                        'amount': liability.amount,
                        'date': liability.date,
                    })              
        # Convert the expense_data_graph into aggregated_data
        aggregated_data = [{'year_month': key, 'expenses': sum(item['amount'] for item in value)} for key, value in expense_data_graph.items()]

        context['expense_data'] = expense_data
        context['aggregated_data'] = aggregated_data

        # Prepare graph_data for generating the Plotly graph
        graph_data = {
            'months': [item['year_month'] for item in aggregated_data],
            'expenses': [item['expenses'] for item in aggregated_data]
        }
        graph_data['chart'] = generate_graph(graph_data)
        context['graph_data'] = mark_safe(graph_data['chart'])  # Use mark_safe to render the JSON as HTML

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
