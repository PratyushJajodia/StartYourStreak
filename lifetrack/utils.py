from math import floor

def calculate_xp_gain(habit, streak):
    """
    Calculate XP based on habit difficulty and current streak.
    """
    base_xp = 10
    
    difficulty_multiplier = 1.0
    if habit.difficulty == 'EASY':
        difficulty_multiplier = 1.0
    elif habit.difficulty == 'MEDIUM':
        difficulty_multiplier = 1.5
    elif habit.difficulty == 'HARD':
        difficulty_multiplier = 2.0
        
    # Streak bonus: e.g., +10% per 5 days, capped at 2x
    streak_bonus = min(1.0 + (streak // 5) * 0.1, 2.0)
    
    total_xp = int(base_xp * difficulty_multiplier * streak_bonus)
    return total_xp

def check_level_up(user_profile):
    """
    Check if user should level up based on current XP.
    Formula: Level N requires 100 * N^1.5 XP (cumulative)
    """
    current_xp = user_profile.xp
    current_level = user_profile.level
    
    # Calculate XP required for NEXT level
    next_level = current_level + 1
    required_xp = int(100 * (next_level ** 1.5))
    
    leveled_up = False
    while current_xp >= required_xp:
        user_profile.level += 1
        current_level += 1
        # Deduct? Or is XP cumulative? 
        # Usually XP is cumulative total. 
        # If cumulative, we check total require against total XP.
        # Let's adjust formula: Total XP for Level N = 100 * (N-1)^1.5 ?
        # Simpler: Total XP to REACH level N. 
        # Let's stick to: XP is total earned. Threshold for Level N is 100 * (N-1)^1.5.
        
        next_level = current_level + 1
        required_xp = int(100 * (next_level ** 1.5)) # Threshold for NEXT level
        leveled_up = True
        
    
    if leveled_up:
        user_profile.save()
        return True, user_profile.level
    
    return False, current_level

def xp_for_next_level(level):
    return int(100 * ((level + 1) ** 1.5))

def check_achievements(user, habit, streak):
    """
    Check and award achievements based on recent activity.
    Returns a list of UserAchievement objects (newly unlocked).
    """
    from .models import Achievement, UserAchievement, Occurence, Habit
    
    unlocked = []
    
    # Get all achievements user DOESN'T have yet
    earned_ids = UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)
    potential_achievements = Achievement.objects.exclude(id__in=earned_ids)
    
    for ach in potential_achievements:
        awarded = False
        
        if ach.condition_type == 'STREAK':
            # Check if this specific habit has reached the streak
            # Or if ANY habit has (usually simpler to check the current one triggering)
            if streak >= ach.threshold:
                awarded = True
                
        elif ach.condition_type == 'TOTAL_COMPLETIONS':
            # Count total completions for user
            # This can be expensive, maybe prefer a cached count in profile
            total = user.profile.total_habits_completed
            if total >= ach.threshold:
                awarded = True
        
        elif ach.condition_type == 'LEVEL':
            if user.profile.level >= ach.threshold:
                awarded = True
                
        elif ach.condition_type == 'HABIT_COUNT':
            count = Habit.objects.filter(user=user).count()
            if count >= ach.threshold:
                awarded = True
                
        if awarded:
            ua = UserAchievement.objects.create(user=user, achievement=ach)
            unlocked.append(ach)
            # Finders keepers: Add XP reward
            user.profile.xp += ach.xp_reward
            user.profile.save()
            
    return unlocked
