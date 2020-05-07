
import LEADTriviaApp
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.shortcuts  import redirect

from pathlib import Path
import sys
import os
import random
import json
import string

from .models import *
# Create your views here.

USERNAME = 'username'
USERID = 'userId'
TEAMID = 'teamId'
TEAMNAME = 'teamname'
GAMEID = 'gameId'
GAMENAME = 'gameName'

APP_ROOT = os.path.abspath(LEADTriviaApp.__path__[0])
MEDIA = os.path.join(str(Path(APP_ROOT).parent),'app','static','app','media')

class SessionState():
    def __init__(self):
        self.has_game=False
        self.game = None

        self.is_orphan = False
        self.has_user=False
        self.user = None

        self.has_team=False
        self.team = None

        self.has_mode = False
        self.mode = None

    def game_state(self):
        if self.game==None:
            return None
        else:
            return self.game.state

def init_session_vars(request):

    if 'mode' not in request.session.keys():
        request.session['mode'] = ''
    if 'gameId' not in request.session.keys():
        request.session['gameId'] = ''
    if 'errors' not in request.session.keys():
        request.session['errors'] = []
    if 'userId' not in request.session.keys():
        request.session['userId'] = ''
    if 'username' not in request.session.keys():
        request.session['username'] = ''
    if 'teamId' not in request.session.keys():
        request.session['teamId'] = ''

def validate_session(request)->SessionState:

    session_state = SessionState()

    gameId = request.POST.get('gameId','')
    userId = request.POST.get('userId','')
    teamId = request.POST.get('teamId','')
    mode = request.POST.get('mode','')

    if gameId == '':
        gameId = request.session.get('gameId','')
    else:
        request.session['gameId'] = int(gameId)
        gameId=int(gameId)

    if userId == '':
        userId = request.session.get('userId','')
    else:
        request.session['userId'] = int(userId)
        userId=int(userId)

    if teamId == '':
        teamId = request.session.get('teamId','')
    else:
        request.session['teamId'] = int(teamId)
        teamId=int(teamId)

    if mode == '':
        mode = request.session.get('mode','')
    else:
        request.session['mode'] = int(mode)
        mode=int(mode)

    user = None

    if userId!='':
        userId = int(userId)
        user = User.objects.filter(id=userId)
        if len(user)>0:
            user = user[0]
            session_state.has_user=True
            session_state.user = user

    if gameId == '':
        return session_state

    gameId = int(gameId)
    game = get_game(gameId)
    if game == None:
        return session_state
    else:
        session_state.has_game=True
        session_state.game=game

    if userId != '':
        u = TeamMember.objects.filter(user__id=userId,game__id=gameId)
        if len(u) == 0:
            session_state.is_orphan = True
            u = OrphanUser.objects.filter(user__id=userId,game__id=gameId)
            if len(u)==0:
                u = add_orphan(gameId,userId)

    if teamId != '':
        teamId = int(teamId)
        team = TriviaGameTeam.objects.filter(game__id=gameId,team__id=teamId)
        if len(team)>0:
            session_state.has_team = True
            session_state.team=team[0]
    
    if mode != '':
        session_state.has_mode = True
        session_state.mode=mode

    return session_state
    
def get_context(session_state:SessionState):
    context = {}

    context['gameId'] = json.dumps(None)
    context['gamename'] = ''
    context['userId'] = json.dumps(None)
    context['username'] = ''
    context['teamId'] = json.dumps(None)
    context['teamname'] = ''

    if session_state.has_user:
        context[USERID] = session_state.user.id
        context[USERNAME] = session_state.user.user_name
    if session_state.has_team:
        context[TEAMID] = session_state.team.id
        context[TEAMNAME] = session_state.team.team.team_name
    if session_state.has_game:
        context[GAMEID] = session_state.game.id
        context[GAMENAME] = session_state.game.name
        
    return context

