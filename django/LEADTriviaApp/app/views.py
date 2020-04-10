from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.shortcuts  import redirect
import random
import json

from .models import *
# Create your views here.

USERNAME = 'username'
USERID = 'userId'
TEAMID = 'teamId'
TEAMNAME = 'teamname'
GAMEID = 'gameId'
GAMENAME = 'gameName'

def set_session_vars(request):
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

    should_set = False
    if should_set:
        create_questions()

    should_set = False
    if should_set:
        request.session['userId'] = 160
        request.session['errors'] = []

        games = get_games()
        request.session['gameId'] = games[len(games)-1].id


def init_db():
    should_init = False
    if should_init:
        try:
            reset_db()
        except:
            pass
        finally:
            create_model()
    

def index(request):
    set_session_vars(request)
    init_db()

    context = {}

    games = get_games()
    _games = []
    for game in games:
        _games.append(game.get_info())

    context['games'] = json.dumps(_games)

    if len(games)==0:
        return HttpResponse("No Games Available")
    game_data = get_gamestate(games[len(games)-1].id)

    if request.session['gameId'] == '':
        pass

    userId = request.session['userId']
    gameId = request.session['gameId']
    if gameId != game_data['Game']['Id']:
        gameId = game_data['Game']['Id']
        request.session['gameId']=gameId
        request.session['userId']=''
    if isinstance(userId,int) and isinstance(gameId,int) and  len(request.session['errors'])==0:
        return redirect(lobby)

    context['gameId'] = request.session['gameId']
    context['userId'] = request.session['userId']
    context['username'] = request.session['username']
    context['errors'] = request.session['errors']
    context['data'] = json.dumps(game_data)

    return render(request,'index.html', context)

def lobby(request):
    set_session_vars(request)
    context = {}

    username = request.POST.get('username', request.session.get('username', ''))
    userId = request.POST.get('userId', request.session.get('userId', ''))
    gameId = request.POST.get('gameId', request.session.get('gameId', ''))
    teamId = request.POST.get('teamId', request.session.get('teamId', ''))
    request.session['gameId'] = gameId
    request.session['errors'] = []

    if gameId != '':
        gameId = int(gameId)
        request.session['gameId'] = gameId
    
    if userId != '':
        userId = int(userId)
        request.session['userId'] = userId
    
    if teamId != '':
        teamId = int(teamId)
        request.session['teamId'] = teamId

    if gameId == '':
        return redirect(index)
    elif userId == '' and username == '':
        request.session['errors'] = ['Please enter a username']
        return redirect(index)
    elif userId == '':
        request.session['username'] = username
        user = create_user(int(gameId),username)
        if user == None:
            request.session['errors'] = ['Username already taken']
            return redirect(index)
        else:
            request.session['userId']=user.id
    else:
        user = get_user(int(gameId), int(userId))
        if user != None:
            request.session['userId']=user['user'].id
            request.session['username']=user['user'].user_name
            request.session['teamId']=user['team'].id
            return redirect(team)
        else:
            user = get_orphan(int(gameId),int(userId))
            if user == None:
                request.session['userId'] = ''
                request.session['teamId'] = ''
                return redirect(index)
            else:
                request.session['username'] = user.user.user_name
        
    state = get_gamestate(gameId)

    context['teams'] = json.dumps(state['Teams'])
    context['orphans'] = json.dumps(state['Orphans'])
    context['game']=json.dumps(state['Game'])
    context['username'] = request.session['username']
    context['gameId'] = request.session['gameId']
    context['errors'] = request.session['errors'] 
    return render(request, 'lobby.html',context)
            
