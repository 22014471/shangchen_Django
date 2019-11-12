from django.shortcuts import render
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_extensions.cache.mixins import CacheResponseMixin

from . import seializers
from .models import Areas
# Create your views here.


class AreasView(CacheResponseMixin, ReadOnlyModelViewSet):
    def get_serializer_class(self):
        if self.action == "list":
            return seializers.AreasGetSerializer
        else:
            return seializers.AreasSubSerializer

    def get_queryset(self):
        if self.action == "list":
            return Areas.objects.filter(parent=None)
        else:
            return Areas.objects.all()
