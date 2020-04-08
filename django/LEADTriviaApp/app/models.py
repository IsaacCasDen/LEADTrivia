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
        questions = TriviaGameQuestions.objects.filter(game__id=self.id)
        nums = [(q.round,q.index) for q in questions]
        nums.sort()
        for i,value in enumerate(nums):
            if value[1]==self.current_question_index:
                if i<len(nums)-1:
                    self.current_round = nums[i+1][0]
                    self.current_question_index = nums[i+1][1]
                    self.save()
                    return True
        return False
                    
    
    def prev_question(self):
        questions = TriviaGameQuestions.objects.filter(game__id=self.id)
        nums = [(q.round,q.index) for q in questions]
        nums.sort()
        for i,value in enumerate(nums):
            if value[1]==self.current_question_index:
                if i>0:
                    self.current_round = nums[i-1][0]
                    self.current_question_index = nums[i-1][1]
                    self.save()
                    break

class TriviaGameTeams(models.Model):
    team = models.ForeignKey(Team,on_delete=models.CASCADE)
    game = models.ForeignKey(TriviaGame,on_delete=models.CASCADE)

class TeamMember(models.Model):
    game = models.ForeignKey(TriviaGame,on_delete=models.CASCADE)
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    team = models.ForeignKey(TriviaGameTeams,on_delete=models.CASCADE)

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

class TriviaQuestionChoices(models.Model):
    group = models.ForeignKey(TriviaQuestionChoiceGroup, on_delete=models.CASCADE)
    choice = models.CharField(max_length=512)
    # visible = models.BooleanField(default=True)

class TriviaGameQuestions(models.Model):
    #Check for correct or wrong
    question = models.ForeignKey(TriviaQuestion,on_delete=models.CASCADE)
    game = models.ForeignKey(TriviaGame,on_delete=models.CASCADE)  
    time = models.IntegerField(default=60)
    index = models.IntegerField()
    round = models.IntegerField(default=1)

    @classmethod
    def create(cls, question, game, time, index, round=1):
        ind = [q.index for q in TriviaGameQuestions.objects.filter(game__id=game.id)]
        while index in ind:
            index += 1
        item = cls(question = question, game = game, time = time, index = index, round = round)
        #item.save()
        return item

class TriviaGameUserAnswer(models.Model):
    game = models.ForeignKey(TriviaGame,on_delete=CASCADE)
    user = models.ForeignKey(TeamMember,on_delete=SET_NULL, null=True)
    question = models.ForeignKey(TriviaGameQuestions, on_delete=CASCADE)
    group = models.ForeignKey(TriviaQuestionChoiceGroup, on_delete=CASCADE)
    answer = models.ForeignKey(TriviaQuestionChoices, on_delete=CASCADE,null=True)

    @classmethod
    def get_team_answers(cls,game_id:int,team_id:int,question_id:int,group_id:int):
        user_answers = TriviaGameUserAnswer.objects.filter(game__id=game_id,user__team__id=team_id,question_id=question_id,group__id=group_id)
        return user_answers

class TriviaGameTeamAnswer(models.Model):
    game = models.ForeignKey(TriviaGame,on_delete=CASCADE)
    team = models.ForeignKey(TriviaGameTeams,on_delete=SET_NULL, null=True)
    question = models.ForeignKey(TriviaGameQuestions, on_delete=CASCADE)
    group = models.ForeignKey(TriviaQuestionChoiceGroup, on_delete=CASCADE)
    answer = models.ForeignKey(TriviaQuestionChoices, on_delete=CASCADE,null=True)

def get_user_answer(game_id:int, user_id:int, question_id:int):
    answers = {}
    choices = []
    user_answers = TriviaGameUserAnswer.objects.filter(game__id=game_id,user__id=user_id,question__id=question_id)
    if len(user_answers) == 0:
        return ""
    
    for user_answer in user_answers:
        groups = TriviaQuestionChoiceGroup.objects.filter(question__id=user_answer.question.id)
        for group in groups:
            choices = TriviaQuestionChoices.objects.filter(group__id=group.id)
            if user_answer.answer in choices:
                answers[group.index]=user_answer.answer.choice
    indices = [(key,answers[key]) for key in answers.keys()]
    indices.sort(key=lambda x:x[0])

    for i in range(0,indices[0][0]):
        indices.insert(i,i)
        
    for i in range(1,len(indices)):
        for j in range(indices[i-1][0]+1,indices[i][0]):
            value = indices[j-1][0] + j
            indices.insert(value,(value,""))

    tgq = TriviaGameQuestions.objects.get(id=question_id)
    question = tgq.question
    
    user_answer = ""
    if '{}' in question.question:
        user_answer = question.question.format(*[value[1] for value in indices])
    elif len(indices)>0:
        user_answer = indices[0][1]

    return user_answer