def team(request):
    set_session_vars(request)
    context = {}

    gameId = request.session.get('gameId','')
    teamId = request.POST.get('teamId')
    if teamId == '':
        teamId = request.session.get('teamId','')
    userId = request.session.get('userId','')
    username = request.session.get('username','')

    if gameId == '' or userId == '':
        return redirect(index)
    
    team=None

    if teamId!='':
        teamId = int(teamId)
    
        team = get_team(gameId,teamId)
        if team==None:
            teamId = ''

    data = None
    users = None

    if teamId == '':
        data = get_gamestate(gameId)
        team = create_team(gameId,"Team {}".format(len(data['Teams'].keys())))
        if team==None:
            request.session['errors']=['Error creating team']
            return redirect(index)
        else:
            teamId=team.id
            add_teammember(gameId,teamId,userId)
            data = get_gamestate(gameId)
            users = data['Teams'][teamId]['members']
    else:
        data = get_gamestate(gameId)
        users = data['Teams'][teamId]['members']
        if teamId not in data['Teams'].keys():
            request.session['teamId'] = ''
            redirect(lobby)
        if username not in users:
            if add_teammember(gameId,teamId,userId):
                data = get_gamestate(gameId)
                users = data['Teams'][teamId]['members']
            else:
                return redirect(lobby)
    team = get_team(gameId,teamId)
    request.session['teamId'] = teamId
    context['game'] = json.dumps(data['Game'])
    context[TEAMNAME] = team.team.team_name
    context['users'] = json.dumps(users)
    context['username']= username
    context['errors'] = request.session['errors']
    
    return render(request,'team.html',context)
    

def leave_team(request):
    set_session_vars(request)
    gameId = request.session.get(GAMEID,'')
    userId = request.session.get(USERID,'')
    teamId = request.session.get(TEAMID,'')
    
    if gameId == '' or userId == '' or teamId == '':
        return redirect(index)
    
    if remove_teammember(gameId,teamId,userId):
        request.session[TEAMID]=''
        return redirect(lobby)
    
    return redirect(team)

def update_teamname(request):
    gameId = request.session.get(GAMEID,'')
    teamId = request.session.get(TEAMID,'')
    new_teamname = request.POST.get('new_teamname','')

    if new_teamname != '':
        if not change_teamname(gameId,teamId,new_teamname):
            request.session['errors'].append('Teamname already taken')
    
    return redirect(team)

def update_username(request):
    gameId = request.session.get(GAMEID,'')
    userId = request.session.get(USERID,'')
    new_username = request.POST.get('new_username','')
    
    if new_username != '':
        if not change_username(gameId,userId,new_username):
            request.session['errors'].append('Username already taken')
        else:
            request.session['username']=new_username

    return redirect(team)

def next_round(request):
    context = {}
    context['round']=1
    return render(request,'next_round.html',context)

def show_question(request):
    set_session_vars(request)
    game = get_games()[0]
    gameId = game.id
   # gameId = request.session.get(GAMEID,'')
    if gameId == '':
        return redirect(index)
    state = get_gamestate(gameId)
    ind = game.current_question_index
    round_ind = game.current_round
    question = get_question(game_id=gameId, ind=ind, round_ind = round_ind)
    context= {}

    context["Question"] = question["question"]
    context["Answer"] = ''
    context["ActualAnswer"] = question['answer']
    context["groups"] = question["groups"]
    context["questionId"] = question["id"]
    return render(request, 'show_question.html',context)

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

def prev_question(request):
    set_session_vars(request)

    game_id = request.POST.get(GAMEID,'')
    if game_id == '':
        game_id = request.session.get(GAMEID,'')
    if game_id == '':
        games = get_games()
        game_id = games[len(get_games)-1].id

    game = get_game(game_id)
    game.prev_question()
    return redirect(show_question)

def next_question(request):
    set_session_vars(request)
    
    game_id = request.POST.get(GAMEID,'')
    if game_id == '':
        game_id = request.session.get(GAMEID,'')
    if game_id == '':
        games = get_games()
        game_id = games[len(get_games)-1].id

    game = get_game(game_id)

    if game.next_question():
        return redirect(show_question)
    else:
        return redirect(round_results)

