import datetime

from django.db import models
from django.utils import timezone

class User(models.Model):
    user_name = models.CharField(max_length=256)

class Team(models.Model):
    team_name = models.CharField(max_length=256)
    # team_members = models.ForeignKey(User,on_delete=models.SET_NULL)

class TeamMember(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    team = models.ForeignKey(Team,on_delete=models.CASCADE)

class TriviaGame(models.Model):
    name = models.CharField(max_length=256)

class TriviaQuestion(models.Model):
    question = models.CharField()

class TriviaQuestionMultipleChoice(TriviaQuestion):
    pass

class TriviaQuestionFillInTheBlanks(TriviaQuestion):
    pass

class TriviaGameTeams(models.Model):
    team = models.ForeignKey(Team,on_delete=models.CASCADE)
    game = models.ForeignKey(TriviaGame,on_delete=models.CASCADE)
