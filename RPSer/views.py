from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from random import random, choice
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

def getuserdict(userobject):
    userdict = dict(
        id = userobject.id,
        username = userobject.username,
        wins = userobject.wins,
        losses = userobject.losses,
        w_l = float(userobject.w_l),
        count = userobject.count,
    )
    return userdict

def rpser(request):
    context = dict()
    # create/get all
    alluserobj, created = User.objects.get_or_create(username="all")
    context["allinfoj"] = json.dumps(getuserdict(alluserobj))
    # if logged in create/get user
    # send user and loggedin as json, username and logged in plaintext
    if request.user.is_authenticated:
        context["loggedin"] = 1
        userobj, created = User.objects.get_or_create(
            username = request.user.username)
        context["userinfoj"] = json.dumps(getuserdict(userobj))
        context["username"] = userobj.username
    else:
        context["loggedin"] = 0
        context["userinfoj"] = context["allinfoj"]
        context["username"] = "all"
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

#def getscores(request):
#    scores = Brain.rackbrain_objects.scoreboard(request.POST.get('username'))
#    console.log("getscores got username:")
#    console.log(request.POST.get('username'))
#    return JsonResponse(scores)

def getthrow(request):
    # data: {userid: modeid, rpser_last: rpser_last, user_last: user_last},
    json_data = json.loads(request.body)
    #state = dict()
    #state["userid"] = json_data['userid'], 
    #    "rpser_last" : json_data['rpser_last'], 
    #    "user_last" : json_data['user_last']}
    xp = Brain.rackbrain_objects.check_xp(json_data)
    # start by randomly picking one
    throw = choice(['R', 'P', 'S'])
    # if not first throw of series, replace with intelligent pick
    if json_data["rpser_last"] != 'N':
        # set score to beat, note break even has expected value 0.5
        maxscore = 0.5
        for option in ["R", "P", "S"]:
            wscore = xp[option]["score"] #+ random()/10
            if wscore > maxscore:
                throw = option
                maxscore = wscore
    return JsonResponse(throw, safe=False)

@transaction.atomic
def logxp(request):
    # data: {userid: modeid, rpser_last: rpser_last, 
    #   user_last: user_last, rpser_throw: nextthrow, rpser_win: won}
    # update user stats
    json_data = json.loads(request.body)
    uobj = User.objects.get(id = json_data['userid'])
    username = uobj.username
    if json_data['rpser_win'] == 1:
        uobj.losses += 1
    elif json_data['rpser_win'] == -1:
        uobj.wins += 1
    uobj.count += 1
    if uobj.losses:
        uobj.w_l = uobj.wins / uobj.losses 
    else:
        uobj.w_l = uobj.wins
    uobj.save()

    # if playing as all, don't doublecount, else remember to also log all
    if username != "all":
        aobj = User.objects.get(username = 'all')
        if json_data['rpser_win'] == 1:
            aobj.losses += 1
        elif json_data['rpser_win'] == -1:
            aobj.wins += 1
        aobj.count += 1
        if aobj.losses:
            aobj.w_l = aobj.wins / aobj.losses
        else:
            aobj.w_l = aobj.wins
        aobj.save()

    # update knowledge in Brain
    obj, created = Brain.objects.get_or_create(
        userid = User(id=json_data['userid']),
        user_last = json_data['user_last'],
        rpser_last = json_data['rpser_last'],
        rpser_next = json_data['rpser_throw'],
        defaults = {'count':1, 'score':json_data['rpser_win']}
    )
    if not created:
        obj.count += 1
        obj.score += json_data['rpser_win']
        obj.save()
    
    return JsonResponse('Log XP OK', safe=False)

def leaderboard(request):
    if request.user.is_authenticated:
        loggedin = True
        thisuser = User.objects.get(username = request.user.username)
    else:
        loggedin = False
    qualcount = 27
    numscores = 3
    #below worked to get top numscores records 
    #top_scores = (User.objects.filter(count__gt=qualcount).order_by('-w_l')
    #    .values_list('w_l', flat=True).distinct())
    #top_records = (User.objects.filter(count__gt=qualcount).order_by('-w_l')
    #    .filter(w_l__in=top_scores[:numscores]))
    sortedusers = User.objects.order_by('-w_l')
    #    .filter(w_l__in=top_scores[:numscores]))
    table = list()
    i = 0
    for sorteduser in sortedusers:
        if sorteduser.username == thisuser.username:
            table.append([
                (i + 1),
                sorteduser.username,
                sorteduser.w_l,
                sorteduser.count,           
            ])
            if i > numscores:
                break
            i += 1
        elif i < numscores and sorteduser.count > qualcount:
            table.append([
                (i + 1),
                sorteduser.username,
                sorteduser.w_l,
                sorteduser.count
            ]) 
            i += 1
        
    
    context = {
        'table' : table,
        'qualcount' : qualcount,
        'numscores' : numscores,
        'loggedin' : loggedin,
    }
    return render(request, 'RPSer/leaderboard.html', context)