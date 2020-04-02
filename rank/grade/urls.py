from django.urls import path
from grade import views


urlpatterns = [
    path('client/', views.ClientView.as_view()),
    path('rank/', views.RankView.as_view()),
]