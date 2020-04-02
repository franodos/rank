from rest_framework import serializers
from grade.models import Client
from django.core.validators import MinValueValidator, MaxValueValidator


class ClientSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    number = serializers.IntegerField(validators=[MinValueValidator(0)])
    grade = serializers.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10000000)])

    def create(self, validated_data):
        return Client.objects.create(**validated_data)




