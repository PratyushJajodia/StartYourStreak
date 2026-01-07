from django.db import models
from django.contrib.auth.models import User
from datetime import date
from django.db.models.signals import post_save
from django.dispatch import receiver

# --- User Profile & Gamification ---

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    xp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    freeze_tokens = models.IntegerField(default=0)
    avatar_url = models.CharField(max_length=255, blank=True, null=True)
    
    # Quick Stats Cache (Optional but good for performance)
    total_habits_completed = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.username} - Lvl {self.level}"

# Signal to create UserProfile when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Achievement(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='trophy') # FontAwesome/Lucide class name
    xp_reward = models.IntegerField(default=50)
    
    # Logic fields
    condition_type = models.CharField(max_length=50, choices=[
        ('STREAK', 'Streak Reach'),
        ('TOTAL_COMPLETIONS', 'Total Completions'),
        ('LEVEL', 'Level Reach'),
        ('HABIT_COUNT', 'Habit Count Created')
    ]) 
    threshold = models.IntegerField(default=1)
    
    def __str__(self):
        return self.name

class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    date_earned = models.DateField(default=date.today)
    
    class Meta:
        unique_together = ('user', 'achievement')

    def __str__(self):
        return f"{self.user.username} earned {self.achievement.name}"


# --- Core Habit Models ---

class Habit(models.Model):
    DIFFICULTY_CHOICES = [
        ('EASY', 'Easy (1x XP)'),
        ('MEDIUM', 'Medium (1.5x XP)'),
        ('HARD', 'Hard (2x XP)'),
    ]
    
    FREQUENCY_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        # Can expand on this later
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, null=True) # New: Notes/Details about the habit
    
    # Gamification Config
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='MEDIUM')
    category = models.CharField(max_length=50, default='General') # e.g. Health, Coding, Mindfulness
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='DAILY')
    
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
    
    # New: Rich Logging
    notes = models.TextField(blank=True, null=True)
    mood = models.CharField(max_length=20, blank=True, null=True) # e.g., 'Happy', 'Tired'
    
    # XP Gained for this specific occurrence (Audit trail)
    xp_gained = models.IntegerField(default=0)
    token_earned = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('habit', 'date')

    def __str__(self):
        return f'{self.habit.name} @ {self.date}'

