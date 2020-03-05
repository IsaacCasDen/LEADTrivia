from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.shortcuts  import redirect
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
        createQuestions()

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

    games = get_games()
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

    context = {}
    context['gameId'] = request.session['gameId']
    context['userId'] = request.session['userId']
    context['username'] = request.session['username']
    context['errors'] = request.session['errors']
    context['data'] = game_data

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
    teamId = request.POST.get('teamId',request.session.get('teamId',''))
    userId = request.session.get('userId','')
    username = request.session.get('username','')

    if gameId == '' or userId == '':
        return redirect(index)
    
    if teamId!='':
        teamId = int(teamId)

    data = None
    users = None
    team=None

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
    context[TEAMNAME] = team.team_name
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

def mcq(request):
    set_session_vars(request)
    game = get_games()[0]
    gameId = game.id
   # gameId = request.session.get(GAMEID,'')
    if gameId == '':
        return redirect(index)
    state = get_gamestate(gameId)
    ind = state["Game"]["QuestionIndex"]
    question = get_question(gameId, ind)
    context= {}

    context["Question"] = question["Question"]
   # context["Answer"] = question["Answer"]
    context["Choices"] = question["Choices"]
    context["QuestionId"] = question["QuestionId"]
    return render(request, 'mcquestion.html',context)

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

def prevQuestion(request):
    set_session_vars(request)
    game = get_game(1)
    game.prev_question()
    return redirect(mcq)

def nextQuestion(request):
    set_session_vars(request)
    game = get_game(1)
    game.next_question()
    return redirect(mcq)

def submitAns(request):
    set_session_vars(request)
    # gameId = request.session.get(GAMEID,'')
    # userId = request.session.get(USERID,'')
    # teamId = request.session.get(TEAMID,'')
    # if gameId == '' or userId == '' or teamId == '':
    #     return redirect(index)
    
    answerId = request.POST.get('answer', '')
    if answerId == '':
        redirect(mcq)
    else: 
        answerId = int(answerId)
        return redirect(mcq)

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
    question = get_question(game_id,game.current_question_index)



    context = {}
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
    return render(request,'create_game.html',context)

def save_game(request):
    
    game_id = request.POST.get('gameId','')
    name = request.POST.get('name','')
    state = request.POST.get('state','')
    currentround = request.POST.get('current_round','')
    currentquestionindex = request.POST.get('current_question_index','')
    startdate = request.POST.get('start_date','')
    starttime = request.POST.get('start_time','')
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
    
    questions = getQuestions(game_id)
    if len(questions)==0:
        createQuestions(game_id)
        questions = getQuestions(game_id)

    context = {}
    context['game'] = json.dumps(game.get_info())
    context['questions'] = json.dumps(questions)

    return render(request,'edit_questions.html',context)
