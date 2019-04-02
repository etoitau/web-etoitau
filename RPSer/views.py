from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from random import random, choice
from RPSer.models import *
import json
import requests
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# RPSer/views.py

# reformats model User object into a dict
def getuserdict(userobject):
    logger.info("getuserdict called")
    userdict = dict(
        id = userobject.id,
        username = userobject.username,
        wins = userobject.wins,
        losses = userobject.losses,
        w_l = float(userobject.w_l),
        count = userobject.count,
    )
    logger.debug("Made dict: {id: %s, username: %s, wins: %s, losses: %s, w_l: %s, count: %s", 
        userdict['id'], userdict['username'], userdict['wins'], userdict['losses'], userdict['w_l'], userdict['count']    
    )
    return userdict

# If main RPSer page is called, pull up available info about user and send to template (and js)
def rpser(request):
    logger.info("rpser called")
    context = dict()
    # create/get uwer 'all' and pass it's info
    alluserobj, created = User.objects.get_or_create(username="all")
    if created:
        logger.info("user 'all' was created")
    context["allinfoj"] = json.dumps(getuserdict(alluserobj))
    # if logged in create/get user, otherwise playing as 'all'
    # send user and loggedin as json, username and logged in plaintext

    if request.user.is_authenticated:
        logger.info("user is authenticated")
        context["loggedin"] = 1
        userobj, created = User.objects.get_or_create(
            username = request.user.username)
        context["userinfoj"] = json.dumps(getuserdict(userobj))
        context["username"] = userobj.username
    else:
        logger.info("user is not authenticated")
        context["loggedin"] = 0
        context["userinfoj"] = context["allinfoj"]
        context["username"] = "all"
    return render(request, "RPSer/rpser.html", context=context)

# page to sign up for account
def signup(request):
    if request.method == 'POST':
        logger.info("signup called: POST")
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('rpser')
    else:
        logger.info("signup called: GET")
        form = UserCreationForm()
        return render(request, 'RPSer/signup.html', {'form': form})

# AJAX request from page for next RPSer throw
def getthrow(request):
    logger.info("getthrow called")
    # incoming data: {userid: modeid, rpser_last: rpser_last, user_last: user_last},
    # load from json and use custom manager to get relavent info from Brain
    json_data = json.loads(request.body)
    xp = Brain.rackbrain_objects.check_xp(json_data)
    # start by picking Rock and then see if paper or scissors would be better
    throw = 'R'
    maxscore = xp[throw]['score']
    logger.debug("%s: %.3f", throw, maxscore)
    for option in ["P", "S"]:
        optscore = xp[option]["score"]
        logger.debug("%s: %.3f", option, optscore)
        if optscore > maxscore:
            throw = option
            maxscore = optscore
    logger.info("getthrow chose: %s", throw)
    return JsonResponse(throw, safe=False)

# AJAX data from page to be added to Brain
@transaction.atomic
def logxp(request):
    # data: {userid: modeid, rpser_last: rpser_last, 
    #   user_last: user_last, rpser_throw: nextthrow, rpser_win: won}
    # update user stats
    logger.info("logxp called")
    logger.info("Updating User data for user")
    json_data = json.loads(request.body)
    uobj = User.objects.get(id = json_data['userid'])
    username = uobj.username
    logger.info("username: %s", username)
    logger.debug("Before update, database has:\nUser wins: %i\nUser losses %i\nUser throws %i", 
        uobj.wins, uobj.losses, uobj.count
    )
    logger.debug("RPSer won?: %i", json_data['rpser_win'])
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
    logger.debug("After update, database has:\nUser wins: %i\nUser losses %i\nUser throws %i", 
        uobj.wins, uobj.losses, uobj.count
    )

    # if playing as all, don't doublecount, else remember to also log all
    if username != "all":
        logger.info("Updating User data for 'all'")
        aobj = User.objects.get(username = 'all')
        logger.debug("Before update, database has:\nAll wins: %i\nAll losses %i\nAll throws %i", 
        aobj.wins, aobj.losses, aobj.count
        )
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
        logger.debug("After update, database has:\nAll wins: %i\nAll losses %i\nAll throws %i", 
        aobj.wins, aobj.losses, aobj.count
        )

    # update knowledge in Brain
    logger.info("Updating Brain for user")
    obj, created = Brain.objects.get_or_create(
        userid = User(id=json_data['userid']),
        user_last = json_data['user_last'],
        rpser_last = json_data['rpser_last'],
        rpser_next = json_data['rpser_throw'],
        defaults = {'count':1, 'score':json_data['rpser_win']}
    )
    logger.debug('get/create Brain object:')
    logger.debug(obj)
    #logger.debug("Play info:\nid: %i\nuser last: %s\nrpser last: %s\n rpser tried: %s\n score: %i\n count: %i", 
    #    obj.userid, obj.user_last, obj.rpser_last, obj.rpser_next, obj.score, obj.count
    #)
    if not created:
        obj.count += 1
        obj.score += json_data['rpser_win']
        obj.save()
        logger.debug("Score updated to: %i and count updated to: %i", obj.score, obj.count)

    # if playing as all, don't doublecount, else remember to also log all    
    if username != "all":
        logger.info("Updating Brain for 'all'")
        obj, created = Brain.objects.get_or_create(
        userid = User(id=aobj.id),
        user_last = json_data['user_last'],
        rpser_last = json_data['rpser_last'],
        rpser_next = json_data['rpser_throw'],
        defaults = {'count':1, 'score':json_data['rpser_win']}
        )
        logger.debug('get/create Brain object:')
        logger.debug(obj)
        #logger.debug("Play info:\nid: %i\nuser last: %s\nrpser last: %s\n rpser tried: %s\n score: %i\n count: %i", 
        #obj.userid, obj.user_last, obj.rpser_last, obj.rpser_next, obj.score, obj.count
        #)
        if not created:
            obj.count += 1
            obj.score += json_data['rpser_win']
            obj.save()
            logger.debug("Score updated to: %i and count updated to: %i", obj.score, obj.count)
    
    return JsonResponse('Log XP OK', safe=False)

# render a leaderboard of players with top win/loss %
def leaderboard(request):
    logger.info("leaderboard called")
    # get info for this user
    if request.user.is_authenticated:
        loggedin = True
        thisuser = User.objects.get(username = request.user.username)
    else:
        loggedin = False
        thisuser = User.objects.get(username = 'all')
    # set minimum throws to qualify for leaderboard and number of top records to show (+ user if not in top)
    qualcount = 27
    numscores = 10
    # get users sorted by w_l ratio
    sortedusers = User.objects.order_by('-w_l')
    # build leaderboard table
    table = list()
    i = 0
    for sorteduser in sortedusers:
        # find this user and show standing in table
        if sorteduser.username == thisuser.username:
            table.append([
                (i + 1),
                sorteduser.username,
                sorteduser.w_l,
                sorteduser.count,           
            ])
            # if all top users have already been shown we can quit now
            if i > numscores:
                break
            i += 1
        # if record is not this user and one of top, add to table
        elif i < numscores and sorteduser.count > qualcount:
            table.append([
                (i + 1),
                sorteduser.username,
                sorteduser.w_l,
                sorteduser.count
            ]) 
            i += 1
    # data to send to page    
    context = {
        'table' : table,
        'qualcount' : qualcount,
        'numscores' : numscores,
        'loggedin' : loggedin,
    }
    return render(request, 'RPSer/leaderboard.html', context)