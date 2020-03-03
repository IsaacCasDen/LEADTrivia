from django.urls import path

from . import views

urlpatterns = [
    path('',views.index, name='index'),
    path('admin_manager/', views.admin_manager, name='admin_manager'),
    path('admin_game/', views.admin_game,name='admin_game'),
    path('create_game/', views.create_game,name='create_game'),
    path('save_game/', views.save_game,name='save_game'),
    path('lobby/',views.lobby,name='lobby'),
    path('team/',views.team, name='team'),
    path('mcq/',views.mcq, name='mcquestion'),
    path('team/leave_team/',views.leave_team, name="leave_team"),
    path('team/update_teamname/',views.update_teamname,name="update_teamname"),
    path('team/update_username/',views.update_username,name="update_username"),
    path('mcq/submit_answer/',views.submitAns,name="submitAns"),
    path('next_round/',views.next_round,name='next_round')
]