def index(request):
    init_session_vars(request)
    session = validate_session(request)
    context = get_context(session)
    
    games = [game.get_info() for game in get_games()]
    context['games'] = json.dumps(games)

    if session.has_game:
        context['gameId'] = session.game.id
        context['gamename'] = session.game.name

    if session.has_user:
        context['userId'] = session.user.id
        context['username'] = session.user.user_name

    if session.has_team:
        set_user_active(session.game.id,session.user.id,False)
        request.session['teamId'] = ''
        request.session['teamname'] = ''

    context['errors'] = request.session['errors']

    return render(request,'index.html', context=context)

def lobby(request):
    init_session_vars(request)
    session = validate_session(request)
    context = get_context(session)

    if session.has_game and session.game.is_ready():
        context['gameId'] = session.game.id
        context['gamename'] = session.game.name
    else: 
        return redirect(index)

    if not session.has_mode:
        return redirect(index)

    if session.has_user and not session.has_team:
        user = get_user(session.game.id,session.user.id)
        if user!=None:
            session.team=user['team']
            session.has_team=True
            request.session['teamId'] = session.team.id
            request.session['teamname'] = session.team.team.team_name

    if session.has_user and session.has_team:
        return redirect(team)
    elif session.has_user:
        context['userId'] = session.user.id
        context['username'] = session.user.user_name
    elif not session.has_user:
        name1 = 'User '
        name2 = len(User.objects.all())
        
        temp_name = name1 + str(name2)
        user = create_user(session.game.id,temp_name)
        while user==None:
            name2 += 1
            temp_name = name1 + str(name2)
            user = create_user(session.game.id,temp_name)
        
        orphan = add_orphan(session.game.id,user.id)

        request.session['userId'] = user.id
        request.session['username'] = user.user_name

        session.has_user=True
        session.is_orphan=True
        session.user=user
    
    state = get_gamestate(session.game.id)

    context['username'] = request.session['username']
    context['teams'] = json.dumps(state['Teams'])
    context['orphans'] = json.dumps(state['Orphans'])
    context['game']= json.dumps(state['Game'])
    context['errors'] = request.session['errors'] 

    if session.mode == 0:
        return render(request, 'User/lobby.html',context)
    else:
        return render(request, 'Competition/comp_lobby.html',context)
       
def team(request):
    init_session_vars(request)
    session = validate_session(request)
    context = get_context(session)

    if not session.has_game or not session.game.is_ready():
        return redirect(index)
        
    if session.has_mode and (session.mode == 1 or (session.mode == 0 and not session.has_user)):
        return redirect(lobby)

    if not session.has_team:
        name1 = 'Team '
        name2 = len(Team.objects.all())
        temp_name = name1 + str(name2)
        team = create_team(session.game.id,temp_name)
        
        while team == None:
            name2 += 1
            temp_name = name1 + str(name2)
            team = create_team(session.game.id,temp_name)
        
        add_teammember(session.game.id,team.id,session.user.id)
        session.team = team
        session.has_team = True
        request.session['teamId']=team.id
        request.session['teamname']=team.team.team_name
    else:
        team = get_team(session.game.id,session.team.id)
        add_teammember(session.game.id,team.id,session.user.id)
        session.team = team
        session.has_team = True
        request.session['teamId']=team.id
        request.session['teamname']=team.team.team_name


    users = [{'isUser':user.id==session.user.id,'username':user.user_name} for user in get_users(session.game.id,session.team.id)]

    data = None

    context[TEAMNAME] = session.team.team.team_name
    context['users'] = json.dumps(users)
    context['username']= session.user.user_name
    context['errors'] = request.session['errors']
    context['game'] = json.dumps(session.game.get_info())
    
    return render(request,'User/team.html',context)
    
def leave_team(request):
    init_session_vars(request)
    session = validate_session(request)
    context = get_context(session)

    if not session.has_game:
        return redirect(index)
    elif not session.has_user or not session.has_team:
        return redirect(lobby)
    
    if remove_teammember(session.game.id,session.team.id,session.user.id):
        request.session[TEAMID]=''
        request.session[TEAMNAME]=''
        return redirect(lobby)
    
    return redirect(team)

