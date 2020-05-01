
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

    if gameId == '':
        gameId = request.session.get('gameId','')
    else:
        request.session['gameId'] = gameId

    if userId == '':
        userId = request.session.get('userId','')
    else:
        request.session['userId'] = userId

    if teamId == '':
        teamId = request.session.get('teamId','')
    else:
        request.session['teamId'] = teamId

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
        userId = int(userId)
        user = TeamMember.objects.filter(user__id=userId,game__id=gameId)
        if len(user)>0:
            session_state.has_user = True
            session_state.user=user[0].user
        else:
            user = OrphanUser.objects.filter(user__id=userId,game__id=gameId)
            if len(user)>0:
                session_state.has_user = True
                session_state.is_orphan = True
                session_state.user=user[0].user
            else:
                user = User.objects.filter(id=userId)
                if len(user)>0:
                    user = add_orphan(gameId,userId)
                    if user!=None:
                        session_state.has_user=True
                        session_state.is_orphan=True
                        session_state.user=user.user


    if teamId != '':
        teamId = int(teamId)
        team = TriviaGameTeam.objects.filter(game__id=gameId,team__id=teamId)
        if len(team)>0:
            session_state.has_team = True
            session_state.team=team[0]
    
    return session_state
    


def index(request):
    init_session_vars(request)
    session = validate_session(request)

    context = {}
    
    games = [game.get_info() for game in get_games()]

    context['games'] = json.dumps(games)

    context['gameId'] = json.dumps(None)
    context['gamename'] = ''
    context['userId'] = json.dumps(None)
    context['username'] = ''
    context['teamId'] = json.dumps(None)
    context['teamname'] = ''

    if session.has_game:
        context['gameId'] = session.game.id
        context['gamename'] = session.game.name

    if session.has_user:
        context['userId'] = session.user.id
        context['username'] = session.user.user_name

    if session.has_team:
        context['teamId'] = session.team.team.id
        context['teamname'] = session.team.team.team_name

    context['errors'] = request.session['errors']

    return render(request,'index.html', context=context)

def lobby(request):
    init_session_vars(request)
    session = validate_session(request)

    context = {}

    if session.has_game:
        context['gameId'] = session.game.id
        context['gamename'] = session.game.name
    else: 
        return redirect(index)

    mode = request.POST.get('mode','')
    if mode == '':
        return redirect(index)
    else:
        mode = int(mode)
        request.session['mode'] = mode

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

    if mode == 0:
        return render(request, 'User/lobby.html',context)
    else:
        return render(request, 'Competition/comp_lobby.html',context)
       
def team(request):
    init_session_vars(request)
    session = validate_session(request)

    if not session.has_game:
        return redirect(index)
    
    mode = request.session['mode']
    
    if mode == 1 or (mode == 0 and not session.has_user):
        return redirect(lobby)

    context = {}

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

    value = {'status':''}

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
            value['status'] = new_teamname
    else:
        value['status'] = 'Error Team name cannot be blank'
        
    return JsonResponse(value)

def update_username(request):
    session = validate_session(request)
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
    mode = request.session['mode']
    context = {}

    gameId = request.session.get(GAMEID,'')
    if gameId == '':
        return redirect(index)

    game = get_game(gameId)
    if game  == None:
        return redirect(index)
        
    context['round'] = game.current_round
    
    if mode == 0:
        return render(request,'User/next_round.html',context)
    else:
        return render(request, 'Competition/comp_next_round.html', context)

def show_question(request):
    mode = request.session['mode']

    init_session_vars(request)
    gameId = request.POST.get('gameId', request.session.get('gameId', ''))


    if gameId != '':
        gameId = int(gameId)
        request.session['gameId'] = gameId
    else:
        return redirect(index)

    result = __current_question_index__(gameId)
    if result['game_finished']:
        return redirect(final_results)
    elif result['round_finished']:
        return redirect(round_results)

    game = get_game(gameId)
    state = get_gamestate(gameId)
    ind = game.current_question_index
    round_index = game.current_round
    question = get_question(game_id=gameId, index=ind, round_index = round_index)
    context= {}
    
    context["Question"] = question["question"].replace("'",'"')
    context["Media"] = json.dumps({'videos': question['videos'], 'images': question['images'],'audios': question['audios']})
    context["Answer"] = ''
    context["ActualAnswer"] = question['answer']
    context["groups"] = question["groups"]
    context["questionId"] = question["id"]
    
    if mode == 0:
        return render(request, 'User/show_question.html',context)
    else:
        return render(request, "Competition/comp_show_question.html",context)

def admin_prev_question(request):
    
    gameId = request.session.get('gameId','')
    if gameId == '':
        redirect(admin_manager)

    gameId = int(gameId)

    game = get_game(gameId)
    game.prev_question()
    return redirect(admin_game)

def admin_next_question(request):
    
    gameId = request.session.get('gameId','')
    if gameId == '':
        return redirect(admin_manager)

    gameId = int(gameId)

    game = get_game(gameId)
    game.next_question()
    return redirect(admin_game)

