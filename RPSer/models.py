from django.db import models
from django.db.models import Q, Sum
from django.core.exceptions import ObjectDoesNotExist

# in views can say <new_inst> = Name.objects.create(<field>=<new data>) to make new instance of Name called <new_inst>
# say <new_inst>.save() to save to database
# can say <Name>.objects.all() to get list of all <Name> objects (i.e. list of all names in Name) 

class User(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=256)
    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    w_l = models.DecimalField(max_digits=4, decimal_places=3, default=0)
    count = models.PositiveIntegerField(default=0)
    
    objects = models.Manager() # default

    class Meta:
        indexes = [
            models.Index(fields=['id', 'username', 'w_l', 'count']),
        ]

#    def __init__(self, id, username, wins, losses, w_l, count, *args, **kwargs):
#        super(User, self).__init__(*args, **kwargs)
#        self.id = id
#        self.username = username
#        self.wins = wins
#        self.losses = losses
#        self.w_l = w_l
#        self.count = count

    def __str__(self):
        return f'{self.id}, {self.username}'

   
class RackBrain(models.Manager):
    def scoreboard(self, user):
        # method for use with Brain like: Brain.objects.scoreboard("kchatman")
        scores = dict()
        try:
            scores["userwins"] = super().get_queryset().filter(Q(userid=user) & ((Q(rpser_last='R') & Q(user_last='P')) |
                (Q(rpser_last='P') & Q(user_last='S')) |
                (Q(rpser_last='S') & Q(user_last='R')))).aggregate(Sum('count'))
        except:
            scores["userwins"] = 0
        try:
            scores["RPSerwins"] = super().get_queryset().filter(Q(userid=user) & ((Q(rpser_last='R') & Q(user_last='S')) |
                (Q(rpser_last='P') & Q(user_last='R')) |
                (Q(rpser_last='S') & Q(user_last='P')))).aggregate(Sum('count'))
        except:    
            scores["RPSerwins"] = 0
        try:
            scores["draws"] = super().get_queryset().filter(Q(userid=user) & ((Q(rpser_last='R') & Q(user_last='R')) |
                (Q(rpser_last='P') & Q(user_last='P')) |
                (Q(rpser_last='S') & Q(user_last='S')))).aggregate(Sum('count'))
        except:
            scores["draws"] = 0
        return scores
    
    def check_xp(self, state):
        # given dict state = {userid, rpser_last, user_last} return data about past experience
        # use like Brain.opjects.check_xp(state) where state is dict with "username", "rpser_last", and "user_last"
        data = dict()
        try:
            options = super().get_queryset().filter(
                Q(userid=state["userid"]) & Q(rpser_last=state["rpser_last"]) & 
                Q(user_last=state["user_last"]))
            for throw in ["R", "P", "S"]:
                try:
                    throw_option = options.get(userid=state["userid"], rpser_last=state["rpser_last"], 
                        user_last=state["user_last"], rpser_next=throw)
                    data[throw] = dict(score = throw_option.score, count = throw_option.count)
                except ObjectDoesNotExist:
                    data[throw] = dict(score = 0, count = 0)   
        except ObjectDoesNotExist:
            for throw in ["R", "P", "S"]:
                data[throw] = dict(score = 0, count = 0)
        return data

class Brain(models.Model):
    id = models.AutoField(primary_key=True)
    userid = models.ForeignKey(User, on_delete=models.CASCADE)
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
        unique_together = ('userid', 'rpser_last', 'user_last', 'rpser_next')
        indexes = [
            models.Index(fields=['userid', 'rpser_last', 'user_last']),
        ]
    count = models.PositiveIntegerField(default=0)
    score = models.IntegerField(default=0)

    objects = models.Manager() # default
    rackbrain_objects = RackBrain() # custom manager defined above

    def __str__(self):
        return f'{self.id}, {self.rpser_last}, {self.user_last}, {self.rpser_next}, count = {self.count}, score = {self.score}'