from django.urls import path
from home import views

urlpatterns = [
    path("", views.index, name="index"),
    path("self/", views.self, name="self"),
    path("SE/", views.SE, name="SE"),
    path("CS/", views.CS, name="CS"),
]