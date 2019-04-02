from django.urls import path
from RPSer import views
from django.contrib.auth.views import LoginView, LogoutView


urlpatterns = [
    path("", views.rpser, name="rpser"),
    path("signup/", views.signup, name="signup"),
    path('logxp/', views.logxp, name="logxp"),
    #path('getscores/', views.getscores, name="getscores"),
    path('getthrow/', views.getthrow, name="getthrow"),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('login/', LoginView.as_view(template_name='RPSer/login.html'), name='login'),
    path('logout/', LogoutView.as_view(template_name='RPSer/logout.html'), name='logout'),
    
]