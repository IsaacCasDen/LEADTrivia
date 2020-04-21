from datetime import datetime

from django.core.mail import send_mail
from django.db import models, transaction
from django.db.models import CASCADE, SET_NULL
from django.utils import timezone
from threading import Lock
import random
import secrets

#test
class User(models.Model):
    
    __SECRET_KEY_LENGTH__ = 6
    __SALT_LENGTH__ = 6

    user_name = models.CharField(max_length=128)
    secret_key = models.CharField(max_length=128,null=True)
    password = models.CharField(max_length=128)
    email = models.CharField(max_length=128)
    is_admin = models.BooleanField(default=False)
    salt = models.CharField(max_length=__SALT_LENGTH__)

    @classmethod
    def create(cls, user_name:str, password:str=None, email:str=None):
        users = User.objects.filter(user_name=user_name)
        if len(users)>0:
            return None

        user = User.objects.create_user(user_name,email,password)
        if password == None:
            user.secret_key = User.create_secret_key()
            user.save()

        return user

    @classmethod
    def create_secret_key(cls):
        alphabet = 'abcdefghiklmnopqrstuvwxyz'
        chars = []
        for i in range(User.__SECRET_KEY_LENGTH__):
            chars.append(secrets.choice(alphabet))

        value = ''.join(chars)
        return value

    def __str__(self):
        return "{}".format(self.user_name)
    def __repr__(self):
        return self.__str__()

class SecretQuestions(models.Model):
    user = models.ForeignKey(User,on_delete=CASCADE)
    question = models.CharField(max_length=512)
    answer = models.CharField(max_length=512)

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
    current_round = models.IntegerField(default=1)
    current_question_index = models.IntegerField(default=0)
    start_time = models.DateTimeField()
    is_cancelled = models.BooleanField(default=False)

    @classmethod
    def create(cls, name:str, start_time:datetime, state:int=0, current_round:int=1, current_question_index:int=1, is_cancelled:bool=False):
        game = TriviaGame()
        game.name = name
        game.start_time = start_time
        game.state = state
        game.current_round = current_round
        game.current_question_index = current_question_index
        game.is_cancelled = is_cancelled
        game.save()
        return game

    def get_info(self):
        value = {}
        value['id'] = self.id
        value['name'] = self.name
        value['state'] = self.state
        value['current_round'] = self.current_round
        value['current_question_index'] = self.current_question_index
        value['start_time'] = self.get_starttime()
        value['is_cancelled'] = self.is_cancelled
        return value

    def get_starttime(self):
        date = self.start_time.strftime("%Y-%m-%d")
        time = self.start_time.strftime("%H:%M:%S")
        return {'date':date,'time':time}

    def start_game(self):
        self.state=1
        self.save()
    
    def finish_game(self):
        self.state=2
        self.save()
    
    def reset_started(self):
        self.state=0
        self.save()

    def next_question(self):
        questions = TriviaGameQuestion.objects.filter(game__id=self.id)
        nums = [(q.round_index,q.index) for q in questions]
        nums.sort()
        for i,value in enumerate(nums):
            if value[0]==self.current_round:
                if value[1]==self.current_question_index:
                    if i<len(nums)-1:
                        if self.current_round == nums[i+1][0]:
                            self.current_question_index = nums[i+1][1]
                            self.save()
                            return True
                        else:
                            game_round = get_game_round(self.id,self.current_round)
                            if game_round == None:
                                compile_round_stats(self.id)
                            else:
                                if game_round.is_finished:
                                    self.current_round = nums[i+1][0]
                                    self.current_question_index = nums[i+1][1]
                                    self.save()
                                else:
                                    compile_round_stats(self.id)
                                    game_round.is_finished = True
                                    game_round.save()
                                return True
                                
                    else:
                        if True:
                            compile_round_stats(self.id)
                            #compile_game_stats(self.id)
                            pass
                        else:
                            # Finish Game
                            pass
        return False
                    
    
    def prev_question(self):
        questions = TriviaGameQuestion.objects.filter(game__id=self.id)
        nums = [(q.round_index,q.index) for q in questions]
        nums.sort()
        for i,value in enumerate(nums):
            if value[0]==self.current_round:
                if value[1]==self.current_question_index:
                    if i>0 and self.current_round <= nums[i-1][0]:
                        self.current_question_index = nums[i-1][1]
                        self.save()
                    break

