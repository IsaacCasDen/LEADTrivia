import datetime

from django.db import models
from django.utils import timezone
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

class TeamMember(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    team = models.ForeignKey(Team,on_delete=models.CASCADE)

    def __str__(self):
        return "Team: {}\tUser:{}".format(team.team_name,user.user_name)
    def __repr__(self):
        return self.__str__()

class TriviaGame(models.Model):
    name = models.CharField(max_length=256)

    def __str__(self):
        return "Trivia Game: {}".format(self.name)

class OrphanUser(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    game = models.ForeignKey(TriviaGame,on_delete=models.CASCADE)

    def __str__(self):
        return "User:{}".format(user.user_name)
    def __repr__(self):
        return self.__str__()

class TriviaQuestion(models.Model):
    question = models.CharField(max_length=512)
    answer = models.CharField(max_length=512)

# class TriviaQuestionMultipleChoice(TriviaQuestion):
#     pass

# class TriviaQuestionFillInTheBlanks(TriviaQuestion):
#     pass

class TriviaGameTeams(models.Model):
    team = models.ForeignKey(Team,on_delete=models.CASCADE)
    game = models.ForeignKey(TriviaGame,on_delete=models.CASCADE)

def new_user(game_id:int, username:str):
    game = TriviaGame.objects.filter(id=game_id)[0]

    user = get_user(game_id,username)
    if user != None:
        return None

    user = User()
    user.user_name = username
    user.save()
    
    ou = OrphanUser()
    ou.user=user
    ou.game=game
    ou.save()

    return user

def change_username(game_id:int,old_name:str,new_name:str):
    user = get_user(game_id,user_name=old_name)
    _user = get_user(game_id,user_name=new_name)
    if _user != None:
        return False
    else:
        user.user_name = new_name
        user.save()
    


def change_teamname(game_id:int,old_name:str,new_name:str):
    team = get_team(game_id,team_name=old_name)
    _team = get_team(game_id,team_name=new_name)
    if _team != None:
        return False
    else:
        team.team_name = new_name
        team.save()

def new_team(game_id:int, teamname:str):
    game = TriviaGame.objects.filter(id=game_id)[0]
    team = get_team(game_id,team_name=teamname)

    if team==None:
        team = Team()
        team.team_name = teamname
        team.save()

        tgt = TriviaGameTeams()
        tgt.team = team
        tgt.game = game
        tgt.save()
    
        return team
    else:
        return None
    
    

def get_user(game_id:int, user_id = None, user_name = None):

    
    if user_id == None and user_name == None:
        return None
    elif user_id != None and not isinstance(user_id,int):
        return None
    elif user_name !=None and not isinstance(user_name,str):
        user_name = str(user_name)
        
    teams = get_teams(game_id)
    users = get_orphans(game_id)

    for user in users:
        if user.user_name == user_name or user.id == user_id:
            return user
    
    for team in teams:
        users = get_users(team.id)
        for user in users:
            if user.user_name == user_name or user.id == user_id:
                return user
    
    return None


def get_users(team_id:int):
    tm = TeamMember.objects.filter(team__id=team_id)
    users = []
    for item in tm:
        users.append(item.user)
    return users

def get_orphans(game_id:int):
    ou = OrphanUser.objects.filter(game__id=game_id)
    users = []
    for item in ou:
        users.append(item.user)
    return users

def get_team(game_id:int, team_id = None, team_name = None):
    
    if game_id == None:
        return None
    elif team_id == None and team_name == None:
        return None
    elif team_id != None and not isinstance(team_id,int):
        return None
    elif team_name !=None and not isinstance(team_name,str):
        team_name = str(team_name)
    
    teams = None

    if team_id !=None and team_name!=None:
        teams = TriviaGameTeams.objects.filter(team__id=team_id,team__team_name=team_name,game__id=game_id)
    elif team_id !=None:
        teams = TriviaGameTeams.objects.filter(team__id=team_id,game__id=game_id)
    else:
        teams = TriviaGameTeams.objects.filter(team__team_name=team_name,game__id=game_id)

    if len(teams)==0:
        return None
    elif len(teams)==1:
        return teams[0].team
    else:
        print(teams)

def get_teams(game_id:int):
    tgt = TriviaGameTeams.objects.filter(game__id=game_id)
    teams = []
    for item in tgt:
        teams.append(item.team)
    return teams

def get_game():
    games = TriviaGame.objects.all()
    # return games[len(games)-1]
    _game = games[len(games)-1]
    game = {}
    game['Game'] = (_game.id, str(_game))
    game['Teams'] = {}
    game['Orphans'] = []

    for orphan in get_orphans(_game.id):
        game['Orphans'].append(str(orphan))
    
    for team in get_teams(_game.id):
        game['Teams'][team.team_name] = []
        for user in get_users(team.id):
            game['Teams'][team.team_name].append(str(user))
    
    return game

def reset_db():
    TriviaGame.objects.all().delete()
    TeamMember.objects.all().delete()
    Team.objects.all().delete()
    User.objects.all().delete()

    
def create_model():
    users = create_users(50)
    teams = create_teams(int(len(users)/4))
    game = create_game()
    assign_users(users,teams)
    assign_teams(teams,game)


def create_users(count:int):
    users = []
    
    for i in range(count):
        user = User()
        user.user_name = "User " + str(i)
        user.save()
        users.append(user)
    
    return users

def create_teams(count:int):
    teams = []

    for i in range(count):
        team = Team()
        team.team_name = "Team " + str(i)
        team.save()
        teams.append(team)
    
    return teams

def create_game():
    game = TriviaGame()
    game.save()
    return game

def assign_users(users:list,teams:list):
    _upt = len(users)/len(teams)
    upt=int(_upt)
    rem=len(users)-(upt*len(teams))
    
    _teams = []
    for i,team in enumerate(teams):
        _team = (team,[])
        _teams.append(_team)
        while len(_team[1])<upt and len(users)>0:
            _team[1].append(users.pop())
        if len(users)<1:
            break
        elif rem>0:
            _team[1].append(users.pop())
            rem-=1
    
    for team in _teams:
        for user in team[1]:
            tm = TeamMember()
            tm.team=team[0]
            tm.user=user
            tm.save()

def assign_teams(teams:list,game:TriviaGame):
    
    for team in teams:
        tgt = TriviaGameTeams()
        tgt.team=team
        tgt.game=game
        tgt.save()
    