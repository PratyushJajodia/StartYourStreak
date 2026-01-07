from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Habit, Occurence
from datetime import date, timedelta

from django.urls import reverse

class StreakTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client = Client()
        self.client.login(username='testuser', password='password')
        self.habit = Habit.objects.create(user=self.user, name="Test Habit")
        self.url = reverse('lifetrack:toggle_habit')

    def test_streak_increment_and_decrement(self):
        # 1. Create a streak of 2 days ending yesterday
        today = date.today()
        yesterday = today - timedelta(days=1)
        day_before = today - timedelta(days=2)
        
        Occurence.objects.create(habit=self.habit, date=yesterday)
        Occurence.objects.create(habit=self.habit, date=day_before)
        
        # Verify initial streak calculation (should happen on toggle or we can trigger it)
        # Let's hit the toggle endpoint to "refresh" or just checking manually?
        # The streak is only updated in the toggle view currently.
        # So let's simulate a toggle for "today".
        
        # 2. Toggle "today" to ON
        response = self.client.post(self.url, {'habit_id': self.habit.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['completed'], True)
        self.assertEqual(response.json()['streak'], 3) # 2 past days + today
        self.assertIn('longest_streak', response.json())
        self.assertEqual(response.json()['longest_streak'], 3)
        
        self.habit.refresh_from_db()
        self.assertEqual(self.habit.current_streak, 3)
        
        # 3. Toggle "today" to OFF (Reproduction of bug)
        # This occurs when user unchecked the habit
        response = self.client.post(self.url, {'habit_id': self.habit.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['completed'], False)
        
        # Expectation: Streak should be 2 (yesterday + day_before)
        # Bug behavior: It returns 0
        self.assertEqual(response.json()['streak'], 2, "Streak should revert to previous value (2) when unchecked")
        
        self.habit.refresh_from_db()
        self.assertEqual(self.habit.current_streak, 2)
