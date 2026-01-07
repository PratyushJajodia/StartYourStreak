import os

file_path = r"c:\Completed Project\Streak_App\lifetrack\lifetrack\migrations\0003_achievement_habit_category_habit_description_and_more.py"

try:
    with open(file_path, 'r') as f:
        print(f.read())
except Exception as e:
    print(f"Error reading file: {e}")
