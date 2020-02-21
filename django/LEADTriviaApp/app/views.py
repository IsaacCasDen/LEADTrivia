from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.shortcuts  import redirect
import json

from .models import *
# Create your views here.

USERNAME = 'username'
USERID = 'userId'
TEAMID = 'teamId'
TEAMNAME = 'teamname'
GAMEID = 'gameId'
GAMENAME = 'gameName'

def index(request):
    game_data = get_game()

    if 'gameId' not in request.session.keys():
        request.session['gameId'] = game_data['Game'][0]

    if 'userId' not in request.session.keys():
        request.session['userId'] = None

    if 'errors' not in request.session.keys():
        request.session['errors'] = []

    context = {}
    context['gameId'] = request.session['gameId']
    context['userId'] = request.session['userId']
    context['errors'] = request.session['errors']
    context['data'] = json.dumps(game_data)

    return render(request,'index.html', context)

def lobby(request):
    context = {}

    userId = request.POST.get('userId', '')
    gameId = request.POST.get('gameId', '')
    if userId == '' and gameId == '':
        return redirect (index)
    elif gameId == '':
        context = {}
        request.session['userId'] = userId
        request.session['errors'] = json.dumps(['Please enter username'])
        return redirect(index)
    else:
        request.session['gameId'] = gameId
        request.session['userId'] = userId
        context['data'] = json.dumps(get_game())

        user = get_user(int(gameId), user_name = userId)
        if user == None:
            # request.session['errors'] = json.dumps(['username has already been taken'])
            # return redirect (index)
            user = new_user(gameId,userId)
        # else:
        context['userId'] = request.session['userId']
        context['gameId'] = request.session['gameId']
        return render(request, 'lobby.html',context)
            
def team(request):
    context = {}
    context['data'] = {}
    data = get_game()

    gameId = request.session.get(GAMEID,'')
    teamId = request.POST.get(TEAMID,'')
    userId = request.session.get(USERID,'')
    
    if userId == '' or gameId == '':
        return redirect(index)
    
    if teamId == '':
        pass

    if id == '':
        context['data'][TEAMNAME] = "Team {}".format(len(data['Teams'].keys()))
        context['data']['users'] = ["New User"]
    else:
        context['data'][TEAMNAME] = id
        context['data']['users'] = data['Teams'][id]
    return render(request,'team.html',context)
    

def leave_team(request):
    userId = request.POST['userId']
    #remove user from team and return to lobby

    return redirect('/app/')