from django.shortcuts import render, redirect
from django.http import HttpResponse
import json

from .models import *

# Create your views here.

def index(request):
    return render(request,'index.html')

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
    return render(request, 'lobby.html',context)

def leave_team(request):
    userId = request.POST['userId']
    #remove user from team and return to lobby

    return redirect('/app/')