def update_teamname(request):
    init_session_vars(request)
    session = validate_session(request)
    context = get_context(session)

    value = {'status':'', 'teamname':''}

    if not session.has_game:
        value['status'] = 'Error: No Game Selected'
        return JsonResponse(value)
    elif not session.has_team:
        value['status'] = 'Error: No Team Selected'
        return JsonResponse(value)

    new_teamname = request.POST.get('new_teamname','')

    if new_teamname != '':
        if not change_teamname(session.game.id,session.team.id,new_teamname):
            value['status'] = 'Teamname already taken'
        else:
            value['teamname'] = new_teamname
            value['status'] = 'okay'
    else:
        value['status'] = 'Error Team name cannot be blank'
        
    return JsonResponse(value)

def update_username(request):
    init_session_vars(request)
    session = validate_session(request)
    context = get_context(session)

    new_username = request.POST.get('new_username','')
    response = {'status':'', 'username':''}
    
    if session.has_user:
        if new_username != '':
            if not change_username(session.user.id,new_username):
                response['status']='Username already taken'
            else:
                request.session['username']=new_username
                response['status']='okay'
                response['username']=new_username
    else:
        response['status'] = 'invalid'
        
    return JsonResponse(response)

def next_round(request):
    init_session_vars(request)
    session = validate_session(request)
    context = get_context(session)
    
    if not session.has_mode or not session.has_game or not session.game.is_ready():
        return redirect(index)
        
    context['round'] = session.game.current_round
    
    if session.mode == 0:
        return render(request,'User/next_round.html',context)
    else:
        return render(request, 'Competition/comp_next_round.html', context)

def show_question(request):
    init_session_vars(request)
    session = validate_session(request)
    context = get_context(session)

    if not session.has_mode or not session.has_game or not session.game.is_ready():
        return redirect(index)
    
    result = __current_question_index__(session.game.id)
    if result['game_finished']:
        return redirect(final_results)
    elif result['round_finished']:
        return redirect(round_results)

    state = get_gamestate(session.game.id)
    ind = session.game.current_question_index
    round_index = session.game.current_round
    question = get_question(game_id=session.game.id, index=ind, round_index = round_index)
    
    context["Question"] = question["question"].replace("'",'"')
    context["Media"] = json.dumps({'videos': question['videos'], 'images': question['images'],'audios': question['audios']})
    context["Answer"] = ''
    context["ActualAnswer"] = question['answer']
    context["groups"] = question["groups"]
    context["questionId"] = question["id"]
    
    if session.mode == 0:
        return render(request, 'User/show_question.html',context)
    else:
        return render(request, "Competition/comp_show_question.html",context)

def admin_prev_question(request):
    
    # gameId = request.session.get('gameId','')
    # if gameId == '':
    #     redirect(admin_manager)

    # gameId = int(gameId)

    # game = get_game(gameId)
    # game.prev_question()
    return redirect(admin_game)

def admin_next_question(request):
    init_session_vars(request)
    session = validate_session(request)
    context = get_context(session)

    if not session.has_game or not session.user.is_admin:
        return redirect(admin_manager)

    session.game.next_question()
    return redirect(admin_game)

def submit_answer(request):
    init_session_vars(request)
    session = validate_session(request)
    context = get_context(session)

    value = {}
    
    if not session.has_game or not session.game.is_ready() or not session.has_team or not session.has_user:
        return redirect(index)
    
    questionId = request.POST.get('questionId','')
    if questionId == '':
        questionId = request.session.get('questionId','')

    if questionId == '':
        return redirect(index)
    questionId = int(questionId)

    options = []
    for key in request.POST.keys():
        if 'option_' in key:
            options.append(key)
    
    choices = []
    for opt in options:
        _,index = opt.split("_")
        choices.append((int(index),int(request.POST[opt])))

    answers_submitted = True

    for groupId, choiceId in choices:
        answers_submitted = answers_submitted and submit_user_choice(session.game.id,questionId,groupId,choiceId,session.user.id)

    value['answer'] = answers_submitted

    return JsonResponse(value)