class TriviaGameTeam(models.Model):
    team = models.ForeignKey(Team,on_delete=models.CASCADE)
    game = models.ForeignKey(TriviaGame,on_delete=models.CASCADE)

class TeamMember(models.Model):
    game = models.ForeignKey(TriviaGame,on_delete=models.CASCADE)
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    team = models.ForeignKey(TriviaGameTeam,on_delete=models.CASCADE)

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

# class TriviaAnswer(models.Model):


class TriviaQuestion(models.Model):
    question = models.CharField(max_length=512)
    answer = models.CharField(max_length=512)
    #working here

class TriviaQuestionChoiceGroup(models.Model):
    question = models.ForeignKey(TriviaQuestion,on_delete=models.CASCADE)
    index = models.IntegerField(default=0)

class TriviaQuestionChoice(models.Model):
    group = models.ForeignKey(TriviaQuestionChoiceGroup, on_delete=models.CASCADE)
    choice = models.CharField(max_length=512)
    # visible = models.BooleanField(default=True)

class TriviaQuestionImage(models.Model):
    question = models.ForeignKey(TriviaQuestion, on_delete=models.CASCADE)
    index = models.IntegerField(default=0)
    file_path = models.CharField(max_length=1024)
    is_local = models.BooleanField(default=True)

class TriviaQuestionVideo(models.Model):
    question = models.ForeignKey(TriviaQuestion, on_delete=models.CASCADE)
    index = models.IntegerField(default=0)
    file_path = models.CharField(max_length=1024)
    is_local = models.BooleanField(default=False)

class TriviaQuestionAudio(models.Model):
    question = models.ForeignKey(TriviaQuestion, on_delete=models.CASCADE)
    index = models.IntegerField(default=0)
    file_path = models.CharField(max_length=1024)
    is_local = models.BooleanField(default=True)

class TriviaGameQuestion(models.Model):
    #Check for correct or wrong
    question = models.ForeignKey(TriviaQuestion,on_delete=models.CASCADE)
    game = models.ForeignKey(TriviaGame,on_delete=models.CASCADE)  
    time = models.IntegerField(default=60)
    index = models.IntegerField()
    round_index = models.IntegerField(default=1)

    @classmethod
    def create(cls, question, game, time, index, round_index=1):
        ind = [q.index for q in TriviaGameQuestion.objects.filter(game__id=game.id)]
        while index in ind:
            index += 1
        item = cls(question = question, game = game, time = time, index = index, round_index = round_index)
        #item.save()
        return item

class TriviaGameUserAnswerChoice(models.Model):
    game = models.ForeignKey(TriviaGame,on_delete=CASCADE)
    user = models.ForeignKey(TeamMember,on_delete=SET_NULL, null=True)
    question = models.ForeignKey(TriviaGameQuestion, on_delete=CASCADE)
    group = models.ForeignKey(TriviaQuestionChoiceGroup, on_delete=CASCADE)
    choice = models.ForeignKey(TriviaQuestionChoice, on_delete=CASCADE,null=True)

    @classmethod
    def get_team_answers(cls,game_id:int,team_id:int,question_id:int,group_id:int):
        user_answers = TriviaGameUserAnswerChoice.objects.filter(game__id=game_id,user__team__id=team_id,question_id=question_id,group__id=group_id)
        return user_answers

class TriviaGameUserAnswer(models.Model):
    game = models.ForeignKey(TriviaGame,on_delete=CASCADE)
    user = models.ForeignKey(TeamMember,on_delete=SET_NULL, null=True)
    question = models.ForeignKey(TriviaGameQuestion, on_delete=CASCADE)
    answer = models.CharField(max_length=512)

    def is_correct(self):
        return self.question.question.answer == self.answer

