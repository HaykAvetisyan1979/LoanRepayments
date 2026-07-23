from django.shortcuts import render

from django.shortcuts import render, redirect
from typing import Any
from django.http import HttpRequest, HttpResponse
from django.views.generic import ListView
from .models import HomePortfolio


class PortfolioListView(ListView):
    template_name = 'data-tables.html'

    @staticmethod
    def __extract_all_data():

        # user_object = Me.objects.first()
        # about_me = AboutMe.objects.first()
        # services = WhatIDo.objects.all()
        # portfolio = HomePortfolio.objects.first()
        items = [1,2,3,4,5,6,7,8,9,0]

        context = {
            # 'user_object':user_object,
            # 'about_me': about_me,
            # 'services_1':services[:2],
            # 'portfolio':portfolio,
            'items':items

        }

        return context

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return render(request, self.template_name, context=self.__extract_all_data())
    