def admin_manager(request):
    init_session_vars(request)
    session = validate_session(request)
    context = get_context(session)

    if not session.has_user:
        request.session['next_page'] = 'admin_manager'
        return redirect(login)
    elif not session.user.is_admin:
        return HttpResponse('Unauthorized', status=401)

    show_activeonly = request.POST.get('show_activeonly','')
    if show_activeonly == '':
        show_activeonly = False
    
    show_activeonly = bool(show_activeonly)

    games = get_games(show_activeonly)
    context['Games'] = []
    for game in games:
        context['Games'].append(json.dumps(game.get_info()))

    return render(request,'Admin/admin_manager.html',context)

def admin_game(request):
    init_session_vars(request)
    session = validate_session(request)
    context = get_context(session)

    if not session.has_user:
        request.session['next_page'] = 'admin_manager'
        return redirect(login)
    elif not session.user.is_admin:
        return HttpResponse('Unauthorized', status=401)

    game_id = request.POST.get(GAMEID,'')
    if game_id == '':
        game_id = request.session.get(GAMEID,'')
    
    if game_id == '':
        redirect(admin_game)
    
    game_id = int(game_id)
    request.session[GAMEID] = game_id

    game = get_game(game_id)
    questions = get_questions(game.id)
    r = __current_question_index__(game.id)

    round_finished = r['round_finished']
    
    is_last_question = False
    is_last_round = False
    count_remaining = 0
    rounds_remaining = 0
    
    item = {'question':'','answer':'','time_allowed':'','time_started':''}
    if game.current_round in questions[0]:
        rounds_remaining = (len(questions[0])-1)-questions[0].index(game.current_round)
        is_last_round = rounds_remaining == 0
        
        for i, question in enumerate(questions[1][game.current_round]):
            if question['round_index'] == game.current_round and question['index'] == game.current_question_index:
                item = question
                count_remaining = (len(questions[1][game.current_round])-1)-i
                if i==len(questions[1][game.current_round])-1:
                    is_last_question = True
                    break

    context['roundFinished'] = json.dumps(round_finished)
    context['countRemaining'] = json.dumps(count_remaining)
    context["lastQuestion"] = json.dumps(is_last_question)
    context['lastRound'] = json.dumps(is_last_round)
    context['roundsRemaining'] = rounds_remaining
    context['name'] = json.dumps(game.name)
    context['currentQuestionIndex'] = json.dumps(game.current_question_index)
    context['currentRound'] = json.dumps(game.current_round)
    context['currentQuestion'] = json.dumps(item['question'])
    context['currentAnswer'] = json.dumps(item['answer'])
    context['timeAllowed'] = ""
    context['timeStarted'] = ""
    if item['time_allowed'] != None:
        context['timeAllowed'] = json.dumps(item['time_allowed'])
    if item['time_started'] != None:
        context['timeStarted'] = json.dumps(item['time_started'].strftime("%Y-%m-%d %H:%M:%S"))

    return render(request,'Admin/admin_game.html',context)

def edit_game(request):
    init_session_vars(request)
    session = validate_session(request)
    context = get_context(session)

    if not session.has_user:
        request.session['next_page'] = 'edit_game'
        return redirect(login)
    elif not session.user.is_admin:
        return HttpResponse('Unauthorized', status=401)

    gameId = request.POST.get('gameId','')
    if gameId == '':
        gameId = request.session.get('gameId','')
    
    if gameId == '':
        return redirect(admin_manager)
    
    request.session[GAMEID] = context[GAMEID]
    

    context['id'] = "undefined"
    context['name'] = "undefined"
    context['state'] = "undefined"
    context['current_round'] = "undefined"
    context['current_question_index'] = "undefined"
    context['start_date'] = "undefined"
    context['start_time'] = "undefined"
    context['is_cancelled'] = "undefined"

    if gameId != '':
        gameId = int(gameId)
        game = get_game(gameId)
        if game!=None:
            request.session[GAMEID] = gameId
            context['id'] = json.dumps(gameId)
            context['name'] = json.dumps(game.name)
            context['state'] = json.dumps(game.state)
            context['current_round'] = json.dumps(game.current_round)
            context['current_question_index'] = json.dumps(game.current_question_index)

            date_obj = game.start_time
            date_date = date_obj.date()
            date_time = date_obj.time()

            context['start_date'] = json.dumps(date_date.strftime("%Y-%m-%d"))
            context['start_time'] = json.dumps(date_time.strftime("%H:%M:%S"))
            context['is_cancelled'] = json.dumps(game.is_cancelled)


    
    return render(request,'Admin/edit_game.html',context)

