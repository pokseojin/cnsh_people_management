from django.urls import path
from . import views

urlpatterns = [
    path('', views.cnsh_map),
]