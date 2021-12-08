from django.conf.urls import url
from django.urls import path
from .settings import MEDIA_ROOT
from . import views
from django.views.static import serve

urlpatterns = [
    path('login/', views.login),
    path('register/', views.register),
    path('home/', views.home),
]
