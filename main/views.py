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
    SalesRecord, DataToPandasDataset, Calculation
)

class HomeListView(ListView):
    """Landing page — loads dashboard KPIs from both data sources."""
    @staticmethod
    def __extract_all_data():

        ds = DataToPandasDataset(table="PastDueLoanRazm")
        df = ds.load_loans_dataframe()
        wi = Calculation()
        rs = wi.WeightedAverageRate()

         # Optional: filter/calculate before sending to template
        # df['BalanceEQ'] = df['principal_amount'] - df['repaid_amount']
        # df['is_overdue']  = df['days_past_due'] > 0

        context = {
        'result': rs,    
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



