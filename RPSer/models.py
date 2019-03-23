from django.db import models
from django.db.models import Q, Sum
from django.core.exceptions import ObjectDoesNotExist

# in views can say <new_inst> = Name.objects.create(<field>=<new data>) to make new instance of Name called <new_inst>
# say <new_inst>.save() to save to database
# can say <Name>.objects.all() to get list of all <Name> objects (i.e. list of all names in Name) 

class User(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=256)
    
    def __str__(self):
        return f'{self.id}, {self.username}' 

class RackBrain(models.Manager):
    def scoreboard(self, user):
        # method for use with Brain like: Brain.objects.scoreboard("kchatman")
        scores = dict()
        scores["userwins"] = self.objects.filter(Q(username=user) & ((Q(rpser_last='R') & Q(user_last='P')) |
            (Q(rpser_last='P') & Q(user_last='S')) |
            (Q(rpser_last='S') & Q(user_last='R')))).aggregate(Sum('count'))
        scores["RPSerwins"] = self.objects.filter(Q(username=user) & ((Q(rpser_last='R') & Q(user_last='S')) |
            (Q(rpser_last='P') & Q(user_last='R')) |
            (Q(rpser_last='S') & Q(user_last='P')))).aggregate(Sum('count'))
        scores["draws"] = self.objects.filter(Q(username=user) & ((Q(rpser_last='R') & Q(user_last='R')) |
            (Q(rpser_last='P') & Q(user_last='P')) |
            (Q(rpser_last='S') & Q(user_last='S')))).aggregate(Sum('count'))
        return scores
    
    def check_xp(self, state):
        # given dict state = {username, rpser_last, user_last} return data about past experience
        # use like Brain.opjects.check_xp(state) where state is dict with "username", "rpser_last", and "user_last"
        data = dict()
        try:
            options = self.objects.filter(Q(username=state["username"] & 
                Q(rpser_last=state["rpser_last"]) & Q(user_last=state["user_last"])))
            for throw in ["R", "P", "S"]:
                try:
                    throw_option = options.objects.get(username=state["username"], rpser_last=state["rpser_last"], 
                        user_last=state["user_last"], rpser_next=[throw])
                    data[throw] = dict(score = throw_option["score"], count = throw_option["count"])
                except ObjectDoesNotExist:
                    data[throw] = dict(score = 0, count = 0)   
        except ObjectDoesNotExist:
            for throw in ["R", "P", "S"]:
                data[throw] = dict(score = 0, count = 0)

class Brain(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.ForeignKey(User, on_delete=models.CASCADE)
    THROW_CHOICES = (
        ('R', 'Rock'),
        ('P', 'Paper'),
        ('S', 'Scissors'),
        ('N', 'None'),
    )
    rpser_last = models.CharField(max_length=1, choices=THROW_CHOICES)
    user_last = models.CharField(max_length=1, choices=THROW_CHOICES)
    rpser_next = models.CharField(max_length=1, choices=THROW_CHOICES)
    class Meta:
        unique_together = ('id', 'rpser_last', 'user_last', 'rpser_next')
        indexes = [
            models.Index(fields=['username', 'rpser_last', 'user_last']),
        ]
    count = models.PositiveIntegerField(default=0)
    score = models.IntegerField(default=0)

    objects = RackBrain()

    def __str__(self):
        return f'{self.id}, {self.rpser_last}{self.user_last}, {self.rpser_next}, count = {self.count}, score = {self.score}'