from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from RPSer.models import *
# from django.http import JsonResponse
import json

import requests

# context dict for page use
# context = {"user": User, "username": "all"}
# user.is_authenticated
# user.id
# user.username

#return JsonResponse(data)

# ajax
# in js use $.get("<url path directed in urls to view>"+<string (in url path)> that tells what to do>), a js function to execute maybe) 
# in urls then path is like path('<url>/<str:<variable>>, <view>)


def rpser(request):
    userinfo = dict()
    userinfo["loggedin"] = request.user.is_authenticated
    if userinfo["loggedin"]:
        userinfo["username"] = request.user.username
    context = {"userinfo": userinfo, "userinfoj": json.dumps(userinfo)}
    return render(request, "RPSer/rpser.html", context=context)

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('rpser')
    else:
        form = UserCreationForm()
        return render(request, 'RPSer/signup.html', {'form': form})