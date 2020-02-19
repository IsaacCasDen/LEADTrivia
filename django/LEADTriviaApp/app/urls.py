from django.urls import path

from . import views

urlpatterns = [
    path('',views.lobby, name='lobby'),
    path('team/',views.team, name='team'),
    path('team/app/leave_team',views.leave_team, name='leave_team'),
]