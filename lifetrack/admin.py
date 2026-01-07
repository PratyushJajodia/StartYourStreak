from django.contrib import admin

from .models import UserProfile, Habit, Occurence, Achievement, UserAchievement

admin.site.register(UserProfile)
admin.site.register(Habit)
admin.site.register(Occurence)
admin.site.register(Achievement)
admin.site.register(UserAchievement)
