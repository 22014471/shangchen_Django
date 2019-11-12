from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^qq/authorization/$", views.OAuthQQView.as_view()),
    url(r"^qq/user/$", views.AuthUserView.as_view()),
]