def submit_answer(request):
    value = {}
    init_session_vars(request)

    gameId = request.session.get(GAMEID,'')
    userId = request.session.get(USERID,'')
    teamId = request.session.get(TEAMID,'')
    
    questionId = request.POST.get('questionId','')
    if questionId == '':
        questionId = request.session.get('questionId','')

    if gameId == '' or userId == '' or teamId == '' or questionId == '':
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
        answers_submitted = answers_submitted and submit_user_choice(gameId,questionId,groupId,choiceId,userId)

    value['answer'] = answers_submitted

    return JsonResponse(value)

def admin_manager(request):
    context = {}

    request.session[GAMEID] = ''
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
    
    item = {'question':'','answer':''}
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

    context = {}
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

    return render(request,'Admin/admin_game.html',context)

def edit_game(request):
    context = {}

    gameId = request.POST.get('gameId','')
    if gameId == '':
        gameId = request.session.get('gameId','')
    
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
    context = {}
    request.session[GAMEID] = ''
    return redirect(edit_game)

def save_game(request):
    
    game_id = request.POST.get('gameId','')
    name = request.POST.get('name','')
    state = request.POST.get('state','')
    currentround = request.POST.get('current_round','')
    currentquestionindex = request.POST.get('current_question_index','')
    startdate = request.POST.get('start_date','')
    starttime = request.POST.get('start_time','')
    timezone = request.POST.get('timezone','')
    iscancelled = request.POST.get('is_cancelled','')
    if iscancelled == '':
        iscancelled = False
    
    val_fail = False
    val_fail = name == '' or state == '' or currentround == '' or currentquestionindex == '' or startdate == '' or starttime == '' or iscancelled == ''
    
    if not val_fail:
        state = int(state)
        currentround = int(currentround)
        currentquestionindex = int(currentquestionindex)

        datetime_str = "{} {}".format(startdate,starttime)
        datetime_val = None
        try:
            datetime_val  = datetime.strptime(datetime_str,"%Y-%m-%d %H:%M")
        except ValueError:
            try:
                datetime_val  = datetime.strptime(datetime_str,"%Y-%m-%d %H:%M:%S")
            except:
                return redirect(edit_game)

        starttime = datetime_val
        iscancelled = bool(iscancelled)

        if game_id == '':
            game = TriviaGame.create(name,starttime,state,currentround,currentquestionindex,iscancelled)
            game_id = game.id
        else:
            game_id = int(game_id)
            game = get_game(game_id)
            game.name=name
            game.state=state
            game.current_round=currentround
            game.current_question_index=currentquestionindex
            game.start_time=starttime
            game.is_cancelled=iscancelled
            game.save()
        
    if val_fail:
        return redirect(create_game)
    else:
        request.session[GAMEID] = game_id
        return redirect(edit_game)
    
def edit_questions(request):

    game_id = request.POST.get('gameId','')
    if game_id == '':
        game_id == request.session.get('gameId','')
    
    if game_id == '':
        return redirect(admin_manager)
    
    game_id = int(game_id)

    game = get_game(game_id)
    if game == None:
        return redirect(admin_game)
    
    questions = get_questions(game_id)
    # if len(questions[1].keys())==0:
    #     create_questions(game_id)
    #     questions = get_questions(game_id)

    context = {}
    context['game'] = json.dumps(game.get_info())
    context['questions'] = json.dumps(questions)

    return render(request,'Admin/edit_questions.html',context)

def round_results(request):
    init_session_vars(request)
    session = validate_session(request)
    mode = request.session['mode']

    context = {}
    
    if not session.has_game:
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

    if mode == 0:
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
    mode = request.session['mode']
    context = {}

    if not session.has_game:
        return redirect(index)
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

    if mode == 0 and session.has_user and session.has_team and session.team.id in game_results['teams']:
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

    if _file.content_type not in ['video/mp4']:
        return
    path = get_temp_location(os.path.join(MEDIA,'video'),'temp',_file.name) 
    write_temp_file(path[0],_file.chunks())
    return JsonResponse({'path':path[1]})
        
def upload_audio(request):
    _file = request.FILES.get('file','')
    if _file == '':
        return JsonResponse({'path':''})

    if _file.content_type not in ['audio/mpeg']:
        return
    path = get_temp_location(os.path.join(MEDIA,'audio'),'temp',_file.name) 
    write_temp_file(path[0],_file.chunks())
    return JsonResponse({'path':path[1]})

def upload_image(request):
    _file = request.FILES.get('file','')
    if _file == '':
        return JsonResponse({'path':''})

    if _file.content_type not in ['image/jpeg','image/jpg']:
        return
    path = get_temp_location(os.path.join(MEDIA,'images'),'temp',_file.name) 
    write_temp_file(path[0],_file.chunks())
    return JsonResponse({'path':path[1]})


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

    