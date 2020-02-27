from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.shortcuts  import redirect
import json

from .models import *
# Create your views here.

def index(request):
    game_data = get_game()

    if 'gameId' not in request.session.keys():
        request.session['gameId'] = game_data['Game'][0]

    if 'userId' not in request.session.keys():
        request.session['userId'] = None

    if 'errors' not in request.session.keys():
        request.session['errors'] = []

    should_set = False
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
    if gameId != game_data['Game']['Id']:
        gameId = game_data['Game']['Id']
        request.session['gameId']=gameId
        request.session['userId']=''
    if isinstance(userId,int) and isinstance(gameId,int) and  len(request.session['errors'])==0:
        return redirect(lobby)

    context = {}
    context['gameId'] = request.session['gameId']
    context['userId'] = request.session['userId']
    context['errors'] = request.session['errors']
    context['data'] = json.dumps(game_data)

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

    if gameId != '':
        gameId = int(gameId)
        request.session['gameId'] = gameId
    
    if userId != '':
        userId = int(userId)
        request.session['userId'] = userId
    
    if teamId != '':
        teamId = int(teamId)
        request.session['teamId'] = teamId

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
    context = {}
    context['data'] = {}
    data = get_game()

    id = request.POST.get('teamId','')
    if id == '':
        context['data']['team_name'] = "Team {}".format(len(data['Teams'].keys()))
        context['data']['users'] = ["New User"]
    else:
        context['data']['team_name'] = id
        context['data']['users'] = data['Teams'][id]
        
    gameId = request.session.get('gameId','')
    teamId = request.POST.get('teamId',request.session.get('teamId',''))
    userId = request.session.get('userId','')
    username = request.session.get('username','')

    if gameId == '' or userId == '':
        return redirect(index)
    
    if teamId!='':
        teamId = int(teamId)

    data = get_gamestate(gameId)    

    team=None

    if teamId == '':
        team = create_team(gameId,"Team {}".format(len(data['Teams'].keys())))
        data = get_gamestate(gameId)

        teamId = team.id
        if team==None:
            request.session['errors']=json.dumps(['Error creating team'])
            return redirect(index)
        else:
            add_teammember(gameId,teamId,userId)
            data = get_gamestate(gameId)
            request.session['teamId'] = teamId
            context[TEAMNAME]=team.team_name
            users = data['Teams'][teamId]['members']
            
    else:
        users = data['Teams'][teamId]['members']
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
        user = new_user(int(gameId), userId)
        request.session['userId'] = userId
        context['data'] = json.dumps(get_game())
        if user == None: 
            request.session['errors'] = json.dumps(['username has already been taken'])
            return redirect (index)
        else:
            return render(request, 'lobby.html',context)
            
def leave_team(request):
    userId = request.POST['userId']
    #remove user from team and return to lobby

    return redirect('/app/')

