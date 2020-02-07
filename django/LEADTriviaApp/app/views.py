from django.shortcuts import render
from django.http import HttpResponse

from .models import *
# Create your views here.


def lobby(request):
    return render(request, 'lobby.html')

