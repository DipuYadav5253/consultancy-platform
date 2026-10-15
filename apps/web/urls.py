from django.urls import path

from . import views

app_name = "web"

urlpatterns = [
    path("", views.home, name="home"),
    path("study/", views.country_list, name="country_list"),
    path("study/<slug:slug>/", views.country_detail, name="country_detail"),
    path("programs/", views.program_list, name="program_list"),
    path("programs/<slug:slug>/", views.program_detail, name="program_detail"),
    path("book/", views.book, name="book"),
    path("robots.txt", views.robots, name="robots"),
]
