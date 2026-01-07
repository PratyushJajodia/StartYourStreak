from django import forms
from django.contrib.auth.models import User
from lifetrack.models import Habit

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    class Meta:
        model = User
        fields = ('username', 'first_name', 'password')
        labels = {'first_name': 'Name'}

class HabitForm(forms.ModelForm):
    class Meta:
        model = Habit
        fields = ('name',)