class TriviaGameTeamAnswerChoice(models.Model):
    game = models.ForeignKey(TriviaGame,on_delete=CASCADE)
    team = models.ForeignKey(TriviaGameTeam,on_delete=SET_NULL, null=True)
    question = models.ForeignKey(TriviaGameQuestion, on_delete=CASCADE)
    group = models.ForeignKey(TriviaQuestionChoiceGroup, on_delete=CASCADE)
    choice = models.ForeignKey(TriviaQuestionChoice, on_delete=CASCADE,null=True)

class TriviaGameTeamAnswer(models.Model):
    game = models.ForeignKey(TriviaGame,on_delete=CASCADE)
    team = models.ForeignKey(TriviaGameTeam,on_delete=SET_NULL, null=True)
    question = models.ForeignKey(TriviaGameQuestion, on_delete=CASCADE)
    answer = models.CharField(max_length=512)

    def is_correct(self):
        return self.question.question.answer == self.answer

class TriviaGameRound(models.Model):
    game = models.ForeignKey(TriviaGame,on_delete=CASCADE)
    round_index = models.IntegerField()
    is_finished = models.BooleanField(default=False)

class TriviaGameRoundResultTeam(models.Model):
    game = models.ForeignKey(TriviaGame,on_delete=CASCADE)
    game_round = models.ForeignKey(TriviaGameRound,on_delete=CASCADE)
    team = models.ForeignKey(TriviaGameTeam,on_delete=SET_NULL, null=True)
    points = models.IntegerField()
    rank = models.IntegerField()

class TriviaGameRoundResultUser(models.Model):
    game = models.ForeignKey(TriviaGame,on_delete=CASCADE)
    game_round = models.ForeignKey(TriviaGameRound,on_delete=CASCADE)
    team = models.ForeignKey(TriviaGameTeam,on_delete=SET_NULL, null=True)
    user = models.ForeignKey(TeamMember,on_delete=SET_NULL, null=True)
    points = models.IntegerField()
    rank = models.IntegerField()

class TriviaGameResultTeam(models.Model):
    game = models.ForeignKey(TriviaGame,on_delete=CASCADE)
    team = models.ForeignKey(TriviaGameTeam,on_delete=SET_NULL, null=True)
    points = models.IntegerField()
    rank = models.IntegerField()

class TriviaGameResultUser(models.Model):
    game = models.ForeignKey(TriviaGame,on_delete=CASCADE)
    team = models.ForeignKey(TriviaGameTeam,on_delete=SET_NULL, null=True)
    user = models.ForeignKey(TeamMember,on_delete=SET_NULL, null=True)
    points = models.IntegerField()
    rank = models.IntegerField()

def get_round_results(game_id:int,round_index:int):
    game_round = get_game_round(game_id,round_index)
    if game_round == None:
        return None

    value = {} 
    teams = {item.team.id:item for item in TriviaGameRoundResultTeam.objects.filter(game_round=game_round.id)}

    value['round'] = {}
    value['round']['id']=game_round.id
    value['round']['index']=game_round.round_index
    value['round']['isFinished']=game_round.is_finished
    value['round']['team_count']=len(teams)

    
    value['teams'] = {}
    for i,key in enumerate(teams.keys()):
        users = []
        value['teams'][key] = {'id':key, 'teamName':teams[key].team.team.team_name,'points':teams[key].points,'rank':teams[key].rank,'questions':{}}
        _users = TriviaGameRoundResultUser.objects.filter(game_round=game_round.id, user__team__id=key)
        for user in _users:
            users.append((user.rank,{'id':user.user.user.id,'username':user.user.user.user_name,'points':user.points,'rank':user.rank}))
        users.sort(key=lambda x:x[0])
        value['teams'][key]['users']=tuple(users)

        answers = TriviaGameTeamAnswer.objects.filter(game__id=game_id,team__id=key,question__round_index=round_index)
        questions = {}
        for answer in answers:
            questions[answer.question.id] = {'Id':answer.question.id,'Index':answer.question.index,'IsCorrect':answer.is_correct()}


        value['teams'][key]['questions'] = questions

    return value
    
def get_game_results():
    pass

