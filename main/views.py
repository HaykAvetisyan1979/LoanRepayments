from django.shortcuts import render, redirect
from typing import Any
from django.http import HttpRequest, HttpResponse
from django.views.generic import ListView
from .models import Home

# class HomeListView(ListView):				
#     template_name = 'index.html'

#     def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:			# def getTab
#         home = Home.objects.first()

#         context ={
#             'home':home,
#         }

#         return render(request, self.template_name, context=context)

class HomeListView(ListView):
    template_name = 'index.html'

    @staticmethod
    def __extract_all_data():

        # user_object = Me.objects.first()
        # about_me = AboutMe.objects.first()
        # services = WhatIDo.objects.all()

        context = {
            # 'user_object':user_object,
            # 'about_me': about_me,
            # 'services_1':services[:2],

        }

        return context

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return render(request, self.template_name, context=self.__extract_all_data())
    
    # def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
    #     form = ContactForm(request.POST)
    #     if form.is_valid():
    #         full_name = form.cleaned_data.get('full_name')
    #         email = form.cleaned_data.get('email')
    #         subject = form.cleaned_data.get('subject')
    #         message = form.cleaned_data.get('message')
            
    #         email_massage = f"Sender Name: {full_name}\nSender Email: {email}\nTopic: {subject}\nMessage:\n{message}"
    #         send_mail(
    #             subject="Message From Portfolio",
    #             message=email_massage,
    #             recipient_list=[EMAIL_SUPPORT_USER],
    #             from_email=EMAIL_HOST_USER
    #         )
    #         form.save()
    #     else:
    #         form = ContactForm()
        
    #     return redirect('/')
