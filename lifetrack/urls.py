from django.urls import path
from lifetrack import views

app_name='lifetrack'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create/', views.create_habit, name='create_habit'),
    path('delete/<int:habit_id>/', views.delete_habit, name='delete_habit'),
    path('toggle/', views.toggle_habit, name='toggle_habit'),
]
