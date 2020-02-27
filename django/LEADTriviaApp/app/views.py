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

def set_session_vars(request):
    if 'gameId' not in request.session.keys():
        request.session['gameId'] = ''
    if 'errors' not in request.session.keys():
        request.session['errors'] = []
    if 'userId' not in request.session.keys():
        request.session['userId'] = ''
    if 'username' not in request.session.keys():
        request.session['username'] = ''
    if 'teamId' not in request.session.keys():
        request.session['teamId'] = ''

    should_set = True
    if should_set:
        request.session['userId'] = 160
        request.session['errors'] = []

        games = get_games()
        request.session['gameId'] = games[len(games)-1].id


def init_db():
    should_init = False
    if should_init:
        try:
            reset_db()
        except:
            pass
        finally:
            create_model()
    

def index(request):
    set_session_vars(request)
    init_db()

    games = get_games()
    game_data = get_gamestate(games[len(games)-1].id)

    if request.session['gameId'] == '':
        pass

    userId = request.session['userId']
    gameId = request.session['gameId']
    if isinstance(userId,int) and isinstance(gameId,int) and  len(request.session['errors'])==0:
        return redirect(lobby)

    context = {}
    context['gameId'] = request.session['gameId']
    context['userId'] = request.session['userId']
    context['username'] = request.session['username']
    context['errors'] = request.session['errors']
    context['data'] = game_data

    return render(request,'index.html', context)

def lobby(request):
    set_session_vars(request)
    context = {}

    username = request.POST.get('username', request.session.get('username', ''))
    userId = request.POST.get('userId', request.session.get('userId', ''))
    gameId = request.POST.get('gameId', request.session.get('gameId', ''))
    teamId = request.POST.get('teamId', request.session.get('teamId', ''))
    request.session['gameId'] = gameId
    request.session['errors'] = []

    if gameId == '':
        return redirect(index)
    elif userId == '' and username == '':
        request.session['errors'] = json.dumps(['Please enter a username'])
        return redirect(index)
    elif userId == '':
        request.session['username'] = username
        user = create_user(int(gameId),username)
        if user == None:
            request.session['errors'] = json.dumps(['Username already taken'])
            return redirect(index)
        else:
            request.session['userId']=user.id
    else:
        user = get_user(int(gameId), int(userId))
        if user != None:
            request.session['userId']=user['user'].id
            request.session['username']=user['user'].user_name
            request.session['teamId']=user['team'].id
            return redirect(team)
        else:
            user = get_orphan(int(gameId),int(userId))
            if user == None:
                request.session['userId'] = ''
                request.session['teamId'] = ''
                return redirect(index)
            else:
                request.session['username'] = user.user.user_name
        
        context['data'] = get_gamestate(gameId)

        
        # else:
        context['username'] = request.session['username']
        context['gameId'] = request.session['gameId']
        context['errors'] = request.session['errors'] 
        return render(request, 'lobby.html',context)
            
def team(request):
    set_session_vars(request)
    context = {}

    gameId = request.session.get('gameId','')
    teamId = request.POST.get('teamId',request.session.get('teamId',''))
    userId = request.session.get('userId','')
    username = request.session.get('username','')

    if gameId == '' or userId == '':
        return redirect(index)
    
    if teamId!='':
        teamId = int(teamId)

    data = get_gamestate(gameId)
    users = data['Teams'][teamId]['members']

    team=None

    if teamId == '':
        team = create_team(gameId,"Team {}".format(len(data['Teams'].keys())))
        if team==None:
            request.session['errors']=json.dumps(['Error creating team'])
            return redirect(index)
        else:
            add_teammember(gameId,teamId,userId)
            request.session['teamId'] = teamId
            context['data'][TEAMNAME]=team.team_name
    else:
        team = get_team(gameId,teamId)
        if username not in users:
            if add_teammember(gameId,teamId,userId):
                users = [user.user_name for user in get_users(gameId,teamId)]
            else:
                redirect(lobby)

        request.session['teamId'] = teamId
        context[TEAMNAME] = team.team_name
        context['users'] = users
        context['username']= username
        context['errors'] = request.session['errors']
    
    return render(request,'team.html',context)
    

def leave_team(request):
    set_session_vars(request)
    gameId = request.session.get(GAMEID,'')
    userId = request.session.get(USERID,'')
    teamId = request.session.get(TEAMID,'')
    
    if gameId == '' or userId == '' or teamId == '':
        return redirect(index)
    
    if remove_teammember(gameId,teamId,userId):
        request.session[TEAMID]=''
        return redirect(lobby)
    
    return redirect(team)

def update_teamname(request):
    gameId = request.session.get(GAMEID,'')
    teamId = request.session.get(TEAMID,'')
    new_teamname = request.POST.get('new_teamname','')

    if new_teamname != '':
        if not change_teamname(gameId,teamId,new_teamname):
            request.session['errors'].append('Teamname already taken')
    
    return redirect(team)

def update_username(request):
    gameId = request.session.get(GAMEID,'')
    userId = request.session.get(USERID,'')
    new_username = request.POST.get('new_username','')
    
    if new_username != '':
        if not change_username(gameId,userId,new_username):
            request.session['errors'].append('Username already taken')
        else:
            request.session['username']=new_username

    return redirect(team)