def create_game(request):
    init_session_vars(request)
    session = validate_session(request)
    context = get_context(session)

    if not session.has_user:
        request.session['next_page'] = 'create_game'
        return redirect(login)
    elif not session.user.is_admin:
        return HttpResponse('Unauthorized', status=401)

    request.session[GAMEID] = ''
    return redirect(edit_game)

def save_game(request):
    init_session_vars(request)
    session = validate_session(request)
    context = get_context(session)
    result = {'status':''}

    if not session.has_user:
        result['status'] = 'Error: Must be logged in to save game'
    elif not session.user.is_admin:
        result['status'] = 'Error: must be logged in to save game'

    name = request.POST.get('name','')
    state = request.POST.get('state','')
    currentround = request.POST.get('current_round','')
    currentquestionindex = request.POST.get('current_question_index','')
    startdate = request.POST.get('date','')
    # starttime = request.POST.get('start_time','')
    # timezone = request.POST.get('timezone','')
    iscancelled = request.POST.get('is_cancelled','')
    
    val_fail = False
    val_fail = name == '' or state == '' or currentround == '' or currentquestionindex == '' or startdate == '' or iscancelled == ''

    if not val_fail:
        state = int(state)
        currentround = int(currentround)
        currentquestionindex = int(currentquestionindex)

        # datetime_str = "{} {}".format(startdate,starttime)
        # datetime_val = None
        try:
            datetime_val  = datetime.strptime(startdate,"%Y-%m-%d %H:%M")
            # datetime_val = datetime_val.fromisoformat(startdate[:len(startdate)-1])
        except ValueError as ex:
            print(ex)
            try:
                datetime_val  = datetime.strptime(startdate,"%Y-%m-%d %H:%M:%S")
            except Exception as ex:
                print(ex)
                result['status'] = "Error: Parsing datetime failed"

        datetime_val = datetime_val.astimezone(timezone.utc)
        starttime = datetime_val
        
        if iscancelled.lower() == 'true':
            iscancelled=True
        else:
            iscancelled=False

        
    if not session.has_game:
        game = TriviaGame.create(name,starttime,state,currentround,currentquestionindex,iscancelled)
        game.save()
        request.session[GAMEID] = game.id
    else:
        session.game.name=name
        session.game.state=state
        session.game.current_round=currentround
        session.game.current_question_index=currentquestionindex
        session.game.start_time=starttime
        session.game.is_cancelled=iscancelled
        session.game.save()
        
    if val_fail:
        result['status'] = 'Error: Form Validation Failed'
    else:
        result['status'] = 'okay'
    
    return JsonResponse(result)
    
def edit_questions(request):
    init_session_vars(request)
    session = validate_session(request)
    context = get_context(session)

    if not session.has_user:
        request.session['next_page'] = 'edit_questions'
        return redirect(login)
    elif not session.user.is_admin:
        return HttpResponse('Unauthorized', status=401)

    if not session.has_game:
        return redirect(admin_manager)
    
    questions = get_questions(session.game.id)
    # if len(questions[1].keys())==0:
    #     create_questions(game_id)
    #     questions = get_questions(game_id)

    
    context['game'] = json.dumps(session.game.get_info())
    context['questions'] = json.dumps(questions)

    return render(request,'Admin/edit_questions.html',context)