def compile_round_stats(game_id:int):
    game = TriviaGame.objects.get(id=game_id)
    if game == None:
        return

    game_round = TriviaGameRound.objects.filter(game__id=game.id,round_index=game.current_round)
    if len(game_round) == 0:
        game_round = TriviaGameRound()
        game_round.round_index = game.current_round
        game_round.game = game
        game_round.save()
    else:
        game_round = game_round[0]
    
    compile_round_stats_teams(game_round.id)
    compile_round_stats_users(game_round.id)

def compile_round_stats_teams(round_id:int):
    game_round = TriviaGameRound.objects.get(id=round_id)
    if game_round == None:
        return
    
    game = game_round.game
    team_list = TriviaGameTeam.objects.filter(game__id=game.id)
    result_list = []
    
    for team in team_list:
        _result = TriviaGameRoundResultTeam.objects.filter(game__id=game.id,game_round=game_round.id,team__id=team.id)
        count = len(_result)
        if len(_result)==1:
            _result = _result[0]
        else:
            _result = TriviaGameRoundResultTeam()
            _result.game=game
            _result.game_round=game_round
            _result.team=team
        
        answers = get_team_answers(game.id,team.id,game_round.round_index)
        _result.points = answers[1]
        result = (team.id,answers[1],_result)
        result_list.append(result)

    result_list.sort(key=lambda x:x[1],reverse=True)
    last_points = None
    last_rank = None
    for i,value in enumerate(result_list):
        if (last_points==None):
            last_points = value[1]
            last_rank = i+1
            value[2].rank=last_rank
        else:
            if last_points == value[1]:
                value[2].rank = last_rank
            else:
                last_points = value[1]
                last_rank += 1
                value[2].rank = last_rank
        value[2].save()
    
def compile_round_stats_users(round_id:int):
    game_round = TriviaGameRound.objects.get(id=round_id)
    if game_round == None:
        return
    
    game = game_round.game
    user_list = TeamMember.objects.filter(game__id=game.id)
    result_list = []
    
    for user in user_list:
        _result = TriviaGameRoundResultUser.objects.filter(game__id=game.id,game_round=game_round.id,user__id=user.id)
        count = len(_result)
        if len(_result)==1:
            _result = _result[0]
        else:
            _result = TriviaGameRoundResultUser()
            _result.game=game
            _result.game_round=game_round
            _result.user=user
        
        answers = get_user_answers(game.id,user.id,game_round.round_index)
        _result.points = answers[1]
        result = (user.id,answers[1],_result)
        result_list.append(result)

    result_list.sort(key=lambda x:x[1],reverse=True)
    last_points = None
    last_rank = None
    for i,value in enumerate(result_list):
        if (last_points==None):
            last_points = value[1]
            last_rank = i+1
            value[2].rank=last_rank
        else:
            if last_points == value[1]:
                value[2].rank = last_rank
            else:
                last_points = value[1]
                last_rank += 1
                value[2].rank = last_rank
        value[2].save()

def get_user_answers(game_id:int, user_id:int,round_index:int):

    questions = None
    questions = TriviaGameQuestion.objects.filter(game__id=game_id,round_index=round_index)

    user_answers = []
    user_points = 0

    for question in questions:
        answer = TriviaGameUserAnswer.objects.filter(game__id=game_id,user__id=user_id,question__id=question.id)
        for a in answer:
                print(a.answer)
        _answer = ""
        _correct = False
        if len(answer)>0:
            answer=answer[0]
            
            _answer=answer.answer
            _correct = answer.is_correct()

        user_answer = (question.id,question.index,question.question.question,question.question.answer,_answer,_correct)
        user_answers.append(user_answer)
        if user_answer[5]:
            user_points+=1

    result = (user_id,user_points,user_answers)
    return result

