from django.db import models
from django.contrib.auth.models import User
from datetime import date

class Habit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    # Streak Tracking
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_completed_date = models.DateField(null=True, blank=True)
    
    # Notification
    reminder_time = models.TimeField(null=True, blank=True)
    
    created_at = models.DateField(default=date.today)

    def __str__(self):
        return f"{self.name} ({self.user.username})"

class Occurence(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE)
    date = models.DateField(default=date.today)
    
    class Meta:
        unique_together = ('habit', 'date')

    def __str__(self):
        return f'{self.habit.name} @ {self.date}'
