from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Habit, Occurence, UserProfile, Achievement, UserAchievement
from .utils import calculate_xp_gain, check_level_up, check_achievements
from .forms import UserForm
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
    
    xp_gained = 0
    leveled_up = False
    new_level = request.user.profile.level
    unlocked_achievements = []
    
    if not created:
        # If it already existed, we are toggling OFF
        # Revoke XP and Tokens
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.xp = max(0, profile.xp - occurrence.xp_gained) # Prevent negative XP?
        
        if occurrence.token_earned:
             profile.freeze_tokens = max(0, profile.freeze_tokens - 1)
             
        profile.save()
        
        occurrence.delete()
        completed = False
    else:
        # Toggled ON
        completed = True
        
    # Recalculate Streak (Existing Logic)
    streak = 0
    check_date = today
    
    if Occurence.objects.filter(habit=habit, date=today).exists():
        streak += 1
        check_date -= timedelta(days=1)
    elif Occurence.objects.filter(habit=habit, date=today - timedelta(days=1)).exists():
        check_date = today - timedelta(days=1)
    else:
        streak = 0
        
    while True:
        if Occurence.objects.filter(habit=habit, date=check_date).exists():
             if check_date != today: 
                streak += 1
             check_date -= timedelta(days=1)
        else:
            break
            
    habit.current_streak = streak
    if streak > habit.longest_streak:
        habit.longest_streak = streak
    
    habit.last_completed_date = today if completed else (today - timedelta(days=1))
    habit.save()

    # --- Gamification Logic ---
    if completed:
        # Ensure profile exists (safeguard for existing users)
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        
        xp_gained = calculate_xp_gain(habit, streak)
        profile.xp += xp_gained
        
        # Check for Freeze Token (Every 7 days)
        if streak > 0 and streak % 7 == 0:
             profile.freeze_tokens += 1
             occurrence.token_earned = True
        
        # Log it in occurrence
        occurrence.xp_gained = xp_gained
        occurrence.save()
        
        leveled_up, new_level = check_level_up(profile)
        profile.save() # check_level_up saves, but ensure XP is saved
        
        unlocked_achievements_objs = check_achievements(request.user, habit, streak)
        unlocked_achievements = [a.name for a in unlocked_achievements_objs]

    return JsonResponse({
        'status': 'ok', 
        'completed': completed, 
        'streak': streak,
        'longest_streak': habit.longest_streak,
        'xp_gained': xp_gained,
        'leveled_up': leveled_up,
        'new_level': new_level,
        'unlocked_achievements': unlocked_achievements
    })

@login_required
def achievements(request):
    all_achievements = Achievement.objects.all().order_by('xp_reward')
    # Optimized query: Get IDs of earned achievements
    earned_ids = UserAchievement.objects.filter(user=request.user).values_list('achievement_id', flat=True)
    
    context = {
        'all_achievements': all_achievements,
        'earned_ids': set(earned_ids) # Set for O(1) lookup in template
    }
    return render(request, 'lifetrack/achievements.html', context)