def submit_answer(request):
    value = {}

    set_session_vars(request)
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

    value['answer'] = True

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

    return render(request,'admin_manager.html',context)

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
    # question = get_question(game_id,game.current_round,game.current_question_index)
    is_last_question = False
    is_last_round = False
    count_remaining = 0
    rounds_remaining = 0
    
    if game.current_round in questions[0]:
        rounds_remaining = (len(questions[0])-1)-questions[0].index(game.current_round)
        is_last_round = rounds_remaining == 0
        
        for i, question in enumerate(questions[1][game.current_round]):
            if question['round_index'] == game.current_round and question['index'] == game.current_question_index:
                count_remaining = (len(questions[1][game.current_round])-1)-i
                if i==len(questions[1][game.current_round])-1:
                    is_last_question = True
                    break

    context = {}
    context['countRemaining'] = json.dumps(count_remaining)
    context["lastQuestion"] = json.dumps(is_last_question)
    context['lastRound'] = json.dumps(is_last_round)
    context['roundsRemaining'] = rounds_remaining
    context['name'] = json.dumps(game.name)
    context['currentQuestionIndex'] = json.dumps(game.current_question_index)
    context['currentRound'] = json.dumps(game.current_round)
    context['currentQuestion'] = json.dumps(question['question'])
    context['currentAnswer'] = json.dumps(question['answer'])

    return render(request,'admin_game.html',context)

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


    
    return render(request,'edit_game.html',context)

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
    if len(questions)==0:
        create_questions(game_id)
        questions = get_questions(game_id)

    context = {}
    context['game'] = json.dumps(game.get_info())
    context['questions'] = json.dumps(questions)

    return render(request,'edit_questions.html',context)

def round_results(request):
    context = {}
    
    gameId = request.session.get('gameId','')
    teamId = request.POST.get('teamId',request.session.get('teamId',''))
    userId = request.session.get('userId','')
    username = request.session.get('username','')
 
    # #------------------------------------------------------------------------------------------------------
    # value = {} 
    # questions = {}
    # questions[0] = {'Id':0,'Index':0,'IsCorrect':False}
    # questions[1] = {'Id':1,'Index':1,'IsCorrect':True}
    # questions[2] = {'Id':2,'Index':2,'IsCorrect':True}

    # users = ((1,{'id':0,'username':'John','points':10,'rank':1}),(2,{'id':1,'username':'Frank','points':6,'rank':2}),(3,{'id':3,'username':'Jim','points':1,'rank':3}))

    # value['round'] = {}
    # value['round'] = {'id':0, 'index':1, 'team_count':12}      
    # value['teams'] = {}
    # value['teams'][4] = {'id':0,'teamName':'Daves','points':17,'rank':1,'questions':questions,'users':users}
    

    # #------------------------------------------------------------------------------------------------------
    # results ={}
    # results['round'] = value['round']
    # results['team'] = value['teams'][teamId]

    if gameId == '' or userId == '':
        return redirect(index)

    if teamId!='':
        teamId = int(teamId)
    else:
        return redirect(index)
    
    game = get_game(gameId)
    round_results = get_round_results(game.id,game.current_round)
    if round_results==None:
        return redirect(show_question)

    results = {}
    results['round'] = round_results['round']
    results['team'] = round_results['teams'][teamId]
    
    data = get_gamestate(gameId)

    request.session['teamId'] = teamId
    context['results'] = json.dumps(results)
    context['game'] = json.dumps(data['Game'])
    context['username']= username
    context['userId'] = userId
    context['errors'] = request.session['errors']

    
    return render(request,'round_results.html',context)

def game_results(request):
    context = {}

    return render(request, 'game_results.html',context)

def current_question_index(request):
    value = {}        
    value['index']='undefined'
        
    game_id = request.POST.get(GAMEID,'')
    if game_id == '':
        game_id = request.session.get(GAMEID,'')

    if game_id != '':
        game = get_game(game_id)
        value['index']=game.current_question_index
        value['round_finished'] = True
        value['game_finished'] = False


    return JsonResponse(value)

