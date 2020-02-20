from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts  import redirect
import json

from .models import *
# Create your views here.

def index(request):
    context = {}
    context['data'] = json.dumps(get_game())
    return render(request,'index.html', context)

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
    return render(request,'team.html',context)

def lobby(request):
    context = {}
    context['data'] = json.dumps(get_game())

    userId = request.POST.get('userId', '')
    gameId = request.POST.get('gameId', '')
    if userId == '' or gameId == '':
        return redirect (index)
    else:
        user = new_user(int(gameId), userId)
        if user == None: 
            return redirect (index)
        else:
            return render(request, 'lobby.html',context)
            
    

