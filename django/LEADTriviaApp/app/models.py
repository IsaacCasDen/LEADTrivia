import datetime

from django.db import models, transaction
from django.utils import timezone
from threading import Lock
import random

class User(models.Model):
    user_name = models.CharField(max_length=256)

    def __str__(self):
        return "{}".format(self.user_name)
    def __repr__(self):
        return self.__str__()

class Team(models.Model):
    team_name = models.CharField(max_length=256)
    # team_members = models.ForeignKey(User,on_delete=models.SET_NULL)

    def __str__(self):
        return "{}".format(self.team_name)
    
    def __repr__(self):
        return self.__str__()

class TriviaGame(models.Model):
    name = models.CharField(max_length=256)
    state = models.IntegerField(default=0)
    current_question_index = models.IntegerField(default=0)

    def start_game(self):
        self.state=1
        self.save()
    
    def finish_game(self):
        self.state=2
        self.save()
    
    def reset_started(self):
        self.state=0
        self.save()

class TeamMember(models.Model):
    game = models.ForeignKey(TriviaGame,on_delete=models.CASCADE)
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    team = models.ForeignKey(Team,on_delete=models.CASCADE)

    def __str__(self):
        return "Team: {}\tUser:{}".format(team.team_name,user.user_name)
    def __repr__(self):
        return self.__str__()

