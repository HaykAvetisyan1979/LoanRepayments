"""
views.py — Thin views. Each view:
  1. Reads filter params from the request
  2. Queries external DB (via ORM proxy models)
  3. Passes data to a Calculation class from models.py
  4. Sends the result dict to a template

Views contain NO calculation logic themselves.
"""

from django.shortcuts import render, redirect, get_object_or_404
from typing import Any
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.generic import ListView
from django.views.decorators.cache import cache_page
import datetime

from .models import (
    SalesRecord, DataToPandasDataset
)

# class HomeListView(ListView):				
#     template_name = 'index.html'

#     def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:			# def getTab
#         home = Home.objects.first()

#         context ={
#             'home':home,
#         }

#         return render(request, self.template_name, context=context)

# class HomeListView(ListView):
#     template_name = 'index.html'

#     @staticmethod
#     def __extract_all_data():

#         # user_object = Me.objects.first()
#         # about_me = AboutMe.objects.first()
#         # services = WhatIDo.objects.all()

#         context = {
#             # 'user_object':user_object,
#             # 'about_me': about_me,
#             # 'services_1':services[:2],

#         }

#         return context

#     def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
#         return render(request, self.template_name, context=self.__extract_all_data())
    
#     # def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
#     #     form = ContactForm(request.POST)
#     #     if form.is_valid():
#     #         full_name = form.cleaned_data.get('full_name')
#     #         email = form.cleaned_data.get('email')
#     #         subject = form.cleaned_data.get('subject')
#     #         message = form.cleaned_data.get('message')
            
#     #         email_massage = f"Sender Name: {full_name}\nSender Email: {email}\nTopic: {subject}\nMessage:\n{message}"
#     #         send_mail(
#     #             subject="Message From Portfolio",
#     #             message=email_massage,
#     #             recipient_list=[EMAIL_SUPPORT_USER],
#     #             from_email=EMAIL_HOST_USER
#     #         )
#     #         form.save()
#     #     else:
#     #         form = ContactForm()
        
#     #     return redirect('/')

class HomeListView(ListView):
    """Landing page — loads dashboard KPIs from both data sources."""
    @staticmethod
    def __extract_all_data():

        ds = DataToPandasDataset(table="PastDueLoanRazm")
        df = ds.load_loans_dataframe()

         # Optional: filter/calculate before sending to template
        # df['BalanceEQ'] = df['principal_amount'] - df['repaid_amount']
        # df['is_overdue']  = df['days_past_due'] > 0

        context = {
        'columns': df.columns.tolist(),          # list of column header names
        'rows':    df.to_dict('records'),         # list of dicts — one per row
        'summary': {
                    'total_rows':       len(df),
                    'total_outstanding': df['BalanceEQ'].sum(),
                    # 'overdue_count':    int(df['is_overdue'].sum()),
                    }
        }

        return context

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return render(request, 'main/index.html', context=self.__extract_all_data())



# def sales_report(request):
#     """Sales summary with optional year/region filters."""
#     # ctx = get_menu_context(request)

#     # Filters from GET params
#     year = request.GET.get('year', datetime.date.today().year)
#     region = request.GET.get('region', '')

#     try:
#         qs = SalesRecord.objects.using('external_db').filter(sale_date__year=year)
#         if region:
#             qs = qs.filter(region=region)

#         engine = CalculationEngine(qs)
#         ctx['data'] = engine.sales_summary()

#         # Available filter options
#         ctx['regions'] = list(
#             SalesRecord.objects.using('external_db')
#             .values_list('region', flat=True)
#             .distinct()
#             .order_by('region')
#         )
#         ctx['db_connected'] = True
#     except Exception as e:
#         ctx['db_connected'] = False
#         ctx['db_error'] = str(e)
#         ctx['data'] = {}

#     ctx['selected_year'] = int(year)
#     ctx['selected_region'] = region
#     ctx['years'] = list(range(datetime.date.today().year, datetime.date.today().year - 5, -1))
#     return render(request, 'core/sales_report.html', ctx)