def round_results(request):
    init_session_vars(request)
    session = validate_session(request)
    context = get_context(session)

    if not session.has_game or not session.game.is_ready() or not session.has_mode:
        return redirect(index)

    round_results = get_round_results(session.game.id,session.game.current_round)
    if round_results==None:
        return redirect(show_question)

    results = {}
    results['round'] = round_results['round']
    
    data = get_gamestate(session.game.id)

    context['results'] = json.dumps(results)
    context['game'] = json.dumps(data['Game'])
    context['errors'] = request.session['errors']

    if session.mode == 0:
        if not session.has_user:
            return redirect(index)

        if not session.has_team:
            return redirect

        round_results = get_round_results(session.game.id,session.game.current_round)

        if session.team.id not in round_results['teams']:
            return render(request,'User/waiting.html',context)

        results['team'] = round_results['teams'][session.team.id]
        results['teamname'] = session.team.team.team_name
        context['username']= session.user.user_name
        context['userId'] = session.user.id
        results['users'] = round_results['users']
        results['teamRank'] = round_results['teamRank'] 
        results['teams'] = round_results['teams']
        context['results'] = json.dumps(results)

        return render(request,'User/round_results.html',context)
    else:
        
        results['users'] = round_results['users']
        results['teamRank'] = round_results['teamRank'] 
        results['teams'] = round_results['teams']
        context['results'] = json.dumps(results)
        
        return render(request, 'Competition/comp_round_results.html', context)

def final_results(request):
    init_session_vars(request)
    session = validate_session(request)
    context = get_context(session)

    if not session.has_game or not session.game.is_ready() or not session.has_mode:
        return redirect(index)


    if session.game.state!=2:
        return redirect(show_question)

    game_results = get_game_results(session.game.id)
    if game_results==None:
        return redirect(show_question)

    results = {}
    results['game'] = game_results['game']
    
    data = get_gamestate(session.game.id)

    context['results'] = json.dumps(results)
    context['game'] = json.dumps(data['Game'])
    context['errors'] = request.session['errors']

    if session.mode == 0 and session.has_user and session.has_team and session.team.id in game_results['teams']:
        results['users'] = game_results['users']
        results['teamRank'] = game_results['teamRank'] 
        results['teams'] = game_results['teams']
        context['results'] = json.dumps(results)
        results['team'] = game_results['teams'][session.team.id]        
        context['username']= session.user.user_name
        context['userId'] = session.user.id
        return render(request,'User/final_results.html',context)
    else:
        results['users'] = game_results['users']
        results['teamRank'] = game_results['teamRank'] 
        results['teams'] = game_results['teams']
        context['results'] = json.dumps(results)
        
        return render(request, 'Competition/comp_final_results.html', context)
    pass

def __current_question_index__(game_id:int):
    value = {}        
    value['index']='undefined'
        
    game = get_game(game_id)
    value['index']=game.current_question_index
    value['round_finished'] = False
    value['game_finished'] = game.state==2

    round_res = get_round_results(game.id,game.current_round)
    if round_res!=None:
        value['round_finished'] = round_res['round']['isFinished']

    return value

def current_question_index(request):
    
    game_id = request.POST.get(GAMEID,'')
    if game_id == '':
        game_id = request.session.get(GAMEID,'')

    value = {}
    if game_id != '':
        value = __current_question_index__(game_id)
    else:
        value['error']='Error gameId missing'

    return JsonResponse(value)

def admin_save_questions(request):
    init_session_vars(request)
    session = validate_session(request)
    context = get_context(session)

    if not session.has_user:
        request.session['next_page'] = 'edit_questions'
        return redirect(login)
    elif not session.user.is_admin:
        return HttpResponse('Unauthorized', status=401)
        
    value = {}
    value['result'] = False

    game_id = request.POST.get('gameId','')
    if game_id == '':
        return JsonResponse(value)
    else:
        game_id=int(game_id)

    _data = request.POST.get('data','')
    if _data == '':
        return JsonResponse(value)

    data = None
    try:
        data = json.loads(_data)
    except:
        return JsonResponse(value)
    
    if data == '':
        return JsonResponse(value)

    save_question_data(game_id,data)
    result = {'saved':True} 
    return JsonResponse(result)

def upload_video(request):
    _file = request.FILES.get('file','')
    if _file == '':
        return JsonResponse({'path':''})

    if not _file.content_type.startswith('video/'):
        return
    create_path(MEDIA,['video'])
    path = get_temp_location(os.path.join(MEDIA,'video'),'temp',_file.name) 
    write_temp_file(path[0],_file.chunks())
    return JsonResponse({'path':path[1]})
        