def get_users_answers(game_id:int):
    game = get_game(game_id)
    users = TeamMember.objects.filter(game__id=game_id)

    answers = {}
    for i in range(1,game.current_round+1):
        answers[i] = []
        for user in users:
            answers[i].append(list(get_user_answers(game_id,user.id,i)))

    for key in answers.keys():
        answers[key].sort(key=lambda x:x[1],reverse=True)
        for i in range(0,len(answers[key])):
            answers[key][i].insert(2,i)
            answers[key][i] = tuple(answers[key][i])

    return answers    

def get_teams_answers(game_id:int):
    game = get_game(game_id)
    teams = TriviaGameTeams.objects.filter(game__id=game_id)

    answers = {}
    for i in range(1,game.current_round+1):
        answers[i] = []
        for team in teams:
            answers[i].append(list(get_team_answers(game_id,team.id,i)))

    for key in answers.keys():
        answers[key].sort(key=lambda x:x[1],reverse=True)
        for i in range(0,len(answers[key])):
            answers[key][i].insert(2,i)
            answers[key][i] = tuple(answers[key][i])

    return answers

def get_user_answers(game_id:int, user_id:int,round_ind:int=None):

    questions = None
    if round_ind == None:
        questions = TriviaGameQuestions.objects.filter(game__id=game_id)
    else:
        questions = TriviaGameQuestions.objects.filter(game__id=game_id,round=round_ind)

    user_answers = []
    user_points = 0

    for question in questions:
        answer = get_user_answer(game_id,user_id,question.id)
        user_answer = (question.id,question.index,question.question.question,question.question.answer,question.question.answer == answer)
        user_answers.append(user_answer)
        if user_answer[4]:
            user_points+=1

    result = (user_id,user_points,user_answers)
    return result

def get_user_answer(game_id:int, user_id:int, question_id:int):
    answers = {}
    choices = []
    user_answers = TriviaGameUserAnswer.objects.filter(game__id=game_id,user__id=user_id,question__id=question_id)
    if len(user_answers) == 0:
        return ""
    
    for user_answer in user_answers:
        groups = TriviaQuestionChoiceGroup.objects.filter(question__id=user_answer.question.id)
        for group in groups:
            choices = TriviaQuestionChoices.objects.filter(group__id=group.id)
            if user_answer.answer in choices:
                answers[group.index]=user_answer.answer.choice
    indices = [(key,answers[key]) for key in answers.keys()]
    indices.sort(key=lambda x:x[0])

    for i in range(0,indices[0][0]):
        indices.insert(i,i)
        
    for i in range(1,len(indices)):
        for j in range(indices[i-1][0]+1,indices[i][0]):
            value = indices[j-1][0] + j
            indices.insert(value,(value,""))


def get_team_answers(game_id:int, team_id:int,round_ind:int=None):

    questions = None
    if round_ind == None:
        questions = TriviaGameQuestions.objects.filter(game__id=game_id)
    else:
        questions = TriviaGameQuestions.objects.filter(game__id=game_id,round=round_ind)

    team_answers = []
    team_points = 0

    for question in questions:
        answer = get_team_answer(game_id,team_id,question.id)
        team_answer = (question.id,question.index,question.question.question,question.question.answer,question.question.answer == answer)
        team_answers.append(team_answer)
        if team_answer[4]:
            team_points+=1

    result = (team_id,team_points,team_answers)
    return result

def get_team_answer(game_id:int, team_id:int, question_id:int):
    answers = {}
    choices = []
    team_answers = TriviaGameTeamAnswer.objects.filter(game__id=game_id,team__id=team_id,question__id=question_id)
    if len(team_answers) == 0:
        return ""

    for team_answer in team_answers:
        groups = TriviaQuestionChoiceGroup.objects.filter(question__id=team_answer.question.id)
        for group in groups:
            choices = TriviaQuestionChoices.objects.filter(group__id=group.id)
            if team_answer.answer in choices:
                answers[group.index]=team_answer.answer.choice
    indices = [(key,answers[key]) for key in answers.keys()]
    indices.sort(key=lambda x:x[0])

    for i in range(0,indices[0][0]):
        indices.insert(i,i)
        
    for i in range(1,len(indices)):
        for j in range(indices[i-1][0]+1,indices[i][0]):
            value = indices[j-1][0] + j
            indices.insert(value,(value,""))

    tgq = TriviaGameQuestions.objects.get(id=question_id)
    question = tgq.question
    
    team_answer = ""
    if '{}' in question.question:
        team_answer = question.question.format(*[value[1] for value in indices])
    else:
        team_answer = indices[0][1]

    return team_answer

