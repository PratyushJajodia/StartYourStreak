from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Habit, Occurence
from .forms import UserForm # We might need to update forms.py too
from datetime import date, timedelta

def index(request):
    if request.user.is_authenticated:
        return redirect('lifetrack:dashboard')
    return render(request, 'lifetrack/landing.html')

def login_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(username=u, password=p)
        if user:
            auth_login(request, user)
            return redirect('lifetrack:dashboard')
        else:
            return render(request, 'lifetrack/login.html', {'error': 'Invalid credentials'})
    return render(request, 'lifetrack/login.html')

def signup_view(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.set_password(user.password)
            user.save()
            auth_login(request, user)
            return redirect('lifetrack:dashboard')
    else:
        form = UserForm()
    return render(request, 'lifetrack/signup.html', {'form': form})

def logout_view(request):
    auth_logout(request)
    return redirect('lifetrack:index')

@login_required
def dashboard(request):
    habits = Habit.objects.filter(user=request.user).order_by('-created_at')
    # Pre-calculate completion status for today to pass to template
    today = date.today()
    for h in habits:
        h.completed_today = Occurence.objects.filter(habit=h, date=today).exists()
    
    return render(request, 'lifetrack/dashboard.html', {'habits': habits})

@login_required
def create_habit(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Habit.objects.create(user=request.user, name=name)
        return redirect('lifetrack:dashboard')
    return render(request, 'lifetrack/create_habit.html')

@login_required
def delete_habit(request, habit_id):
    habit = get_object_or_404(Habit, id=habit_id, user=request.user)
    habit.delete()
    return redirect('lifetrack:dashboard')

@login_required
@require_POST
def toggle_habit(request):
    habit_id = request.POST.get('habit_id')
    habit = get_object_or_404(Habit, id=habit_id, user=request.user)
    today = date.today()
    
    occurrence, created = Occurence.objects.get_or_create(habit=habit, date=today)
    
    if not created:
        # If it already existed, we are toggling OFF
        occurrence.delete()
        completed = False
    else:
        # Toggled ON
        completed = True
        
    # Recalculate Streak
    # Simple algorithm: count consecutive days backwards from today (or yesterday)
    streak = 0
    check_date = today
    
    # 1. Check today's status
    if Occurence.objects.filter(habit=habit, date=today).exists():
        streak += 1
        check_date -= timedelta(days=1)
    elif Occurence.objects.filter(habit=habit, date=today - timedelta(days=1)).exists():
        # Allowed to continue streak if today is missed but yesterday was done (until midnight passes)
        # But for *current* value, if not done today, is streak broken? 
        # Usually streak counts completed days. If I haven't done it today, my streak is technically valid from yesterday.
        pass
    else:
        streak = 0
        
    # Walk backwards
    while True:
        if Occurence.objects.filter(habit=habit, date=check_date).exists():
             if check_date != today: # Avoid double counting if we started with today
                streak += 1
             check_date -= timedelta(days=1)
        else:
            break
            
    habit.current_streak = streak
    if streak > habit.longest_streak:
        habit.longest_streak = streak
    
    habit.last_completed_date = today if completed else (today - timedelta(days=1)) # Approx
    habit.save()

    return JsonResponse({'status': 'ok', 'completed': completed, 'streak': streak})
