from django.urls import path

from . import views

urlpatterns = [
    path('',views.index, name='index'),
    path('lobby/',views.lobby,name='lobby'),
    path('team/',views.team, name='team'),
    path('mcq/',views.mcq, name='mcquestion'),
    path('team/leave_team/',views.leave_team, name="leave_team"),
    path('team/update_teamname/',views.update_teamname,name="update_teamname"),
    path('team/update_username/',views.update_username,name="update_username"),
    path('mcq/submit_answer/',views.submitAns,name="submitAns"),
]