def upload_audio(request):
    _file = request.FILES.get('file','')
    if _file == '':
        return JsonResponse({'path':''})

    if not _file.content_type.startswith('audio/'):
        return
    create_path(MEDIA,['audio'])
    path = get_temp_location(os.path.join(MEDIA,'audio'),'temp',_file.name) 
    write_temp_file(path[0],_file.chunks())
    return JsonResponse({'path':path[1]})

def upload_image(request):
    _file = request.FILES.get('file','')
    if _file == '':
        return JsonResponse({'path':''})
    
    if not _file.content_type.startswith('image/'):
        return
    create_path(MEDIA,['images'])
    path = get_temp_location(os.path.join(MEDIA,'images'),'temp',_file.name) 
    write_temp_file(path[0],_file.chunks())
    return JsonResponse({'path':path[1]})

def create_path(root,folders):
    
    path = root
    if not os.path.exists(path):
        os.mkdir(path)
    
    for i,folder in enumerate(folders):
        path = os.path.join(path,folder)
        if not os.path.exists(path):
            os.mkdir(path)


def write_temp_file(path,chunks):
    try:
        with open(path,'wb+') as f:
            for chunk in chunks:
                f.write(chunk)
    except Exception as e:
        print(e)

def get_temp_location(root,folder,filename)->str:
    path = ''
    rel_path = ''
    if not os.path.exists(root):
        os.mkdir(root)

    path = os.path.join(root,folder)
    if not os.path.exists(path):
        os.mkdir(path)

    while rel_path=='' or os.path.exists(os.path.join(path,rel_path)):
        N=random.randint(5,8)
        rel_path = ''.join(random.choices(string.ascii_uppercase,k=N))
    
    path = os.path.join(path,rel_path)
    if not os.path.exists(path):
        os.mkdir(path)
    
    rel_path = os.path.join(rel_path,filename)
    path = os.path.join(path,filename)

    return (path,rel_path)

def login(request):
    init_session_vars(request)
    session = validate_session(request)
    context = get_context(session)

    if session.has_user:
        return perform_redirects(request)

    context['username'] = request.session.get('last_username','')
    return render(request,'login.html',context)

def logout(request):
    request.session['mode'] = ''
    request.session['gameId'] = ''
    request.session['errors'] = []
    request.session['userId'] = ''
    request.session['username'] = ''
    request.session['teamId'] = ''
    return redirect(index)
    

def login_user(request):
    init_session_vars(request)

    user_name = request.POST.get('username','')
    password = request.POST.get('password')

    if user_name == '' or password == '':
        request.session['last_username'] = user_name
        return redirect(login)
    
    user = authenticate_user(user_name,password)
    if user == None:
        request.session['last_username'] = user_name
        return redirect(login)

    request.session[USERID] = user.id
    request.session[USERNAME] = user.user_name
    request.session['next_page'] = 'admin_manager'

    if user.is_temp_pwd:
        return redirect(user_change_password)

    return perform_redirects(request)

def perform_redirects(request):
    next_page = request.session.get('next_page','')
    if next_page != '':
        request.session['next_page'] = ''
        if next_page == 'admin_manager':
            return redirect(admin_manager)
        elif next_page == 'edit_questions':
            return redirect(edit_questions)
        elif next_page == 'create_game':
            return redirect(create_game)
        elif next_page == 'edit_game':
            return redirect(edit_game)
        
    return redirect(index)

def user_change_password(request):
    init_session_vars(request)
    return render(request,'user_change_password.html')


def change_password(request):
    init_session_vars(request)

    user_id = request.session.get(USERID,'')

    if user_id == '':
        return redirect(login_user)

    old_password = request.POST.get('oldPassword', '')
    new_password = request.POST.get('password', '')
    conf_password = request.POST.get('passwordConfirm', '')

    if old_password == '' or new_password == '' or conf_password == '':
        return redirect(user_change_password)
    
    if not change_user_password(user_id,old_password,new_password,conf_password):
        return redirect(user_change_password)
    
    return perform_redirects(request)