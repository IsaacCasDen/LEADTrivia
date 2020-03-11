from django.urls import path

from . import views

urlpatterns = [
    path('',views.index, name='index'),
    path('admin_manager/', views.admin_manager, name='admin_manager'),
    path('admin_game/', views.admin_game,name='admin_game'),
    path('admin_game/admin_prev_question/', views.admin_prev_question,name='admin_prev_question'),
    path('admin_game/admin_next_question/', views.admin_next_question,name='admin_next_question'),
    path('admin_game/', views.admin_game,name='admin_game'),
    path('edit_game/', views.edit_game,name='edit_game'),
    path('create_game/', views.create_game,name='create_game'),
    path('save_game/', views.save_game,name='save_game'),
    path('lobby/',views.lobby,name='lobby'),
    path('team/',views.team, name='team'),
    path('show_question/',views.show_question, name='show_question'),
    path('team/leave_team/',views.leave_team, name="leave_team"),
    path('team/update_teamname/',views.update_teamname,name="update_teamname"),
    path('team/update_username/',views.update_username,name="update_username"),
    path('show_question/submit_answer/',views.submit_answer,name="submit_answer"),
    path('next_round/',views.next_round,name='next_round'),
    path('show_question/prev_question/',views.prev_question, name="prev_question"),
    path('show_question/next_question/',views.next_question, name="next_question"),
    path('show_question/current_question_index/', views.current_question_index, name='current_question_index'),
    path('edit_game/edit_questions/',views.edit_questions,name="edit_questions"),
    path('round_results/', views.round_results, name = "round_results"),
]