def submit_user_answer(game_id:int,question_id:int,group_id:int,choice_id:int,user_id:int):
    
    team_answer = ""
    if '{}' in question.question:
        team_answer = question.question.format(*[value[1] for value in indices])
    else:
        team_answer = indices[0][1]

    return team_answer

def submit_user_answer(game_id:int,question_id:int,group_id:int,choice_id:int,user_id:int):
      
    game = TriviaGame.objects.get(id=game_id)
    if game == None:
        return False

    user = TeamMember.objects.filter(game__id=game_id,user__id=user_id)
    if len(user)==0:
        return False
    else:
        user = user[0]

    answer = TriviaGameUserAnswer.objects.filter(game__id=game_id, user__id=user.id, question__id=question_id,group__id=group_id)
    if len(answer)==1:
        answer = answer[0]
        answer.answer = TriviaQuestionChoices.objects.get(id=choice_id)
    elif len(answer)==0:
        group = TriviaQuestionChoiceGroup.objects.get(id=group_id)
        if group == None:
            return False
        answer = TriviaGameUserAnswer()
        answer.user = user
        answer.group = group
        answer.question=TriviaGameQuestions.objects.get(id=question_id)
        answer.answer = TriviaQuestionChoices.objects.get(id=choice_id)
        answer.game=game

    answer.save()
    return submit_team_answer(game_id,answer.user.team.id,question_id,group_id,answer.id)

def submit_team_answer(game_id:int, team_id, question_id: int, group_id:int,choice_id:int) -> bool:
    
    user_answers = TriviaGameUserAnswer.get_team_answers(game_id=game_id,team_id=team_id,question_id=question_id,group_id=group_id)
    team_members = TeamMember.objects.filter(team__id=team_id)
    if not len(user_answers)>(len(team_members)/2):
        return False

    answer = TriviaGameTeamAnswer.objects.filter(game__id=game_id,team__id=team_id,question__id=question_id,group__id=group_id)
    if len(answer)==0:
        answer = TriviaGameTeamAnswer()
        answer.game = TriviaGame.objects.get(id=game_id)
        answer.team = TriviaGameTeams.objects.get(id=team_id)
        answer.question = TriviaGameQuestions.objects.get(id=question_id)
        answer.group = TriviaQuestionChoiceGroup.objects.get(id=group_id)
    else:
        answer = answer[0]

    answers = {}
    for a in user_answers:
        if a.id not in answers:
            answers[a.id] = [a,1]
        else:
            answers[a.id][1] += 1
        
    consensus = [None,None]
    for a in answers:
        if consensus[1]==None or answers[a][1]>consensus[1]:
            consensus[0]=answers[a][0]
            consensus[1]=answers[a][1]
    
    answer.answer=consensus[0].answer
    answer.save()

    return True

def get_round_results(game_id:int, round_ind:int, team_id:int = None):
    results = []
    if team_id == None:
        result = {}
        teams = TriviaGameTeams.objects.filter(game__id=game_id)
        for team in teams:
            result = get_round_result(team_id)
    else:
        result = get_round_result(game_id,round_ind,team_id)
        results.append(result)

    return results

