from django.shortcuts import render
from django.http import HttpResponse
import json

from .models import *

# Create your views here.

def index(request):
    return HttpResponse("Where's your use case now???")


def team(request):
    context = {}
    context['data'] = json.dumps(get_game())
    return render(request,'team.html',context)


