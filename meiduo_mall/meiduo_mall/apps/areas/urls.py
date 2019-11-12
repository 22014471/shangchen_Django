from django.conf.urls import url
from rest_framework import routers

from . import views

urlpatterns = [
]

router = routers.DefaultRouter()
router.register('areas', views.AreasView, base_name="areas")
urlpatterns += router.urls