def get_round_result(game_id:int, round_ind:int, team_id:int):

    questions = TriviaGameQuestions.objects.filter(game__id=game_id,round=round_ind)
    
    users = {}
    team_users = TeamMember.objects.filter(game__id=game_id,team__id=team_id)
    for user in team_users:
        users[user.id] = {}
        users[user.id]={'answers':{},'points':0}
        users[user.id]['user']={'id':user.id,'user_name':user.user.user_name}
        for question in questions:
            users[user.id]['answers'][question.id]={}
            users[user.id]['answers'][question.id]['id'] = question.id
            users[user.id]['answers'][question.id]['value'] = get_user_answer(game_id,user.id,question.id)
            users[user.id]['answers'][question.id]['answer'] = question.question.answer
            users[user.id]['answers'][question.id]['is_correct'] = users[user.id]['answers'][question.id]['value'] == users[user.id]['answers'][question.id]['answer']
            if users[user.id]['answers'][question.id]['is_correct']:
                users[user.id]['points'] += 1

    team_answers = TriviaGameTeamAnswer.objects.filter(game__id=game_id,team__id=team_id,question__round=round_ind)
    team = {'answers':{},'points':0}
    for question in questions:
        team['answers'][question.id]={}
        team['answers'][question.id]['id'] = question.id
        team['answers'][question.id]['index'] = question.index
        team['answers'][question.id]['value'] = get_team_answer(game_id,team_id,question.id)
        team['answers'][question.id]['answer'] = question.question.answer
        team['answers'][question.id]['is_correct'] = team['answers'][question.id]['value'] == team['answers'][question.id]['answer']
        if team['answers'][question.id]['is_correct']:
            team['points'] += 1

    result = {}
    result['GameId'] = game_id
    result['Team'] = {}
    result['Team']['Id'] = team_id
    result['Team']['Rank'] = '?'
    result['Team']['Points'] = team['points']
    result['Team']['Users'] = [{'Id':id,'Name':users[id]['user']['user_name'],'Points':users[id]['points']} for id in users.keys()]
    result['Team']['Questions'] = {}
    # result['Team']['Users'] = [{'Id':3,'Name':"Jeff",'Points':6},{'Id':4,'Name':"James",'Points':2},{'Id':5,'Name':"John",'Points':12}]
    #  = {'id':id for id in team['answers'].keys()}
    for i,key in enumerate(team['answers'].keys()):
        result['Team']['Questions'][key] = {}
        result['Team']['Questions'][key] = {'id':key,'IsCorrect':team['answers'][key]['is_correct'],'Index':team['answers'][key]['index']}

    return result

def get_final_results(game_id:int,team_id:int=None):
    pass

def get_final_result(game_id:int,team_id:int):
    pass

def get_questions(game_id):
    questions = []
    q = [q for q in TriviaGameQuestions.objects.filter(game__id=game_id)]
    for item in q:
        value = get_question(question_id=item.id)
        questions.append(value)
    return questions

def get_question(game_id:int=None, ind:int= None, question_id:int=None):
    if game_id==None and ind==None and question_id == None:
        return None
    
    question = None

    if game_id!=None and ind!=None:
        question = TriviaGameQuestions.objects.filter(game__id=game_id, index=ind)
        if len(question)==1:
            question=question[0]
        else:
            return None
    elif question_id!=None:
        question = TriviaGameQuestions.objects.get(id=question_id)
    
    if question == None:
        return None

    value = {}
    value['id']=question.id
    value['question']=question.question.question
    value['answer']=question.question.answer
    value['groups'] = []
    groups = TriviaQuestionChoiceGroup.objects.filter(question__id=question.question.id)
    for i,group in enumerate(groups):
        _group = {}
        _group['id']=group.id
        _group['index'] = group.index
        _group['choices'] = [{'id':c.id, 'value':c.choice} for c in TriviaQuestionChoices.objects.filter(group__id=group.id)]
        value['groups'].append(_group)
    

    return value

def create_questions(game_id:int):
    game = get_game(game_id)

    create_question(game.id,0,"My mama always said life was like {}. You never know what you're gonna get.","My mama always said life was like a box of chocolates. You never know what you're gonna get.",[["a box of chocolates","peanut brittle","confused elves"]])
    create_question(game.id,1,"If you got rid of every {} with {}, then you'd have three {} left.","If you got rid of every cop with some sort of drink problem, then you'd have three cops left.",[['cop','moose','priest'],['some sort of drink problem','a pineapple on their head','a car in their garage'],['cops','moose','priests']])
    create_question(game.id,2,"Which of these is a type of computer?","Apple",[['Apple', 'Nectarine','Orange']])
    create_question(game.id,3,"What was the name of the first satellite sent to space?","Sputnik 1",[["Sputnik 1","Gallileo 1","Neo 3"]])
    create_question(game.id,4,"In which U.S. state was Tennessee Williams born?","Mississippi",[["Mississippi","Tenessee", "Alabama"]])


def create_question(game_id:int, index:int, question:str, answer:str, choices:list, round:int=1):
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
            choice = TriviaQuestionChoices()
            choice.choice=_choice
            choice.group = group
            choice.save()

    tq = TriviaGameQuestions()
    tq.game=game
    tq.index = index
    tq.question = q
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

            tgt = TriviaGameTeams()
            tgt.team = team
            tgt.game = game
            tgt.save()

            return tgt
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
    
    teams = TriviaGameTeams.objects.filter(game__id=game_id,id=team_id)

    if len(teams)>0:
        if len(teams)==1:
            return teams[0]
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
    