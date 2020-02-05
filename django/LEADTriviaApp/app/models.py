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

def get_users(team_id:int):
    tm = TeamMember.objects.filter(team__id=team_id)
    users = []
    for item in tm:
        users.append(item.user)
    return users

def get_teams(game_id:int):
    tgt = TriviaGameTeams.objects.filter(game__id=game_id)
    teams = []
    for item in tgt:
        teams.append(item.team)
    return teams

def get_game():
    games = TriviaGame.objects.all()
    # return games[len(games)-1]
    teams = []
    game = [games[len(games)-1],('Teams:',teams)]
    
    
    for team in get_teams(game[0].id):
        _team = (team,[])
        teams.append(_team)
        for user in get_users(team.id):
            _team[1].append(user)
    
    return game

        

    

def reset_db():
    TriviaGame.objects.all().delete()
    TeamMember.objects.all().delete()
    Team.objects.all().delete()
    User.objects.all().delete()

    
def create_model():
    users = create_users()
    teams = create_teams()
    game = create_game()
    assign_users(users,teams)
    assign_teams(teams,game)


def create_users():
    users = []
    
    for i in range(6):
        user = User()
        user.user_name = "User " + str(i)
        user.save()
        users.append(user)
    
    return users

def create_teams():
    teams = []

    for i in range(2):
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
    if upt<_upt:
        upt+=1

    _teams = []
    for i,team in enumerate(teams):
        _team = (team,[])
        _teams.append(_team)
        while len(_team[1])<upt and len(users)>0:
            _team[1].append(users.pop())
        if len(users)<1:
            break
    
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
    