def get_user_answer(game_id:int, user_id:int, question_id:int):
    answers = {}
    user_choices = TriviaGameUserAnswerChoice.objects.filter(game__id=game_id,user__id=user_id,question__id=question_id)
    if len(user_choices) == 0:
        return ""
    
    for user_choice in user_choices:
        groups = TriviaQuestionChoiceGroup.objects.filter(question__id=user_choice.question.id)
        for group in groups:
            choices = TriviaQuestionChoice.objects.filter(group__id=group.id)
            if user_choice.choice in choices:
                answers[group.index]=user_choice.choice.choice
            else:
                answers[group.index]="{}"
    indices = [(key,answers[key]) for key in answers.keys()]
    indices.sort(key=lambda x:x[0])

    for i in range(0,indices[0][0]):
        indices.insert(i,i)
        
    for i in range(1,len(indices)):
        for j in range(indices[i-1][0]+1,indices[i][0]):
            value = indices[j-1][0] + j
            indices.insert(value,(value,""))

    tgq = TriviaGameQuestion.objects.get(id=question_id)
    question = tgq.question
    
    user_answer = ""
    if '{}' in question.question:
        # user_answer = question.question
        # for value in indices:
        #     user_answer = user_answer.replace("{}",value[1],1)
        user_answer = question.question.format(*[value[1] for value in indices])
    else:
        user_answer = indices[0][1]

    return user_answer

def get_team_answers(game_id:int, team_id:int,round_index:int):

    questions = None
    questions = TriviaGameQuestion.objects.filter(game__id=game_id,round_index=round_index)

    team_answers = []
    team_points = 0

    for question in questions:
        answer = TriviaGameTeamAnswer.objects.filter(game__id=game_id,team__id=team_id,question__id=question.id)

        _answer = ""
        _correct = False
        if len(answer)>0:
            answer=answer[0]
            _answer=answer.answer
            _correct = answer.is_correct()

        team_answer = (question.id,question.index,question.question.question,question.question.answer,_answer,_correct)
        team_answers.append(team_answer)
        if team_answer[5]:
            team_points+=1

    result = (team_id,team_points,team_answers)
    return result

def get_team_answer(game_id:int, team_id:int, question_id:int):
    answers = {}
    team_choices = TriviaGameTeamAnswerChoice.objects.filter(game__id=game_id,team__id=team_id,question__id=question_id)
    if len(team_choices) == 0:
        return ""

    for team_choice in team_choices:
        groups = TriviaQuestionChoiceGroup.objects.filter(question__id=team_choice.question.id)
        for group in groups:
            choices = TriviaQuestionChoice.objects.filter(group__id=group.id)
            if team_choice.choice in choices:
                answers[group.index]=team_choice.choice.choice
            else:
                if group.index not in answers:
                    answers[group.index]="{}"
    indices = [(key,answers[key]) for key in answers.keys()]
    indices.sort(key=lambda x:x[0])

    for i in range(0,indices[0][0]):
        indices.insert(i,i)
        
    for i in range(1,len(indices)):
        for j in range(indices[i-1][0]+1,indices[i][0]):
            value = indices[j-1][0] + j
            indices.insert(value,(value,""))

    tgq = TriviaGameQuestion.objects.get(id=question_id)
    question = tgq.question
    
    team_answer = ""
    if '{}' in question.question:
        # team_answer = question.question
        # for value in indices:
        #     team_answer = team_answer.replace("{}",value[1],1)
        team_answer = question.question.format(*[value[1] for value in indices])
    else:
        team_answer = indices[0][1]

    return team_answer

def submit_user_choice(game_id:int,question_id:int,group_id:int,choice_id:int,user_id:int):
      
    game = TriviaGame.objects.get(id=game_id)
    if game == None:
        return False

    user = TeamMember.objects.filter(game__id=game_id,user__id=user_id)
    if len(user)==0:
        return False
    else:
        user = user[0]

    choice = TriviaGameUserAnswerChoice.objects.filter(game__id=game_id, user__id=user.id, question__id=question_id,group__id=group_id)
    if len(choice)==1:
        choice = choice[0]
        choice.choice = TriviaQuestionChoice.objects.get(id=choice_id)
    elif len(choice)==0:
        group = TriviaQuestionChoiceGroup.objects.get(id=group_id)
        if group == None:
            return False
        choice = TriviaGameUserAnswerChoice()
        choice.user = user
        choice.group = group
        choice.question=TriviaGameQuestion.objects.get(id=question_id)
        choice.answer = TriviaQuestionChoice.objects.get(id=choice_id)
        choice.game=game

    choice.save()
    update_user_answer(game_id,question_id,user.id)
    update_team_choice(game_id,choice.user.team.id,question_id,group_id)
    return True

