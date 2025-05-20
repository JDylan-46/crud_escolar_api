from django.shortcuts import render
from django.db.models import *
from django.db import transaction
from crud_escolar_api.serializers import *
from crud_escolar_api.models import *
from rest_framework.authentication import BasicAuthentication, SessionAuthentication, TokenAuthentication
from rest_framework.generics import CreateAPIView, DestroyAPIView, UpdateAPIView
from rest_framework import permissions
from rest_framework import generics
from rest_framework import status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from rest_framework import viewsets
from django.shortcuts import get_object_or_404
from django.core import serializers
from django.utils.html import strip_tags
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from datetime import datetime
from django.conf import settings
from django.template.loader import render_to_string
import string
import random
import json

class EventosAll(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = EventosSerializer

    def get_queryset(self):
        return Eventos.objects.order_by("id")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        lista = self.get_serializer(queryset, many=True).data
        # Convierte publico_json de string a array
        for evento in lista:
            try:
                evento["publico_json"] = json.loads(evento["publico_json"])
            except Exception:
                evento["publico_json"] = []
        return Response(lista, 200)

class EventosView(generics.CreateAPIView):
    #permission_classes = (permissions.IsAuthenticated,)
    
    def get(self, request, *args, **kwargs):
        evento_obj = get_object_or_404(Eventos, id=request.GET.get("id"))
        evento = EventosSerializer(evento_obj, many=False).data

    # Decodificar JSON
        try:
            evento["publico_json"] = json.loads(evento["publico_json"])
        except Exception:
            evento["publico_json"] = []

        return Response(evento, 200)

    #Registrar nuevo evento
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        if isinstance(data.get("publico_json"), list):
            data["publico_json"] = json.dumps(data["publico_json"])

        responsable_user_id = data.get("responsable_user_id")
        responsable_rol = data.get("responsable_rol")
        nombre_responsable = ""

        if responsable_rol == "Maestro":
            maestro = Maestros.objects.filter(user_id=responsable_user_id).first()
            if maestro:
                nombre_responsable = f"{maestro.user.first_name} {maestro.user.last_name}"
        elif responsable_rol == "Administrador":
            admin = Administradores.objects.filter(user_id=responsable_user_id).first()
            if admin:
                nombre_responsable = f"{admin.user.first_name} {admin.user.last_name}"
        data["responsable"] = nombre_responsable
        data["responsable_user_id"] = responsable_user_id
        data["responsable_rol"] = responsable_rol

        even = EventosSerializer(data=data)
        if even.is_valid():
            evento = even.save()
            return Response({"evento_created_id": evento.id}, 201)
        return Response(even.errors, status=status.HTTP_400_BAD_REQUEST)

class EventosViewEdit(generics.CreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def put(self, request, *args, **kwargs):
        evento = get_object_or_404(Eventos, id=request.data["id"])
        evento.nombreEv = request.data["nombreEv"]
        evento.tipo_evento = request.data["tipo_evento"]
        evento.fecha_realizacion = request.data["fecha_realizacion"]
        evento.horaInicio = request.data["horaInicio"]
        evento.horaFin = request.data["horaFin"]
        evento.lugar = request.data["lugar"]
        responsable_user_id = request.data.get("responsable_user_id")
        responsable_rol = request.data.get("responsable_rol")
        nombre_responsable = ""

        if responsable_rol == "Maestro":
            maestro = Maestros.objects.filter(user_id=responsable_user_id).first()
            if maestro:
                nombre_responsable = f"{maestro.user.first_name} {maestro.user.last_name}"
        elif responsable_rol == "Administrador":
            admin = Administradores.objects.filter(user_id=responsable_user_id).first()
            if admin:
                nombre_responsable = f"{admin.user.first_name} {admin.user.last_name}"

        evento.responsable = nombre_responsable
        evento.responsable_user_id = responsable_user_id
        evento.responsable_rol = responsable_rol
        evento.publico_json = json.dumps(request.data["publico_json"])
        evento.programa_educativo = request.data["programa_educativo"]
        evento.descripcion_breve = request.data["descripcion_breve"]
        evento.cupo = request.data["cupo"]
        evento.save()
        
        even = EventosSerializer(evento, many=False).data

        return Response(even, 200)

    def delete(self, request, *args, **kwargs):
        profile = get_object_or_404(Eventos, id=request.GET.get("id"))
        try:
            profile.delete()
            return Response({"details": "Evento eliminado"}, 200)
        except Exception as e:
            return Response({"details": "Algo pasó al eliminar"}, 400)