from django.urls import path
from home import views
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(url='https://etoitau.github.io/home/index.html'), name="index"),
    path("self/", RedirectView.as_view(url='https://etoitau.github.io/home/self.html'), name="self"),
    path("SE/", RedirectView.as_view(url='https://etoitau.github.io/home/SE.html'), name="SE"),
    path("CS/", RedirectView.as_view(url='https://etoitau.github.io/home/CS.html'), name="CS"),
]