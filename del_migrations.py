import os

files = [
    r"c:\Completed Project\Streak_App\lifetrack\lifetrack\migrations\0001_initial.py",
    r"c:\Completed Project\Streak_App\lifetrack\lifetrack\migrations\0002_remove_habit_list_rename_sdate_habit_created_at_and_more.py",
    r"c:\Completed Project\Streak_App\lifetrack\lifetrack\migrations\0003_achievement_habit_category_habit_description_and_more.py",
    r"c:\Completed Project\Streak_App\lifetrack\lifetrack\migrations\0004_occurence_token_earned.py"
]

for f in files:
    try:
        if os.path.exists(f):
            os.remove(f)
            print(f"Deleted {f}")
        else:
            print(f"File not found: {f}")
    except Exception as e:
        print(f"Error deleting {f}: {e}")