def update_user_answer(game_id:int,question_id:int,user_id:int):
    game = get_game(game_id)
    if game == None:
        return

    user = TeamMember.objects.get(id=user_id)
    if user == None:
        return

    question = TriviaGameQuestion.objects.get(id=question_id)
    if question==None:
        return

    game_answer = TriviaGameUserAnswer.objects.filter(game__id=game_id,user__id=user_id,question__id=question_id)
    if len(game_answer) == 0:
        game_answer = TriviaGameUserAnswer()
        game_answer.game=game
        game_answer.user=user
        game_answer.question=question
    else:
        game_answer=game_answer[0]

    game_answer.answer=get_user_answer(game_id,user_id,question_id)
    game_answer.save()

def update_team_answer(game_id:int,question_id:int,team_id:int):
    game = get_game(game_id)
    if game == None:
        return

    team = TriviaGameTeam.objects.get(team__id=team_id)
    if team == None:
        return

    question = TriviaGameQuestion.objects.get(id=question_id)
    if question==None:
        return

    game_answer = TriviaGameTeamAnswer.objects.filter(game__id=game_id,team__id=team_id,question__id=question_id)
    if len(game_answer) == 0:
        game_answer = TriviaGameTeamAnswer()
        game_answer.game=game
        game_answer.team=team
        game_answer.question=question
    else:
        game_answer=game_answer[0]

    game_answer.answer=get_team_answer(game_id,team_id,question_id)
    game_answer.save()

def update_team_choice(game_id:int, team_id:int, question_id: int, group_id:int) -> bool:
    
    game = TriviaGame.objects.get(id=game_id)
    if game == None:
        return False

    team = TriviaGameTeam.objects.filter(game__id=game_id,team__id=team_id)
    if len(team)==0:
        return
    else:
        team=team[0]

    team_members = TeamMember.objects.filter(team__id=team.id)
    team_choices = {}
    for user in team_members:
        user_choice = TriviaGameUserAnswerChoice.objects.filter(game__id=game_id,user__id=user.id,question__id=question_id,group__id=group_id)
        # user_choice = TriviaGameUserAnswerChoice.objects.filter(game__id=game.id,question__id=question_id,group__id=group_id,choice__id=choice_id)
        if len(user_choice)>0:
            user_choice=user_choice[0]
            if user_choice.choice.id in team_choices:
                team_choices[user_choice.choice.id] += 1
            else:
                team_choices[user_choice.choice.id] = 1


    team_choice = None
    for key in team_choices:
        if team_choices[key] > len(team_members)/2:
            team_choice = TriviaQuestionChoice.objects.get(id=key)
            break

    choice = TriviaGameTeamAnswerChoice.objects.filter(game__id=game_id,team__id=team.id,question__id=question_id,group__id=group_id)
    if len(choice)==0:
        choice = TriviaGameTeamAnswerChoice()
        choice.game = TriviaGame.objects.get(id=game_id)
        choice.team = TriviaGameTeam.objects.get(id=team.id)
        choice.question = TriviaGameQuestion.objects.get(id=question_id)
        choice.group = TriviaQuestionChoiceGroup.objects.get(id=group_id)
    else:
        choice = choice[0]

    choice.choice=team_choice
    choice.save()
    update_team_answer(game_id,question_id,team.id)
    return team_choice!=None

def get_questions(game_id:int,round_index:int=None):

    rounds = {}
    q = None
    if round_index == None:
        q = TriviaGameQuestion.objects.filter(game__id=game_id)
    else:
        q=TriviaGameQuestion.objects.filter(game__id=game_id,round_index=round_index)
    
    for item in q:
        value = get_question(question_id=item.id)
        if value['round_index'] in rounds:
            rounds[value['round_index']].append(value)
        else:
            rounds[value['round_index']] = [value]

    round_list = list(rounds.keys())
    round_list.sort()

    for _round in rounds.keys():
        rounds[_round].sort(key=lambda x: (x['round_index'],x['index']))

    return (round_list,rounds)