class OrphanUser(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    game = models.ForeignKey(TriviaGame,on_delete=models.CASCADE)

    def __str__(self):
        return "User:{}".format(self.user)
    def __repr__(self):
        return self.__str__()

class TriviaQuestion(models.Model):
    question = models.CharField(max_length=512)
    answer = models.CharField(max_length=512)
    #working here

class TriviaQuestionChoices(models.Model):
    question = models.ForeignKey(TriviaQuestion,on_delete=models.CASCADE)
    choice = models.CharField(max_length=512)

# class TriviaQuestionMultipleChoice(TriviaQuestion):
#     pass

# class TriviaQuestionFillInTheBlanks(TriviaQuestion):
#     pass

class TriviaGameTeams(models.Model):
    team = models.ForeignKey(Team,on_delete=models.CASCADE)
    game = models.ForeignKey(TriviaGame,on_delete=models.CASCADE)

class TriviaGameQuestions(models.Model):
    question = models.ForeignKey(TriviaQuestion,on_delete=models.CASCADE)
    game = models.ForeignKey(TriviaGame,on_delete=models.CASCADE)  
    time = models.IntegerField(default=60)
    index = models.IntegerField()

    @classmethod
    def create(cls, question, game, time, index):
        ind = [q.index for q in TriviaGameQuestions.objects.filter(game__id=game.id)]
        while index in ind:
            index += 1
        item = cls(question = question, game = game, time = time, index = index)
        #item.save()
        return item



def getQuestions(game_id):
    questions = []
    q = [q.question for q in TriviaGameQuestions.objects.filter(game__id=game_id)]
    for item in q:
        value = {}
        value['question']=item.question
        value['answer']=item.answer
        value['choices']=[c.choice for c in TriviaQuestionChoices.objects.filter(question__id=item.id)]
        questions.append(value)
    return questions

        
    
def createQuestions():
    game = TriviaGame.objects.all()[0]

    q = TriviaQuestion()
    q.question = "Bullshit Question1"
    q.answer = "Bullshit Answer1"
    q.save()
    c = TriviaQuestionChoices()
    c.question = q
    c.choice = "Bullshit Answer1"
    c.save()
    c = TriviaQuestionChoices()
    c.question = q
    c.choice = "Bullshit Answer2"
    c.save()
    c = TriviaQuestionChoices()
    c.question = q
    c.choice = "Bullshit Answer3"
    c.save()

    tq = TriviaGameQuestions.create(question = q, game = game, time = 60, index = 0)
    tq.save()

    q = TriviaQuestion()
    q.question = "Bullshit Question2"
    q.answer = "Bullshit Answer1"
    q.save()
    c = TriviaQuestionChoices()
    c.question = q
    c.choice = "Bullshit Answer1"
    c.save()
    c = TriviaQuestionChoices()
    c.question = q
    c.choice = "Bullshit Answer2"
    c.save()
    c = TriviaQuestionChoices()
    c.question = q
    c.choice = "Bullshit Answer3"
    c.save()

    tq = TriviaGameQuestions.create(question = q, game = game, time = 60, index = 1)
    tq.save()

    q = TriviaQuestion()
    q.question = "Bullshit Question3"
    q.answer = "Bullshit Answer1"
    q.save()
    c = TriviaQuestionChoices()
    c.question = q
    c.choice = "Bullshit Answer1"
    c.save()
    c = TriviaQuestionChoices()
    c.question = q
    c.choice = "Bullshit Answer2"
    c.save()
    c = TriviaQuestionChoices()
    c.question = q
    c.choice = "Bullshit Answer3"
    c.save()

    tq = TriviaGameQuestions.create(question = q, game = game, time = 60, index = 2)
    tq.save()


createuser_lock = Lock()
def create_user(game_id:int, username:str):
    if createuser_lock.acquire():
        try:
            if not is_username_available(game_id,username):
                return None

            game = TriviaGame.objects.filter(id=game_id)[0]

            user = User()
            user.user_name = username
            user.save()
            
            ou = OrphanUser()
            ou.user=user
            ou.game=game
            ou.save()

            return user
        finally:
            createuser_lock.release()

usernamechange_lock = Lock()
def change_username(game_id:int,user_id:int,value:str):
    if usernamechange_lock.acquire():
        try:
            if not is_username_available(game_id,value):
                return None

            user = get_user(game_id,user_id)['user']

            if user == None:
                return False
            else:
                user.user_name = value
                user.save()
                return user
        finally:
            usernamechange_lock.release()
    
def is_username_available(game_id:int,name:str):
    usernames = [user.user.user_name for user in get_orphans(game_id)]
    if name in usernames:
        return False
    
    usernames =  [[user.user_name for user in get_users(game_id,team.id)] for team in get_teams(game_id)]
    usernames = [y for x in usernames for y in x]
    if name in usernames:
        return False
    
    return True

def is_teamname_available(game_id:int,name:str):
    teamnames = [team.team.team_name for team in get_teams(game_id)]
    if name in teamnames:
        return False
    
    return True

teamnamechange_lock = Lock()
def change_teamname(game_id:int,team_id:int,value:str):
    if teamnamechange_lock.acquire():
        try:
            if not is_teamname_available(game_id,value):
                return None

            team = get_team(game_id,team_id)

            if team == None:
                return None

            else:
                team.team_name = value
                team.save()
                return team
            
        finally:
            teamnamechange_lock.release()

createteam_lock = Lock()
def create_team(game_id:int, teamname:str):
    if createteam_lock.acquire():
        try:
            if not is_teamname_available(game_id,teamname):
                return None

            game = TriviaGame.objects.filter(id=game_id)[0]
    
            team = Team()
            team.team_name = teamname
            team.save()

            tgt = TriviaGameTeams()
            tgt.team = team
            tgt.game = game
            tgt.save()

            return team
        finally:
            createteam_lock.release()
    

def get_user(game_id:int, user_id:int):

    users = TeamMember.objects.filter(game__id=game_id,user__id=user_id)
    if len(users)>0:
        if len(users)==1:
            result = {}
            result['user']=users[0].user
            result['team']=users[0].team
            return result
        else:
            pass
    
    return None

def get_users(game_id:int, team_id:int):
    tm = TeamMember.objects.filter(game__id=game_id,team__id=team_id)
    users = []
    for item in tm:
        users.append(item.user)
    return users

def get_orphan(game_id:int,user_id:int):
    orphans = OrphanUser.objects.filter(game__id=game_id,user__id=user_id)
    if len(orphans)>0:
        if len(orphans)==1:
            return orphans[0]
        else:
            pass
    
    return None

def get_orphans(game_id:int):
    orphans = OrphanUser.objects.filter(game__id=game_id)
    orphans = [orphan for orphan in orphans]
    return orphans

def get_team(game_id:int, team_id:int):
    
    teams = TriviaGameTeams.objects.filter(game__id=game_id,team__id=team_id)

    if len(teams)>0:
        if len(teams)==1:
            return teams[0].team
        else:
            pass

    return None

def get_teams(game_id:int):
    teams = [team for team in TriviaGameTeams.objects.filter(game__id=game_id)]
    return teams


def get_gamestate(game_id:int):
    game = get_game(game_id)

    result = {}
    result['Game'] = {}
    result['Teams'] = {}
    result['Orphans'] = [orphan.user.user_name for orphan in get_orphans(game_id)]
    result['Game']['Id']=game.id
    result['Game']['Name']=game.name
    result['Game']['State']=game.state
    
    for team in get_teams(game_id):
        result['Teams'][team.id]={}
        result['Teams'][team.id]['id']=team.team.id
        result['Teams'][team.id]['name']=team.team.team_name
        result['Teams'][team.id]['members']=\
            [user.user_name for user in get_users(game_id,team.team.id)]

    return result

def get_game(game_id:int):
    game = TriviaGame.objects.get(id=game_id,state=0)
    return game

def get_games(only_open:bool=True):

    if only_open:
        games = [game for game in TriviaGame.objects.all() if game.state != 2]
    else:
        games = [game for game in TriviaGame.objects.all()]
    return games

# def get_game():
#     games = TriviaGame.objects.all()
#     # return games[len(games)-1]
#     _game = games[len(games)-1]
#     game = {}
#     game['Game'] = [_game.id, _game.name]
#     game['Teams'] = {}
#     game['Orphans'] = []

#     for orphan in get_orphans(_game.id):
#         game['Orphans'].append(str(orphan))
    
#     for team in get_teams(_game.id):
#         t = {}
#         t['id']=team.team.id
#         t['name']=team.team.team_name
#         t['members']=[str(user) for user in get_users(_game.id,team.id)]
#         game['Teams'][team.team.id] =
    
#     return game

def add_teammember(game_id:int, team_id:int, user_id:int) -> bool:
    game = TriviaGame.objects.filter(id=game_id)
    team = get_team(game_id=game_id,team_id=team_id)
    user = get_orphan(game_id=game_id,user_id=user_id)

    if user == None:
        return False
        
    if len(game)>0:
        game = game[0]
    else:
        return False

    tm = TeamMember()
    tm.game=game
    tm.team=team
    tm.user=user.user
    tm.save()
    user.delete()

    return True

def remove_teammember(game_id:str, team_id:int, user_id:int):
    try:
        game = TriviaGame.objects.get(id=game_id)
        user = TeamMember.objects.filter(user__id=user_id,team__id=team_id)
        if len(user)>0:
            if len(user)==1:
                user=user[0]
                orphan = OrphanUser()
                orphan.user = user.user
                orphan.game=game
                orphan.save()
                user.delete()
                return True
            else:
                pass
    except:
        pass
    return False

def reset_db():
    TriviaGame.objects.all().delete()
    TeamMember.objects.all().delete()
    OrphanUser.objects.all().delete()
    TriviaGameTeams.objects.all().delete()
    Team.objects.all().delete()
    User.objects.all().delete()

    
def create_model():
    game = create_game()
    users = create_orphans(game.id,50)
    teams = create_teams(game.id,users,int(len(users)/4))

def create_game():
    game = TriviaGame()
    game.name="Trivia Game"
    game.save()
    return game

def create_orphans(game_id:int,count:int):
    users = []
    
    for i in range(count):
        username = "User {}".format(str(i))
        user = create_user(game_id,username)
        users.append(user)
    
    return users

def create_teams(game_id:int,users:list,count:int):
    teams = []

    _upt = len(users)/count
    upt=int(_upt)
    rem=len(users)-(upt*count)
    
    for i in range(0,count):
        teamname = "Team {}".format(str(i))
        team = create_team(game_id,teamname)
        for u in range(0,upt):
            if len(users)==0:
                break
            add_teammember(game_id,team.id,users.pop().id)
        
        if rem>0 and len(users)>0:
            add_teammember(game_id,team.id,users.pop().id)
            rem -= 1
        
        teams.append(team)

    return teams
    