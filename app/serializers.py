from rest_framework import serializers
from .models import ClaseHorario

class ClaseConflictoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    seccion = serializers.CharField()
    profesor = serializers.CharField()
    asignatura = serializers.CharField()
    horario = serializers.CharField()


class DatosClaseSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    multiple = serializers.BooleanField()

    # Caso una sola actividad
    seccion = serializers.CharField(required=False)
    profesor = serializers.CharField(required=False)
    asignatura = serializers.CharField(required=False)
    horario = serializers.CharField(required=False)
    numero_clase = serializers.IntegerField(required=False)
    hora_escaneo = serializers.CharField(required=False)

    # Caso múltiples actividades
    actividades = ClaseConflictoSerializer(many=True, required=False)

    fuera_horario = serializers.BooleanField(required=False)
