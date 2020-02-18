from django.shortcuts import render
from django.http import HttpResponse
import json

from .models import *

from .models import *
# Create your views here.

def index(request):
    return render(request,'index.html')


def team(request):
    context = {}
    context['data'] = json.dumps(get_game())
    return render(request,'team.html',context)

def lobby(request):
    return render(request, 'lobby.html')

