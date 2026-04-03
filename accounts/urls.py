from django.contrib import admin
from django.urls import path
from .views import google_login, google_callback

app_name = "accounts"
urlpatterns = [
    # ...

    path("google/login/", google_login, name="google_login"),
    path("google/callback/", google_callback, name="google_callback"),
]