def get_question(game_id:int=None, round_index:int = None, index:int = None, question_id:int=None):
    if game_id==None and index==None and question_id == None:
        return None
    
    question = None

    if game_id!=None and index!=None:
        if round_index == None:
            game = get_game(game_id)
            round_index = game.current_round
        question = TriviaGameQuestion.objects.filter(game__id=game_id, round_index = round_index, index=index)
        if len(question)==1:
            question=question[0]
        else:
            return None
    elif question_id!=None:
        question = TriviaGameQuestion.objects.get(id=question_id)
    
    if question == None:
        return None

    value = {}
    value['id']=question.id
    value['question']=question.question.question
    value['answer']=question.question.answer
    value['round_index']=question.round_index
    value['index']=question.index
    value['groups'] = []
    
    groups = TriviaQuestionChoiceGroup.objects.filter(question__id=question.question.id)
    for i,group in enumerate(groups):
        _group = {}
        _group['id']=group.id
        _group['index'] = group.index
        _group['choices'] = [{'id':c.id, 'value':c.choice} for c in TriviaQuestionChoice.objects.filter(group__id=group.id)]
        value['groups'].append(_group)
    
    value['videos'] = []
    videos = TriviaQuestionVideo.objects.filter(question__id=question.question.id)
    for i,media in enumerate(videos):
        _media = {}
        _media['id']=media.id
        _media['file_path']=media.file_path
        _media['is_local']=media.is_local
        value['videos'].append(_media)

    value['images'] = []
    images = TriviaQuestionImage.objects.filter(question__id=question.question.id)
    for i,media in enumerate(videos):
        _media = {}
        _media['id']=media.id
        _media['file_path']=media.file_path
        _media['is_local']=media.is_local
        value['images'].append(_media)

    value['audios'] = []
    audios = TriviaQuestionAudio.objects.filter(question__id=question.question.id)
    for i,media in enumerate(videos):
        _media = {}
        _media['id']=media.id
        _media['file_path']=media.file_path
        _media['is_local']=media.is_local
        value['audios'].append(_media)

    return value

def create_questions(game_id:int):
    game = get_game(game_id)

    create_question(game.id,0,"My mama always said life was like {}. You never know what you're gonna get.","My mama always said life was like a box of chocolates. You never know what you're gonna get.",[["a box of chocolates","peanut brittle","confused elves"]],2,[('https://www.youtube.com/embed/CJh59vZ8ccc?controls=0&amp;start=30;end=40',False)])
    create_question(game.id,0,"If you got rid of every {} with {}, then you'd have three {} left.","If you got rid of every cop with some sort of drink problem, then you'd have three cops left.",[['cop','moose','priest'],['some sort of drink problem','a pineapple on their head','a car in their garage'],['cops','moose','priests']],1,[('static/app/media/video/ants.mp4',True)],[('static/app/media/image/ShruggingTom.png',True)],[('static/app/media/audio/30 Second Timer With Jeopardy Thinking Music.mp3',True)])
    create_question(game.id,1,"Which of these is a type of computer?","Apple",[['Apple', 'Nectarine','Orange']],2,[('static/app/media/video/ants.mp4',True)],[('static/app/media/image/ShruggingTom.png',True)],[('static/app/media/audio/30 Second Timer With Jeopardy Thinking Music.mp3',True)])
    create_question(game.id,1,"What was the name of the first satellite sent to space?","Sputnik 1",[["Sputnik 1","Gallileo 1","Neo 3"]],1,[('static/app/media/video/ants.mp4',True)],[('static/app/media/image/ShruggingTom.png',True)],[('static/app/media/audio/30 Second Timer With Jeopardy Thinking Music.mp3',True)])
    create_question(game.id,2,"In which U.S. state was Tennessee Williams born?","Mississippi",[["Mississippi","Tenessee", "Alabama"]],1,[('static/app/media/video/ants.mp4',True)],[('static/app/media/image/ShruggingTom.png',True)],[('static/app/media/audio/30 Second Timer With Jeopardy Thinking Music.mp3',True)])


