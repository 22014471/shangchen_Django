from rest_framework import serializers

from .models import Areas


class AreasGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Areas
        fields = ("id", "name")


class AreasSubSerializer(serializers.ModelSerializer):
    subs = AreasGetSerializer(many=True, read_only=True)

    class Meta:
        model = Areas
        fields = ("id", "name", "subs")