def create_question(game_id:int, index:int, question:str, answer:str, choices:list, round_index:int=1,videos:list=[],images:list=[],audios:list=[]):
    game = TriviaGame.objects.get(id=game_id)
    if game == None:
        return False

    q = TriviaQuestion()
    q.question = question
    q.answer = answer
    q.save()
    
    for i,choice_list in enumerate(choices):
        group = TriviaQuestionChoiceGroup()
        group.index=i
        group.question = q
        group.save()
        for _choice in choice_list:
            choice = TriviaQuestionChoice()
            choice.choice=_choice
            choice.group = group
            choice.save()

    for i,value in enumerate(videos):
        tv = TriviaQuestionVideo()
        tv.question=q
        tv.index=i
        tv.file_path=value[0]
        tv.is_local=value[1]
        tv.save()
    
    for i,value in enumerate(images):
        ti = TriviaQuestionImage()
        ti.question=q
        ti.index=i
        ti.file_path=value
        ti.is_local=value[1]
        ti.save()
    
    for i,value in enumerate(audios):
        ta = TriviaQuestionAudio()
        ta.question=q
        ta.index=i
        ta.file_path=value
        ta.is_local=value[1]
        ta.save()
    

    tq = TriviaGameQuestion()
    tq.game=game
    tq.index = index
    tq.question = q
    tq.round_index = round_index
    tq.save()

    return True    

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

            tgt = TriviaGameTeam()
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
    
    teams = TriviaGameTeam.objects.filter(game__id=game_id,id=team_id)

    if len(teams)>0:
        if len(teams)==1:
            return teams[0]
        else:
            pass

    return None

def get_teams(game_id:int):
    teams = [team for team in TriviaGameTeam.objects.filter(game__id=game_id)]
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
    result['Game']['QuestionIndex']=game.current_question_index
    result['Game']['IsCancelled'] = game.is_cancelled
    result['Game']['StartTime']= game.get_starttime()
    
    for team in get_teams(game_id):
        result['Teams'][team.id]={}
        result['Teams'][team.id]['id']=team.id
        result['Teams'][team.id]['name']=team.team.team_name
        result['Teams'][team.id]['members']=\
            [user.user_name for user in get_users(game_id,team.id)]

    return result

def get_game(game_id:int) -> TriviaGame:
    game = TriviaGame.objects.get(id=game_id)
    return game

def get_games(only_open:bool=True) -> list:

    if only_open:
        games = [game for game in TriviaGame.objects.all() if game.state != 2]
    else:
        games = [game for game in TriviaGame.objects.all()]
    return games

def get_game_round(game_id:int,round_ind:int) -> TriviaGameRound:
    game_round = TriviaGameRound.objects.filter(game__id=game_id, round_index=round_ind)
    if len(game_round)>0:
        return game_round[0]
    else:
        return None

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
    TriviaGameTeam.objects.all().delete()
    Team.objects.all().delete()
    User.objects.all().delete()
    SecretQuestions.objects.all().delete()
    TriviaQuestion.objects.all().delete()
    TriviaQuestionChoiceGroup.objects.all().delete()
    TriviaQuestionChoice.objects.all().delete()
    TriviaGameQuestion.objects.all().delete()
    TriviaGameUserAnswerChoice.objects.all().delete()
    TriviaGameUserAnswer.objects.all().delete()
    TriviaGameTeamAnswerChoice.objects.all().delete()
    TriviaGameTeamAnswer.objects.all().delete()
    TriviaGameRound.objects.all().delete()
    TriviaGameRoundResultTeam.objects.all().delete()
    TriviaGameRoundResultUser.objects.all().delete()
    TriviaGameResultTeam.objects.all().delete()
    TriviaGameResultUser.objects.all().delete()

    
def create_model():
    game = create_game()
    users = create_orphans(game.id,50)
    teams = create_teams(game.id,users,int(len(users)/4))

def create_game():
    game = TriviaGame()
    game.name="Trivia Game"
    game.start_time = datetime.strptime("02/25/20 19:30:00","%m/%d/%y %H:%M:%S")
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
    